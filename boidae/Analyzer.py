__author__ = 'Artanis'


from llvm.core import *
from llvm.ee import *
from llvm.passes import *
from Error import *
from Node import *


load_library_permanently('./cio.lib')


class Analyzer(object):
    def __init__(self, parser, error_handler=None):
        self.input = parser.parse()
        self.error_handler = error_handler

        # the LLVM module, which holds all the IR code
        self.llvm_module = Module.new("boidae")

        # the LLVM instruction builder. Created whenever a new function is entered
        self.llvm_builder = None

        # a dictionary that keeps track of which variables are defined in the current scope
        # and what their LLVM representation is
        self.named_variables = {}

        # the function optimization passes manager
        self.llvm_pass_manager = FunctionPassManager.new(self.llvm_module)

        # the LLVM execution engine
        self.llvm_executor = ExecutionEngine.new(self.llvm_module)

        # set up the optimizer pipeline
        # start with registering info about how the target lays out data structures
        self.llvm_pass_manager.add(self.llvm_executor.target_data)

        # do simple "peephole" optimizations and bit-twiddling optimizations
        self.llvm_pass_manager.add(PASS_INSTCOMBINE)

        # reassociate expressions
        self.llvm_pass_manager.add(PASS_REASSOCIATE)

        # eliminate common sub-expressions
        self.llvm_pass_manager.add(PASS_GVN)

        # simplify the control flow graph (deleting unreachable blocks, etc)
        self.llvm_pass_manager.add(PASS_SIMPLIFYCFG)

        # promote allocas to registers
        self.llvm_pass_manager.add(PASS_MEM2REG)

        self.llvm_pass_manager.initialize()

    def create_alloca(self, function, variable_name):
        """
        creates an alloca instruction in the entry block of the function
        """

        entry_block = function.entry_basic_block
        builder = Builder.new(entry_block)
        builder.position_at_beginning(entry_block)
        return builder.alloca(ty=Type.double(), name=variable_name)

    def generate(self, node):
        if isinstance(node, NumberExprNode):
            return self.gen_number_expr(node)
        elif isinstance(node, VariableExprNode):
            return self.gen_variable_expr(node)
        elif isinstance(node, BinaryExprNode):
            return self.gen_binary_expr(node)
        elif isinstance(node, CallExprNode):
            return self.gen_call_expr(node)
        elif isinstance(node, IfExprNode):
            return self.gen_if_expr(node)
        elif isinstance(node, ForExprNode):
            return self.gen_for_expr(node)
        elif isinstance(node, VarExprNode):
            return self.gen_var_expr(node)
        elif isinstance(node, UnaryExprNode):
            return self.gen_unary_expr(node)
        elif isinstance(node, PrototypeNode):
            return self.gen_prototype(node)
        elif isinstance(node, FunctionNode):
            return self.gen_function(node)
        else:
            raise RuntimeError("Unknown nodes")

    def gen_number_expr(self, node):
        return Constant.real(Type.double(), node.value)

    def gen_variable_expr(self, node):
        if node.name in self.named_variables:
            return self.llvm_builder.load(self.named_variables[node.name], node.name)
        else:
            raise UndefinedVariable(node)

    def gen_binary_expr(self, node):
        lhs = self.generate(node.lhs)
        rhs = self.generate(node.rhs)

        if node.op_name == '=':
            if not isinstance(node.lhs, VariableExprNode):
                raise InvalidAssignmentDestination(node.line)

            self.llvm_builder.store(rhs, self.named_variables[node.lhs.name])
            return rhs
        elif node.op_name == '+':
            return self.llvm_builder.fadd(lhs, rhs, 'add')
        elif node.op_name == '-':
            return self.llvm_builder.fsub(lhs, rhs, 'sub')
        elif node.op_name == '*':
            return self.llvm_builder.fmul(lhs, rhs, 'mul')
        elif node.op_name == '<':
            result = self.llvm_builder.fcmp(FCMPEnum.FCMP_ULT, lhs, rhs, 'cmp')

            # convert bool 0 or 1 to double 0.0 or 1.0
            return self.llvm_builder.uitofp(result, Type.double(), 'bool')
        else:
            try:
                callee = self.llvm_module.get_function_named('binary' + node.op_name)
                return self.llvm_builder.call(callee, [lhs, rhs], 'binop')
            except llvm.LLVMException:
                raise UndefinedOperator(node)

    def gen_call_expr(self, node):
        try:
            # look up the name in the global module table
            callee = self.llvm_module.get_function_named(node.name)
        except llvm.LLVMException:
            raise UndefinedFunction(node)

        if len(callee.args) != len(node.args):
            raise MismatchedArgument(len(callee.args), node)

        args = [self.generate(arg) for arg in node.args]

        return self.llvm_builder.call(callee, args, 'call')

    def gen_if_expr(self, node):
        condition = self.generate(node.condition)

        # convert condition to a bool by comparing equal to 0.0
        condition = self.llvm_builder.fcmp(FCMPEnum.FCMP_ONE, condition,
                                           Constant.real(Type.double(), 0), 'cond')

        function = self.llvm_builder.basic_block.function

        # create blocks for the then and else cases.
        then_block = function.append_basic_block('then')
        else_block = function.append_basic_block('else')
        merge_block = function.append_basic_block('merge')

        self.llvm_builder.cbranch(condition, then_block, else_block)

        # emit 'then' branch
        self.llvm_builder.position_at_end(then_block)
        true_value = self.generate(node.true)
        self.llvm_builder.branch(merge_block)

        # code generator of 'then' can change the current block;
        # update then_block for the PHI node
        then_block = self.llvm_builder.basic_block

        # emit 'else' branch
        self.llvm_builder.position_at_end(else_block)
        false_value = self.generate(node.false)
        self.llvm_builder.branch(merge_block)

        # code generator of 'else' can change the current block;
        # update else_block for the PHI node
        else_block = self.llvm_builder.basic_block

        self.llvm_builder.position_at_end(merge_block)
        phi = self.llvm_builder.phi(Type.double(), 'if')
        phi.add_incoming(true_value, then_block)
        phi.add_incoming(false_value, else_block)
        return phi

    def gen_for_expr(self, node):
        function = self.llvm_builder.basic_block.function
        header_block = function.append_basic_block('header')
        body_block = function.append_basic_block('body')
        after_block = function.append_basic_block('after')

        ###############
        # Entry Block #
        ###############

        variable = self.create_alloca(function, node.variable_name)
        begin_value = self.generate(node.begin)
        self.llvm_builder.store(begin_value, variable)

        # Within the loop, the variable is defined equal to the alloca. If it
        # shadows an existing variable, we have to restore it, so save it now.
        old_value = self.named_variables.get(node.variable_name, None)
        self.named_variables[node.variable_name] = variable

        self.llvm_builder.branch(header_block)

        ################
        # Header Block #
        ################

        self.llvm_builder.position_at_end(header_block)

        end_condition = self.generate(node.end)
        end_condition = self.llvm_builder.fcmp(FCMPEnum.FCMP_ONE, end_condition,
                                               Constant.real(Type.double(), 0), 'cond')

        self.llvm_builder.cbranch(end_condition, body_block, after_block)

        ##############
        # Body Block #
        ##############

        self.llvm_builder.position_at_end(body_block)

        self.generate(node.body)

        cur_value = self.llvm_builder.load(variable)
        step_value = Constant.real(Type.double(), 1) if node.step is None else self.generate(node.step)
        next_value = self.llvm_builder.fadd(cur_value, step_value, 'next')
        self.llvm_builder.store(next_value, variable)

        self.llvm_builder.branch(header_block)

        ###############
        # After Block #
        ###############

        self.llvm_builder.position_at_end(after_block)

        # restore the unshadowed variable
        if old_value is not None:
            self.named_variables[node.variable_name] = old_value
        else:
            del self.named_variables[node.variable_name]

        # always return 0.0
        return Constant.real(Type.double(), 0)

    def gen_var_expr(self, node):
        old_variables = {}
        function = self.llvm_builder.basic_block.function

        for var_name, expr in node.variable_names.iteritems():
            # emit the initializer before adding the variable to scope, this prevents
            # the initializer from referencing the variable itself, and permits stuff
            # like this:
            #  var a = 1 in
            #    var a = a in ...   # refers to outer 'a'
            if expr is not None:
                var_value = self.generate(expr)
            else:
                var_value = Constant.real(Type.double(), 0)

            variable = self.create_alloca(function, var_name)
            self.llvm_builder.store(var_value, variable)

            old_variables[var_name] = self.named_variables.get(var_name, None)
            self.named_variables[var_name] = variable

        body = self.generate(node.body)

        for var_name in node.variable_names:
            if old_variables[var_name] is not None:
                self.named_variables[var_name] = old_variables[var_name]
            else:
                del self.named_variables[var_name]

        return body

    def gen_unary_expr(self, node):
        operand = self.generate(node.operand)
        callee = self.llvm_module.get_function_named('unary' + node.op_name)
        return self.llvm_builder.call(callee, [operand], 'unop')

    def gen_prototype(self, node):
        function_type = Type.function(Type.double(), [Type.double()] * len(node.arg_names), False)

        try:
            function = Function.new(self.llvm_module, function_type, node.name)
        except llvm.LLVMException:
            # if the name conflicted, there was already something with the same name
            function = self.llvm_module.get_function_named(node.name)

            if not function.is_declaration:
                # if the function already has a body, don't allow redefinition or reextern
                raise RedefinedFunction(node)

            if len(function.args) != len(node.arg_names):
                # if the function has a differnent number of args, reject
                raise MismatchedDeclaration(len(function.args), node)

        for arg, arg_name in zip(function.args, node.arg_names):
            arg.name = arg_name

        return function

    def gen_function(self, node):
        # clear scope
        self.named_variables.clear()

        try:
            previous = self.llvm_module.get_function_named(node.name)
        except llvm.LLVMException:
            previous = None

        # create a function object
        function = self.generate(node.prototype)

        # create a new basic block to start insertion into
        block = function.append_basic_block('entry')
        self.llvm_builder = Builder.new(block)

        # add arguments to variable symbol table
        for arg in function.args:
            alloca = self.create_alloca(function, arg.name)
            self.llvm_builder.store(arg, alloca)
            self.named_variables[arg.name] = alloca

        try:
            return_value = self.generate(node.body)
            self.llvm_builder.ret(return_value)

            # validate the generated code, checking for consistency
            function.verify()

            # optimize the function
            self.llvm_pass_manager.run(function)
        except:
            if previous is None:
                # allow users to redefine a function that they incorrectly typed in before,
                # but don't remove a previously defined forward declaration
                function.delete()

            raise

        # if this is a binary / unary operator, install it
        if isinstance(node.prototype, BinOpPrototypeNode):
            op_name = node.prototype.op_name
            precedence = node.prototype.precedence
            OperatorManager.register_binop(op_name, precedence)
        elif isinstance(node.prototype, UnOpPrototypeNode):
            OperatorManager.register_unop(node.prototype.op_name)

        return function

    def analyze(self):
        for node in self.input:
            try:
                code = self.generate(node)

                if isinstance(node, TopLevelExpr):
                    result = self.llvm_executor.run_function(code, []).as_real(Type.double())
                    yield (node, result)
            except BoidaeSemanticError as e:
                if self.error_handler is not None:
                    self.error_handler(e)


def test_basic():
    from Interpreter import Interpreter
    from Lexer import Lexer
    from Parser import Parser

    code = \
        """\
        4 + 5

        def foo(a b) a * a + 2 * a * b + b * b
        def foo(a) a
        def foo(a b) a + b
        def bar(a) foo(a, 4.0) + bar(31337)
        foo(1, 2)

        extern cos(x)
        cos(1.234)
        cos(1.234, 1.234)

        def identity() x
        def identity() error(x)
        def identity(x) x

        extern tan(a);
        def tan(a) c;
        tan(1);

        def opt(x) (1 + 2 + x) * (x + (1 + 2))

        def unary! (v)
            if v then
                0
            else
                1
        !0

        def binary: 1 (x y)
            y

        extern flush()
        extern putchard(x)
        extern printd(x)
        def test(x)
            printd(x):
            putchard(32):  # ' '
            x = 4:
            printd(x):
            putchard(10):  # newline
            flush()
        test(123)

        def invalid(x)
            (x + 1) = 2

        1 = 2

        def fibr(x)
            if (x < 3) then
                1
            else
                fibr(x - 1) + fibr(x - 2)

        def fibi(x)
           var a = 1, b = 1, c in
           (for i = 2, i < x in
              c = a + b:
              a = b:
              b = c):
           b

        fibr(10)
        fibi(10)\
        """

    def error_handler(error):
        print error

    lexer = Lexer(Interpreter(code))
    parser = Parser(lexer, error_handler)
    analyzer = Analyzer(parser, error_handler)

    for node, result in analyzer.analyze():
        print "Result of '%s': %f" % (node, result)


def test_mandel():
    from Interpreter import Interpreter
    from Lexer import Lexer
    from Parser import Parser

    code = \
        """
        # low-precedence operator that ignores operands
        def binary: 1 (x y)
            y

        # logical unary not
        def unary!(v)
            if v then
                0
            else
                1

        # unary negate
        def unary-(v)
            0 - v

        # define > with the same precedence as <
        def binary> 10 (LHS RHS)
            RHS < LHS

        # binary logical or, which does not short circuit
        def binary| 5 (LHS RHS)
            if LHS then
                1
            else if RHS then
                1
            else
                0

        # binary logical and, which does not short circuit
        def binary& 6 (LHS RHS)
            if !LHS then
                0
            else
                !!RHS

        # define = with slightly lower precedence than relationals
        def binary= 9 (LHS RHS)
            !(LHS < RHS | LHS > RHS)

        extern putchard(char)

        def printdensity(d)
            if d > 8 then
                putchard(32)  # ' '
            else if d > 4 then
                putchard(46)  # '.'
            else if d > 2 then
                putchard(43)  # '+'
            else
                putchard(42)  # '*'

        # determine whether the specific location diverges
        # solve for z = z^2 + c in the complex plane
        def iterate(real imag iters creal cimag)
            if iters > 255 | (real * real + imag * imag > 4) then
                iters
            else
                iterate(real * real - imag * imag + creal,
                        2 * real * imag + cimag,
                        iters + 1, creal, cimag)

        # return the number of iterations required for the iteration to escape
        def getiternum(real imag)
            iterate(real, imag, 0, real, imag)

        # compute and plot the mandelbrot set with the specified 2 dimensional
        # range info
        def plotmandel(xmin xmax xstep ymin ymax ystep)
            for y = ymin, y < ymax, ystep in (
                (for x = xmin, x < xmax, xstep in
                     printdensity(getiternum(x, y))):
                putchard(10)  # newline
            )

        # this is a convenient helper function for plotting the mandelbrot set
        # from the specified position with the specified magnification
        def mandel(realstart imagstart realmag imagmag)
            plotmandel(realstart, realstart + realmag * 78, realmag,
                       imagstart, imagstart + imagmag * 40, imagmag)

        extern flush()

        mandel(-2.3, -1.3, 0.05, 0.07):
        flush()

        putchard(10):
        mandel(-2, -1, 0.02, 0.04):
        flush()

        putchard(10):
        mandel(-0.9, -1.4, 0.02, 0.03):
        flush()
        """

    def error_handler(error):
        print error

    lexer = Lexer(Interpreter(code))
    parser = Parser(lexer, error_handler)
    analyzer = Analyzer(parser, error_handler)

    for node, result in analyzer.analyze():
        print "Result of '%s': %f" % (node, result)


if __name__ == "__main__":
    from Interpreter import Interpreter
    from Lexer import Lexer
    from Parser import Parser

    def error_handler(error):
        print error

    lexer = Lexer(Interpreter())
    parser = Parser(lexer, error_handler)
    analyzer = Analyzer(parser, error_handler)

    for node, result in analyzer.analyze():
        print result

