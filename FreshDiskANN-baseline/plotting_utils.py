from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


ITERATION_RE = re.compile(r"Running with i = (?P<value>-?\d+)")
SEARCH_TIME_RE = re.compile(r"search current time:\s*(?P<value>-?\d+)")


SCHEMAS = (
    {
        "name": "search_memory_index",
        "markers": ("Mean Latency (ms)", "99.9 Latency"),
        "columns": (
            "l_search",
            "qps",
            "mean_latency_ms",
            "p999_latency_ms",
            "recall",
        ),
    },
    {
        "name": "search_disk_index",
        "markers": ("Beamwidth", "Mean IOs", "CPU (s)"),
        "columns": (
            "l_search",
            "beamwidth",
            "qps",
            "mean_latency_ms",
            "p999_latency_ms",
            "mean_ios",
            "cpu_us_reported",
            "recall",
        ),
    },
    {
        "name": "motivation_or_overall",
        "markers": ("50 Lat", "90 Lat", "95 Lat", "99 Lat", "Disk IOs"),
        "columns": (
            "l_search",
            "qps",
            "mean_latency_ms",
            "p50_latency_ms",
            "p90_latency_ms",
            "p95_latency_ms",
            "p99_latency_ms",
            "p999_latency_ms",
            "recall",
            "mean_ios",
        ),
    },
)


def _find_schema(line: str) -> Optional[Dict[str, Any]]:
    for schema in SCHEMAS:
        if all(marker in line for marker in schema["markers"]):
            return schema
    return None


def _to_number(token: str) -> Optional[float]:
    try:
        return float(token)
    except ValueError:
        return None


def _normalize_value(column: str, value: float) -> Any:
    if column in {"l_search", "beamwidth", "iteration", "search_current_time_s"}:
        if value.is_integer():
            return int(value)
    return value


def _empty_optional_columns() -> Dict[str, Any]:
    return {
        "beamwidth": None,
        "p50_latency_ms": None,
        "p90_latency_ms": None,
        "p95_latency_ms": None,
        "p99_latency_ms": None,
        "mean_ios": None,
        "cpu_us_reported": None,
        "recall": None,
        "search_current_time_s": None,
    }


def parse_benchmark_text(text: str, source: str = "<memory>") -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    current_schema: Optional[Dict[str, Any]] = None
    current_iteration: Optional[int] = None
    current_search_time: Optional[int] = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        iteration_match = ITERATION_RE.search(line)
        if iteration_match:
            current_iteration = int(iteration_match.group("value"))
            continue

        search_time_match = SEARCH_TIME_RE.search(line)
        if search_time_match:
            current_search_time = int(search_time_match.group("value"))
            continue

        schema = _find_schema(line)
        if schema is not None:
            current_schema = schema
            continue

        if current_schema is None:
            continue

        if set(line) == {"="}:
            continue

        tokens = line.split()
        values = [_to_number(token) for token in tokens]
        if any(value is None for value in values):
            continue

        columns = current_schema["columns"]
        if len(values) != len(columns):
            continue

        row: Dict[str, Any] = {
            "source": source,
            "schema": current_schema["name"],
            "iteration": current_iteration,
            "line_number": line_number,
            "raw_line": raw_line,
        }
        row.update(_empty_optional_columns())
        row["search_current_time_s"] = current_search_time

        for column, value in zip(columns, values):
            row[column] = _normalize_value(column, value)

        rows.append(row)

    return rows


def _read_delimited(path: Path, delimiter: str) -> List[Dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        rows = []
        for line_number, row in enumerate(reader, start=2):
            record = {
                "source": str(path),
                "schema": "delimited",
                "iteration": None,
                "line_number": line_number,
                "raw_line": None,
            }
            record.update(_empty_optional_columns())
            record.update(row)
            rows.append(record)
        return rows


def load_benchmark_rows(path: Path | str) -> List[Dict[str, Any]]:
    benchmark_path = Path(path)
    suffix = benchmark_path.suffix.lower()

    if suffix == ".csv":
        return _read_delimited(benchmark_path, ",")
    if suffix == ".tsv":
        return _read_delimited(benchmark_path, "\t")

    text = benchmark_path.read_text(encoding="utf-8")
    return parse_benchmark_text(text, source=str(benchmark_path))


def load_many_logs(paths: Sequence[Path | str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in paths:
        rows.extend(load_benchmark_rows(path))
    return rows


def write_csv(rows: Iterable[Dict[str, Any]], path: Path | str) -> Path:
    output_path = Path(path)
    rows = list(rows)
    if not rows:
        raise ValueError("No rows to write.")

    fieldnames = sorted({key for row in rows for key in row.keys()})
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return output_path


def maybe_to_dataframe(rows: Sequence[Dict[str, Any]]) -> Any:
    try:
        import pandas as pd
    except ImportError:
        return list(rows)

    return pd.DataFrame(rows)


def require_dataframe(rows: Sequence[Dict[str, Any]]):
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas is not installed. Run `python3 -m pip install pandas matplotlib jupyter` first."
        ) from exc

    return pd.DataFrame(rows)

    return pd.DataFrame(rows)
