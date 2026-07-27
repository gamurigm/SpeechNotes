"""Evalúa el JTL CSV de JMeter sin dependencias externas."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path


def percentile(values: list[int], quantile: float) -> int:
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jtl", type=Path)
    parser.add_argument("--max-error-rate", type=float, default=1.0)
    parser.add_argument("--max-p95-ms", type=int, default=2000)
    parser.add_argument("--min-samples", type=int, default=100)
    args = parser.parse_args()

    with args.jtl.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))

    if len(rows) < args.min_samples:
        print(f"FAIL samples={len(rows)} expected>={args.min_samples}")
        return 1

    elapsed = [int(row["elapsed"]) for row in rows]
    failures = sum(row.get("success", "false").lower() != "true" for row in rows)
    error_rate = failures / len(rows) * 100
    p95_ms = percentile(elapsed, 0.95)
    status = error_rate <= args.max_error_rate and p95_ms <= args.max_p95_ms
    print(
        f"{'PASS' if status else 'FAIL'} samples={len(rows)} failures={failures} "
        f"error_rate={error_rate:.2f}% p95_ms={p95_ms}"
    )
    return 0 if status else 1


if __name__ == "__main__":
    sys.exit(main())
