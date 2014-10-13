__author__ = 'Artanis'


from llvm.core import *
from llvm.ee import *
from llvm.passes import *
from Error import *
from Node import *


load_library_permanently('./cio.lib')


class Analyzer(object):
    def __init__(self, parser):
        self.input = parser.parse()
        self.errors = []

        # The LLVM module, which holds all the IR code.
        self.llvm_module = Module.new("boidae")

        # The LLVM instruction builder. Created whenever a new function is entered.
        self.llvm_builder = None

        # A dictionary that keeps track of which values are defined in the current scope
        # and what their LLVM representation is.
        self.named_values = {}

        # The function optimization passes manager.
        self.llvm_pass_manager = FunctionPassManager.new(self.llvm_module)

        # The LLVM execution engine.
        self.llvm_executor = ExecutionEngine.new(self.llvm_module)

        # Set up the optimizer pipeline. Start with registering info about how the
        # target lays out data structures.
        self.llvm_pass_manager.add(self.llvm_executor.target_data)

        # Do simple "peephole" optimizations and bit-twiddling optimizations.
        self.llvm_pass_manager.add(PASS_INSTCOMBINE)

        # Reassociate expressions.
        self.llvm_pass_manager.add(PASS_REASSOCIATE)

        # Eliminate Common SubExpressions.
        self.llvm_pass_manager.add(PASS_GVN)

        # Simplify the control flow graph (deleting unreachable blocks, etc).
        self.llvm_pass_manager.add(PASS_SIMPLIFYCFG)

        self.llvm_pass_manager.initialize()

    def pop_sementic_errors(self):
        result = self.errors
        self.errors = []
        return result

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
        if node.name in self.named_values:
            return self.named_values[node.name]
        else:
            raise UndefinedVariable(node)

    def gen_binary_expr(self, node):
        lhs = self.generate(node.lhs)
        rhs = self.generate(node.rhs)

        if node.op_name == '+':
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
        entry_block = self.llvm_builder.basic_block
        header_block = function.append_basic_block('header')
        body_block = function.append_basic_block('body')
        after_block = function.append_basic_block('after')

        ###############
        # Entry Block #
        ###############

        begin_value = self.generate(node.begin)

        self.llvm_builder.branch(header_block)

        ################
        # Header Block #
        ################

        self.llvm_builder.position_at_end(header_block)

        variable_phi = self.llvm_builder.phi(Type.double(), node.variable_name)
        variable_phi.add_incoming(begin_value, entry_block)

        # Within the loop, the variable is defined equal to the PHI node. If it
        # shadows an existing variable, we have to restore it, so save it now.
        old_value = self.named_values.get(node.variable_name, None)
        self.named_values[node.variable_name] = variable_phi

        end_condition = self.generate(node.end)
        end_condition = self.llvm_builder.fcmp(FCMPEnum.FCMP_ONE, end_condition,
                                               Constant.real(Type.double(), 0), 'cond')

        self.llvm_builder.cbranch(end_condition, body_block, after_block)

        ##############
        # Body Block #
        ##############

        self.llvm_builder.position_at_end(body_block)

        self.generate(node.body)

        step_value = Constant.real(Type.double(), 1) if node.step is None else self.generate(node.step)
        next_value = self.llvm_builder.fadd(variable_phi, step_value, 'next')

        self.llvm_builder.branch(header_block)

        body_block = self.llvm_builder.basic_block
        variable_phi.add_incoming(next_value, body_block)

        ###############
        # After Block #
        ###############

        self.llvm_builder.position_at_end(after_block)

        # restore the unshadowed variable
        if old_value is not None:
            self.named_values[node.variable_name] = old_value
        else:
            del self.named_values[node.variable_name]

        # always return 0.0
        return Constant.real(Type.double(), 0)

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

            # add arguments to variable symbol table
            self.named_values[arg.name] = arg

        return function

    def gen_function(self, node):
        # clear scope
        self.named_values.clear()

        try:
            previous = self.llvm_module.get_function_named(node.name)
        except llvm.LLVMException:
            previous = None

        # create a function object
        function = self.generate(node.prototype)

        # create a new basic block to start insertion into
        block = function.append_basic_block('entry')
        self.llvm_builder = Builder.new(block)

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
                self.errors.append(e)


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

        extern cos(x)
        cos(1.234)
        cos(1.234, 1.234)

        def identity() x
        def identity() error(x)
        def identity(x) x

        extern tan(a);
        def tan(a) c;
        def invoke() tan(1);

        def opt(x) (1+2+x)*(x+(1+2))

        def unary! (v)
           if v then
              0
           else
              1

        def binary> 10 (LHS RHS)
            RHS < LHS

        !0
        10 > 5

        extern putchard(x)
        for i = 0, i < 10, 2 in
            putchard(42)  # output a '*' (ASCII 42)
        putchard(10)  # output a newline (ASCII 10)
        """

    lexer = Lexer(Interpreter(code))
    parser = Parser(lexer)
    analyzer = Analyzer(parser)

    for node, result in analyzer.analyze():
        print "Result of '%s': %f" % (node, result)

    print

    for error in analyzer.pop_sementic_errors():
        print error

    print


def test_mandel():
    from Interpreter import Interpreter
    from Lexer import Lexer
    from Parser import Parser
    import sys

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
            mandelhelper(realstart, realstart + realmag * 78, realmag,
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

    lexer = Lexer(Interpreter(code))
    parser = Parser(lexer)
    analyzer = Analyzer(parser)

    for node, result in analyzer.analyze():
        print "Result of '%s': %f" % (node, result)
        sys.stdout.flush()

if __name__ == "__main__":
    test_mandel()

