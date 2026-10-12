"""Run beside 2.py to plot the latest saved experiment for each market size."""

import argparse
import csv
import math
from pathlib import Path
from statistics import mean, stdev

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


parser = argparse.ArgumentParser(description="Plot saved experiment means and confidence intervals.")
parser.add_argument("--distribution", choices=["integer", "continuous"], default="integer")
parser.add_argument("--sizes", type=int, nargs="+", default=[50, 100, 200, 500])
parser.add_argument("--no-show", action="store_true", help="Save without opening a window.")
args = parser.parse_args()
folder = Path(__file__).resolve().parent / ("results" if args.distribution == "integer" else "results_continuous")
sizes = sorted(set(args.sizes))
rules = ["Original", "Cheapest first", "Most expensive first"]
colors = ["#3465A4", "#17836B", "#C05A35"]
averages = {rule: [] for rule in rules}
margins = {rule: [] for rule in rules}
# Two-sided 95% t critical value for 20 independent markets (19 df).
t_critical = 2.093024054
reference_settings = None
sources = []

for size in sizes:
    # Timestamped filenames sort chronologically. Use one run per size,
    # so rerunning an experiment does not double-count its markets.
    candidates = sorted(folder.glob(f"market_results_n{size}_*.csv"))
    if not candidates:
        raise FileNotFoundError(f"No saved experiment for size {size} in {folder}")
    source = candidates[-1]
    with source.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    settings = {}
    grouped = {rule: [] for rule in rules}
    for row in rows:
        rule = row["rule"]
        seed = int(row["market_seed"])
        key = (seed, rule)
        if int(row["market_size"]) != size or rule not in rules:
            raise ValueError(f"Unexpected size or rule in {source.name}")
        if key in settings:
            raise ValueError(f"Duplicate market/rule in {source.name}: {key}")
        settings[key] = (int(row["shuffle_seed"]), int(row["orders_per_market"]))
        if row.get("distribution", args.distribution) != args.distribution:
            raise ValueError(f"Distribution mismatch in {source.name}")
        if not row["efficiency"]:
            raise ValueError("Undefined efficiency: this plot requires positive-surplus markets.")
        efficiency = float(row["efficiency"])
        if not math.isfinite(efficiency) or not 0 <= efficiency <= 1:
            raise ValueError(f"Invalid efficiency in {source.name}: {efficiency}")
        grouped[rule].append(efficiency)

    seeds = {seed for seed, rule in settings}
    if not seeds or set(settings) != {(seed, rule) for seed in seeds for rule in rules}:
        raise ValueError(f"Missing market/rule rows in {source.name}")
    if reference_settings is None:
        reference_settings = settings
    elif settings != reference_settings:
        raise ValueError("Market seeds, shuffle seeds or repetition counts differ between files.")

    sources.append(source.name)
    print(f"Using {source.name}")
    for rule in rules:
        values = grouped[rule]
        if len(values) != 20:
            raise ValueError("This t critical value requires exactly 20 markets per rule.")
        average = 100 * mean(values)
        margin = 100 * t_critical * stdev(values) / math.sqrt(len(values))
        averages[rule].append(average)
        margins[rule].append(margin)
        print(f"  {rule}: {average:.2f}% (95% CI {average-margin:.2f}% to {average+margin:.2f}%)")

# Each plotted point gives every market equal weight.
fig, ax = plt.subplots(figsize=(9, 5.5), layout="constrained")
for rule, color in zip(rules, colors):
    values = averages[rule]
    ax.errorbar(sizes, values, yerr=margins[rule], marker="o", linewidth=2.3,
                capsize=4, color=color, label=rule)
    for size, value, margin in zip(sizes, values, margins[rule]):
        ax.annotate(f"{value:.1f}%", (size, value + margin), xytext=(0, 8),
                    textcoords="offset points", ha="center", fontsize=9, color=color)

ax.axhline(100 * (1 - math.exp(-2)), color="#555555", linestyle="--",
           linewidth=1.2, label="Cheapest-first theory: 86.47%")
ax.set_title(
    f"Market efficiency - {args.distribution} uniform values",
    fontsize=16,
    pad=16,
)
ax.set_xlabel("Buyers and sellers per side")
ax.set_ylabel("Mean allocative efficiency")
ax.set_xticks(sizes)
ax.set_ylim(0, 105)
ax.yaxis.set_major_formatter(PercentFormatter(xmax=100))
ax.grid(axis="y", alpha=0.2)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="center right", frameon=False)
repetitions = sorted({orders for shuffle, orders in reference_settings.values()})
fig.supxlabel(
    f"{len(seeds)} markets per size; buyer-order repetitions per market: {repetitions}.\n"
    "Error bars: pointwise 95% t intervals across markets (19 df).\n"
    "Theory assumes continuous uniform values and a large market.",
    fontsize=9,
)

output = folder / "efficiency_by_market_size_ci.png"
fig.savefig(output, dpi=200)
# Keep the exact input filenames with the graph for reproducibility.
output.with_suffix(".sources.txt").write_text("\n".join(sources) + "\n", encoding="utf-8")
print(f"Saved graph to: {output}")
if not args.no_show:
    plt.show()
else:
    plt.close(fig)

