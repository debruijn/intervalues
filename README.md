# intervalues
Efficient combining of intervals of numbers while keeping track of how frequent numbers within those intervals are
featured.

## Motivation
This package will be useful in the following cases:
- If you have too many intervals and can't easily see which value is featured the most across them.
- If you have a large number of integers to keep track of and you need to do this more memory efficient than a list
- If you have a list of continuous intervals that need to be combined

## Features
Contains the following classes:
- IntervalSet (optimized towards combining)
- IntervalList (unstructured collection - faster to create)
- IntervalCounter (optimized towards tracking counts)

Both integer and float intervals will be supported.

### Extended feature list
S/L/C indicate whether this feature is supported by Sets, Lists or Counters. F/I indicate Float or Integer versions of 
these.
- L/C: Sampling from a constructed List or Counter, and other statistical uses (CDF/PDF)
- C: Weight/values for intervals? Could be attribute of "UnitInterval"
- S/L/C: Complex intervals (which means to include 2D logic; this might extend to higher dimensions)
- S/L/C: Transforming individual or combined intervals with monotonic functions
- F: support for open and closed intervals (this distinction is currently ignored for floats)
