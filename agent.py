"""Nebius Token Factory orchestration for BioBatch Sentinel."""
from __future__ import annotations

import json
import re
from typing import Any
import pandas as pd
from openai import OpenAI

from analysis_tools import available_tools, data_profile, run_tool

BASE_URL = "https://api.tokenfactory.us-central1.nebius.com/v1/"
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"
MAX_AGENT_STEPS = 3


def _parse_json(text: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating optional Markdown code fences."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start >= 0 and end > start:
        obj = json.loads(cleaned[start:end + 1])
        if isinstance(obj, dict):
            return obj
    raise ValueError("The model did not return a valid JSON object.")


def _compact(obj: Any, max_chars: int = 10000) -> str:
    text = json.dumps(obj, ensure_ascii=False, default=str)
    return text[:max_chars]


def run_agentic_investigation(
    df: pd.DataFrame,
    api_key: str,
    model: str = DEFAULT_MODEL,
    target: str | None = None,
    group_column: str | None = None,
    max_steps: int = MAX_AGENT_STEPS,
) -> dict[str, Any]:
    """Run a bounded observe -> choose tool -> inspect result -> repeat loop."""
    if not api_key or not api_key.strip():
        raise ValueError("NEBIUS_API_KEY is missing. Add it to your local .env file and restart the app.")

    client = OpenAI(base_url=BASE_URL, api_key=api_key.strip(), timeout=75.0, max_retries=1)
    profile = data_profile(df)
    allowed_tools = available_tools(df, target, group_column)
    used_tools: set[str] = set()
    trace: list[dict[str, Any]] = [{
        "step": 0,
        "tool": "inspect_data",
        "reason": "Mandatory initial audit of the uploaded experimental table.",
        "result": profile,
    }]
    evidence: list[dict[str, Any]] = [profile]

    system_prompt = (
        "You are BioBatch Sentinel, an assistant for investigating uploaded biotechnology experiment data. "
        "Choose tools only from the supplied allow-list. Return exactly one JSON object with keys: "
        "tool (tool name or finish), reason (one short sentence), and column (optional column name). "
        "Do not output chain-of-thought. Use only the supplied summary and past tool results. "
        "Never claim causation from observational data, never invent measurements, and do not recommend "
        "unvalidated changes to lab protocols. Avoid repeating already-used tools. If evidence is sufficient "
        "or no useful tool remains, choose finish."
    )

    for step_number in range(1, max(0, min(int(max_steps), MAX_AGENT_STEPS)) + 1):
        remaining = [tool for tool in allowed_tools if tool["name"] not in used_tools]
        if not remaining:
            break
        prompt_payload = {
            "task": "Investigate the uploaded experimental data for data-quality issues or potentially useful measurable patterns.",
            "dataset_profile": {
                "rows": profile["rows"],
                "columns": profile["columns"],
                "numeric_summary": profile["numeric_summary"],
            },
            "selected_response_column": target,
            "selected_group_column": group_column,
            "available_tools": remaining,
            "already_used_tools": sorted(used_tools),
            "previous_results": evidence[-4:],
            "instruction": "Pick one most useful next tool, or finish if remaining tools are not useful. Return JSON only.",
        }
        response = client.chat.completions.create(
            model=model,
            temperature=0.1,
            max_tokens=350,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": _compact(prompt_payload)},
            ],
        )
        raw = response.choices[0].message.content or ""
        choice = _parse_json(raw)
        tool_name = str(choice.get("tool", "finish"))
        reason = str(choice.get("reason", "Selected based on the current evidence."))[:300]
        if tool_name == "finish":
            if not used_tools and remaining:
                # Do not let the model stop before any substantive analysis has run.
                tool_name = remaining[0]["name"]
                reason = "The workflow requires at least one evidence-producing analysis tool before it can finish."
            else:
                trace.append({"step": step_number, "tool": "finish", "reason": reason, "result": {"message": "The agent decided no additional tool was needed."}})
                break
        permitted_names = {tool["name"] for tool in remaining}
        if tool_name not in permitted_names:
            raise ValueError(f"Nemotron selected unavailable or repeated tool '{tool_name}'. Please run again.")

        requested_column = choice.get("column")
        if requested_column not in df.columns:
            requested_column = target if target in df.columns else None
        result = run_tool(tool_name, df, target, group_column, requested_column)
        used_tools.add(tool_name)
        item = {"step": step_number, "tool": tool_name, "reason": reason, "result": result}
        trace.append(item)
        evidence.append(result)

    report_prompt = {
        "task": "Write a compact, evidence-grounded investigation report for a biotechnology researcher.",
        "data_profile": {"rows": profile["rows"], "columns": profile["columns"], "numeric_summary": profile["numeric_summary"]},
        "selected_response_column": target,
        "selected_group_column": group_column,
        "tool_results": evidence[1:],
        "required_sections": ["observations", "possible_explanations_to_check", "limitations", "next_data_checks"],
        "rules": [
            "Do not invent data, values, literature citations, or causes.",
            "Distinguish directly measured observations from hypotheses.",
            "If results are insufficient, say so.",
            "Correlation is not causation.",
            "Do not prescribe laboratory protocol changes.",
            "Return JSON with keys: headline, observations (array), possible_explanations_to_check (array), limitations (array), next_data_checks (array).",
        ],
    }
    response = client.chat.completions.create(
        model=model,
        temperature=0.1,
        max_tokens=850,
        messages=[
            {"role": "system", "content": "You write cautious, concise scientific data-investigation reports. Return valid JSON only. Do not reveal private chain-of-thought."},
            {"role": "user", "content": _compact(report_prompt, max_chars=16000)},
        ],
    )
    raw_report = response.choices[0].message.content or ""
    report = _parse_json(raw_report)
    return {
        "mode": "agentic",
        "model": model,
        "profile": profile,
        "trace": trace,
        "report": report,
    }


def run_local_audit(df: pd.DataFrame, target: str | None = None, group_column: str | None = None) -> dict[str, Any]:
    """A deterministic offline smoke test; it does not satisfy the hackathon model-use requirement."""
    profile = data_profile(df)
    tools = ["missingness_report"]
    numeric = list(df.select_dtypes(include=["number"]).columns)
    if len(numeric) >= 2:
        tools.append("correlation_scan")
    if target in numeric and group_column in df.columns:
        tools.append("group_comparison")
    if numeric:
        tools.append("outlier_scan")
    results = [profile]
    trace = [{"step": 0, "tool": "inspect_data", "reason": "Mandatory initial audit.", "result": profile}]
    for step, name in enumerate(tools, start=1):
        result = run_tool(name, df, target, group_column, target if target in df.columns else None)
        trace.append({"step": step, "tool": name, "reason": "Offline baseline check; fixed deterministic sequence, not agent-selected.", "result": result})
        results.append(result)
    report = {
        "headline": "Offline data audit complete (no LLM agent run).",
        "observations": [
            f"Uploaded table has {profile['rows']} rows and {profile['columns_count']} columns.",
            f"Numeric columns detected: {len(profile['numeric_columns'])}.",
            "See the tool results for missingness, associations, group summaries, and possible outliers.",
        ],
        "possible_explanations_to_check": ["Treat any pattern as a hypothesis until the original experimental records and study design are reviewed."],
        "limitations": ["This is deterministic local analysis, not a Nemotron-driven agent run.", "No causal claim can be drawn from these summaries alone."],
        "next_data_checks": ["Confirm column meanings and units.", "Confirm the experimental unit, batch structure, and replicate design.", "Run the agentic workflow with a working Nebius Token Factory API key."],
    }
    return {"mode": "local", "profile": profile, "trace": trace, "report": report}
