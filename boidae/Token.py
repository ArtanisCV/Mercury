__author__ = 'Artanis'


class Token(object):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name


class EOFToken(Token):
    def __init__(self):
        Token.__init__(self, "EOF")


class DefToken(Token):
    keyword = "def"

    @staticmethod
    def include(token_name):
        return token_name == DefToken.keyword

    def __init__(self):
        Token.__init__(self, DefToken.keyword)


class ExternToken(Token):
    keyword = "extern"

    @staticmethod
    def include(token_name):
        return token_name == ExternToken.keyword

    def __init__(self):
        Token.__init__(self, ExternToken.keyword)


class IdentifierToken(Token):
    def __init__(self, name):
        Token.__init__(self, name)


class NumberToken(Token):
    def __init__(self, num_str):
        Token.__init__(self, num_str)

        self.value = float(num_str)

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        # strict equivalence for floating numbers
        return isinstance(other, NumberToken) and self.value == other.value


class BinOpToken(Token):
    binaryOps = {'<', '+', '-', '*'}

    @staticmethod
    def include(char):
        return char in BinOpToken.binaryOps

    def __init__(self, char):
        assert BinOpToken.include(char)
        Token.__init__(self, char)


class CharacterToken(Token):
    def __init__(self, char):
        Token.__init__(self, char)


class WhitespacesToken(Token):
    def __init__(self, name):
        Token.__init__(self, name)


class CommentToken(Token):
    def __init__(self, name):
        Token.__init__(self, name)


class KeywordValidator(object):
    keywordTokens = [DefToken, ExternToken]

    @staticmethod
    def try_keyword(token_name):
        for keywordToken in KeywordValidator.keywordTokens:
            if keywordToken.include(token_name):
                return keywordToken()

        return None


class OperatorValidator(object):
    operatorTokens = [BinOpToken]

    @staticmethod
    def try_operator(token_name):
        for operatorToken in OperatorValidator.operatorTokens:
            if operatorToken.include(token_name):
                return BinOpToken(token_name)

        return None
