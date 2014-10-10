__author__ = 'Artanis'


class Token(object):
    def __init__(self, name, line):
        self.__name = name
        self.__line = line

    @property
    def name(self):
        return self.__name

    @property
    def line(self):
        return self.__line

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name


class EOFToken(Token):
    def __init__(self, line):
        Token.__init__(self, "EOF", line)


class DefToken(Token):
    keyword = "def"

    @staticmethod
    def include(name):
        return name == DefToken.keyword

    def __init__(self, line):
        Token.__init__(self, DefToken.keyword, line)


class ExternToken(Token):
    keyword = "extern"

    @staticmethod
    def include(name):
        return name == ExternToken.keyword

    def __init__(self, line):
        Token.__init__(self, ExternToken.keyword, line)


class IdentifierToken(Token):
    def __init__(self, name, line):
        Token.__init__(self, name, line)


class NumberToken(Token):
    def __init__(self, name, line):
        Token.__init__(self, name, line)

        self.__value = float(name)

    @property
    def value(self):
        return self.__value

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        # strict equivalence for floating numbers
        return isinstance(other, NumberToken) and self.value == other.value


class BinOpToken(Token):
    binaryOps = {'<', '+', '-', '*'}

    @staticmethod
    def include(name):
        return name in BinOpToken.binaryOps

    def __init__(self, name, line):
        assert BinOpToken.include(name)
        Token.__init__(self, name, line)


class CharacterToken(Token):
    def __init__(self, name, line):
        Token.__init__(self, name, line)


class WhitespacesToken(Token):
    def __init__(self, name, line):
        Token.__init__(self, name, line)


class CommentToken(Token):
    def __init__(self, name, line):
        Token.__init__(self, name, line)


class KeywordValidator(object):
    keywordTokens = [DefToken, ExternToken]

    @staticmethod
    def try_keyword(name, line):
        for keywordToken in KeywordValidator.keywordTokens:
            if keywordToken.include(name):
                return keywordToken(line)

        return None


class OperatorValidator(object):
    operatorTokens = [BinOpToken]

    @staticmethod
    def try_operator(name, line):
        for operatorToken in OperatorValidator.operatorTokens:
            if operatorToken.include(name):
                return BinOpToken(name, line)

        return None
