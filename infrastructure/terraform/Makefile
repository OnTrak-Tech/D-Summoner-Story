# D-Summoner-Story Terraform Makefile
# Simplifies common infrastructure operations

.PHONY: help init plan apply deploy destroy clean validate fmt check-fmt lint

# Default environment
ENV ?= dev
REGION ?= us-east-1

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)D-Summoner-Story Infrastructure Management$(NC)"
	@echo "=========================================="
	@echo ""
	@echo "$(GREEN)Usage:$(NC) make [target] [ENV=environment] [REGION=region]"
	@echo ""
	@echo "$(GREEN)Targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Examples:$(NC)"
	@echo "  make deploy                    # Deploy to dev environment"
	@echo "  make deploy ENV=prod           # Deploy to prod environment"
	@echo "  make plan ENV=staging          # Plan staging deployment"
	@echo "  make destroy ENV=dev           # Destroy dev environment"

init: ## Initialize Terraform
	@echo "$(BLUE)[INFO]$(NC) Initializing Terraform..."
	terraform init

validate: ## Validate Terraform configuration
	@echo "$(BLUE)[INFO]$(NC) Validating Terraform configuration..."
	terraform validate

fmt: ## Format Terraform files
	@echo "$(BLUE)[INFO]$(NC) Formatting Terraform files..."
	terraform fmt -recursive

check-fmt: ## Check if Terraform files are formatted
	@echo "$(BLUE)[INFO]$(NC) Checking Terraform formatting..."
	terraform fmt -check -recursive

lint: validate check-fmt ## Run linting (validate + format check)
	@echo "$(GREEN)[SUCCESS]$(NC) Linting completed"

plan: init validate ## Plan Terraform deployment
	@echo "$(BLUE)[INFO]$(NC) Planning deployment for environment: $(ENV)"
	terraform plan \
		-var="environment=$(ENV)" \
		-var="aws_region=$(REGION)" \
		-out=tfplan-$(ENV)

apply: ## Apply Terraform plan
	@echo "$(BLUE)[INFO]$(NC) Applying Terraform plan for environment: $(ENV)"
	@if [ ! -f "tfplan-$(ENV)" ]; then \
		echo "$(RED)[ERROR]$(NC) No plan file found. Run 'make plan ENV=$(ENV)' first."; \
		exit 1; \
	fi
	terraform apply tfplan-$(ENV)
	@rm -f tfplan-$(ENV)

deploy: ## Full deployment (plan + apply)
	@echo "$(BLUE)[INFO]$(NC) Starting full deployment for environment: $(ENV)"
	@./deploy.sh -e $(ENV) -r $(REGION)

quick-deploy: init validate ## Quick deployment without backend setup
	@echo "$(BLUE)[INFO]$(NC) Quick deployment for environment: $(ENV)"
	terraform plan \
		-var="environment=$(ENV)" \
		-var="aws_region=$(REGION)" \
		-out=tfplan-$(ENV)
	terraform apply tfplan-$(ENV)
	@rm -f tfplan-$(ENV)

destroy: ## Destroy infrastructure
	@echo "$(YELLOW)[WARNING]$(NC) This will destroy all resources for environment: $(ENV)"
	@./destroy.sh -e $(ENV) -r $(REGION)

force-destroy: ## Force destroy without confirmation
	@echo "$(RED)[WARNING]$(NC) Force destroying environment: $(ENV)"
	@./destroy.sh -e $(ENV) -r $(REGION) -f

clean: ## Clean local Terraform files
	@echo "$(BLUE)[INFO]$(NC) Cleaning local Terraform files..."
	rm -rf .terraform/
	rm -f terraform.tfstate*
	rm -f tfplan*
	rm -f .terraform.lock.hcl
	@echo "$(GREEN)[SUCCESS]$(NC) Local files cleaned"

output: ## Show Terraform outputs
	@echo "$(BLUE)[INFO]$(NC) Terraform outputs for environment: $(ENV)"
	@terraform output

status: ## Show infrastructure status
	@echo "$(BLUE)[INFO]$(NC) Infrastructure status for environment: $(ENV)"
	@echo "$(GREEN)Terraform State:$(NC)"
	@terraform show -json | jq -r '.values.root_module.resources[] | select(.type != "data") | "\(.type).\(.name): \(.values.id // .values.arn // "N/A")"' 2>/dev/null || echo "No resources found"

refresh: ## Refresh Terraform state
	@echo "$(BLUE)[INFO]$(NC) Refreshing Terraform state..."
	terraform refresh \
		-var="environment=$(ENV)" \
		-var="aws_region=$(REGION)"

import: ## Import existing AWS resource (usage: make import RESOURCE=aws_s3_bucket.example ID=bucket-name)
	@if [ -z "$(RESOURCE)" ] || [ -z "$(ID)" ]; then \
		echo "$(RED)[ERROR]$(NC) Usage: make import RESOURCE=resource_address ID=resource_id"; \
		exit 1; \
	fi
	terraform import $(RESOURCE) $(ID)

workspace-list: ## List Terraform workspaces
	@echo "$(BLUE)[INFO]$(NC) Available Terraform workspaces:"
	terraform workspace list

workspace-new: ## Create new workspace (usage: make workspace-new NAME=workspace-name)
	@if [ -z "$(NAME)" ]; then \
		echo "$(RED)[ERROR]$(NC) Usage: make workspace-new NAME=workspace-name"; \
		exit 1; \
	fi
	terraform workspace new $(NAME)

workspace-select: ## Select workspace (usage: make workspace-select NAME=workspace-name)
	@if [ -z "$(NAME)" ]; then \
		echo "$(RED)[ERROR]$(NC) Usage: make workspace-select NAME=workspace-name"; \
		exit 1; \
	fi
	terraform workspace select $(NAME)

cost-estimate: ## Estimate infrastructure costs (requires infracost)
	@if ! command -v infracost &> /dev/null; then \
		echo "$(RED)[ERROR]$(NC) infracost is not installed. Visit: https://www.infracost.io/docs/"; \
		exit 1; \
	fi
	@echo "$(BLUE)[INFO]$(NC) Estimating costs for environment: $(ENV)"
	infracost breakdown --path . \
		--terraform-var="environment=$(ENV)" \
		--terraform-var="aws_region=$(REGION)"

security-scan: ## Run security scan (requires tfsec)
	@if ! command -v tfsec &> /dev/null; then \
		echo "$(RED)[ERROR]$(NC) tfsec is not installed. Visit: https://github.com/aquasecurity/tfsec"; \
		exit 1; \
	fi
	@echo "$(BLUE)[INFO]$(NC) Running security scan..."
	tfsec .

docs: ## Generate Terraform documentation (requires terraform-docs)
	@if ! command -v terraform-docs &> /dev/null; then \
		echo "$(RED)[ERROR]$(NC) terraform-docs is not installed. Visit: https://terraform-docs.io/"; \
		exit 1; \
	fi
	@echo "$(BLUE)[INFO]$(NC) Generating documentation..."
	terraform-docs markdown table --output-file README-generated.md .

# Development helpers
dev-setup: ## Setup development environment
	@echo "$(BLUE)[INFO]$(NC) Setting up development environment..."
	@if [ ! -f "backend.tf" ]; then \
		echo "$(YELLOW)[WARNING]$(NC) No backend.tf found. Using local state."; \
	fi
	make init validate

dev-deploy: ENV=dev ## Deploy to development environment
dev-deploy: deploy

staging-deploy: ENV=staging ## Deploy to staging environment  
staging-deploy: deploy

prod-deploy: ENV=prod ## Deploy to production environment
prod-deploy: deploy

# Monitoring helpers
logs: ## Tail CloudWatch logs for Lambda functions
	@echo "$(BLUE)[INFO]$(NC) Available log groups:"
	@aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/d-summoner-story-$(ENV)" --query 'logGroups[].logGroupName' --output table

tail-auth: ## Tail auth Lambda logs
	@aws logs tail "/aws/lambda/d-summoner-story-$(ENV)-auth" --follow

tail-fetcher: ## Tail data fetcher Lambda logs
	@aws logs tail "/aws/lambda/d-summoner-story-$(ENV)-data-fetcher" --follow

tail-processor: ## Tail data processor Lambda logs
	@aws logs tail "/aws/lambda/d-summoner-story-$(ENV)-data-processor" --follow

tail-generator: ## Tail insight generator Lambda logs
	@aws logs tail "/aws/lambda/d-summoner-story-$(ENV)-insight-generator" --follow

tail-server: ## Tail recap server Lambda logs
	@aws logs tail "/aws/lambda/d-summoner-story-$(ENV)-recap-server" --follow

dashboard: ## Open CloudWatch dashboard
	@echo "$(BLUE)[INFO]$(NC) Opening CloudWatch dashboard..."
	@DASHBOARD_URL=$$(terraform output -raw cloudwatch_dashboard_url 2>/dev/null); \
	if [ -n "$$DASHBOARD_URL" ]; then \
		echo "Dashboard URL: $$DASHBOARD_URL"; \
		if command -v open &> /dev/null; then \
			open "$$DASHBOARD_URL"; \
		elif command -v xdg-open &> /dev/null; then \
			xdg-open "$$DASHBOARD_URL"; \
		fi; \
	else \
		echo "$(RED)[ERROR]$(NC) Dashboard URL not found. Deploy infrastructure first."; \
	fi