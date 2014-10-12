__author__ = 'Artanis'


from collections import deque


class Buffer(object):
    def __init__(self, generator):
        self.generator = generator
        self.buffer = deque()
        self.index = 0

    @property
    def cursor(self):
        return self.index

    def peek(self, condition=None):
        if self.index < len(self.buffer):
            item = self.buffer[self.index]
        else:
            try:
                item = self.generator.next()
            except StopIteration:
                return None

            if item is not None:
                self.buffer.append(item)

        if item is not None:
            if (condition is None) or (condition(item)):
                return item

        return None

    def move(self, condition=None):
        item = self.peek(condition)

        if item is not None:
            self.index += 1

        return item

    def reject(self, cursor=None):
        self.index = 0 if cursor is None else cursor

    def accept(self):
        result = []

        while self.index > 0:
            result.append(self.buffer.popleft())
            self.index -= 1

        return result