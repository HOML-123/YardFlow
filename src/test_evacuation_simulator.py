
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evacuation_simulator import simulate_evacuation


class TestEvacuationSimulator(unittest.TestCase):

    def test_baseline_accounts_for_all_containers(self):
        hourly, summary = simulate_evacuation(
            scenario_name="Test Baseline",
            total_containers=100,
            arrivals_per_hour=10,
            total_trucks=4,
            containers_per_truck_per_hour=5,
            simulation_limit_hours=24
        )

        self.assertEqual(summary["total_container_demand"], 100)
        self.assertEqual(summary["total_containers_arrived"], 100)
        self.assertEqual(summary["total_containers_evacuated"], 100)
        self.assertEqual(summary["containers_still_waiting"], 0)
        self.assertTrue(summary["completed_within_limit"])

    def test_zero_capacity_disruption_leaves_a_queue(self):
        hourly, summary = simulate_evacuation(
            scenario_name="Test Full Disruption",
            total_containers=100,
            arrivals_per_hour=10,
            total_trucks=4,
            containers_per_truck_per_hour=5,
            simulation_limit_hours=10,
            disruption_start_hour=1,
            disruption_end_hour=10,
            disruption_availability=0
        )

        self.assertEqual(summary["total_containers_evacuated"], 20)
        self.assertEqual(summary["containers_still_waiting"], 80)
        self.assertFalse(summary["completed_within_limit"])

    def test_disruption_increases_queue(self):
        baseline_hourly, baseline_summary = simulate_evacuation(
            scenario_name="Test Baseline",
            total_containers=300,
            arrivals_per_hour=30,
            total_trucks=4,
            containers_per_truck_per_hour=5,
            simulation_limit_hours=24
        )

        disrupted_hourly, disrupted_summary = simulate_evacuation(
            scenario_name="Test Disruption",
            total_containers=300,
            arrivals_per_hour=30,
            total_trucks=4,
            containers_per_truck_per_hour=5,
            simulation_limit_hours=24,
            disruption_start_hour=2,
            disruption_end_hour=8,
            disruption_availability=0.5
        )

        self.assertGreater(
            disrupted_summary["maximum_queue"],
            baseline_summary["maximum_queue"]
        )

    def test_recovery_trucks_reduce_queue_hours(self):
        baseline_hourly, baseline_summary = simulate_evacuation(
            scenario_name="Test Disruption",
            total_containers=900,
            arrivals_per_hour=30,
            total_trucks=4,
            containers_per_truck_per_hour=5,
            simulation_limit_hours=24,
            disruption_start_hour=2,
            disruption_end_hour=8,
            disruption_availability=0.5
        )

        recovery_hourly, recovery_summary = simulate_evacuation(
            scenario_name="Test Recovery",
            total_containers=900,
            arrivals_per_hour=30,
            total_trucks=4,
            containers_per_truck_per_hour=5,
            simulation_limit_hours=24,
            disruption_start_hour=2,
            disruption_end_hour=8,
            disruption_availability=0.5,
            extra_trucks_start_hour=8,
            extra_trucks_end_hour=16,
            extra_trucks=4
        )

        self.assertLess(
            recovery_summary["queue_hours"],
            baseline_summary["queue_hours"]
        )

    def test_hourly_results_have_required_fields(self):
        hourly, summary = simulate_evacuation(
            scenario_name="Test Fields",
            total_containers=100,
            arrivals_per_hour=10,
            total_trucks=4,
            containers_per_truck_per_hour=5,
            simulation_limit_hours=12
        )

        required_columns = {
            "hour",
            "arrivals",
            "queue_remaining",
            "containers_evacuated",
            "cumulative_evacuated",
            "available_capacity"
        }

        self.assertTrue(required_columns.issubset(set(hourly.columns)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
