"""Matching rules shared by the experiments. No files are written on import."""

RULES = ("Original", "Cheapest first", "Most expensive first")


def first_available_market(buyers, sellers):
    """Return (surplus, trade count); preserve inputs and allow one trade each.

    All sellers start available. Each buyer checks sellers in the supplied
    order and buys from the first with cost strictly below their valuation.
    """
    available = list(sellers)
    surplus = 0
    trades = 0
    for value in buyers:
        for index, cost in enumerate(available):
            if value > cost:
                surplus += value - cost
                trades += 1
                available.pop(index)
                break
    return surplus, trades


def optimal_market_surplus(buyers, sellers):
    """Maximum total surplus, including when the two sides differ in size."""
    surplus = 0
    for value, cost in zip(sorted(buyers, reverse=True), sorted(sellers)):
        if value <= cost:
            break
        surplus += value - cost
    return surplus


def seller_orders(sellers):
    return {
        "Original": list(sellers),
        "Cheapest first": sorted(sellers),
        "Most expensive first": sorted(sellers, reverse=True),
    }
