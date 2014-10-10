__author__ = 'Artanis'


from Token import *


class Node:
    """
    Base class for all AST nodes
    """

    def __init__(self, line):
        self.__line = line

    @property
    def line(self):
        return self.__line


class ExprNode(Node):
    """
    Base class for all expression nodes
    """

    pass


class NumberExprNode(ExprNode):
    """
    Expression class for numeric literals like "1.0"
    """

    def __init__(self, number):
        ExprNode.__init__(self, number.line)

        self.__number = number

    @property
    def value(self):
        return self.__number.value

    def __str__(self):
        return str(self.__number)


class VariableExprNode(ExprNode):
    """
    Expression class for referencing a variable like "a"
    """

    def __init__(self, identifier):
        ExprNode.__init__(self, identifier.line)

        self.__identifier = identifier

    @property
    def name(self):
        return self.__identifier.name

    def __str__(self):
        return str(self.__identifier)


class BinaryExprNode(ExprNode):
    """
    Expression class for a binary operator
    """

    def __init__(self, binop, lhs, rhs):
        ExprNode.__init__(self, lhs.line)

        self.__op = binop
        self.__lhs = lhs
        self.__rhs = rhs

    @property
    def op(self):
        return self.__op.name

    @property
    def lhs(self):
        return self.__lhs

    @property
    def rhs(self):
        return self.__rhs

    def __str__(self):
        return str(self.__lhs) + str(self.__op) + str(self.__rhs)


class CallExprNode(ExprNode):
    """
    Expression class for function calls
    """

    def __init__(self, callee, args):
        ExprNode.__init__(self, callee.line)

        self.__callee = callee
        self.__args = args

    @property
    def callee(self):
        return self.__callee.name

    @property
    def args(self):
        return self.__args

    def __str__(self):
        return str(self.__callee) + "(" + ','.join([str(arg) for arg in self.__args]) + ")"


class PrototypeNode(Node):
    """
    This class represents the "prototype" for a function,
    which captures its name, and its argument names (thus implicitly the number
    of arguments the function takes).
    """

    def __init__(self, identifier, args):
        Node.__init__(self, identifier.line)

        self.__identifier = identifier
        self.__args = args

    @property
    def name(self):
        return self.__identifier.name

    @property
    def args(self):
        return [str(arg) for arg in self.__args]

    def __str__(self):
        return str(self.__identifier) + "(" + ' '.join([str(arg) for arg in self.__args]) + ")"


class FunctionNode(Node):
    """
    This class represents a function definition itself
    """

    def __init__(self, prototype, expr):
        Node.__init__(self, prototype.line)

        self.__prototype = prototype
        self.__body = expr

    @property
    def prototype(self):
        return self.__prototype

    @property
    def body(self):
        return self.__body

    def __str__(self):
        return str(self.__prototype) + " " + str(self.__body)


class BinopPrecedence(object):
    precedence = {
        '<': 10, '+': 20, '-': 20, '*': 40
    }

    @staticmethod
    def get_precedence(binop):
        if not isinstance(binop, BinOpToken):
            return -1

        return BinopPrecedence.precedence[binop.name]