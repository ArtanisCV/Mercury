__author__ = 'Artanis'


class Token(object):
    def __init__(self, name):
        self.name = name


class EOFToken(Token):
    def __init__(self):
        Token.__init__(self, "EOF")


class IdentifierToken(Token):
    def __init__(self, name):
        Token.__init__(self, name)


class DefToken(Token):
    def __init__(self, keyword):
        Token.__init__(self, keyword)


class ExternToken(Token):
    def __init__(self, keyword):
        Token.__init__(self, keyword)


class NumberToken(Token):
    def __init__(self, num_str):
        Token.__init__(self, num_str)

        self.value = float(num_str)


class UnknownToken(Token):
    def __init__(self, char):
        Token.__init__(self, char)