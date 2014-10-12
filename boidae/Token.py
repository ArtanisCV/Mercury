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


class BinaryToken(Token):
    def __init__(self, line):
        Token.__init__(self, "binary", line)


class UnaryToken(Token):
    def __init__(self, line):
        Token.__init__(self, "unary", line)


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
    def __init__(self, name, line):
        assert OperatorManager.is_binop(name)
        Token.__init__(self, name, line)


class UnOpToken(Token):
    def __init__(self, name, line):
        assert OperatorManager.is_unop(name)
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


class KeywordManager(object):
    keyword_token_map = {"def": DefToken, "extern": ExternToken,
                         "if": IfToken, "else": ElseToken, "then": ThenToken,
                         "for": ForToken, "in": InToken,
                         "binary": BinaryToken, "unary": UnaryToken}

    @staticmethod
    def try_keyword(name, line):
        if name in KeywordManager.keyword_token_map:
            token = KeywordManager.keyword_token_map[name](line)
            assert token.name == name
            return token
        else:
            return None


class OperatorManager(object):
    binaryOps = {'<', '+', '-', '*'}
    unaryOps = {}

    @staticmethod
    def is_binop(char):
        return char in OperatorManager.binaryOps

    @staticmethod
    def is_unop(char):
        return char in OperatorManager.unaryOps

    @staticmethod
    def try_operator(name, line):
        if OperatorManager.is_binop(name):
            return BinOpToken(name, line)
        elif OperatorManager.is_unop(name):
            return UnOpToken(name, line)
        else:
            return None
