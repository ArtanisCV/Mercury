__author__ = 'Artanis'


class ForwardIterator(object):
    def __init__(self, data, index=0):
        self.data = data
        self.index = index

    def terminated(self):
        return self.index >= len(self.data)

    def peek(self):
        if self.terminated():
            return None

        return self.data[self.index]

    def next(self):
        if self.terminated():
            return None

        element = self.data[self.index]
        self.index += 1
        return element

    def clone(self):
        return ForwardIterator(self.data, self.index)

    def __eq__(self, other):
        return self.index == other.index

    def __ne__(self, other):
        return self.index != other.index