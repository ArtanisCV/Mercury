__author__ = "Artanis"


from Token import *
from Iterator import ForwardIterator


class Lexer(object):
    def redo(self, code_str):
        self.codes = code_str
        self.current = ForwardIterator(self.codes)
        self.line = 1

    def get_current(self):
        return self.current.clone()

    def get_line(self):
        return self.line

    def add_line(self):
        self.line += 1

    def collect(self, previous):
        codes = []

        while previous != self.current:
            codes.append(previous.next())

        return ''.join(codes)

    def restore(self, previous):
        self.current = previous

    def expect(self, condition=None):
        char = self.current.peek()

        if char is not None:
            if condition is None or condition(char):
                self.current.next()
                return True

        return False

    def try_identifier_or_keyword(self):
        """
        identifier: [a-zA-Z][a-zA-Z0-9]*
        """

        previous = self.get_current()

        # [a-zA-Z]
        if not self.expect(str.isalpha):
            self.restore(previous)
            return None

        # [a-zA-Z0-9]*
        while self.expect(str.isalnum):
            pass

        name = self.collect(previous)
        token = KeywordValidator.try_keyword(name, self.get_line())
        return IdentifierToken(name, self.get_line()) if token is None else token

    def try_number(self):
        """
        number: ([0-9]+(\.[0-9]+)?)|(.[0-9]+)
        """

        previous = self.get_current()

        # [0-9]*
        while self.expect(str.isdigit):
            pass

        # (.[0-9]+)?
        if self.expect(lambda c: c == '.'):
            if not self.expect(str.isdigit):
                # no digit follows '.'
                self.restore(previous)
                return None

            while self.expect(str.isdigit):
                pass

        name = self.collect(previous)
        if len(name) == 0:
            self.restore(previous)
            return None

        return NumberToken(name, self.get_line())

    def try_whitespaces(self):
        previous = self.get_current()
        begin_line = self.get_line()

        while self.expect(str.isspace):
            pass

        name = self.collect(previous)
        if len(name) == 0:
            self.restore(previous)
            return None

        for char in name:
            if char == '\n':
                self.add_line()

        return WhitespacesToken(name, begin_line)

    def try_comment(self):
        """
        comment: #.*
        """

        previous = self.get_current()
        begin_line = self.get_line()

        if not self.expect(lambda c: c == '#'):
            self.restore(previous)
            return None

        while self.expect(lambda c: c != '\n'):
            pass

        if self.expect():
            # eat '\n'
            self.add_line()

        return CommentToken(self.collect(previous), begin_line)

    def try_character_or_operator(self):
        previous = self.get_current()

        if not self.expect():
            self.restore(previous)
            return None

        name = self.collect(previous)
        token = OperatorValidator.try_operator(name, self.get_line())
        return CharacterToken(name, self.get_line()) if token is None else token

    def tokenize(self, code_str):
        self.redo(code_str)
        tokens = []

        while True:
            token = self.try_identifier_or_keyword()
            if token is not None:
                tokens.append(token)
                continue

            token = self.try_number()
            if token is not None:
                tokens.append(token)
                continue

            if self.try_whitespaces() is not None:
                continue

            if self.try_comment() is not None:
                continue

            token = self.try_character_or_operator()
            if token is not None:
                tokens.append(token)
            else:
                break

        tokens.append(EOFToken(self.get_line()))

        return tokens


if __name__ == "__main__":
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
        extern print();  # external function print\
        """

    for token in Lexer().tokenize(code):
        print "%s(%d): %s" % (token.__class__.__name__, token.line, token)
