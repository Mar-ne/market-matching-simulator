"""Run integer or continuous markets and save reproducible CSV results."""

import argparse
import csv
import random
from datetime import datetime
from pathlib import Path

from market import RULES, first_available_market, optimal_market_surplus, seller_orders

ROOT = Path(__file__).resolve().parent


def simulate_market(size, seed, orders=100, distribution="integer"):
    """Return three summary rows for one market, sharing buyer shuffles."""
    if size < 1 or orders < 1:
        raise ValueError("Size and orders must be positive.")
    if distribution not in ("integer", "continuous"):
        raise ValueError("Unknown distribution.")
    rng = random.Random(seed)
    shuffle_rng = random.Random(10000 + seed)
    draw = (lambda: rng.randint(1, 100)) if distribution == "integer" else rng.random
    buyers = [draw() for _ in range(size)]
    sellers = [draw() for _ in range(size)]
    optimum = optimal_market_surplus(buyers, sellers)
    variants = seller_orders(sellers)
    totals = {rule: 0 for rule in RULES}
    counts = {rule: 0 for rule in RULES}
    for _ in range(orders):
        buyer_order = buyers.copy()
        shuffle_rng.shuffle(buyer_order)
        for rule, seller_order in variants.items():
            surplus, trades = first_available_market(buyer_order, seller_order)
            totals[rule] += surplus
            counts[rule] += trades
    return [dict(
        distribution=distribution, market_seed=seed, shuffle_seed=10000 + seed,
        market_size=size, orders_per_market=orders, rule=rule,
        optimal_surplus=optimum, average_surplus=totals[rule] / orders,
        efficiency=totals[rule] / orders / optimum if optimum > 0 else None,
        average_trades=counts[rule] / orders,
        surplus_per_trade=totals[rule] / counts[rule] if counts[rule] else None,
    ) for rule in RULES]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distribution", choices=["integer", "continuous"], default="integer")
    parser.add_argument("--sizes", type=int, nargs="+", default=[50, 100, 200, 500])
    parser.add_argument("--markets", type=int, default=20)
    parser.add_argument("--orders", type=int, default=100)
    args = parser.parse_args()
    if min(args.sizes + [args.markets, args.orders]) < 1:
        parser.error("Sizes, markets and orders must all be positive.")
    folder = ROOT / ("results" if args.distribution == "integer" else "results_continuous")
    folder.mkdir(exist_ok=True)
    for size in sorted(set(args.sizes)):
        rows = []
        for seed in range(args.markets):
            rows.extend(simulate_market(size, seed, args.orders, args.distribution))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output = folder / f"market_results_n{size}_{timestamp}.csv"
        with output.open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Saved {len(rows)} rows to {output}", flush=True)


if __name__ == "__main__":
    main()
