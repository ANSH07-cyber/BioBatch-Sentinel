from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from agent import DEFAULT_MODEL, run_agentic_investigation, run_local_audit
from analysis_tools import time_course_analysis

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

st.set_page_config(page_title="BioBatch Sentinel", page_icon="🧫", layout="wide")
st.title("🧫 BioBatch Sentinel")
st.caption("Agentic investigation for biotechnology experimental data")
st.markdown(
    "Upload real experiment records, inspect data quality, and let a bounded AI agent choose "
    "which statistical tools to run. This prototype supports scientific investigation—not autonomous lab control."
)

with st.expander("Project and dataset notes", expanded=False):
    st.markdown(
        "**Starter dataset:** [Black liquor valorization Machine learning model — Mendeley Data](https://data.mendeley.com/datasets/r52r3tsc3x/1). "
        "The page describes microbial fermentation measurements used to model COD consumption, biomass, and polymer production. "
        "Download the data files from the source, then upload the relevant CSV/XLSX file below. "
        "Credit the dataset contributors and retain the CC BY 4.0 attribution when reusing it. "
        "Inspect the actual file schema before interpreting column meanings."
    )
    st.markdown("The app does not upload the full dataset to the model. It sends compact data summaries and the results of local statistical tools to Nebius Token Factory.")

uploaded_files = st.file_uploader(
    "Upload experimental data (CSV or Excel)",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True,
    help="Start with the real CSV/XLSX files from the dataset. MATLAB scripts are not read by this MVP.",
)

@st.cache_data(show_spinner=False)
def parse_files(file_payloads: tuple[tuple[str, bytes], ...]):
    tables = {}
    for filename, content in file_payloads:
        try:
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content))
                tables[filename] = df
            else:
                excel = pd.ExcelFile(io.BytesIO(content))
                for sheet in excel.sheet_names:
                    name = f"{filename} — {sheet}"
                    tables[name] = pd.read_excel(excel, sheet_name=sheet)
        except Exception as exc:
            tables[f"ERROR — {filename}"] = pd.DataFrame({"Load error": [str(exc)]})
    return tables

if not uploaded_files:
    st.info("Start by downloading the real experimental data from the Mendeley link above and uploading a CSV or Excel file.")
    st.markdown("**First milestone:** successfully load the real file and confirm its columns before we define the investigation rules.")
    st.stop()

payloads = tuple((f.name, f.getvalue()) for f in uploaded_files)
tables = parse_files(payloads)
valid_tables = {name: df for name, df in tables.items() if not name.startswith("ERROR — ")}
for name, df in tables.items():
    if name.startswith("ERROR — "):
        st.error(f"{name}: {df.iloc[0, 0]}")
if not valid_tables:
    st.stop()

source_name = st.selectbox("Choose a dataset or worksheet", options=list(valid_tables.keys()))
df = valid_tables[source_name].copy()
# Drop blank rows and columns but do not silently impute or modify measured values.
df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

if df.empty or df.shape[1] == 0:
    st.error("The selected sheet has no non-empty rows or columns.")
    st.stop()

st.subheader("1. Inspect the uploaded experiment table")
metric_cols = st.columns(3)
metric_cols[0].metric("Rows", f"{len(df):,}")
metric_cols[1].metric("Columns", f"{len(df.columns):,}")
metric_cols[2].metric("Numeric columns", len(df.select_dtypes(include=["number"]).columns))
st.dataframe(df.head(20), use_container_width=True, hide_index=False)

numeric_cols = [str(c) for c in df.select_dtypes(include=["number"]).columns]
all_cols = [str(c) for c in df.columns]
control_cols = st.columns(2)
with control_cols[0]:
    target_choice = st.selectbox("Response/measurement to investigate (optional)", options=["(Not selected)"] + numeric_cols)
with control_cols[1]:
    group_choice = st.selectbox("Batch / condition / group column (optional)", options=["(Not selected)"] + all_cols)
target = None if target_choice == "(Not selected)" else target_choice
group_column = None if group_choice == "(Not selected)" else group_choice

st.subheader("2. Run the investigation")
col_local, col_agent = st.columns(2)
with col_local:
    run_local = st.button("Run local baseline audit", use_container_width=True, help="Runs deterministic stats for inspecting the real dataset; does not make a Nebius model call.")
with col_agent:
    run_agent = st.button("Run Nemotron agent", type="primary", use_container_width=True, help="Uses Nebius Token Factory and is the mode required to demonstrate model integration for the hackathon.")

if run_local:
    with st.spinner("Running deterministic analysis tools…"):
        try:
            st.session_state["last_result"] = run_local_audit(df, target, group_column)
        except Exception as exc:
            st.error(f"Local audit failed: {exc}")

if run_agent:
    api_key = os.getenv("NEBIUS_API_KEY", "")
    model = os.getenv("NEBIUS_MODEL", DEFAULT_MODEL)
    if not api_key:
        st.error("NEBIUS_API_KEY is not configured. Copy .env.example to .env, add your Token Factory API key, save, and restart Streamlit.")
    else:
        with st.spinner("Nemotron is selecting and running analysis tools…"):
            try:
                st.session_state["last_result"] = run_agentic_investigation(df, api_key, model, target, group_column)
            except Exception as exc:
                st.error(f"Agent run failed: {exc}")
                st.caption("Check that the API key, model name, and Token Factory access are valid. No successful agent run is claimed unless this completes.")


st.divider()
st.subheader("3. Time-aware strain investigation")
st.markdown(
    "Compare a measured response across time points while keeping selected experimental conditions separate. "
    "The local result is descriptive analysis; it does not establish a cause."
)

# Choose safe defaults based on the uploaded table schema.
def _default_index(options: list[str], preferred: str, fallback: int = 0) -> int:
    return options.index(preferred) if preferred in options else fallback

ts_cols = st.columns(3)
with ts_cols[0]:
    ts_response = st.selectbox(
        "Response to follow over time",
        options=numeric_cols,
        index=_default_index(numeric_cols, "Viable"),
        key="ts_response",
    )
with ts_cols[1]:
    ts_group = st.selectbox(
        "Compare groups/strains",
        options=all_cols,
        index=_default_index(all_cols, "Strain"),
        key="ts_group",
    )
with ts_cols[2]:
    ts_time = st.selectbox(
        "Numeric time column",
        options=numeric_cols,
        index=_default_index(numeric_cols, "Time"),
        key="ts_time",
    )

label_options = ["(Use numeric time)"] + [c for c in all_cols if c != ts_time and c not in numeric_cols]
with st.container():
    ts_more = st.columns(2)
    with ts_more[0]:
        ts_timepoint_choice = st.selectbox(
            "Nominal timepoint label (if available)",
            options=label_options,
            index=_default_index(label_options, "Time_name"),
            key="ts_timepoint",
            help="For datasets with labels such as t0, t1, t2, grouping by the label can match nominal timepoints even if measured times vary slightly."
        )
    with ts_more[1]:
        replicate_options = ["(None)"] + all_cols
        ts_replicate_choice = st.selectbox(
            "Replicate identifier (if available)",
            options=replicate_options,
            index=_default_index(replicate_options, "Rep"),
            key="ts_replicate",
        )

excluded_from_strata = {ts_response, ts_group, ts_time, ts_timepoint_choice, ts_replicate_choice, "(Use numeric time)", "(None)"}
strata_candidates = []
for c in all_cols:
    if c in excluded_from_strata:
        continue
    try:
        cardinality = int(df[c].nunique(dropna=True))
    except Exception:
        cardinality = len(df)
    if 2 <= cardinality <= 12:
        strata_candidates.append(c)
preferred_strata = [c for c in ["Temperature", "MS"] if c in strata_candidates]
st_ts_strata = st.multiselect(
    "Keep these conditions separate (recommended)",
    options=strata_candidates,
    default=preferred_strata,
    key="ts_strata",
    help="For example, Temperature and MS are kept as separate analysis groups rather than blended together."
)
run_time_course = st.button("Run time-aware analysis", use_container_width=True, key="run_time_course")
if run_time_course:
    with st.spinner("Comparing the selected response across timepoints and conditions…"):
        try:
            time_result = time_course_analysis(
                df,
                response_column=ts_response,
                group_column=ts_group,
                time_column=ts_time,
                timepoint_column=None if ts_timepoint_choice == "(Use numeric time)" else ts_timepoint_choice,
                replicate_column=None if ts_replicate_choice == "(None)" else ts_replicate_choice,
                stratify_columns=st_ts_strata,
            )
            st.session_state["time_course_result"] = {
                "source_name": source_name,
                "result": time_result,
            }
        except Exception as exc:
            st.error(f"Time-aware analysis failed: {exc}")

saved_time_result = st.session_state.get("time_course_result")
if saved_time_result and saved_time_result.get("source_name") == source_name:
    tc = saved_time_result.get("result", {})
    if tc.get("message"):
        st.warning(tc["message"])
    elif tc.get("timepoint_summary"):
        st.success(
            f"Time-aware summary complete: {tc['rows_used']:,} of {tc['rows_total']:,} rows included; "
            f"{len(tc['timepoint_summary']):,} group/timepoint summaries generated."
        )
        st.caption(tc.get("caution", "Descriptive analysis only."))
        trend_df = pd.DataFrame(tc.get("trend_summary", []))
        if not trend_df.empty:
            st.markdown("**First-to-last observed change by strain/group**")
            st.dataframe(trend_df, use_container_width=True, hide_index=True)

        summary_df = pd.DataFrame(tc.get("timepoint_summary", []))
        condition_columns = tc.get("stratify_columns", [])
        group_column_result = tc.get("group_column")
        timepoint_column_result = tc.get("timepoint_column")
        if condition_columns:
            summary_df["_condition_key"] = summary_df.apply(
                lambda row: " | ".join(f"{name}={row[name]}" for name in condition_columns), axis=1
            )
        else:
            summary_df["_condition_key"] = "All selected records"

        condition_groups = list(summary_df.groupby("_condition_key", sort=False, dropna=False))
        max_plots = 12
        for plot_index, (condition_label, subset) in enumerate(condition_groups[:max_plots]):
            with st.expander(f"Time-course chart — {condition_label}", expanded=(plot_index == 0)):
                x_key = timepoint_column_result if timepoint_column_result else tc.get("time_column")
                pivot = subset.pivot_table(
                    index=x_key,
                    columns=group_column_result,
                    values="mean_response",
                    aggfunc="mean",
                    dropna=False,
                )
                if timepoint_column_result:
                    order = tc.get("timepoint_order", [])
                    valid_order = [value for value in order if value in pivot.index]
                    pivot = pivot.reindex(valid_order)
                else:
                    pivot = pivot.sort_index()
                st.line_chart(pivot, height=320)
                display_columns = [
                    name for name in [group_column_result, *condition_columns, x_key, "time_median", "time_min", "time_max", "mean_response", "median_response", "sd_response", "n_observations", "n_replicates"]
                    if name and name in subset.columns
                ]
                st.dataframe(
                    subset[display_columns].sort_values([c for c in ["time_median", group_column_result] if c in subset.columns], kind="stable"),
                    use_container_width=True,
                    hide_index=True,
                )
        if len(condition_groups) > max_plots:
            st.info(f"Showing {max_plots} condition charts; {len(condition_groups) - max_plots} additional combinations are included in the downloadable JSON.")
        tc_download = json.dumps(tc, indent=2, ensure_ascii=False, default=str).encode("utf-8")
        st.download_button(
            "Download time-course analysis JSON",
            data=tc_download,
            file_name="biobatch_time_course_analysis.json",
            mime="application/json",
            key="download_time_course_json",
        )


result = st.session_state.get("last_result")
if result:
    st.divider()
    st.subheader("4. Investigation report")
    if result.get("mode") == "agentic":
        st.success(f"Agent run completed with {result.get('model', 'configured Nemotron model')}")
    else:
        st.warning("Offline baseline only — this run did not call Nemotron and does not meet the hackathon model-integration requirement by itself.")
    report = result.get("report", {})
    st.markdown(f"### {report.get('headline', 'Investigation summary')}")
    for section, heading in [
        ("observations", "Observed findings"),
        ("possible_explanations_to_check", "Possible explanations to investigate"),
        ("limitations", "Limitations and uncertainty"),
        ("next_data_checks", "Suggested next data checks"),
    ]:
        values = report.get(section, [])
        st.markdown(f"**{heading}**")
        if values:
            for item in values:
                st.markdown(f"- {item}")
        else:
            st.write("Not reported.")

    st.subheader("Agent execution trace")
    for item in result.get("trace", []):
        label = f"Step {item.get('step', '?')}: {item.get('tool', 'unknown tool')}"
        with st.expander(label, expanded=(item.get("step") == 0)):
            st.caption(item.get("reason", ""))
            st.json(item.get("result", {}))

    download_bytes = json.dumps(result, indent=2, ensure_ascii=False, default=str).encode("utf-8")
    st.download_button("Download investigation JSON", data=download_bytes, file_name="biobatch_sentinel_report.json", mime="application/json")

st.caption("Research prototype only. Confirm units, replicate structure, experimental design, and source records before drawing scientific conclusions. Flagged outliers are not automatically errors; correlations are not causal explanations.")
