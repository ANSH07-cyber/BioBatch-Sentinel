"""Deterministic analysis tools for BioBatch Sentinel.

These tools report descriptive patterns in uploaded experimental data. They do not
infer causation or recommend unvalidated changes to laboratory protocols.
"""
from __future__ import annotations

from typing import Any
import math
import numpy as np
import pandas as pd


def _clean(value: Any) -> Any:
    """Convert pandas/numpy values into JSON-safe Python values."""
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_clean(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not math.isfinite(float(value)) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    if isinstance(value, (str, int, bool)):
        return value
    return str(value)


def data_profile(df: pd.DataFrame) -> dict[str, Any]:
    columns = []
    for column in df.columns:
        series = df[column]
        columns.append({
            "name": str(column),
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_pct": round(float(series.isna().mean() * 100), 2) if len(df) else 0.0,
            "unique_count": int(series.nunique(dropna=True)),
        })

    numeric_summary: dict[str, Any] = {}
    for column in df.select_dtypes(include=[np.number]).columns:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if len(series):
            numeric_summary[str(column)] = {
                "count": int(series.count()),
                "mean": _clean(series.mean()),
                "std": _clean(series.std()),
                "min": _clean(series.min()),
                "median": _clean(series.median()),
                "max": _clean(series.max()),
            }

    return {
        "tool": "inspect_data",
        "rows": int(df.shape[0]),
        "columns_count": int(df.shape[1]),
        "numeric_columns": [str(c) for c in df.select_dtypes(include=[np.number]).columns],
        "categorical_columns": [str(c) for c in df.select_dtypes(exclude=[np.number]).columns],
        "columns": columns,
        "numeric_summary": numeric_summary,
    }


def missingness_report(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"tool": "missingness_report", "message": "The uploaded table is empty."}
    rows = []
    for column in df.columns:
        count = int(df[column].isna().sum())
        if count:
            rows.append({
                "column": str(column),
                "missing_count": count,
                "missing_pct": round(100 * count / len(df), 2),
            })
    rows.sort(key=lambda x: x["missing_pct"], reverse=True)
    return {
        "tool": "missingness_report",
        "rows_checked": int(len(df)),
        "columns_with_missing_values": rows,
        "message": "No missing values found in the uploaded table." if not rows else None,
    }


def correlation_scan(df: pd.DataFrame, target: str | None = None) -> dict[str, Any]:
    numeric = df.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        return {"tool": "correlation_scan", "message": "At least two numeric columns are needed."}

    if target and target in numeric.columns:
        correlations = numeric.corr(numeric_only=True)[target].drop(labels=[target], errors="ignore")
        correlations = correlations.dropna().sort_values(key=lambda s: s.abs(), ascending=False)
        return {
            "tool": "correlation_scan",
            "target": target,
            "method": "Pearson correlation",
            "associations": [
                {"feature": str(k), "correlation": round(float(v), 4), "absolute_correlation": round(abs(float(v)), 4)}
                for k, v in correlations.head(10).items()
            ],
            "caution": "Correlation describes linear association in these records; it does not establish causation.",
        }

    corr = numeric.corr(numeric_only=True)
    pairs = []
    cols = list(corr.columns)
    for i, left in enumerate(cols):
        for right in cols[i + 1:]:
            value = corr.loc[left, right]
            if pd.notna(value):
                pairs.append({"column_a": str(left), "column_b": str(right), "correlation": round(float(value), 4), "absolute_correlation": round(abs(float(value)), 4)})
    pairs.sort(key=lambda item: item["absolute_correlation"], reverse=True)
    return {
        "tool": "correlation_scan",
        "method": "Pearson correlation",
        "strongest_pairs": pairs[:10],
        "caution": "Correlation describes linear association in these records; it does not establish causation.",
    }


def group_comparison(df: pd.DataFrame, target: str | None, group_column: str | None) -> dict[str, Any]:
    if not target or target not in df.columns:
        return {"tool": "group_comparison", "message": "Choose a valid numeric response column first."}
    if target not in df.select_dtypes(include=[np.number]).columns:
        return {"tool": "group_comparison", "message": f"'{target}' is not numeric."}
    if not group_column or group_column not in df.columns:
        return {"tool": "group_comparison", "message": "Choose a group/batch/condition column first."}

    usable = df[[target, group_column]].copy()
    usable[target] = pd.to_numeric(usable[target], errors="coerce")
    usable = usable.dropna(subset=[target, group_column])
    if usable.empty:
        return {"tool": "group_comparison", "message": "No rows have both a response value and a group value."}

    grouped = usable.groupby(group_column, dropna=False)[target].agg(["count", "mean", "median", "std", "min", "max"]).reset_index()
    grouped = grouped.sort_values("mean", ascending=False)
    records = []
    for _, row in grouped.head(30).iterrows():
        records.append({
            "group": _clean(row[group_column]),
            "n": int(row["count"]),
            "mean": _clean(row["mean"]),
            "median": _clean(row["median"]),
            "std": _clean(row["std"]),
            "min": _clean(row["min"]),
            "max": _clean(row["max"]),
        })
    return {
        "tool": "group_comparison",
        "response_column": target,
        "group_column": group_column,
        "groups_returned": len(records),
        "group_statistics": records,
        "caution": "These are descriptive comparisons. Small samples, replicates, confounding variables, and experimental design may limit interpretation.",
    }


def outlier_scan(df: pd.DataFrame, column: str | None, context_columns: list[str] | None = None) -> dict[str, Any]:
    if not column or column not in df.columns:
        return {"tool": "outlier_scan", "message": "Choose a valid column to scan."}
    values = pd.to_numeric(df[column], errors="coerce")
    valid = values.dropna()
    if len(valid) < 4:
        return {"tool": "outlier_scan", "column": column, "message": "At least four numeric observations are needed for an IQR scan."}
    q1 = float(valid.quantile(0.25))
    q3 = float(valid.quantile(0.75))
    iqr = q3 - q1
    if iqr == 0:
        low, high = q1, q3
    else:
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    mask = values.notna() & ((values < low) | (values > high))
    row_ids = df.index[mask]
    context = [c for c in (context_columns or []) if c in df.columns and c != column][:4]
    observations = []
    for idx in row_ids[:15]:
        item = {"row_index": str(idx), column: _clean(values.loc[idx])}
        for c in context:
            item[c] = _clean(df.loc[idx, c])
        observations.append(item)
    return {
        "tool": "outlier_scan",
        "column": column,
        "method": "1.5 × IQR rule",
        "lower_bound": round(float(low), 6),
        "upper_bound": round(float(high), 6),
        "flagged_count": int(mask.sum()),
        "observations_shown": observations,
        "caution": "An outlier is a review flag, not proof of an error or failed experiment. Check source records and lab context.",
    }



def time_course_analysis(
    df: pd.DataFrame,
    response_column: str | None,
    group_column: str | None,
    time_column: str = "Time",
    timepoint_column: str | None = "Time_name",
    replicate_column: str | None = "Rep",
    stratify_columns: list[str] | None = None,
) -> dict[str, Any]:
    """Summarize a numeric response over time without mixing selected conditions.

    If a timepoint label (for example, Time_name) is available, records are
    summarized at that nominal timepoint and the median measured time is retained
    for ordering/context. Replicates are counted, not silently treated as extra
    independent experiments. This is descriptive analysis, not causal inference.
    """
    numeric = list(df.select_dtypes(include=[np.number]).columns)
    if not response_column or response_column not in numeric:
        return {"tool": "time_course_analysis", "message": "Choose a valid numeric response column."}
    if not group_column or group_column not in df.columns:
        return {"tool": "time_course_analysis", "message": "Choose a valid group/strain column."}
    if group_column == response_column:
        return {"tool": "time_course_analysis", "message": "The response and group columns must be different."}
    if not time_column or time_column not in numeric:
        return {"tool": "time_course_analysis", "message": "Choose a valid numeric time column."}
    if time_column in {response_column, group_column}:
        return {"tool": "time_course_analysis", "message": "The time column must differ from the response and group columns."}
    if timepoint_column and timepoint_column not in df.columns:
        return {"tool": "time_course_analysis", "message": f"Timepoint label column '{timepoint_column}' was not found."}

    strata = []
    for name in (stratify_columns or []):
        if name in df.columns and name not in {response_column, group_column, time_column, timepoint_column, replicate_column} and name not in strata:
            strata.append(name)
    usable_columns = list(dict.fromkeys(
        [response_column, group_column, time_column]
        + ([timepoint_column] if timepoint_column else [])
        + ([replicate_column] if replicate_column and replicate_column in df.columns else [])
        + strata
    ))
    data = df[usable_columns].copy()
    data[response_column] = pd.to_numeric(data[response_column], errors="coerce")
    data[time_column] = pd.to_numeric(data[time_column], errors="coerce")
    rows_total = int(len(data))
    data = data.dropna(subset=[response_column, group_column, time_column])
    rows_used = int(len(data))
    if data.empty:
        return {"tool": "time_course_analysis", "message": "No rows have valid response, group, and time values.", "rows_total": rows_total, "rows_used": 0}

    time_key = timepoint_column if timepoint_column else time_column
    group_keys = [group_column] + strata + [time_key]
    aggregations: dict[str, tuple[str, str]] = {
        "mean_response": (response_column, "mean"),
        "median_response": (response_column, "median"),
        "sd_response": (response_column, "std"),
        "min_response": (response_column, "min"),
        "max_response": (response_column, "max"),
        "n_observations": (response_column, "count"),
        "time_median": (time_column, "median"),
        "time_min": (time_column, "min"),
        "time_max": (time_column, "max"),
    }
    has_replicate = bool(replicate_column and replicate_column in data.columns)
    if has_replicate:
        aggregations["n_replicates"] = (replicate_column, "nunique")
    summary = data.groupby(group_keys, dropna=False, observed=True, sort=False).agg(**aggregations).reset_index()
    summary = summary.sort_values(strata + [group_column, "time_median"], kind="stable").reset_index(drop=True)

    if timepoint_column:
        order_table = data.groupby(timepoint_column, dropna=False, observed=True)[time_column].median().reset_index()
        order_table = order_table.sort_values(time_column, kind="stable")
        timepoint_order = [_clean(v) for v in order_table[timepoint_column].tolist()]
    else:
        timepoint_order = [_clean(v) for v in sorted(data[time_column].dropna().unique().tolist())]

    trend_keys = strata + [group_column]
    trend_records: list[dict[str, Any]] = []
    for key_values, part in summary.groupby(trend_keys, dropna=False, observed=True, sort=False):
        if not isinstance(key_values, tuple):
            key_values = (key_values,)
        part = part.sort_values("time_median", kind="stable")
        first = part.iloc[0]
        last = part.iloc[-1]
        start_mean = float(first["mean_response"])
        end_mean = float(last["mean_response"])
        relative = ((end_mean - start_mean) / abs(start_mean) * 100.0) if start_mean != 0 else None
        item: dict[str, Any] = {column: _clean(value) for column, value in zip(trend_keys, key_values)}
        item.update({
            "first_timepoint": _clean(first[time_key]),
            "last_timepoint": _clean(last[time_key]),
            "first_median_time": _clean(first["time_median"]),
            "last_median_time": _clean(last["time_median"]),
            "start_mean": _clean(start_mean),
            "end_mean": _clean(end_mean),
            "absolute_change": _clean(end_mean - start_mean),
            "relative_change_pct": _clean(relative),
            "timepoints_observed": int(part[time_key].nunique(dropna=False)),
        })
        trend_records.append(item)

    summary_records = []
    for record in summary.to_dict(orient="records"):
        summary_records.append({key: _clean(value) for key, value in record.items()})

    return {
        "tool": "time_course_analysis",
        "response_column": response_column,
        "group_column": group_column,
        "time_column": time_column,
        "timepoint_column": timepoint_column,
        "replicate_column": replicate_column if has_replicate else None,
        "stratify_columns": strata,
        "rows_total": rows_total,
        "rows_used": rows_used,
        "rows_excluded_for_missing_response_group_or_time": rows_total - rows_used,
        "timepoint_order": timepoint_order,
        "timepoint_summary": summary_records,
        "trend_summary": trend_records,
        "caution": (
            "Descriptive time-course summaries only. Confirm units, the meaning of timepoint labels, "
            "experimental unit, and repeated-measures design. Differences do not establish causation; "
            "do not combine different conditions unless that choice is justified."
        ),
    }


def available_tools(df: pd.DataFrame, target: str | None, group_column: str | None) -> list[dict[str, str]]:
    tools = [
        {"name": "missingness_report", "description": "Check which columns have missing values and how much is missing."},
    ]
    numeric = list(df.select_dtypes(include=[np.number]).columns)
    if len(numeric) >= 2:
        tools.append({"name": "correlation_scan", "description": "Find the strongest linear associations among numeric measurements; if a numeric target is selected, correlate other numeric columns with that target."})
    if target in numeric and group_column in df.columns:
        tools.append({"name": "group_comparison", "description": "Compare a numeric target using descriptive statistics across a batch, condition, or group column."})
        if "Time" in numeric:
            tools.append({"name": "time_course_analysis", "description": "Summarize the selected numeric response across time by strain/group, retaining Time_name, Rep, and Temperature/MS condition strata when those columns exist. Use this to investigate changes over time without mixing selected conditions."})
    if numeric:
        tools.append({"name": "outlier_scan", "description": "Use the 1.5×IQR rule to flag unusual numeric observations for review."})
    return tools


def run_tool(name: str, df: pd.DataFrame, target: str | None = None, group_column: str | None = None, column: str | None = None) -> dict[str, Any]:
    """Dispatch only to explicitly allow-listed local analysis tools."""
    if name == "inspect_data":
        result = data_profile(df)
    elif name == "missingness_report":
        result = missingness_report(df)
    elif name == "correlation_scan":
        result = correlation_scan(df, target if target in df.select_dtypes(include=[np.number]).columns else None)
    elif name == "group_comparison":
        result = group_comparison(df, target, group_column)
    elif name == "time_course_analysis":
        numeric = list(df.select_dtypes(include=[np.number]).columns)
        time_name = "Time" if "Time" in numeric else (numeric[0] if numeric else None)
        timepoint_name = "Time_name" if "Time_name" in df.columns else None
        replicate_name = "Rep" if "Rep" in df.columns else None
        strata = [name for name in ["Temperature", "MS"] if name in df.columns]
        result = time_course_analysis(
            df,
            response_column=target,
            group_column=group_column,
            time_column=time_name,
            timepoint_column=timepoint_name,
            replicate_column=replicate_name,
            stratify_columns=strata,
        )
    elif name == "outlier_scan":
        target_column = column or (target if target in df.select_dtypes(include=[np.number]).columns else None)
        numeric = list(df.select_dtypes(include=[np.number]).columns)
        if target_column is None and numeric:
            target_column = numeric[0]
        result = outlier_scan(df, target_column, [group_column] if group_column else [])
    else:
        raise ValueError(f"Tool not allowed: {name}")
    return _clean(result)
