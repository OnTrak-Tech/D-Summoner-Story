# D-Summoner-Story

League of Legends Year in Review (serverless). Fetch a player's year of matches, compute insights (KDA, win rate, trends, champion stats), and generate an AI-powered narrative recap.

- Requirements: `.kiro/specs/lol-year-in-review/requirements.md`
- Design: `.kiro/specs/lol-year-in-review/design.md`
- Implementation Plan: `.kiro/specs/lol-year-in-review/tasks.md`

## Project Structure

- `backend/` — Python AWS Lambda functions and tests
- `frontend/` — React (Vite + TS) web UI with Tailwind + Chart.js
- `infrastructure/terraform/` — Terraform IaC for AWS
- `.github/workflows/` — CI/CD pipelines

## Local Development

Backend (Python 3.12):
- Create a virtual env and install deps
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r backend/requirements.txt`
- Run tests: `pytest -q`

Frontend (Node 18+):
- Install deps: `cd frontend && npm install`
- Start dev server: `npm run dev`

## CI/CD and Secrets

- CI runs backend and frontend checks on pushes/PRs.
- Deploy job (on `main`) runs Terraform in `infrastructure/terraform/`.
- Configure GitHub repository secrets:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION` (e.g., `us-east-1`)

Runtime secrets (e.g., Riot API key) are stored in AWS Secrets Manager and consumed by Lambdas via IAM, not committed to the repo or exposed in CI logs.

## Notes

- Initial Lambda handlers are placeholders; implementation follows the plan in `tasks.md`.
- Terraform is scaffolded; resources will be added incrementally.
