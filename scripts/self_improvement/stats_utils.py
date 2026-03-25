"""
Statistical utility functions for the self-improvement loop.

Provides Welch's t-test, confidence intervals, seasonality detection,
and formatted summary output for pattern analysis.
"""

import math
from datetime import datetime
from typing import Any


def welch_ttest(group_a: list[float], group_b: list[float]) -> dict[str, Any]:
    """Run Welch's t-test (unequal variance) comparing two groups.

    Returns dict with t_stat, p_value, significant, ci_low, ci_high,
    mean_diff, and pct_diff. Falls back gracefully when scipy is missing
    or sample sizes are too small.
    """
    result = {
        "t_stat": 0.0,
        "p_value": 1.0,
        "significant": False,
        "ci_low": 0.0,
        "ci_high": 0.0,
        "mean_diff": 0.0,
        "pct_diff": 0.0,
    }

    # Edge cases: need at least 2 in each group for variance
    if len(group_a) < 2 or len(group_b) < 2:
        return result

    mean_a = sum(group_a) / len(group_a)
    mean_b = sum(group_b) / len(group_b)
    result["mean_diff"] = mean_a - mean_b
    result["pct_diff"] = (mean_a - mean_b) / max(abs(mean_b), 1e-9) * 100

    # Zero variance in either group → can't compute t-test
    var_a = sum((x - mean_a) ** 2 for x in group_a) / (len(group_a) - 1)
    var_b = sum((x - mean_b) ** 2 for x in group_b) / (len(group_b) - 1)
    if var_a == 0 and var_b == 0:
        return result

    try:
        from scipy.stats import ttest_ind
    except ImportError:
        raise ImportError(
            "scipy is required for statistical guardrails. "
            "Install it with: pip install scipy>=1.11.0"
        )

    stat_result = ttest_ind(group_a, group_b, equal_var=False)
    t_stat = float(stat_result.statistic)
    p_value = float(stat_result.pvalue)

    # Handle NaN from degenerate inputs
    if math.isnan(t_stat) or math.isnan(p_value):
        return result

    result["t_stat"] = round(t_stat, 4)
    result["p_value"] = round(p_value, 4)
    result["significant"] = p_value < 0.05  # caller can override threshold

    # Confidence interval for the difference
    ci_low, ci_high = confidence_interval_pct(group_a, group_b)
    result["ci_low"] = ci_low
    result["ci_high"] = ci_high

    return result


def confidence_interval_pct(
    group_a: list[float], group_b: list[float], confidence: float = 0.95
) -> tuple[float, float]:
    """Compute analytical CI for percentage difference (mean_a - mean_b) / mean_b.

    Returns (ci_low, ci_high) as percentages.
    """
    if len(group_a) < 2 or len(group_b) < 2:
        return (0.0, 0.0)

    mean_a = sum(group_a) / len(group_a)
    mean_b = sum(group_b) / len(group_b)
    if abs(mean_b) < 1e-9:
        return (0.0, 0.0)

    n_a, n_b = len(group_a), len(group_b)
    var_a = sum((x - mean_a) ** 2 for x in group_a) / (n_a - 1)
    var_b = sum((x - mean_b) ** 2 for x in group_b) / (n_b - 1)

    se = math.sqrt(var_a / n_a + var_b / n_b)

    # Welch-Satterthwaite degrees of freedom
    num = (var_a / n_a + var_b / n_b) ** 2
    denom_a = (var_a / n_a) ** 2 / (n_a - 1) if var_a > 0 else 0
    denom_b = (var_b / n_b) ** 2 / (n_b - 1) if var_b > 0 else 0
    denom = denom_a + denom_b
    if denom == 0:
        return (0.0, 0.0)
    df = num / denom

    try:
        from scipy.stats import t as t_dist
    except ImportError:
        # Approximate with z for large df
        t_crit = 1.96
    else:
        alpha = 1 - confidence
        t_crit = float(t_dist.ppf(1 - alpha / 2, df))

    diff = mean_a - mean_b
    ci_low_abs = diff - t_crit * se
    ci_high_abs = diff + t_crit * se

    # Convert to percentage relative to mean_b
    ci_low_pct = round(ci_low_abs / abs(mean_b) * 100, 1)
    ci_high_pct = round(ci_high_abs / abs(mean_b) * 100, 1)

    return (ci_low_pct, ci_high_pct)


def is_seasonal(
    entries: list[dict], date_field: str = "published_at", window_days: int = 14
) -> bool:
    """Check if all entries fall within a single narrow time window.

    Returns True only if ALL entries are within `window_days` of each other,
    suggesting the pattern may be seasonal rather than persistent.
    """
    dates = []
    for e in entries:
        raw = e.get(date_field)
        if not raw:
            continue
        try:
            dates.append(datetime.fromisoformat(str(raw)))
        except (ValueError, TypeError):
            continue

    if len(dates) < 2:
        return False

    earliest = min(dates)
    latest = max(dates)
    span = (latest - earliest).days

    return span <= window_days


def format_stat_summary(
    label: str,
    pct_diff: float,
    ci_low: float,
    ci_high: float,
    p_value: float,
    n: int,
) -> str:
    """Format a human-readable statistical summary.

    Example: "Tuesday posts perform 23% better [CI: 8%-38%, p=0.02, n=14]"
    """
    return (
        f"{label} perform {pct_diff:+.0f}% better "
        f"[CI: {ci_low:.0f}%-{ci_high:.0f}%, p={p_value:.2f}, n={n}]"
    )
