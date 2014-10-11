__author__ = 'Artanis'


from llvm.core import *
from llvm.ee import *
from llvm.passes import *
from Error import *
from Node import *


class Analyzer(object):
    def __init__(self):
        self.redo()

    def redo(self):
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

    def generate(self, node):
        if isinstance(node, NumberExprNode):
            return self.gen_number_expr(node)
        elif isinstance(node, VariableExprNode):
            return self.gen_variable_expr(node)
        elif isinstance(node, BinaryExprNode):
            return self.gen_binary_expr(node)
        elif isinstance(node, CallExprNode):
            return self.gen_call_expr(node)
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
            raise UndefinedOperator(node)

    def gen_call_expr(self, node):
        # look up the name in the global module table
        try:
            callee = self.llvm_module.get_function_named(node.name)
        except llvm.LLVMException:
            raise UndefinedFunction(node)

        if len(callee.args) != len(node.args):
            raise MismatchedArgument(len(callee.args), node)

        args = [self.generate(arg) for arg in node.args]

        return self.llvm_builder.call(callee, args, 'call')

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

        return function

    def analyze(self, node_list):
        self.redo()

        for node in node_list:
            try:
                code = self.generate(node)

                if isinstance(node, TopLevelExpr):
                    result = self.llvm_executor.run_function(code, []).as_real(Type.double())
                    print "Result of '%s': %f" % (node, result)
            except BoidaeSemanticError as e:
                print e


if __name__ == "__main__":
    from Lexer import Lexer
    from Parser import Parser

    code = \
        """\
        4 + 5

        9 + 10

        def foo(a b)
            a * a + 2 * a * b + b * b

        def foo(a)
            a

        def foo(a b)
            a + b

        def bar(a)
            foo(a, 4.0) + bar(31337)

        extern cos(x)

        cos(1.234)

        cos(1.234, 1.234)

        def identity()
            x

        def identity()
            error(x)

        def identity(x)
            x

        extern tan(a);

        def tan(a) c;

        def invoke() tan(1);

        def opt(x) (1+2+x)*(x+(1+2))
        """

    tokens = Lexer().tokenize(code)
    nodes = Parser().parse(tokens)[0]
    Analyzer().analyze(nodes)