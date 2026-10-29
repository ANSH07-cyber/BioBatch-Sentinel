
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from nebius_agent import run_nebius_agent
from analysis_tools import (
    data_profile,
    available_tools,
    run_tool,
)

ROOT = Path(__file__).resolve().parent

# Main data folder inside the project.
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Also allow the existing shared dataset folder:
# PROJECTS/BioBatch_Datasets
SHARED_DATASET_DIR = ROOT.parent / "BioBatch_Datasets"

app = FastAPI(title="BioBatch Sentinel Local API")


class AuditRequest(BaseModel):
    filename: str
    target: str | None = None
    group_column: str | None = None


class AgentAuditRequest(AuditRequest):
    question: str = (
        "Audit data quality and summarize viable-count "
        "patterns across strains and time."
    )


def resolve_dataset(filename: str) -> Path:
    """Find a dataset by filename in the approved data folders."""
    if not filename or Path(filename).name != filename:
        raise HTTPException(
            status_code=400,
            detail="Provide a filename, not a filesystem path.",
        )

    candidates = [
        DATA_DIR / filename,
        SHARED_DATASET_DIR / filename,
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise HTTPException(
        status_code=404,
        detail=(
            f"File not found: {filename}. "
            f"Checked {DATA_DIR} and {SHARED_DATASET_DIR}."
        ),
    )


def load_dataset(filename: str) -> pd.DataFrame:
    """Load CSV or Excel data, preferring the Excel sheet named Data."""
    file_path = resolve_dataset(filename)
    suffix = file_path.suffix.lower()

    try:
        if suffix == ".csv":
            df = pd.read_csv(file_path)

        elif suffix in {".xlsx", ".xls"}:
            with pd.ExcelFile(file_path) as workbook:
                if not workbook.sheet_names:
                    raise HTTPException(
                        status_code=400,
                        detail="The Excel workbook contains no sheets.",
                    )

                sheet_name = (
                    "Data"
                    if "Data" in workbook.sheet_names
                    else workbook.sheet_names[0]
                )

            df = pd.read_excel(file_path, sheet_name=sheet_name)

        else:
            raise HTTPException(
                status_code=400,
                detail="Only CSV, XLSX and XLS files are supported.",
            )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read dataset: {exc}",
        ) from exc

    df = (
        df.dropna(axis=0, how="all")
        .dropna(axis=1, how="all")
    )

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="The dataset is empty.",
        )

    return df


def valid_column(df: pd.DataFrame, column: str | None) -> str | None:
    """Return a requested column only if it exists."""
    if column is not None and column in df.columns:
        return column
    return None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "project": "BioBatch Sentinel",
        "mode": "local",
    }


@app.post("/audit")
def audit(request: AuditRequest):
    """Run the existing deterministic local analysis pipeline."""
    df = load_dataset(request.filename)

    target = valid_column(df, request.target)
    group = valid_column(df, request.group_column)

    try:
        profile = data_profile(df)

        trace = [{
            "step": 0,
            "tool": "inspect_data",
            "reason": "Initial dataset inspection.",
            "result": profile,
        }]

        tools = available_tools(df, target, group)

        for step, tool in enumerate(tools, start=1):
            result = run_tool(
                tool["name"],
                df,
                target=target,
                group_column=group,
            )

            trace.append({
                "step": step,
                "tool": tool["name"],
                "reason": "Local deterministic analysis.",
                "result": result,
            })

        return {
            "project": "BioBatch Sentinel",
            "mode": "local",
            "filename": request.filename,
            "profile": profile,
            "trace": trace,
            "caution": (
                "Descriptive analysis only. Correlations do not establish "
                "causation, and flagged outliers require scientific review."
            ),
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}",
        ) from exc


@app.post("/agent-audit")
def agent_audit(request: AgentAuditRequest):
    """Run the Nebius-powered agent with real local analysis tools."""
    df = load_dataset(request.filename)

    target = valid_column(df, request.target)
    group = valid_column(df, request.group_column)

    try:
        result = run_nebius_agent(
            df,
            question=request.question,
            target=target,
            group_column=group,
        )

        result["filename"] = request.filename
        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent analysis failed: {exc}",
        ) from exc
