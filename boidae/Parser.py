__author__ = 'Artanis'

from Token import *
from Node import *
from Error import *
from Buffer import Buffer


class Parser(object):
    def __init__(self, lexer):
        self.input = Buffer(lexer.tokenize())
        self.errors = []

        self.is_eof = lambda t: isinstance(t, EOFToken)
        self.is_def = lambda t: isinstance(t, DefToken)
        self.is_extern = lambda t: isinstance(t, ExternToken)
        self.is_if = lambda t: isinstance(t, IfToken)
        self.is_then = lambda t: isinstance(t, ThenToken)
        self.is_else = lambda t: isinstance(t, ElseToken)
        self.is_for = lambda t: isinstance(t, ForToken)
        self.is_in = lambda t: isinstance(t, InToken)
        self.is_var = lambda t: isinstance(t, VarToken)
        self.is_identifer = lambda t: isinstance(t, IdentifierToken)
        self.is_number = lambda t: isinstance(t, NumberToken)
        self.is_character = lambda t: isinstance(t, CharacterToken)
        self.is_binary = lambda t: isinstance(t, BinaryToken)
        self.is_unary = lambda t: isinstance(t, UnaryToken)
        self.is_binop = lambda t: OperatorManager.is_binop(t)
        self.is_unop = lambda t: OperatorManager.is_unop(t)

    def pop_syntax_errors(self):
        result = self.errors
        self.errors = []
        return result

    def collect(self):
        return self.input.accept()

    def look(self, condition=None):
        return self.input.peek(condition)

    def expect(self, condition=None):
        return self.input.move(condition)

    def try_number_expr(self):
        """
        number_expr ::= number
        """

        number = self.expect(self.is_number)
        if number is None:
            return None

        return NumberExprNode(number)

    def try_paren_expr(self):
        """
        paren_expr ::= '(' expr ')'
        """

        left_paren = self.expect(lambda t: t.name == '(')
        if left_paren is None:
            return None

        expr = self.try_expr()

        right_paren = self.expect(lambda t: t.name == ')')
        if right_paren is None:
            raise ExpectedRightParen(left_paren.line if expr is None else expr.line)

        return expr

    def try_identifier_expr(self):
        """
        identifier_expr
            ::= identifier
            ::= identifier '(' ')'
            ::= identifier '(' expr (',' expr)* ')'
        """

        identifier = self.expect(self.is_identifer)
        if identifier is None:
            return None

        left_paren = self.expect(lambda t: t.name == '(')
        if left_paren is None:
            return VariableExprNode(identifier)
        else:
            args = []

            while True:
                arg = self.try_expr()
                if arg is not None:
                    args.append(arg)

                    self.expect(lambda t: t.name == ',')
                else:
                    right_paren = self.expect(lambda t: t.name == ')')
                    if right_paren is None:
                        raise ExpectedRightParen(left_paren.line if len(args) == 0 else args[-1].line)

                    return CallExprNode(identifier, args)

    def try_if_expr(self):
        """
        if_expr ::= if expr then expr else expr
        """

        token = self.expect(self.is_if)
        if token is None:
            return None

        condition = self.try_expr()
        if condition is None:
            raise ExpectedExpr(token.line)

        token = self.expect(self.is_then)
        if token is None:
            raise ExpectedThen(condition.line)

        true = self.try_expr()
        if true is None:
            raise ExpectedExpr(token.line)

        token = self.expect(self.is_else)
        if token is None:
            raise ExpectedElse(true.line)

        false = self.try_expr()
        if false is None:
            raise ExpectedExpr(token.line)

        return IfExprNode(condition, true, false)

    def try_for_expr(self):
        """
        for_expr ::= for identifier '=' expr ',' expr (',' expr)? in expr
        """

        token = self.expect(self.is_for)
        if token is None:
            return None

        variable = self.expect(self.is_identifer)
        if variable is None:
            raise ExpectedIdentifier(token.line)

        token = self.expect(lambda t: t.name == '=')
        if token is None:
            raise ExpectedEqualSign(variable.line)

        begin = self.try_expr()
        if begin is None:
            raise ExpectedExpr(token.line)

        token = self.expect(lambda t: t.name == ',')
        if token is None:
            raise ExpectedComma(begin.line)

        end = self.try_expr()
        if end is None:
            raise ExpectedExpr(token.line)

        token = self.expect(lambda t: t.name == ',')
        if token is not None:
            step = self.try_expr()
            if step is None:
                raise ExpectedExpr(token.line)
        else:
            step = None

        token = self.expect(self.is_in)
        if token is None:
            raise ExpectedIn(end.line if step is None else step.line)

        body = self.try_expr()
        if body is None:
            raise ExpectedExpr(token.line)

        return ForExprNode(variable, begin, end, step, body)

    def try_var_expr(self):
        """
        var_expr ::= var identifier ('=' expr)? (',' identifier ('=' expr)?)* in expr
        """

        var_token = self.expect(self.is_var)
        if var_token is None:
            return None

        variables = {}
        while True:
            identifier = self.expect(self.is_identifer)
            if identifier is None:
                break

            assignment = self.expect(lambda t: t.name == '=')
            if assignment is not None:
                expr = self.try_expr()
                if expr is None:
                    raise ExpectedExpr(assignment.line)

                variables[identifier] = expr
            else:
                variables[identifier] = None

            self.expect(lambda t: t.name == ',')

        if len(variables) == 0:
            raise ExpectedVariableList(var_token.line)

        in_token = self.expect(self.is_in)
        if in_token is None:
            raise ExpectedIn(max([var.line for var in variables.keys()]))

        body = self.try_expr()
        if body is None:
            raise ExpectedExpr(in_token.line)

        return VarExprNode(variables, body)

    def try_primary_expr(self):
        """
        primary_expr
            ::= number_expr
            ::= paren_expr
            ::= identifier_expr
            ::= if_expr
            ::= for_expr
            ::= var_expr
        """

        expr = self.try_number_expr()
        if expr is not None:
            return expr

        expr = self.try_paren_expr()
        if expr is not None:
            return expr

        expr = self.try_identifier_expr()
        if expr is not None:
            return expr

        expr = self.try_if_expr()
        if expr is not None:
            return expr

        expr = self.try_for_expr()
        if expr is not None:
            return expr

        return self.try_var_expr()

    def try_unary_expr(self):
        """
        unary_expr
            ::= primary_expr
            ::= unop unary_expr
        """

        unop = self.expect(self.is_unop)
        if unop is None:
            return self.try_primary_expr()

        operand = self.try_unary_expr()
        if operand is None:
            raise ExpectedOperand(unop.line)

        return UnaryExprNode(unop, operand)

    def try_binop_rhs(self, lhs, lhs_prec):
        """
        binop_rhs ::= (binop unary_expr)*
        """

        while True:
            binop = self.look(self.is_binop)
            if binop is None:
                return lhs

            prec = OperatorManager.get_binop_precedence(binop)
            if prec < lhs_prec:
                return lhs

            self.expect(self.is_binop)  # eat binop

            rhs = self.try_unary_expr()
            if rhs is None:
                raise ExpectedUnaryExpr(binop.line)

            next_binop = self.look(self.is_binop)
            if next_binop is not None and \
               OperatorManager.get_binop_precedence(next_binop) > prec:
                rhs = self.try_binop_rhs(rhs, prec + 1)

            lhs = BinaryExprNode(binop, lhs, rhs)

    def try_expr(self):
        """
        expr ::= unary_expr binop_rhs
        """

        lhs = self.try_unary_expr()
        if lhs is None:
            return None

        return self.try_binop_rhs(lhs, 0)

    def try_normal_prototype(self):
        """
        normal_prototype ::= identifier '(' identifier* ')'
        """

        identifier = self.expect(self.is_identifer)
        if identifier is None:
            return None

        left_paren = self.expect(lambda t: t.name == '(')
        if left_paren is None:
            raise ExpectedLeftParen(identifier.line)

        args = []
        while True:
            arg = self.expect(self.is_identifer)
            if arg is not None:
                args.append(arg)
            else:
                right_paren = self.expect(lambda t: t.name == ')')
                if right_paren is None:
                    raise ExpectedRightParen(left_paren.line if len(args) == 0 else args[-1].line)

                return PrototypeNode(identifier, args)

    def try_binary_prototype(self):
        """
        binary_prototype ::= binary character number? '(' identifier identifier ')'
        """

        binary = self.expect(self.is_binary)
        if binary is None:
            return None

        operator = self.expect(self.is_character)
        if operator is None:
            raise ExpectedOperator(binary.line)

        precedence = self.expect(self.is_number)

        left_paren = self.expect(lambda t: t.name == '(')
        if left_paren is None:
            raise ExpectedLeftParen(operator.line if precedence is None else precedence.line)

        arg1 = self.expect(self.is_identifer)
        if arg1 is None:
            raise ExpectedIdentifier(left_paren.line)

        arg2 = self.expect(self.is_identifer)
        if arg2 is None:
            raise ExpectedIdentifier(arg1.line)

        right_paren = self.expect(lambda t: t.name == ')')
        if right_paren is None:
            raise ExpectedRightParen(arg2.line)

        return BinOpPrototypeNode(IdentifierToken(binary.name + operator.name, binary.line),
                                  precedence, [arg1, arg2])

    def try_unary_prototype(self):
        """
        unary_prototype ::= unary character '(' identifier ')'
        """

        unary = self.expect(self.is_unary)
        if unary is None:
            return None

        operator = self.expect(self.is_character)
        if operator is None:
            raise ExpectedOperator(unary.line)

        left_paren = self.expect(lambda t: t.name == '(')
        if left_paren is None:
            raise ExpectedLeftParen(operator.line)

        arg = self.expect(self.is_identifer)
        if arg is None:
            raise ExpectedIdentifier(left_paren.line)

        right_paren = self.expect(lambda t: t.name == ')')
        if right_paren is None:
            raise ExpectedRightParen(arg.line)

        return UnOpPrototypeNode(IdentifierToken(unary.name + operator.name, unary.line), [arg])

    def try_prototype(self):
        """
        prototype
            ::= normal_prototype
            ::= binary_prototype
            ::= unary_prototype
        """

        prototype = self.try_normal_prototype()
        if prototype is not None:
            return prototype

        prototype = self.try_binary_prototype()
        if prototype is not None:
            return prototype

        prototype = self.try_unary_prototype()
        if prototype is not None:
            return prototype

    def try_function(self):
        """
        function ::= def prototype expr
        """

        keyword = self.expect(self.is_def)
        if keyword is None:
            return None

        prototype = self.try_prototype()
        if prototype is None:
            raise ExpectedPrototype(keyword.line)

        expr = self.try_expr()
        if expr is None:
            raise ExpectedExpr(prototype.line)

        return FunctionNode(prototype, expr)

    def try_declaration(self):
        """
        declaration ::= extern prototype
        """

        keyword = self.expect(self.is_extern)
        if keyword is None:
            return None

        prototype = self.try_prototype()
        if prototype is None:
            raise ExpectedPrototype(keyword.line)

        return prototype

    def try_toplevel_expr(self):
        """
        toplevel_expr ::= expr

        we make an anonymous prototype to represent a top-level expr
        """

        expr = self.try_expr()
        if expr is None:
            return None

        return TopLevelExpr(expr)

    def try_negligible_character(self):
        # ignore top-level semicolons
        return self.expect(lambda t: t.name == ';')

    def try_eof(self):
        return self.expect(self.is_eof)

    def try_unknown(self):
        # try to recovery from syntax errors by eating an unknown token
        token = self.expect()
        if token is not None:
            raise UnknownToken(token)

    def parse(self):
        while True:
            try:
                node = self.try_function()
                if node is not None:
                    yield node
                    continue

                node = self.try_declaration()
                if node is not None:
                    yield node
                    continue

                node = self.try_toplevel_expr()
                if node is not None:
                    yield node
                    continue

                if self.try_negligible_character() is not None:
                    continue

                if self.try_eof() is not None:
                    break

                self.try_unknown()
            except BoidaeSyntaxError as e:
                self.errors.append(e)


if __name__ == "__main__":
    from Interpreter import Interpreter
    from Lexer import Lexer

    code = \
        """\
        def foo(x y)
            x + foo(y, 4.0);

        def cond(x) if
        def cond(x) if x < 2
        def cond(x) if x < 2 then
        def cond(x) if x < 2 then 2
        def cond(x) if x < 2 then 2 else
        def cond(x) if x < 2 then 2 else x

        def loop(x) for
        def loop(x) for i
        def loop(x) for i =
        def loop(x) for i = 1
        def loop(x) for i = 1,
        def loop(x) for i = 1, 10
        def loop(x) for i = 1, 10 in
        def loop(x) for i = 1, 10 in cond(10)
        def loop(x) for i = 1, 10,
        def loop(x) for i = 1, 10, 1
        def loop(x) for i = 1, 10, 1 in cond(10)

        def sum(x y)
            (x + y

        def mul(x y)
            x * y + z);

        def empty()
            1

        y;
        x + y;
        empty();

        x + + y;

        extern sin(x);
        extern print();

        def unary
        def unary!
        def unary!(
        def unary!(v
        def unary!(v)
        def unary!(v)
           if v then
              0
           else
              1

        def binary
        def binary>
        def binary> (
        def binary> (LHS
        def binary> (LHS RHS
        def binary> (LHS RHS) RHS < LHS
        def binary> 10 (LHS RHS)
        def binary> 10 (LHS RHS) RHS < LHS

        def assign(x)
            x = 4

        def variable(x) var
        def variable(x) var a
        def variable(x) var a in
        def variable(x) var a in sin(a * x)
        def variable(x) var a = 1 in sin(a * x)\
        """

    lexer = Lexer(Interpreter(code))
    parser = Parser(lexer)

    for node in parser.parse():
        print '%s(%d): %s' % (node.__class__.__name__, node.line, node)

    print

    for error in parser.pop_syntax_errors():
        print error