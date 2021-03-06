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
    def op_name(self):
        return self.__op.name

    @property
    def lhs(self):
        return self.__lhs

    @property
    def rhs(self):
        return self.__rhs

    def __str__(self):
        return str(self.__lhs) + " " + str(self.__op) + " " + str(self.__rhs)


class CallExprNode(ExprNode):
    """
    Expression class for function calls
    """

    def __init__(self, callee, args):
        ExprNode.__init__(self, callee.line)

        self.__callee = callee
        self.__args = args

    @property
    def name(self):
        return self.__callee.name

    @property
    def args(self):
        return self.__args

    def __str__(self):
        return str(self.__callee) + "(" + ", ".join([str(arg) for arg in self.__args]) + ")"


class IfExprNode(ExprNode):
    """
    Expression class for if/then/else
    """

    def __init__(self, condition, true, false):
        ExprNode.__init__(self, condition.line)

        self.__condition = condition
        self.__true = true
        self.__false = false

    @property
    def condition(self):
        return self.__condition

    @property
    def true(self):
        return self.__true

    @property
    def false(self):
        return self.__false

    def __str__(self):
        return "if %s then %s else %s" % (self.__condition, self.__true, self.__false)


class ForExprNode(ExprNode):
    """
    Expression class for for/in
    """

    def __init__(self, variable, begin, end, step, body):
        ExprNode.__init__(self, variable.line)

        self.__variable = variable
        self.__begin = begin
        self.__end = end
        self.__step = step
        self.__body = body

    @property
    def variable_name(self):
        return self.__variable.name

    @property
    def begin(self):
        return self.__begin

    @property
    def end(self):
        return self.__end

    @property
    def step(self):
        return self.__step

    @property
    def body(self):
        return self.__body

    def __str__(self):
        if self.__step is None:
            return "for %s = %s, %s in %s" % \
                   (self.__variable, self.__begin, self.__end, self.__body)
        else:
            return "for %s = %s, %s, %s in %s" % \
                   (self.__variable, self.__begin, self.__end, self.__step, self.__body)


class UnaryExprNode(ExprNode):
    """
    Expression class for a unary operator
    """

    def __init__(self, unop, operand):
        ExprNode.__init__(self, unop.line)

        self.__operator = unop
        self.__operand = operand

    @property
    def op_name(self):
        return self.__operator.name

    @property
    def operand(self):
        return self.__operand

    def __str__(self):
        return str(self.__operator) + str(self.__operand)


class VarExprNode(ExprNode):
    """
    Expression class for var/in
    """

    def __init__(self, variables, body):
        ExprNode.__init__(self, min([var.line for var in variables.keys()]))

        self.__variables = variables
        self.__body = body

    @property
    def variable_names(self):
        return dict([(var.name, expr) for var, expr in self.__variables.iteritems()])

    @property
    def body(self):
        return self.__body

    def __str__(self):
        var_list = []
        for var, expr in self.__variables.items():
            var_list.append("%s" % var if expr is None else "%s = %s" % (var, expr))

        return "var " + ", ".join(var_list) + " in " + str(self.__body)


class PrototypeNode(Node):
    """
    This class represents the "prototype" for a function,
    which captures its name, and its argument names (thus implicitly the number
    of arguments the function takes)
    """

    def __init__(self, identifier, args):
        Node.__init__(self, identifier.line)

        self.__identifier = identifier
        self.__args = args

    @property
    def name(self):
        return self.__identifier.name

    @property
    def arg_names(self):
        return [str(arg) for arg in self.__args]

    def __str__(self):
        return str(self.__identifier) + "(" + ' '.join([str(arg) for arg in self.__args]) + ")"


class BinOpPrototypeNode(PrototypeNode):
    """
    This class represents the "prototype" for a user-defined binary operator
    """

    def __init__(self, identifier, precedence, args):
        assert len(args) == 2
        PrototypeNode.__init__(self, identifier, args)

        self.__precedence = precedence

    @property
    def op_name(self):
        return self.name[-1]

    @property
    def precedence(self):
        return 0 if self.__precedence is None else int(self.__precedence.name)

    def __str__(self):
        return str(self.name) + " " + str(self.precedence) + " (" + \
               ' '.join([arg_name for arg_name in self.arg_names]) + ")"


class UnOpPrototypeNode(PrototypeNode):
    """
    This class represents the "prototype" for a user-defined unary operator
    """

    def __init__(self, identifier, args):
        assert len(args) == 1
        PrototypeNode.__init__(self, identifier, args)

    @property
    def op_name(self):
        return self.name[-1]

    def __str__(self):
        return str(self.name) + " (" + ' '.join([arg_name for arg_name in self.arg_names]) + ")"


class FunctionNode(Node):
    """
    This class represents a function definition
    """

    def __init__(self, prototype, expr):
        Node.__init__(self, prototype.line)

        self.__prototype = prototype
        self.__body = expr

    @property
    def name(self):
        return self.__prototype.name

    @property
    def prototype(self):
        return self.__prototype

    @property
    def body(self):
        return self.__body

    def __str__(self):
        return str(self.__prototype) + " " + str(self.__body)


class TopLevelExpr(FunctionNode):
    """
    This class represents a top-level expression
    """

    def __init__(self, expr):
        # make an anonymous prototype to represent a top-level expr
        FunctionNode.__init__(self, PrototypeNode(Token("", expr.line), []), expr)

        self.__expr = expr

    def __str__(self):
        return str(self.__expr)