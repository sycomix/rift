import itertools
import logging
from dataclasses import dataclass
from typing import Iterable, Union

from rift.lsp.types import Position, Range, TextDocumentContentChangeEvent
from rift.util.ofdict import ofdict, todict

logger = logging.getLogger(__name__)


class RangeSet:
    ranges: set[Range]

    def __iter__(self):
        yield from self.ranges

    def __init__(self, ranges: "Iterable[Union[Range, RangeSet]]" = []):
        self.ranges = set()
        for range in ranges:
            if isinstance(range, RangeSet):
                self.ranges.update(range.ranges)
            elif isinstance(range, Range):
                self.add(range)
            else:
                raise TypeError(f"Expected Range or RangeSet, got {type(range)}")

    def __todict__(self):
        return list(self.ranges)

    @classmethod
    def __ofdict__(cls, d):
        ranges = ofdict(list[Range], d)
        return cls(ranges)

    @property
    def is_empty(self):
        return all(len(r) == 0 for r in self.ranges)

    def add(self, range: Range):
        acc = range
        ranges = set()
        for r in self.ranges:
            if acc.end in r or acc.start in r:
                acc = Range.union([acc, r])
            else:
                ranges.add(r)
        ranges.add(acc)
        self.ranges = ranges
        # logger.info("done adding")

    def normalize(self):
        classes: list[Range] = []
        for r in self.ranges:
            if len(r) == 0:
                continue
            ins = []
            outs = []
            for c in classes:
                if c.end in r or c.start in r:
                    ins.append(c)
                else:
                    outs.append(c)
            if ins:
                x = Range.union([r] + ins)
                outs.append(x)
            else:
                outs.append(r)
            classes = outs
        return RangeSet(classes)

    def __contains__(self, pos: Position):
        return any(pos in range for range in self.ranges)

    def cover(self):
        if len(self.ranges) == 0:
            raise ValueError("empty range set")
        return Range.union(self.ranges)

    def apply_edit(self, edit: TextDocumentContentChangeEvent):
        ranges = set()
        n = len(edit.text)
        δ = n - len(edit.range)
        for range in self.ranges:
            if edit.range.end <= range.start:
                ranges.add(range + δ)
            elif edit.range.start >= range.end:
                ranges.add(range)
            else:
                if edit.range.start in range:
                    ranges.add(Range(range.start, edit.range.start))
                if edit.range.end in range:
                    ranges.add(Range(edit.range.start + n, range.end + δ))
        self.ranges = ranges
        # return RangeSet(ranges)
