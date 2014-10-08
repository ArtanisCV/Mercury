__author__ = 'Artanis'


class AST:
    pass


class Expr(AST):
    """
    Base class for all expression nodes
    """

    pass


class NumberExpr(Expr):
    """
    Expression class for numeric literals like "1.0"
    """

    def __init__(self, number_token):
        self.value = number_token.value

    def __str__(self):
        return str(self.value)


class VariableExpr(Expr):
    """
    Expression class for referencing a variable like "a"
    """

    def __init__(self, identifier_token):
        self.name = identifier_token.name

    def __str__(self):
        return self.name


class BinaryExpr(Expr):
    """
    Expression class for a binary operator
    """

    def __init__(self, binop, lhs, rhs):
        self.op = binop.name
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return str(self.lhs) + str(self.op) + str(self.rhs)


class CallExpr(Expr):
    """
    Expression class for function calls
    """

    def __init__(self, identifier, args):
        self.callee = identifier.name
        self.args = args

    def __str__(self):
        return self.callee + "(" + ','.join([str(arg) for arg in self.args]) + ")"


class Prototype(AST):
    """
    This class represents the "prototype" for a function,
    which captures its name, and its argument names (thus implicitly the number
    of arguments the function takes).
    """

    def __init__(self, identifier, args):
        self.name = identifier.name
        self.args = [arg.name for arg in args]

    def __str__(self):
        return self.name + "(" + ' '.join(self.args) + ")"


class Function(AST):
    """
    This class represents a function definition itself
    """

    def __init__(self, prototype, expr):
        self.prototype = prototype
        self.body = expr

    def __str__(self):
        return str(self.prototype) + " " + str(self.body)


class Unknown(AST):
    """
    This class represents an unknown token
    """

    def __init__(self, token):
        self.name = token.name

    def __str__(self):
        return self.name


class Error:
    """
    This class provides helper functions for error handling.
    """

    def __init__(self, msg):
        print "Error:", msg