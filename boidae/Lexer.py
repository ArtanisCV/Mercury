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

    def reject(self, previous):
        self.current = previous
        return None

    def accept(self, previous):
        sub_code = []

        while previous != self.current:
            sub_code.append(previous.next())

        return ''.join(sub_code)

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
            return self.reject(previous)

        # [a-zA-Z0-9]*
        while self.expect(str.isalnum):
            pass

        token_name = self.accept(previous)
        token = KeywordValidator.is_keyword(token_name)
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
                return self.reject(previous)
            else:
                while self.expect(str.isdigit):
                    pass

        token_name = self.accept(previous)
        if len(token_name) != 0:
            return NumberToken(token_name)
        else:
            return self.reject(previous)

    def try_whitespace(self):
        previous = self.get_current()

        while self.expect(str.isspace):
            pass

        token_name = self.accept(previous)
        if len(token_name) != 0:
            return WhitespaceToken(token_name)
        else:
            return self.reject(previous)

    def try_comment(self):
        """
        comment: #.*
        """

        previous = self.get_current()

        if self.expect(lambda c: c == '#'):
            while self.expect(lambda c: c != '\n'):
                pass

            self.expect()  # eat '\n'

            return CommentToken(self.accept(previous))
        else:
            return self.reject(previous)

    def try_character(self):
        previous = self.get_current()

        if self.expect():
            return CharacterToken(self.accept(previous))
        else:
            return self.reject(previous)

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

            if self.try_whitespace() is not None:
                continue

            if self.try_comment() is not None:
                continue

            token = self.try_character()
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
        """

    for token in Lexer().tokenize(code):
        print token
