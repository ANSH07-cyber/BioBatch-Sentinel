# BioBatch Sentinel

**An agentic investigation assistant for biotechnology experimental data.** It loads real CSV/Excel experiment data, performs deterministic data-quality and statistical checks, lets an NVIDIA Nemotron model choose which allowed tool to run next, and generates an evidence-grounded investigation report.

> Research prototype only. It does not control lab equipment, prescribe laboratory protocol changes, or establish causation from correlations.

## Real starter dataset

Start with **Black liquor valorization Machine learning model**, Mendeley Data, Version 1, DOI [10.17632/r52r3tsc3x.1](https://data.mendeley.com/datasets/r52r3tsc3x/1). The data page says that it includes microbial fermentation experiments with multiple batches/replicates and is used to model COD consumption, biomass, and polymer production. The page lists the license as **CC BY 4.0**.

- Download the actual data files from the dataset page and select a CSV or Excel file/sheet in the app.
- Retain attribution to the dataset contributors and follow the published license conditions.
- The starter app does not assume column names in advance; inspect the actual schema before selecting response and group columns.
- MATLAB scripts from the source package are not loaded by this MVP.

## Features

- CSV and Excel workbook upload (including individual worksheets)
- Schema and missing-value audit
- Numeric association scan, group summary, and IQR outlier flags
- Time-aware strain/group investigation with replicate counts and optional condition stratification (for example, Temperature and MS)
- Bounded agent loop: Nemotron selects from an allow-list of local tools based on the data profile and previous tool outputs
- Trace of selected tools, concise rationale, and outputs
- Structured report distinguishing observations, hypotheses to check, limitations, and next data checks
- JSON report download

The app sends compact data summaries and tool outputs to Nebius Token Factory, not the complete uploaded dataset. Do not upload confidential or personally identifiable research data to an external service without authorization.

## Setup (Windows PowerShell)

1. Install Python 3.10+.
2. Open PowerShell in this folder and create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and add your actual Nebius Token Factory API key:

   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

4. Run the app:

   ```powershell
   streamlit run app.py
   ```

5. Download the real Mendeley dataset, upload a CSV/Excel file, inspect the columns, and choose a numeric response column and an optional batch/condition column.
6. Use **Run Nemotron agent** for the model-powered agent run. **Run local baseline audit** is only for inspecting data before API access is ready and does not by itself meet the hackathon's model integration requirement.

## Model endpoint

The default uses Nebius Token Factory's OpenAI-compatible endpoint and the model name shown on Nebius's Nemotron page. If your account has access to a different NVIDIA open model, set `NEBIUS_MODEL` accordingly.

- Endpoint: `https://api.tokenfactory.us-central1.nebius.com/v1/`
- Key variable: `NEBIUS_API_KEY`
- Model variable: `NEBIUS_MODEL`

Check current access and model availability in your Token Factory account; model availability can change.

## GitHub checklist for hackathon submission

- Create a public repository and include an open-source license (for example MIT, subject to dataset-license separation).
- Never commit `.env`, API keys, or private data.
- Include screenshots/demo video and actual run instructions.
- Explain where Nemotron and Token Factory are used.
- Submit a working demo, a public repository, and a public YouTube demo video under the current official rules.

## Project structure

```text
biobatch-sentinel/
├── app.py              # Streamlit UI and data upload
├── agent.py            # Nebius/Nemotron agent loop and report
├── analysis_tools.py   # Allow-listed deterministic tools, including time-course analysis
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```
