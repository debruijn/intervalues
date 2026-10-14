"""Resolve synthetic solar setpoints from day-ahead, intraday, and live prices."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import IntEnum

from intervalues import IntervalMap, PriorityIntervalMap, PrioritySourceHandle


class DispatchPriority(IntEnum):
    DAY_AHEAD_TRADE = 10
    INTRADAY_TRADE = 20
    LIVE_PRICE_RULE = 30


SLOT = timedelta(minutes=15)
DAY_AHEAD_OFF_THRESHOLD_EUR_MWH = 0.0
LIVE_OFF_THRESHOLD_EUR_MWH = 0.0
LIVE_RESTART_THRESHOLD_EUR_MWH = 35.0


@dataclass(frozen=True)
class SolarDispatchScenario:
    slots: tuple[datetime, ...]
    day_ahead_prices_eur_mwh: tuple[float, ...]
    live_prices_eur_mwh: tuple[float, ...]
    available_power_mw: tuple[float, ...]
    decisions: PriorityIntervalMap[bool]
    source_names: dict[PrioritySourceHandle, str]


def build_solar_dispatch() -> SolarDispatchScenario:
    """Build a deterministic two-hour, 15-minute dispatch example."""
    first_slot = datetime(2026, 6, 17, 10, 0, tzinfo=timezone.utc)
    slots = tuple(first_slot + index * SLOT for index in range(8))
    day_ahead_prices = (18.0, -8.0, -6.0, -2.0, 15.0, -1.0, 24.0, 20.0)
    live_prices = (-1.0, -4.0, 40.0, 18.0, -2.0, 20.0, 40.0, 12.0)
    available_power_mw = (20.0, 35.0, 50.0, 65.0, 75.0, 80.0, 76.0, 60.0)

    day_ahead = IntervalMap[bool]()
    for slot, price in zip(slots, day_ahead_prices):
        if price <= DAY_AHEAD_OFF_THRESHOLD_EUR_MWH:
            day_ahead.assign(slot, slot + SLOT, False)

    intraday = IntervalMap[bool]()
    intraday.assign(slots[3], slots[3] + SLOT, True)
    intraday.assign(slots[6], slots[6] + SLOT, False)

    traded_plan = PriorityIntervalMap[bool](default=True)
    traded_plan.add(day_ahead, priority=DispatchPriority.DAY_AHEAD_TRADE)
    traded_plan.add(intraday, priority=DispatchPriority.INTRADAY_TRADE)

    live_price_override = IntervalMap[bool]()
    for slot, price in zip(slots, live_prices):
        planned_to_run = traded_plan[slot]
        if planned_to_run and price < LIVE_OFF_THRESHOLD_EUR_MWH:
            live_price_override.assign(slot, slot + SLOT, False)
        elif not planned_to_run and price >= LIVE_RESTART_THRESHOLD_EUR_MWH:
            live_price_override.assign(slot, slot + SLOT, True)

    decisions = PriorityIntervalMap[bool](default=True)
    day_ahead_handle, _ = decisions.add(day_ahead, priority=DispatchPriority.DAY_AHEAD_TRADE)
    intraday_handle, _ = decisions.add(intraday, priority=DispatchPriority.INTRADAY_TRADE)
    live_handle, _ = decisions.add(live_price_override, priority=DispatchPriority.LIVE_PRICE_RULE)
    source_names = {
        day_ahead_handle: "day-ahead trade",
        intraday_handle: "intraday trade",
        live_handle: "live-price rule",
    }
    return SolarDispatchScenario(
        slots=slots,
        day_ahead_prices_eur_mwh=day_ahead_prices,
        live_prices_eur_mwh=live_prices,
        available_power_mw=available_power_mw,
        decisions=decisions,
        source_names=source_names,
    )


def main() -> None:
    scenario = build_solar_dispatch()
    results = scenario.decisions.lookup_many(scenario.slots, with_priority=True)

    print("Illustrative policy only; prices, trades, and available power are synthetic.")
    print(
        f"{'UTC start':<22} | {'DA price':>8} | {'Live price':>10} | "
        f"{'Available MW':>12} | {'Dispatch MW':>11} | Setpoint source"
    )
    for index, (slot, result) in enumerate(zip(scenario.slots, results)):
        if result.value is None:
            raise RuntimeError("solar dispatch unexpectedly resolved to an empty setpoint")
        source = (
            "default on"
            if result.source is None
            else scenario.source_names[result.source]
        )
        dispatched_power = scenario.available_power_mw[index] if result.value else 0.0
        print(
            f"{slot.isoformat(timespec='minutes'):<22} | "
            f"{scenario.day_ahead_prices_eur_mwh[index]:>8.1f} | "
            f"{scenario.live_prices_eur_mwh[index]:>10.1f} | "
            f"{scenario.available_power_mw[index]:>12.1f} | "
            f"{dispatched_power:>11.1f} | {source}"
        )


if __name__ == "__main__":
    main()
