import pandas as pd
from analysis_tools import data_profile, missingness_report, correlation_scan, group_comparison, outlier_scan


def test_profile_reports_dimensions():
    df = pd.DataFrame({"batch": ["A", "A", "B", "B"], "yield": [1.0, 2.0, 4.0, 5.0], "pH": [6.1, 6.2, 6.7, 6.8]})
    result = data_profile(df)
    assert result["rows"] == 4
    assert result["columns_count"] == 3
    assert "yield" in result["numeric_columns"]


def test_missingness_report_detects_missing():
    df = pd.DataFrame({"x": [1.0, None], "y": ["a", "b"]})
    result = missingness_report(df)
    assert result["columns_with_missing_values"][0]["column"] == "x"
    assert result["columns_with_missing_values"][0]["missing_count"] == 1


def test_group_comparison_descriptive_stats():
    df = pd.DataFrame({"batch": ["A", "A", "B", "B"], "yield": [1.0, 3.0, 4.0, 6.0]})
    result = group_comparison(df, "yield", "batch")
    means = {x["group"]: x["mean"] for x in result["group_statistics"]}
    assert means["A"] == 2.0
    assert means["B"] == 5.0


def test_correlation_scan_target():
    df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, 4, 6, 8], "z": [5, 3, 2, 1]})
    result = correlation_scan(df, "y")
    assert result["associations"][0]["feature"] == "x"
    assert result["associations"][0]["correlation"] > 0.99


def test_outlier_scan_flags_observation():
    df = pd.DataFrame({"measurement": [1, 2, 2, 3, 3, 4, 100], "batch": list("ABCDEFG")})
    result = outlier_scan(df, "measurement", ["batch"])
    assert result["flagged_count"] >= 1


def test_time_course_analysis_preserves_strata_and_replicates():
    from analysis_tools import time_course_analysis

    df = pd.DataFrame({
        "Strain": ["A", "A", "A", "A", "B", "B", "B", "B"],
        "Rep": ["R1", "R2", "R1", "R2", "R1", "R2", "R1", "R2"],
        "Time_name": ["t0", "t0", "t1", "t1", "t0", "t0", "t1", "t1"],
        "Time": [0, 0, 10, 10, 0, 0, 11, 11],
        "Temperature": [12] * 8,
        "MS": [210] * 8,
        "Viable": [10, 12, 20, 22, 8, 10, 16, 18],
    })
    result = time_course_analysis(
        df,
        response_column="Viable",
        group_column="Strain",
        time_column="Time",
        timepoint_column="Time_name",
        replicate_column="Rep",
        stratify_columns=["Temperature", "MS"],
    )

    assert result["tool"] == "time_course_analysis"
    assert result["rows_used"] == 8
    assert result["timepoint_order"] == ["t0", "t1"]
    t0_a = next(x for x in result["timepoint_summary"] if x["Strain"] == "A" and x["Time_name"] == "t0")
    assert t0_a["mean_response"] == 11
    assert t0_a["n_replicates"] == 2
    trend_a = next(x for x in result["trend_summary"] if x["Strain"] == "A")
    assert trend_a["absolute_change"] == 10
    assert round(trend_a["relative_change_pct"], 2) == 90.91


def test_time_course_analysis_handles_missing_required_values():
    from analysis_tools import time_course_analysis

    df = pd.DataFrame({
        "Strain": ["A", "A", "B"],
        "Rep": ["R1", "R2", "R1"],
        "Time_name": ["t0", "t1", "t0"],
        "Time": [0, 10, 0],
        "Viable": [10, None, 5],
    })
    result = time_course_analysis(df, "Viable", "Strain", "Time", "Time_name", "Rep")
    assert result["rows_total"] == 3
    assert result["rows_used"] == 2
    assert result["rows_excluded_for_missing_response_group_or_time"] == 1
