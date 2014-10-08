__author__ = 'Artanis'

from Token import *
from AST import *
from Iterator import ForwardIterator


class Parser(object):
    def __init__(self):
        self.tokens = []
        self.current = ForwardIterator(self.tokens)

    def redo(self, token_list):
        self.tokens = token_list
        self.current = ForwardIterator(self.tokens)

    def get_current(self):
        return self.current.clone()

    def reject(self, previous):
        self.current = previous
        return None

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

    @staticmethod
    def is_number_token(token):
        return isinstance(token, NumberToken)

    @staticmethod
    def is_identifier_token(token):
        return isinstance(token, IdentifierToken)

    @staticmethod
    def is_def_token(token):
        return isinstance(token, DefToken)

    @staticmethod
    def is_extern_token(token):
        return isinstance(token, ExternToken)

    @staticmethod
    def is_eof_token(token):
        return isinstance(token, EOFToken)

    @staticmethod
    def is_character_token(token, char=None):
        return isinstance(token, CharacterToken) and (char is None or token.name == char)

    binop_precedence = {
        '<': 10, '+': 20, '-': 20, '*': 40
    }

    @staticmethod
    def is_binop(token):
        return Parser.is_character_token(token) and (token.name in Parser.binop_precedence)

    @staticmethod
    def get_binop_precedence(binop_token):
        return Parser.binop_precedence[binop_token.name]

    def try_numberexpr(self):
        """
        numberexpr ::= number
        """

        previous = self.get_current()

        number = self.expect(Parser.is_number_token)
        if number is not None:
            return NumberExpr(number)
        else:
            return self.reject(previous)

    def try_parenexpr(self):
        """
        parenexpr ::= '(' expr ')'
        """

        previous = self.get_current()

        token = self.expect(lambda t: Parser.is_character_token(t, '('))
        if token is not None:
            expr = self.try_expr()

            token = self.expect(lambda t: Parser.is_character_token(t, ')'))
            if token is None:
                return Error("Expected ')'")

            return expr
        else:
            return self.reject(previous)

    def try_identifierexpr(self):
        """
        identifierexpr
            ::= identifier
            ::= identifier '(' ')'
            ::= identifier '(' expr (',' expr)* ')'
        """

        previous = self.get_current()

        identifier = self.expect(Parser.is_identifier_token)
        if identifier is not None:
            token = self.expect(lambda t: Parser.is_character_token(t, '('))
            if token is None:
                return VariableExpr(identifier)
            else:
                args = []

                while True:
                    arg = self.try_expr()
                    if arg is not None:
                        args.append(arg)

                        self.expect(lambda t: Parser.is_character_token(t, ','))
                    else:
                        token = self.expect(lambda t: Parser.is_character_token(t, ')'))
                        if token is None:
                            return Error("Expected ')' at the end of argument list")
                        else:
                            break

                return CallExpr(identifier, args)
        else:
            return self.reject(previous)

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

        previous = self.get_current()

        while True:
            binop = self.look(Parser.is_binop)
            if binop is None:
                return lhs

            prec = Parser.get_binop_precedence(binop)
            if prec < lhs_prec:
                return lhs

            self.expect(Parser.is_binop)  # eat binop

            rhs = self.try_primary()
            if rhs is None:
                return self.reject(previous)

            next_binop = self.look(Parser.is_binop)
            if next_binop is not None and Parser.get_binop_precedence(next_binop) > prec:
                rhs = self.try_binoprhs(rhs, prec + 1)  # +1 for left associativity

                if rhs is None:
                    return self.reject(previous)

            lhs = BinaryExpr(binop, lhs, rhs)

    def try_expr(self):
        """
        expr ::= primary binoprhs
        """

        previous = self.get_current()

        lhs = self.try_primary()
        if lhs is None:
            return self.reject(previous)

        expr = self.try_binoprhs(lhs, 0)
        if expr is None:
            return self.reject(previous)
        else:
            return expr

    def try_prototype(self):
        """
        prototype ::= identifier '(' identifier* ')'
        """

        previous = self.get_current()

        identifier = self.expect(Parser.is_identifier_token)
        if identifier is None:
            return self.reject(previous)

        token = self.expect(lambda t: Parser.is_character_token(t, '('))
        if token is None:
            return self.reject(previous)

        args = []
        while True:
            token = self.expect(Parser.is_identifier_token)
            if token is not None:
                args.append(token)
            else:
                token = self.expect(lambda t: Parser.is_character_token(t, ')'))
                if token is None:
                    return Error("Expected ')' at the end of prototype")
                else:
                    break

        return Prototype(identifier, args)

    def try_function(self):
        """
        function ::= 'def' prototype expression
        """

        previous = self.get_current()

        if self.expect(Parser.is_def_token) is None:
            return self.reject(previous)

        prototype = self.try_prototype()
        if prototype is None:
            return self.reject(previous)

        expr = self.try_expr()
        if expr is None:
            return self.reject(previous)

        return Function(prototype, expr)

    def try_declaration(self):
        """
        declaration ::= 'extern' prototype
        """

        previous = self.get_current()

        if self.expect(Parser.is_extern_token) is None:
            return self.reject(previous)

        prototype = self.try_prototype()
        if prototype is None:
            return self.reject(previous)

        return prototype

    def try_toplevel_expr(self):
        """
        toplevelexpr ::= expr
        """

        expr = self.try_expr()
        if expr is not None:
            # make an anonymous prototype
            return Function(Prototype(Token(""), []), expr)
        else:
            return None

    def try_unknown(self):
        token = self.expect()

        if token is not None:
            return Unknown(token)
        else:
            return None

    def parse(self, token_list):
        self.redo(token_list)
        asts = []

        while True:
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

            # ignore top-level semicolons
            if self.expect(lambda t: Parser.is_character_token(t, ';')) is not None:
                continue

            if self.expect(Parser.is_eof_token) is not None:
                break

            self.try_unknown()

        return asts


if __name__ == "__main__":
    from Lexer import Lexer

    code = \
        """
        def foo(x y)
            x + foo(y, 4.0);

        def foo(x y)
            x + y

        y;

        def foo(x y)
            x + y);

        extern sin(a);
        """

    for ast in Parser().parse(Lexer().tokenize(code)):
        print ast