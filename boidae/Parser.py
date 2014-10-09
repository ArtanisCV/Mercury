__author__ = 'Artanis'

from Token import *
from AST import *
from Iterator import ForwardIterator


class Parser(object):
    def __init__(self):
        self.tokens = []
        self.current = ForwardIterator(self.tokens)

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

        return NumberExprAST(number)

    def try_parenexpr(self):
        """
        parenexpr ::= '(' expr ')'
        """

        previous = self.get_current()

        left_paren = self.expect(lambda t: t == CharacterToken('('))
        if left_paren is None:
            self.restore(previous)
            return None

        expr = self.try_expr()

        right_paren = self.expect(lambda t: t == CharacterToken(')'))
        if right_paren is None:
            raise ParseError()

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

        left_paren = self.expect(lambda t: t == CharacterToken('('))
        if left_paren is None:
            return VariableExprAST(identifier)
        else:
            args = []

            while True:
                arg = self.try_expr()
                if arg is not None:
                    args.append(arg)

                    self.expect(lambda t: t == CharacterToken(','))
                else:
                    right_paren = self.expect(lambda t: t == CharacterToken(')'))
                    if right_paren is None:
                        raise ParseError()

                    return CallExprAST(identifier, args)

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
                raise ParseError

            next_binop = self.look(self.is_binop)
            if next_binop is not None and BinopPrecedence.get_precedence(next_binop) > prec:
                rhs = self.try_binoprhs(rhs, prec + 1)  # +1 for left associativity

            lhs = BinaryExprAST(binop, lhs, rhs)

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

        left_paren = self.expect(lambda t: t == CharacterToken('('))
        if left_paren is None:
            self.restore(previous)
            return None

        args = []
        while True:
            arg = self.expect(self.is_identifer)
            if arg is not None:
                args.append(arg)
            else:
                right_paren = self.expect(lambda t: t == CharacterToken(')'))
                if right_paren is None:
                    raise ParseError()

                return PrototypeAST(identifier, args)

    def try_function(self):
        """
        function ::= 'def' prototype expression
        """

        previous = self.get_current()

        if self.expect(self.is_def) is None:
            self.restore(previous)
            return None

        prototype = self.try_prototype()
        if prototype is None:
            raise ParseError()

        expr = self.try_expr()
        if expr is None:
            raise ParseError()

        return FunctionAST(prototype, expr)

    def try_declaration(self):
        """
        declaration ::= 'extern' prototype
        """

        previous = self.get_current()

        if self.expect(self.is_extern) is None:
            self.restore(previous)
            return None

        prototype = self.try_prototype()
        if prototype is None:
            raise ParseError()

        return prototype

    def try_toplevel_expr(self):
        """
        toplevelexpr ::= expr

        we make an anonymous prototype to represent a top-level expr
        """

        expr = self.try_expr()
        if expr is None:
            return None

        return FunctionAST(PrototypeAST(Token(""), []), expr)

    def try_negligible_character(self):
        # ignore top-level semicolons
        return self.expect(lambda t: t == CharacterToken(';'))

    def try_eof(self):
        return self.expect(self.is_eof)

    def try_unknown(self):
        # try to recovery from syntax errors by eating an unknown character
        if self.expect() is not None:
            raise ParseError()

    def parse(self, token_list):
        self.redo(token_list)
        asts = []

        while True:
            previous = self.get_current()

            try:
                ast = self.try_function()
                if ast is not None:
                    asts.append(ast)
                    continue

                ast = self.try_declaration()
                if ast is not None:
                    asts.append(ast)
                    continue

                ast = self.try_toplevel_expr()
                if ast is not None:
                    asts.append(ast)
                    continue

                if self.try_negligible_character() is not None:
                    continue

                if self.try_eof() is not None:
                    break

                self.try_unknown()
            except ParseError:
                self.record_error(previous)

        return asts


if __name__ == "__main__":
    from Lexer import Lexer

    code = \
        """
        def foo(x y)
            x + foo(y, 4.0);

        def foo(x y)
            (x + y

        def foo(x y)
            x + y);

        def foo()
            1

        y;

        x + y;

        x + + y;

        extern sin(a);
        """

    parser = Parser()

    for ast in parser.parse(Lexer().tokenize(code)):
        print ast