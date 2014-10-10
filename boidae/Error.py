__author__ = 'Artanis'


class BoidaeSyntaxError(Exception):
    def __init__(self, msg, line):
        self.msg = msg
        self.line = line

    def __str__(self):
        return "Syntax Error (%d): %s" % (self.line, self.msg)


class ExpectedRightParen(BoidaeSyntaxError):
    def __init__(self, line):
        BoidaeSyntaxError.__init__(self, "Expected ')'", line)


class ExpectedPrototype(BoidaeSyntaxError):
    def __init__(self, line):
        BoidaeSyntaxError.__init__(self, "Expected prototype", line)


class ExpectedPrimaryExpr(BoidaeSyntaxError):
    def __init__(self, line):
        BoidaeSyntaxError.__init__(self, "Expected primary expression", line)


class ExpectedExpr(BoidaeSyntaxError):
    def __init__(self, line):
        BoidaeSyntaxError.__init__(self, "Expected expression", line)


class UnknownToken(BoidaeSyntaxError):
    def __init__(self, token):
        BoidaeSyntaxError.__init__(self, "Unknown token '%s'" % token, token.line)


class BoidaeSemanticError(Exception):
    def __init__(self, msg, line):
        self.msg = msg
        self.line = line

    def __str__(self):
        return "Semantic Error (%d): %s" % (self.line, self.msg)


class UndefinedVariable(BoidaeSemanticError):
    def __init__(self, node):
        BoidaeSemanticError.__init__(self, "Undefined variable '%s'" % node, node.line)


class UndefinedOperator(BoidaeSemanticError):
    def __init__(self, node):
        BoidaeSemanticError.__init__(self, "Undefined operator '%s'" % node, node.line)


class UndefinedFunction(BoidaeSemanticError):
    def __init__(self, node):
        BoidaeSemanticError.__init__(self, "Undefined function '%s'" % node, node.line)


class MismatchedArgument(BoidaeSemanticError):
    def __init__(self, expected_size, node):
        msg = "Mismatched argument list (expect %d arguments, actually get %d)" % \
              (expected_size, len(node.args))
        BoidaeSemanticError.__init__(self, msg, node.line)


class RedefinedFunction(BoidaeSemanticError):
    def __init__(self, node):
        BoidaeSemanticError.__init__(self, "Redefined function '%s'" % node, node.line)


class MismatchedDeclaration(BoidaeSemanticError):
    def __init__(self, previous_size, node):
        msg = "Mismatched declaration (previous: %d arguments, current: %d)" \
              % (previous_size, len(node.args))
        BoidaeSemanticError.__init__(self, msg, node.line)