from datetime import timedelta, timezone
from pathlib import Path
from runpy import run_path


EXAMPLE = run_path(
    str(Path(__file__).resolve().parents[1] / "examples" / "example_solar_market_dispatch.py")
)


def test_solar_dispatch_example_uses_quarter_hour_priority_rules():
    scenario = EXAMPLE["build_solar_dispatch"]()
    priorities = EXAMPLE["DispatchPriority"]

    assert all(slot.tzinfo is timezone.utc for slot in scenario.slots)
    assert all(
        later - earlier == timedelta(minutes=15)
        for earlier, later in zip(scenario.slots, scenario.slots[1:])
    )

    results = scenario.decisions.lookup_many(scenario.slots, with_priority=True)
    assert tuple(result.value for result in results) == (
        False,
        False,
        True,
        True,
        False,
        False,
        True,
        True,
    )
    assert tuple(result.priority for result in results) == (
        priorities.LIVE_PRICE_RULE,
        priorities.DAY_AHEAD_TRADE,
        priorities.LIVE_PRICE_RULE,
        priorities.INTRADAY_TRADE,
        priorities.LIVE_PRICE_RULE,
        priorities.DAY_AHEAD_TRADE,
        priorities.LIVE_PRICE_RULE,
        None,
    )
    assert tuple(
        scenario.source_names.get(result.source, "default on")
        for result in results
    ) == (
        "live-price rule",
        "day-ahead trade",
        "live-price rule",
        "intraday trade",
        "live-price rule",
        "day-ahead trade",
        "live-price rule",
        "default on",
    )

    dispatched_power = tuple(
        available if result.value else 0.0
        for available, result in zip(scenario.available_power_mw, results)
    )
    assert dispatched_power == (0.0, 0.0, 50.0, 65.0, 0.0, 0.0, 76.0, 60.0)


def test_solar_dispatch_output_columns_align(capsys):
    EXAMPLE["main"]()

    lines = capsys.readouterr().out.splitlines()[1:]
    pipe_positions = [
        tuple(index for index, character in enumerate(line) if character == "|")
        for line in lines
    ]
    assert len(set(pipe_positions)) == 1
