__author__ = 'Artanis'


class Interpreter(object):
    def __init__(self, string=None):
        self.string = string

    def read_from_string(self, string):
        for char in string:
            yield char

    def read_from_stdin(self):
        while True:
            try:
                string = raw_input(">>> ").strip()

                while string != "" and string[-1] == '\\':
                    string = string[:-1] + raw_input("... ").strip()

                string += ';'  # insert a semicolon to end an expression

                for char in string:
                    yield char
            except EOFError:
                break

    def read(self):
        if self.string is None:
            return self.read_from_stdin()
        else:
            return self.read_from_string(self.string)