import intervalues
from random import random


class IntervalPdf(intervalues.IntervalMeter):

    def __init__(self, data=None):
        super().__init__(data)
        self.normalize()

    def normalize(self):
        total = self.total_length(force=True)
        for k, v in self.items():
            self.data[k] = v / total

    def pop(self, __key):
        item = self.data.pop(__key)
        self.normalize()
        return item

    def popitem(self):
        item = self.data.popitem()
        self.normalize()
        return item

    def total_length(self, force=False):
        if not force:
            return 1
        return super().total_length()

    def __mul__(self, other):
        return self.copy()

    def __imul__(self, other):
        return self

    def __repr__(self):
        return f"IntervalPDF:{dict(self.data)}"

    def check_intervals(self):
        super().check_intervals()
        if self.total_length(force=True) != 1:
            self.normalize()

    def align_intervals(self):
        super().align_intervals()
        self.normalize()

    def cumulative(self, x):
        pre = sum([self.get_length(i) for i in self.keys() if i.max() < x])
        this = self.find_which_contains(x)
        if this:
            this = self.get_length(this) * (x - this.min()) / (this.max() - this.min())
        return pre + this

    def cumsum(self, x):
        return self.cumulative(x)

    def inverse_cumulative(self, p):
        keys = sorted(self.keys())
        sum_p, iter, last = 0, -1, 0
        while sum_p < p:
            iter += 1
            last = sum_p
            sum_p += self.get_length(keys[iter])
        if iter == -1:
            return 0

        where_in_curr = (p - last) / self.get_length(keys[iter])
        min_curr, max_curr = keys[iter].min(), keys[iter].max()
        x = where_in_curr * (max_curr - min_curr) + min_curr
        print(where_in_curr, keys[iter], min_curr, max_curr)

        return x

    def sample(self, k=1):
        return (self.inverse_cumulative(random()) for _ in range(k))

    def as_meter(self):
        return intervalues.IntervalMeter(tuple(self))
