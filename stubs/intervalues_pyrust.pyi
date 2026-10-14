from collections.abc import Sequence

def combine_intervals_int(raw_ivs: Sequence[tuple[float, ...]]) -> list[tuple[float, float, float]]: ...
def combine_intervals_float(
    raw_ivs: Sequence[tuple[float, ...]],
    nr_decimal: int,
) -> list[tuple[float, float, float]]: ...
