"""Run with python -m unittest -v test_market."""

import itertools
import unittest

from market import first_available_market, optimal_market_surplus
from run_experiment import simulate_market


def brute_force_optimum(buyers, sellers):
    """Independent oracle: try skipping or matching each buyer to any seller."""
    if not buyers:
        return 0
    best = brute_force_optimum(buyers[1:], sellers)
    for index, cost in enumerate(sellers):
        best = max(best, buyers[0] - cost + brute_force_optimum(
            buyers[1:], sellers[:index] + sellers[index + 1:]))
    return best


class MarketTests(unittest.TestCase):
    def test_one_trade_per_buyer_and_seller(self):
        self.assertEqual(first_available_market([10], [3, 4, 5]), (7, 1))
        self.assertEqual(first_available_market([10, 9], [3]), (7, 1))

    def test_inputs_unchanged(self):
        buyers, sellers = [7, 10], [3, 8]
        first_available_market(buyers, sellers)
        self.assertEqual(buyers, [7, 10])
        self.assertEqual(sellers, [3, 8])

    def test_rejection_skips_seller_not_buyer(self):
        self.assertEqual(first_available_market([7], [8, 3]), (4, 1))

    def test_empty_and_no_gain(self):
        for buyers, sellers in [([], [1]), ([2], []), ([2, 3], [5, 8]), ([3], [3])]:
            self.assertEqual(first_available_market(buyers, sellers), (0, 0))
            self.assertEqual(optimal_market_surplus(buyers, sellers), 0)

    def test_exact_expected_surplus(self):
        orders = list(itertools.permutations([7, 10]))
        self.assertEqual(sum(first_available_market(b, [3, 8])[0] for b in orders) / 2, 6.5)
        self.assertEqual(sum(first_available_market(b, [8, 3])[0] for b in orders) / 2, 6)

    def test_benchmark_against_exhaustive_allocations(self):
        # 729 markets, including equal values and duplicates.
        for values in itertools.product(range(3), repeat=6):
            buyers, sellers = values[:3], values[3:]
            optimum = optimal_market_surplus(buyers, sellers)
            self.assertEqual(optimum, brute_force_optimum(buyers, sellers))
            surplus, count = first_available_market(buyers, sellers)
            self.assertTrue(0 <= surplus <= optimum)
            self.assertLessEqual(count, min(len(buyers), len(sellers)))
        self.assertEqual(optimal_market_surplus([10, 8, 7], [2]), 8)

    def test_seed_reproducibility(self):
        for distribution in ["integer", "continuous"]:
            self.assertEqual(simulate_market(10, 4, 10, distribution),
                             simulate_market(10, 4, 10, distribution))


if __name__ == "__main__":
    unittest.main()
