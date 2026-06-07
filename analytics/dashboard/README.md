# DevEx Intelligence Dashboard

Streamlit dashboard that visualizes DORA metrics across engineering teams — deployment frequency, lead time, change failure rate, and MTTR — with AI-generated analysis from the DORA Analyst agent. Built on `devex-warehouse` models and designed for live demos without AWS.

## Run locally

```bash
cd analytics/dashboard
uv run streamlit run app.py
```

Or with Docker:

```bash
docker-compose up
```

## Demo mode

The dashboard runs in demo mode by default using realistic mock data. No AWS credentials required.

To connect to real DynamoDB:

```bash
export DEVEX_EVENTS_TABLE=your-table-name
export AWS_REGION=us-east-1
uv run streamlit run app.py
```

## Pages

- **Overview** — DORA metrics across all teams
- **Team Detail** — deep dive with AI analysis
- **Golden Path Adoption** — platform adoption tracking
