__author__ = 'Artanis'


from llvm.core import *
from Error import *
from Node import *


class Analyzer(object):
    def __init__(self):
        # The LLVM module, which holds all the IR code.
        self.llvm_module = Module.new("jit")

        # The LLVM instruction builder. Created whenever a new function is entered.
        self.llvm_builder = None

        # A dictionary that keeps track of which values are defined in the current scope
        # and what their LLVM representation is.
        self.named_values = {}

    def redo(self):
        self.llvm_module = Module.new("jit")
        self.llvm_builder = None
        self.named_values = {}

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

    def gen_variable_expr(self, variable_expr):
        if variable_expr.name in self.named_values:
            return self.named_values[variable_expr.name]
        else:
            raise UndefinedVariable(variable_expr)

    def gen_binary_expr(self, node):
        lhs = self.generate(node.lhs)
        rhs = self.generate(node.rhs)

        if node.op == '+':
            return self.llvm_builder.fadd(lhs, rhs, 'add')
        elif node.op == '-':
            return self.llvm_builder.fsub(lhs, rhs, 'sub')
        elif node.op == '*':
            return self.llvm_builder.fmul(lhs, rhs, 'mul')
        elif node.op == '<':
            res = self.llvm_builder.fcmp(FCMPEnum.FCMP_ULT, lhs, rhs, 'cmp')

            # convert bool 0 or 1 to double 0.0 or 1.0
            return self.llvm_builder.uitofp(res, Type.double(), 'bool')
        else:
            raise UndefinedOperator(node)

    def gen_call_expr(self, node):
        # look up the name in the global module table
        try:
            callee = self.llvm_module.get_function_named(node.callee)
        except llvm.LLVMException:
            raise UndefinedFunction(node)

        if len(callee.args) != len(node.args):
            raise MismatchedArgument(len(callee.args), node)

        args = [self.generate(arg) for arg in node.args]

        return self.llvm_builder.call(callee, args, 'call')

    def gen_prototype(self, node):
        function_type = Type.function(Type.double(), [Type.double()] * len(node.args), False)

        function = Function.new(self.llvm_module, function_type, node.name)

        if function.name != node.name:
            # if the name conflicted, there was already something with the same name
            function.delete()
            function = self.llvm_module.get_function_named(node.name)

            if not function.is_declaration:
                # if the function already has a body, don't allow redefinition or reextern
                raise RedefinedFunction(self)

            if len(function.args) != len(node.args):
                # if the function has a differnent number of args, reject
                raise MismatchedDeclaration(len(function.args), node)

        for arg, arg_name in zip(function.args, node.args):
            arg.name = arg_name

            # add arguments to variable symbol table
            self.named_values[arg.name] = arg

        return function

    def gen_function(self, node):
        # clear scope
        self.named_values.clear()

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
        except:
            raise

        return function

    def analyze(self, node_list):
        self.redo()

        for node in node_list:
            try:
                print self.generate(node)
            except BoidaeSemanticError as e:
                print e


if __name__ == "__main__":
    from Lexer import Lexer
    from Parser import Parser

    code = \
        """\
        4 + 5

        def foo(a b)
            a * a + 2 * a * b + b * b

        def bar(a)
            foo(a, 4.0) + bar(31337)

        extern cos(x)

        cos(1.234)\

        def error()
            x

        hello(x)
        """

    tokens = Lexer().tokenize(code)
    nodes = Parser().parse(tokens)[0]

    Analyzer().analyze(nodes)