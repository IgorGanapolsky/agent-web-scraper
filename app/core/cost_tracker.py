"""Module for tracking API usage and costs."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

# Default cost per API call (in USD)
DEFAULT_COST_PER_CALL = 0.01


class CostTracker:
    """Track API usage and costs."""

    def __init__(self, data_dir: str = "data/usage"):
        """Initialize the cost tracker.

        Args:
            data_dir: Directory to store usage data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.current_month = datetime.now().strftime("%Y-%m")
        self.usage_file = self.data_dir / f"api_usage_{self.current_month}.json"
        self._ensure_usage_file()

    def _ensure_usage_file(self) -> None:
        """Ensure the usage file exists with proper structure."""
        if not self.usage_file.exists():
            self._initialize_usage_file()

    def _initialize_usage_file(self) -> None:
        """Initialize a new usage file for the current month."""
        data = {
            "month": self.current_month,
            "total_searches": 0,
            "total_cost": 0.0,
            "searches": [],
        }
        with open(self.usage_file, "w") as f:
            json.dump(data, f, indent=2)

    def track_usage(
        self, cost: float = DEFAULT_COST_PER_CALL, **metadata
    ) -> dict[str, Any]:
        """Track an API call with its associated cost.

        Args:
            cost: Cost of the API call in USD
            **metadata: Additional metadata to store with the usage record

        Returns:
            Dict containing the updated usage data
        """
        # Check if we need to rotate to a new month
        current_month = datetime.now().strftime("%Y-%m")
        if current_month != self.current_month:
            self.current_month = current_month
            self.usage_file = self.data_dir / f"api_usage_{self.current_month}.json"
            self._ensure_usage_file()

        # Load existing data
        with open(self.usage_file) as f:
            data = cast(dict[str, Any], json.load(f))

        # Update data
        search_data = {
            "timestamp": datetime.now().isoformat(),
            "cost": cost,
            **metadata,
        }

        data["searches"].append(search_data)
        data["total_searches"] += 1
        data["total_cost"] = round(data["total_cost"] + cost, 2)

        # Save updated data
        with open(self.usage_file, "w") as f:
            json.dump(data, f, indent=2)

        return data

    def get_current_month_usage(self) -> dict[str, Any]:
        """Get the current month's usage data.

        Returns:
            Dict containing the current month's usage data
        """
        if not self.usage_file.exists():
            return {
                "month": self.current_month,
                "total_searches": 0,
                "total_cost": 0.0,
                "searches": [],
            }

        with open(self.usage_file) as f:
            # Assuming the loaded JSON conforms to Dict[str, Any]
            return cast(dict[str, Any], json.load(f))

    def get_historical_usage(self) -> list[dict[str, Any]]:
        """Get historical usage data for all months.

        Returns:
            List of monthly usage data
        """
        usage_files = sorted(self.data_dir.glob("api_usage_*.json"))
        historical_data = []

        for file in usage_files:
            with open(file) as f:
                # Assuming the loaded JSON conforms to Dict[str, Any]
                historical_data.append(cast(dict[str, Any], json.load(f)))

        return historical_data


# Global instance for easy importing
cost_tracker = CostTracker()


def track_api_usage(cost: float = DEFAULT_COST_PER_CALL, **metadata) -> dict[str, Any]:
    """Convenience function to track API usage.

    Args:
        cost: Cost of the API call in USD
        **metadata: Additional metadata to store with the usage record

    Returns:
        Dict containing the updated usage data
    """
    return cost_tracker.track_usage(cost, **metadata)


def get_usage_summary() -> dict[str, Any]:
    """Get a summary of the current month's API usage.

    Returns:
        Dict containing usage summary
    """
    usage = cost_tracker.get_current_month_usage()
    return {
        "month": usage["month"],
        "total_searches": usage["total_searches"],
        "total_cost": usage["total_cost"],
        "average_cost_per_search": (
            round(usage["total_cost"] / usage["total_searches"], 4)
            if usage["total_searches"] > 0
            else 0
        ),
    }
