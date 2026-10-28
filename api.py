
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from analysis_tools import (
    data_profile,
    missingness_report,
    available_tools,
    run_tool,
)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

app = FastAPI(title="BioBatch Sentinel Local API")


class AuditRequest(BaseModel):
    filename: str
    target: str | None = None
    group_column: str | None = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "project": "BioBatch Sentinel",
        "mode": "local"
    }


@app.post("/audit")
def audit(request: AuditRequest):
    # Only allow files placed directly inside the data folder.
    if Path(request.filename).name != request.filename:
        raise HTTPException(400, "Provide a filename, not a path.")

    file_path = DATA_DIR / request.filename

    if not file_path.is_file():
        raise HTTPException(
            404,
            f"File not found in {DATA_DIR.name}/: {request.filename}"
        )

    try:
        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            df = pd.read_csv(file_path)
        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(
                400, "Only CSV, XLSX and XLS files are supported."
            )

        df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

        if df.empty:
            raise HTTPException(400, "The dataset is empty.")

        target = request.target
        group = request.group_column

        if target not in df.columns:
            target = None

        if group not in df.columns:
            group = None

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
        raise HTTPException(500, f"Analysis failed: {exc}") from exc
