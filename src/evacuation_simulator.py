
import math
import pandas as pd


def simulate_evacuation(
    scenario_name,
    total_containers=900,
    arrivals_per_hour=30,
    total_trucks=8,
    containers_per_truck_per_hour=4,
    simulation_limit_hours=48,
    disruption_start_hour=None,
    disruption_end_hour=None,
    disruption_availability=1.0,
    extra_trucks_start_hour=None,
    extra_trucks_end_hour=None,
    extra_trucks=0,
    recovery_start_hour=None,
    recovery_end_hour=None,
    recovery_service_multiplier=1.0,
):
    if total_containers < 0:
        raise ValueError("Total containers cannot be negative.")

    if arrivals_per_hour <= 0:
        raise ValueError("Arrivals per hour must be greater than zero.")

    if total_trucks < 0 or extra_trucks < 0:
        raise ValueError("Truck counts cannot be negative.")

    if containers_per_truck_per_hour <= 0:
        raise ValueError("Service rate must be greater than zero.")

    if simulation_limit_hours <= 0:
        raise ValueError("Simulation limit must be greater than zero.")

    if not 0 <= disruption_availability <= 1:
        raise ValueError("Disruption availability must be between 0 and 1.")

    if recovery_service_multiplier < 1:
        raise ValueError("Recovery service multiplier must be at least 1.")

    intervals = [
        (disruption_start_hour, disruption_end_hour, "disruption"),
        (extra_trucks_start_hour, extra_trucks_end_hour, "extra trucks"),
        (recovery_start_hour, recovery_end_hour, "recovery"),
    ]

    for start, end, label in intervals:
        if (start is None) != (end is None):
            raise ValueError(
                f"Both start and end hours must be provided for {label}."
            )

        if start is not None and (start < 1 or end < start):
            raise ValueError(f"Invalid {label} time interval.")

    remaining_to_arrive = total_containers
    queue = 0
    cumulative_evacuated = 0
    records = []
    completion_hour = 0 if total_containers == 0 else None

    for hour in range(1, simulation_limit_hours + 1):
        arrivals = min(arrivals_per_hour, remaining_to_arrive)
        remaining_to_arrive -= arrivals
        queue += arrivals

        disruption_active = (
            disruption_start_hour is not None
            and disruption_start_hour <= hour < disruption_end_hour
        )

        extra_resources_active = (
            extra_trucks_start_hour is not None
            and extra_trucks_start_hour <= hour < extra_trucks_end_hour
        )

        recovery_active = (
            recovery_start_hour is not None
            and recovery_start_hour <= hour < recovery_end_hour
        )

        availability = (
            disruption_availability if disruption_active else 1.0
        )

        available_trucks = math.floor(total_trucks * availability)

        if extra_resources_active:
            available_trucks += extra_trucks

        service_multiplier = (
            recovery_service_multiplier if recovery_active else 1.0
        )

        hourly_capacity = math.floor(
            available_trucks
            * containers_per_truck_per_hour
            * service_multiplier
        )

        queue_before_evacuation = queue
        evacuated = min(queue, hourly_capacity)
        queue -= evacuated
        cumulative_evacuated += evacuated

        resource_utilisation = (
            evacuated / hourly_capacity * 100
            if hourly_capacity > 0
            else 0.0
        )

        records.append({
            "scenario": scenario_name,
            "hour": hour,
            "arrivals": arrivals,
            "queue_before_evacuation": queue_before_evacuation,
            "available_trucks": available_trucks,
            "available_capacity": hourly_capacity,
            "containers_evacuated": evacuated,
            "queue_remaining": queue,
            "cumulative_evacuated": cumulative_evacuated,
            "resource_utilisation_percent": round(
                resource_utilisation, 2
            ),
            "disruption_active": disruption_active,
            "extra_resources_active": extra_resources_active,
            "recovery_active": recovery_active,
        })

        if (
            remaining_to_arrive == 0
            and queue == 0
            and completion_hour is None
        ):
            completion_hour = hour
            break

    hourly_results = pd.DataFrame(records)

    if hourly_results.empty:
        raise RuntimeError("The simulation produced no hourly records.")

    total_arrived = int(hourly_results["arrivals"].sum())
    total_evacuated = int(hourly_results["containers_evacuated"].sum())
    containers_still_waiting = int(queue)

    completed = (
        remaining_to_arrive == 0
        and containers_still_waiting == 0
    )

    summary = {
        "scenario": scenario_name,
        "total_container_demand": total_containers,
        "total_containers_arrived": total_arrived,
        "total_containers_evacuated": total_evacuated,
        "containers_still_waiting": containers_still_waiting,
        "containers_not_yet_arrived": int(remaining_to_arrive),
        "total_trucks": total_trucks,
        "extra_trucks_configured": extra_trucks,
        "baseline_hourly_capacity": (
            total_trucks * containers_per_truck_per_hour
        ),
        "maximum_queue": int(
            hourly_results["queue_remaining"].max()
        ),
        "average_queue": round(
            hourly_results["queue_remaining"].mean(), 2
        ),
        "queue_hours": int(
            hourly_results["queue_remaining"].sum()
        ),
        "completion_hour": completion_hour,
        "simulation_hours_run": len(hourly_results),
        "completed_within_limit": completed,
        "average_hourly_resource_utilisation_percent": round(
            hourly_results["resource_utilisation_percent"].mean(), 2
        ),
    }

    return hourly_results, summary
