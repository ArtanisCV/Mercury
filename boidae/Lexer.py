__author__ = "Artanis"


from Token import *
from Iterator import ForwardIterator


class Lexer(object):
    def __init__(self):
        self.codes = ""
        self.current = ForwardIterator(self.codes)

    def redo(self, code_str):
        self.codes = code_str
        self.current = ForwardIterator(self.codes)

    def get_current(self):
        return self.current.clone()

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

        token_name = self.collect(previous)
        token = KeywordValidator.try_keyword(token_name)
        return IdentifierToken(token_name) if token is None else token

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

        token_name = self.collect(previous)
        if len(token_name) == 0:
            self.restore(previous)
            return None

        return NumberToken(token_name)

    def try_whitespaces(self):
        previous = self.get_current()

        while self.expect(str.isspace):
            pass

        token_name = self.collect(previous)
        if len(token_name) == 0:
            self.restore(previous)
            return None

        return WhitespacesToken(token_name)

    def try_comment(self):
        """
        comment: #.*
        """

        previous = self.get_current()

        if not self.expect(lambda c: c == '#'):
            self.restore(previous)
            return None

        while self.expect(lambda c: c != '\n'):
            pass

        self.expect()  # eat '\n'

        return CommentToken(self.collect(previous))

    def try_character_or_operator(self):
        previous = self.get_current()

        if not self.expect():
            self.restore(previous)
            return None

        token_name = self.collect(previous)
        token = OperatorValidator.try_operator(token_name)
        return CharacterToken(token_name) if token is None else token

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

        tokens.append(EOFToken())

        return tokens


if __name__ == "__main__":
    code = \
        """
        # Compute the x'th fibonacci number.
        def fib(x)
            if x < 3 then
                1
            else
                fib(x - 1) + fib(x - 2)

        fib(40)

        # Compute the sum of two numbers.
        def sum(x1 x2)
            x1 + x2

        sum(.1, 10.1)

        extern cos(x);
        extern print();
        """

    for token in Lexer().tokenize(code):
        print token.__class__.__name__ + ":", token
