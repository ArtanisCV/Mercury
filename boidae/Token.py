__author__ = 'Artanis'


class Token(object):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Type: " + self.__class__.__name__ + " | Name: " + self.name


class EOFToken(Token):
    def __init__(self):
        Token.__init__(self, "EOF")


class WhitespaceToken(Token):
    def __init__(self, name):
        Token.__init__(self, name)


class CommentToken(Token):
    def __init__(self, name):
        Token.__init__(self, name)


class IdentifierToken(Token):
    def __init__(self, name):
        Token.__init__(self, name)


class DefToken(Token):
    keyword = "def"

    def __init__(self):
        Token.__init__(self, DefToken.keyword)


class ExternToken(Token):
    keyword = "extern"

    def __init__(self):
        Token.__init__(self, ExternToken.keyword)


class NumberToken(Token):
    def __init__(self, num_str):
        Token.__init__(self, num_str)

        self.value = float(num_str)

    def __str__(self):
        return Token.__str__(self) + " | Value: " + str(self.value)


class CharacterToken(Token):
    def __init__(self, char):
        Token.__init__(self, char)


class KeywordValidator(object):
    keywordTokens = [DefToken, ExternToken]

    @staticmethod
    def is_keyword(token_name):
        for keywordToken in KeywordValidator.keywordTokens:
            if token_name == keywordToken.keyword:
                return keywordToken()

        return None