# coding=utf-8
"""
author = neo
"""


class Queue(object):

    def __init__(self):
        self.items = []

    def isEmpty(self):
        return self.items == []

    def enqueue(self,item):
        self.items.insert(0,item)

    def dequeue(self,item):
        self.items.pop()

    def size(self):
        return len(self.items)


q = Queue()
q.enqueue(888)
q.enqueue('11e')
print(q.size())
print(q.items)
