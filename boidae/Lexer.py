__author__ = "Artanis"


from Buffer import Buffer
from Token import *


class Lexer(object):
    def __init__(self, interpreter):
        self.input = Buffer(interpreter.read())
        self.line = 1

    def get_line(self):
        return self.line

    def add_line(self):
        self.line += 1

    def collect(self):
        return ''.join(self.input.accept())

    def restore(self):
        self.input.reject()

    def expect(self, condition=None):
        return self.input.move(condition) is not None

    def try_identifier_or_keyword(self):
        """
        identifier: [a-zA-Z][a-zA-Z0-9]*
        """

        # [a-zA-Z]
        if not self.expect(str.isalpha):
            self.restore()
            return None

        # [a-zA-Z0-9]*
        while self.expect(str.isalnum):
            pass

        name = self.collect()
        token = KeywordManager.try_keyword(name, self.get_line())
        return IdentifierToken(name, self.get_line()) if token is None else token

    def try_number(self):
        """
        number: ([0-9]+(\.[0-9]+)?)|(.[0-9]+)
        """

        # [0-9]*
        while self.expect(str.isdigit):
            pass

        # (.[0-9]+)?
        if self.expect(lambda c: c == '.'):
            if not self.expect(str.isdigit):
                # no digit follows '.'
                self.restore()
                return None

            while self.expect(str.isdigit):
                pass

        name = self.collect()
        if len(name) == 0:
            self.restore()
            return None

        return NumberToken(name, self.get_line())

    def try_whitespaces(self):
        begin_line = self.get_line()

        while self.expect(str.isspace):
            pass

        name = self.collect()
        if len(name) == 0:
            self.restore()
            return None

        for char in name:
            if char == '\n':
                self.add_line()

        return WhitespacesToken(name, begin_line)

    def try_comment(self):
        """
        comment: #.*
        """

        begin_line = self.get_line()

        if not self.expect(lambda c: c == '#'):
            self.restore()
            return None

        while self.expect(lambda c: c != '\n'):
            pass

        if self.expect():
            # eat '\n'
            self.add_line()

        return CommentToken(self.collect(), begin_line)

    def try_character_or_operator(self):
        if not self.expect():
            self.restore()
            return None

        name = self.collect()
        token = OperatorManager.try_operator(name, self.get_line())
        return CharacterToken(name, self.get_line()) if token is None else token

    def tokenize(self):
        while True:
            token = self.try_identifier_or_keyword()
            if token is not None:
                yield token
                continue

            token = self.try_number()
            if token is not None:
                yield token
                continue

            if self.try_whitespaces() is not None:
                continue

            if self.try_comment() is not None:
                continue

            token = self.try_character_or_operator()
            if token is not None:
                yield token
            else:
                break

        yield EOFToken(self.get_line())


if __name__ == "__main__":
    from Interpreter import Interpreter

    code = \
        """\
        # Compute the x'th fibonacci number.
        def fib(x)
            if x < 3 then
                1
            else
                fib(x - 1) + fib(x - 2)
        fib(40)

        # Print multiple '*' ('x' indicates the number of '*')
        def star(x)
            for i = 1, i < n, 1.0 in
                putchard(42)
        star(100)

        # Compute the sum of two numbers.
        def sum(x1 x2)
            x1 + x2
        sum(.1, 10.1)

        extern cos(x);  # external function cos
        extern print();  # external function print

        # Logical unary not.
        def unary!(v)
           if v then
              0
           else
              1

        # Define > with the same precedence as <.
        def binary> 10 (LHS RHS)
            RHS < LHS\
        """

    lexer = Lexer(Interpreter(code))

    for token in lexer.tokenize():
        print "%s(%d): %s" % (token.__class__.__name__, token.line, token)
