"""
Performance metrics collection for LLM calls.

This module provides classes for collecting and tracking performance metrics
such as response times, token usage, and error rates.
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, List, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LLMCallMetrics:
    """Data class for storing metrics from a single LLM call."""

    model: str
    duration: float
    input_tokens: int
    output_tokens: int
    success: bool
    error_type: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    @property
    def total_tokens(self) -> int:
        """Get total token count (input + output)."""
        return self.input_tokens + self.output_tokens

    @property
    def tokens_per_second(self) -> float:
        """Get processing rate in tokens per second."""
        if self.duration <= 0:
            return 0.0
        return self.total_tokens / self.duration


class MetricsCollector:
    """
    Thread-safe metrics collector for LLM performance monitoring.

    This class collects and aggregates metrics from LLM calls, providing
    both real-time and historical performance insights.
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize the metrics collector.

        Args:
            max_history: Maximum number of call metrics to keep in memory
        """
        self.max_history = max_history
        self._lock = Lock()
        self._call_history: deque = deque(maxlen=max_history)
        self._model_stats = defaultdict(
            lambda: {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_duration": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "error_counts": defaultdict(int),
            }
        )

        logger.debug(f"Initialized MetricsCollector with max_history={max_history}")

    def record_success(
        self, model: str, duration: float, input_tokens: int, output_tokens: int
    ) -> None:
        """
        Record a successful LLM call.

        Args:
            model: The model identifier used
            duration: Time taken for the call in seconds
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        metrics = LLMCallMetrics(
            model=model,
            duration=duration,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            success=True,
        )

        self._record_metrics(metrics)
        logger.debug(
            f"Recorded successful call for {model}: {duration:.2f}s, {metrics.total_tokens} tokens"
        )

    def record_error(self, model: str, error_type: str, duration: float) -> None:
        """
        Record a failed LLM call.

        Args:
            model: The model identifier used
            error_type: Type of error that occurred
            duration: Time taken before the error occurred in seconds
        """
        metrics = LLMCallMetrics(
            model=model,
            duration=duration,
            input_tokens=0,  # Unknown for failed calls
            output_tokens=0,
            success=False,
            error_type=error_type,
        )

        self._record_metrics(metrics)
        logger.debug(
            f"Recorded failed call for {model}: {error_type} after {duration:.2f}s"
        )

    def _record_metrics(self, metrics: LLMCallMetrics) -> None:
        """Thread-safe method to record metrics internally."""
        with self._lock:
            # Add to call history
            self._call_history.append(metrics)

            # Update model statistics
            stats = self._model_stats[metrics.model]
            stats["total_calls"] += 1
            stats["total_duration"] += metrics.duration
            stats["total_input_tokens"] += metrics.input_tokens
            stats["total_output_tokens"] += metrics.output_tokens

            if metrics.success:
                stats["successful_calls"] += 1
            else:
                stats["failed_calls"] += 1
                if metrics.error_type:
                    stats["error_counts"][metrics.error_type] += 1

    def get_model_stats(self, model: str) -> Dict[str, Any]:
        """
        Get aggregated statistics for a specific model.

        Args:
            model: The model identifier

        Returns:
            Dictionary containing aggregated statistics
        """
        with self._lock:
            if model not in self._model_stats:
                return {}

            stats = self._model_stats[model].copy()

            # Calculate derived metrics
            if stats["total_calls"] > 0:
                stats["success_rate"] = stats["successful_calls"] / stats["total_calls"]
                stats["failure_rate"] = stats["failed_calls"] / stats["total_calls"]
                stats["average_duration"] = (
                    stats["total_duration"] / stats["total_calls"]
                )
            else:
                stats["success_rate"] = 0.0
                stats["failure_rate"] = 0.0
                stats["average_duration"] = 0.0

            total_tokens = stats["total_input_tokens"] + stats["total_output_tokens"]
            if stats["total_duration"] > 0:
                stats["average_tokens_per_second"] = (
                    total_tokens / stats["total_duration"]
                )
            else:
                stats["average_tokens_per_second"] = 0.0

            # Convert error_counts to regular dict for JSON serialization
            stats["error_counts"] = dict(stats["error_counts"])

            return stats

    def get_overall_stats(self) -> Dict[str, Any]:
        """
        Get aggregated statistics across all models.

        Returns:
            Dictionary containing overall statistics
        """
        with self._lock:
            if not self._model_stats:
                return {}

            overall = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_duration": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "models": list(self._model_stats.keys()),
                "error_counts": defaultdict(int),
            }

            # Aggregate across all models
            for stats in self._model_stats.values():
                overall["total_calls"] += stats["total_calls"]
                overall["successful_calls"] += stats["successful_calls"]
                overall["failed_calls"] += stats["failed_calls"]
                overall["total_duration"] += stats["total_duration"]
                overall["total_input_tokens"] += stats["total_input_tokens"]
                overall["total_output_tokens"] += stats["total_output_tokens"]

                for error_type, count in stats["error_counts"].items():
                    overall["error_counts"][error_type] += count

            # Calculate derived metrics
            if overall["total_calls"] > 0:
                overall["success_rate"] = (
                    overall["successful_calls"] / overall["total_calls"]
                )
                overall["failure_rate"] = (
                    overall["failed_calls"] / overall["total_calls"]
                )
                overall["average_duration"] = (
                    overall["total_duration"] / overall["total_calls"]
                )
            else:
                overall["success_rate"] = 0.0
                overall["failure_rate"] = 0.0
                overall["average_duration"] = 0.0

            total_tokens = (
                overall["total_input_tokens"] + overall["total_output_tokens"]
            )
            if overall["total_duration"] > 0:
                overall["average_tokens_per_second"] = (
                    total_tokens / overall["total_duration"]
                )
            else:
                overall["average_tokens_per_second"] = 0.0

            # Convert error_counts to regular dict
            overall["error_counts"] = dict(overall["error_counts"])

            return overall

    def get_recent_calls(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent LLM calls.

        Args:
            count: Number of recent calls to return

        Returns:
            List of recent call metrics as dictionaries
        """
        with self._lock:
            recent_calls = list(self._call_history)[-count:]
            return [
                {
                    "model": call.model,
                    "duration": call.duration,
                    "input_tokens": call.input_tokens,
                    "output_tokens": call.output_tokens,
                    "total_tokens": call.total_tokens,
                    "tokens_per_second": call.tokens_per_second,
                    "success": call.success,
                    "error_type": call.error_type,
                    "timestamp": call.timestamp,
                }
                for call in recent_calls
            ]

    def clear_metrics(self) -> None:
        """Clear all collected metrics. Useful for testing."""
        with self._lock:
            self._call_history.clear()
            self._model_stats.clear()
        logger.debug("Cleared all metrics")

    def get_metrics_summary(self) -> str:
        """
        Get a human-readable summary of current metrics.

        Returns:
            Formatted string summary of metrics
        """
        overall = self.get_overall_stats()
        if not overall:
            return "No metrics available"

        summary = f"""
LLM Metrics Summary:
  Total Calls: {overall['total_calls']}
  Success Rate: {overall['success_rate']:.1%}
  Average Duration: {overall['average_duration']:.2f}s
  Average Tokens/sec: {overall['average_tokens_per_second']:.1f}
  Total Tokens: {overall['total_input_tokens'] + overall['total_output_tokens']:,}
  Models: {', '.join(overall['models'])}
        """.strip()

        if overall["error_counts"]:
            error_summary = ", ".join(
                [
                    f"{error}: {count}"
                    for error, count in overall["error_counts"].items()
                ]
            )
            summary += f"\n  Errors: {error_summary}"

        return summary
