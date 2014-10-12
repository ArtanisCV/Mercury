__author__ = 'Artanis'


class Interpreter(object):
    def __init__(self, code_str):
        self.code = code_str

    def read(self):
        for char in self.code:
            yield char