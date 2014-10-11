__author__ = 'Artanis'

from Token import *
from Node import *
from Error import *
from Iterator import ForwardIterator


class Parser(object):
    def __init__(self):
        self.is_eof = lambda t: isinstance(t, EOFToken)
        self.is_def = lambda t: isinstance(t, DefToken)
        self.is_extern = lambda t: isinstance(t, ExternToken)
        self.is_identifer = lambda t: isinstance(t, IdentifierToken)
        self.is_number = lambda t: isinstance(t, NumberToken)
        self.is_binop = lambda t: isinstance(t, BinOpToken)

    def redo(self, token_list):
        self.tokens = token_list
        self.current = ForwardIterator(self.tokens)

    def get_current(self):
        return self.current.clone()

    def collect(self, previous):
        tokens = []

        while previous != self.current:
            tokens.append(previous.next())

        return tokens

    def restore(self, previous):
        self.current = previous

    def record_error(self, previous):
        tokens = self.collect(previous)
        msg = ' '.join([str(token) for token in tokens])
        print "Error occurs when parsing: " + msg

    def look(self, condition=None):
        token = self.current.peek()

        if token is not None:
            if condition is None or condition(token):
                return token

        return None

    def expect(self, condition=None):
        token = self.look(condition)

        if token is not None:
            if condition is None or condition(token):
                return self.current.next()

        return None

    def try_numberexpr(self):
        """
        numberexpr ::= number
        """

        previous = self.get_current()

        number = self.expect(self.is_number)
        if number is None:
            self.restore(previous)
            return None

        return NumberExprNode(number)

    def try_parenexpr(self):
        """
        parenexpr ::= '(' expr ')'
        """

        previous = self.get_current()

        left_paren = self.expect(lambda t: t.name == '(')
        if left_paren is None:
            self.restore(previous)
            return None

        expr = self.try_expr()

        right_paren = self.expect(lambda t: t.name == ')')
        if right_paren is None:
            raise ExpectedRightParen(left_paren.line)

        return expr

    def try_identifierexpr(self):
        """
        identifierexpr
            ::= identifier
            ::= identifier '(' ')'
            ::= identifier '(' expr (',' expr)* ')'
        """

        previous = self.get_current()

        identifier = self.expect(self.is_identifer)
        if identifier is None:
            self.restore(previous)
            return None

        left_paren = self.expect(lambda t: t.name == '(')
        if left_paren is None:
            return VariableExprNode(identifier)
        else:
            args = []

            while True:
                arg = self.try_expr()
                if arg is not None:
                    args.append(arg)

                    self.expect(lambda t: t.name == ',')
                else:
                    right_paren = self.expect(lambda t: t.name == ')')
                    if right_paren is None:
                        raise ExpectedRightParen(identifier.line)

                    return CallExprNode(identifier, args)

    def try_primary(self):
        """
        primary
            ::= numberexpr
            ::= parenexpr
            ::= identifierexpr
        """

        expr = self.try_numberexpr()
        if expr is not None:
            return expr

        expr = self.try_parenexpr()
        if expr is not None:
            return expr

        return self.try_identifierexpr()

    def try_binoprhs(self, lhs, lhs_prec):
        """
        binoprhs ::= (binop primary)*
        """

        while True:
            binop = self.look(self.is_binop)
            if binop is None:
                return lhs

            prec = BinopPrecedence.get_precedence(binop)
            if prec < lhs_prec:
                return lhs

            self.expect(self.is_binop)  # eat binop

            rhs = self.try_primary()
            if rhs is None:
                raise ExpectedPrimaryExpr(lhs.line)

            next_binop = self.look(self.is_binop)
            if next_binop is not None and BinopPrecedence.get_precedence(next_binop) > prec:
                rhs = self.try_binoprhs(rhs, prec + 1)  # +1 for left associativity

            lhs = BinaryExprNode(binop, lhs, rhs)

    def try_expr(self):
        """
        expr ::= primary binoprhs
        """

        previous = self.get_current()

        lhs = self.try_primary()
        if lhs is None:
            self.restore(previous)
            return None

        return self.try_binoprhs(lhs, 0)

    def try_prototype(self):
        """
        prototype ::= identifier '(' identifier* ')'
        """

        previous = self.get_current()

        identifier = self.expect(self.is_identifer)
        if identifier is None:
            self.restore(previous)
            return None

        left_paren = self.expect(lambda t: t.name == '(')
        if left_paren is None:
            self.restore(previous)
            return None

        args = []
        while True:
            arg = self.expect(self.is_identifer)
            if arg is not None:
                args.append(arg)
            else:
                right_paren = self.expect(lambda t: t.name == ')')
                if right_paren is None:
                    raise ExpectedRightParen(identifier.line)

                return PrototypeNode(identifier, args)

    def try_function(self):
        """
        function ::= 'def' prototype expression
        """

        previous = self.get_current()

        keyword = self.expect(self.is_def)
        if keyword is None:
            self.restore(previous)
            return None

        prototype = self.try_prototype()
        if prototype is None:
            raise ExpectedPrototype(keyword.line)

        expr = self.try_expr()
        if expr is None:
            raise ExpectedExpr(keyword.line)

        return FunctionNode(prototype, expr)

    def try_declaration(self):
        """
        declaration ::= 'extern' prototype
        """

        previous = self.get_current()

        keyword = self.expect(self.is_extern)
        if keyword is None:
            self.restore(previous)
            return None

        prototype = self.try_prototype()
        if prototype is None:
            raise ExpectedPrototype(keyword.line)

        return prototype

    def try_toplevel_expr(self):
        """
        toplevelexpr ::= expr

        we make an anonymous prototype to represent a top-level expr
        """

        expr = self.try_expr()
        if expr is None:
            return None

        return TopLevelExpr(expr)

    def try_negligible_character(self):
        # ignore top-level semicolons
        return self.expect(lambda t: t.name == ';')

    def try_eof(self):
        return self.expect(self.is_eof)

    def try_unknown(self):
        # try to recovery from syntax errors by eating an unknown token
        token = self.expect()
        if token is not None:
            raise UnknownToken(token)

    def parse(self, token_list):
        self.redo(token_list)
        nodes, errors = [], []

        while True:
            try:
                node = self.try_function()
                if node is not None:
                    nodes.append(node)
                    continue

                node = self.try_declaration()
                if node is not None:
                    nodes.append(node)
                    continue

                node = self.try_toplevel_expr()
                if node is not None:
                    nodes.append(node)
                    continue

                if self.try_negligible_character() is not None:
                    continue

                if self.try_eof() is not None:
                    break

                self.try_unknown()
            except BoidaeSyntaxError as e:
                errors.append(e)

        return nodes, errors


if __name__ == "__main__":
    from Lexer import Lexer

    code = \
        """\
        def foo(x y)
            x + foo(y, 4.0);

        def sum(x y)
            (x + y

        def mul(x y)
            x * y + z);

        def empty()
            1

        y;

        x + y;

        x + + y;

        empty();

        extern sin(a);\
        """

    parser = Parser()
    nodes, errors = parser.parse(Lexer().tokenize(code))

    for node in nodes:
        print '%s(%d): %s' % (node.__class__.__name__, node.line, node)

    print
    for error in errors:
        print error