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

    def retrieve(self, start_idx):
        return self.code[start_idx: self.current_idx]

    def restore(self, start_idx):
        self.current_idx = start_idx
        return None

    def try_char(self, condition):
        start_idx = self.current_idx

        char = self.next()
        if condition(char):
            return self.retrieve(start_idx)
        else:
            return self.restore(start_idx)

    def try_identifier_or_keyword(self):
        """
        identifier: [a-zA-Z][a-zA-Z0-9]*
        """

        start_idx = self.current_idx

        # [a-zA-Z]
        char = self.try_char(str.isalpha)
        if char is None:
            return self.restore(start_idx)

        # [a-zA-Z0-9]*
        char = self.try_char(str.isalnum)
        while char is not None:
            char = self.try_char(str.isalnum)

        token_name = self.retrieve(start_idx)
        token = KeywordValidator.is_keyword(token_name)
        return IdentifierToken(token_name) if token is None else token

    def try_number(self):
        """
        number: ([0-9]+(\.[0-9]+)?)|(.[0-9]+)
        """

        start_idx = self.current_idx

        # [0-9]*
        char = self.try_char(str.isdigit)
        if char is not None:
            char = self.try_char(str.isdigit)
            while char is not None:
                char = self.try_char(str.isdigit)

        # (.[0-9]+)?
        char = self.try_char(lambda c: c == '.')
        if char is not None:
            char = self.try_char(str.isdigit)
            if char is None:
                # no digit follows '.'
                return self.restore(start_idx)
            else:
                char = self.try_char(str.isdigit)
                while char is not None:
                    char = self.try_char(str.isdigit)

        token_name = self.retrieve(start_idx)
        if len(token_name) != 0:
            return NumberToken(token_name)
        else:
            return self.restore(start_idx)

    def eat_spaces(self):
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
        tokens = []

        while self.has_next():
            token = self.try_identifier_or_keyword()
            if token is not None:
                tokens.append(token)
                continue

            token = self.try_number()
            if token is not None:
                tokens.append(token)
                continue

            if self.eat_spaces() or self.eat_comment():
                continue

            tokens.append(self.eat_unknown())

        tokens.append(EOFToken())

        return tokens