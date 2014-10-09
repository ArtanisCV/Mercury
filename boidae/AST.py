__author__ = 'Artanis'


from Token import *


class AST:
    pass


class ExprAST(AST):
    """
    Base class for all expression nodes
    """

    pass


class NumberExprAST(ExprAST):
    """
    Expression class for numeric literals like "1.0"
    """

    def __init__(self, number):
        self.number = number

    def __str__(self):
        return str(self.number)


class VariableExprAST(ExprAST):
    """
    Expression class for referencing a variable like "a"
    """

    def __init__(self, identifier):
        self.identifier = identifier

    def __str__(self):
        return str(self.identifier)


class BinaryExprAST(ExprAST):
    """
    Expression class for a binary operator
    """

    def __init__(self, binop, lhs, rhs):
        self.op = binop
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return str(self.lhs) + str(self.op) + str(self.rhs)


class CallExprAST(ExprAST):
    """
    Expression class for function calls
    """

    def __init__(self, identifier, args):
        self.callee = identifier
        self.args = args

    def __str__(self):
        return str(self.callee) + "(" + ','.join([str(arg) for arg in self.args]) + ")"


class PrototypeAST(AST):
    """
    This class represents the "prototype" for a function,
    which captures its name, and its argument names (thus implicitly the number
    of arguments the function takes).
    """

    def __init__(self, identifier, args):
        self.identifier = identifier
        self.args = args

    def __str__(self):
        return str(self.identifier) + "(" + ' '.join([str(arg) for arg in self.args]) + ")"


class FunctionAST(AST):
    """
    This class represents a function definition itself
    """

    def __init__(self, prototype, expr):
        self.prototype = prototype
        self.body = expr

    def __str__(self):
        return str(self.prototype) + " " + str(self.body)


class BinopPrecedence(object):
    precedence = {
        '<': 10, '+': 20, '-': 20, '*': 40
    }

    @staticmethod
    def get_precedence(binop):
        if not isinstance(binop, BinOpToken):
            return -1

        return BinopPrecedence.precedence[binop.name]


class ParseError(Exception):
    pass
