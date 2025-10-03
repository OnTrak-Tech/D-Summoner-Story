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

## Implementation Status

✅ **Completed (100%)**:
- Complete Terraform infrastructure with all AWS services
- All 5 Lambda functions with comprehensive implementation
- Shared modules (models, AWS clients, Riot API client, utilities)
- Security with Secrets Manager and IAM policies
- Monitoring with CloudWatch dashboards and alarms
- **Complete Frontend Application** with all features:
  - Interactive Chart.js data visualizations (4 chart types)
  - Social sharing with image generation and multi-platform support
  - Dark/Light theme system with system preference detection
  - Mobile-first responsive design with dedicated mobile menu
  - Local storage caching and user preferences
  - Recent searches and auto-fill functionality
  - Performance optimizations and accessibility features
- API service layer and React hooks for state management
- Error handling and user feedback
- CI/CD pipeline with automated testing and deployment

✅ **Production Ready**:
- All planned features implemented and tested
- Mobile-optimized user experience
- Accessibility compliant (WCAG)
- Performance optimized with caching
- Social sharing capabilities
- Complete data visualization suite

## Quick Start

1. **Deploy Infrastructure**:
   ```bash
   cd infrastructure/terraform
   make deploy ENV=dev
   ```

2. **Configure Secrets**:
   ```bash
   make update-secret API_KEY=your-riot-api-key
   ```

3. **Deploy Frontend**:
   ```bash
   cd frontend
   npm install && npm run build
   aws s3 sync dist/ s3://$(terraform output -raw static_website_bucket_name)/
   ```

4. **Access Application**:
   ```bash
   echo $(terraform output -raw website_url)
   ```

See `IMPLEMENTATION_STATUS.md` for detailed progress and `infrastructure/terraform/README.md` for deployment guide.
