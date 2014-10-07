__author__ = "Artanis"


from .Token import *


class Lexer(object):
    def __init__(self):
        self.code = ""
        self.current_idx = 0

    def redo(self, code):
        self.code = code
        self.current_idx = 0

    def has_next(self):
        return self.current_idx >= len(self.code)

    def next(self):
        if not self.has_next():
            return None

        char = self.code[self.current_idx]
        self.current_idx += 1
        return char

    def restore(self, position):
        self.current_idx = position

    def try_char(self, condition):
        start_idx = self.current_idx

        char = self.next()
        if condition(char):
            return char
        else:
            self.restore(start_idx)
            return None

    def try_identifier_or_keyword(self):
        """
        identifier: [a-zA-Z][a-zA-Z0-9]*
        """

        start_idx = self.current_idx
        token_name = []

        # [a-zA-Z]
        char = self.try_char(str.isalpha)
        if char is None:
            self.restore(start_idx)
            return None
        else:
            token_name.append(char)

        # [a-zA-Z0-9]*
        char = self.try_char(str.isalnum)
        while char is not None:
            token_name.append(char)
            char = self.try_char(str.isalnum)

        token_name = ''.join(token_name)
        if token_name == "def":
            return DefToken(token_name)
        elif token_name == "extern":
            return ExternToken(token_name)
        else:
            return IdentifierToken(token_name)

    def try_number(self):
        """
        number: ([0-9]+(\.[0-9]+)?)|(.[0-9]+)
        """

        start_idx = self.current_idx
        token_name = []

        # [0-9]*
        char = self.try_char(str.isdigit)
        if char is not None:
            token_name.append(char)

            char = self.try_char(str.isdigit)
            while char is not None:
                token_name.append(char)
                char = self.try_char(str.isdigit)

        # (.[0-9]+)?
        char = self.try_char(lambda c: c == '.')
        if char is not None:
            token_name.append(char)

            char = self.try_char(str.isdigit)
            if char is None:
                # no digit follows '.'
                self.restore(start_idx)
                return None
            else:
                token_name.append(char)

                char = self.try_char(str.isdigit)
                while char is not None:
                    token_name.append(char)
                    char = self.try_char(str.isdigit)

        if len(token_name) != 0:
            token_name = ''.join(token_name)
            return NumberToken(token_name)
        else:
            self.restore(start_idx)
            return None

    def eat_space(self):
        has_space = False

        while self.try_char(str.isspace) is not None:
            has_space = True

        return has_space

    def eat_comment(self):
        if self.try_char(lambda c: c == '#') is not None:
            while self.next() != '\n':
                pass

            return True
        else:
            return False

    def eat_unknown(self):
        return UnknownToken(self.next())

    def get_token(self, code):
        self.redo(code)

        while self.has_next():
            token = self.try_identifier_or_keyword()
            if token is not None:
                yield token
                continue

            token = self.try_number()
            if token is not None:
                yield token
                continue

            if self.eat_space() or self.eat_comment():
                continue

            yield self.eat_unknown()

        yield EOFToken()