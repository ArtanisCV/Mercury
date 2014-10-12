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
    def __init__(self, line):
        Token.__init__(self, "def", line)


class ExternToken(Token):
    def __init__(self, line):
        Token.__init__(self, "extern", line)


class IfToken(Token):
    def __init__(self, line):
        Token.__init__(self, "if", line)


class ThenToken(Token):
    def __init__(self, line):
        Token.__init__(self, "then", line)


class ElseToken(Token):
    def __init__(self, line):
        Token.__init__(self, "else", line)


class ForToken(Token):
    def __init__(self, line):
        Token.__init__(self, "for", line)


class InToken(Token):
    def __init__(self, line):
        Token.__init__(self, "in", line)


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
    keyword_token_map = {"def": DefToken, "extern": ExternToken,
                         "if": IfToken, "else": ElseToken, "then": ThenToken,
                         "for": ForToken, "in": InToken}

    @staticmethod
    def try_keyword(name, line):
        if name in KeywordValidator.keyword_token_map:
            token = KeywordValidator.keyword_token_map[name](line)
            assert token.name == name
            return token
        else:
            return None


class OperatorValidator(object):
    operatorTokens = [BinOpToken]

    @staticmethod
    def try_operator(name, line):
        for operatorToken in OperatorValidator.operatorTokens:
            if operatorToken.include(name):
                return BinOpToken(name, line)

        return None
