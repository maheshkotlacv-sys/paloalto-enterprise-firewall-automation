# run `make help` to see targets

TERRAFORM_DIR := terraform
ANSIBLE_DIR   := ansible
PYTHON_DIR    := python
INVENTORY     := ansible/inventory/hosts.yml

.PHONY: help tf-init tf-plan tf-apply tf-destroy ansible-check ansible-deploy \
        ansible-vpn ansible-panorama backup audit compliance threat-sync \
        test lint pre-commit clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# terraform
tf-init: ## init terraform (no backend)
	terraform -chdir=$(TERRAFORM_DIR) init -backend=false

tf-plan: ## plan - needs terraform.tfvars
	terraform -chdir=$(TERRAFORM_DIR) init
	terraform -chdir=$(TERRAFORM_DIR) plan -var-file=terraform.tfvars -out=tf.plan

tf-apply: ## apply the plan
	terraform -chdir=$(TERRAFORM_DIR) apply tf.plan

tf-destroy: ## destroy everything (will prompt)
	terraform -chdir=$(TERRAFORM_DIR) destroy -var-file=terraform.tfvars

tf-validate: ## fmt check + validate
	terraform -chdir=$(TERRAFORM_DIR) fmt -check -recursive
	terraform -chdir=$(TERRAFORM_DIR) init -backend=false
	terraform -chdir=$(TERRAFORM_DIR) validate

# ansible
ansible-check: ## dry run - no changes applied
	ansible-playbook -i $(INVENTORY) $(ANSIBLE_DIR)/playbooks/site.yml --check --diff

ansible-deploy: ## full deployment
	ansible-playbook -i $(INVENTORY) $(ANSIBLE_DIR)/playbooks/site.yml

ansible-vpn: ## vpn config only
	ansible-playbook -i $(INVENTORY) $(ANSIBLE_DIR)/playbooks/deploy_vpn.yml

ansible-panorama: ## commit + push via panorama
	ansible-playbook -i $(INVENTORY) $(ANSIBLE_DIR)/playbooks/site.yml -l panorama

ansible-rollback: ## emergency rollback to last committed config
	ansible-playbook -i $(INVENTORY) $(ANSIBLE_DIR)/playbooks/rollback.yml

# python day-2 ops
backup: ## backup config to s3 (set PA_BACKUP_BUCKET)
	cd $(PYTHON_DIR) && python3 pan_config_backup.py \
		--inventory ../ansible/inventory/hosts.yml \
		--bucket $${PA_BACKUP_BUCKET:-pa-config-backups}

audit: ## rule audit - outputs report.html
	cd $(PYTHON_DIR) && python3 pan_rule_audit.py \
		--device $${PANOS_HOSTNAME} \
		--days 90 \
		--output rule-audit-report.html

compliance: ## cis compliance report
	cd $(PYTHON_DIR) && python3 pan_compliance_report.py \
		--device $${PANOS_HOSTNAME} \
		--output compliance-report.html
	@echo "report at python/compliance-report.html"

threat-sync: ## sync threat intel to EDL (set EDL_BUCKET, optionally FEEDS_FILE)
	cd $(PYTHON_DIR) && python3 pan_threat_intel_sync.py \
		--bucket $${EDL_BUCKET:-pa-edl-bucket} \
		$${FEEDS_FILE:+--feeds $$FEEDS_FILE}

# tests + linting
test: ## run pytest
	pytest tests/ -v --tb=short

lint: ## ansible-lint + terraform fmt check
	ansible-lint $(ANSIBLE_DIR)/
	terraform -chdir=$(TERRAFORM_DIR) fmt -check -recursive
	cd $(PYTHON_DIR) && python3 -m py_compile pan_config_backup.py pan_log_analyzer.py \
		pan_rule_audit.py pan_compliance_report.py pan_threat_intel_sync.py \
		utils/pan_connector.py utils/report_generator.py && echo "python syntax ok"

pre-commit: ## run all pre-commit hooks
	pre-commit run --all-files

clean: ## remove terraform artefacts + pycache
	rm -rf $(TERRAFORM_DIR)/.terraform $(TERRAFORM_DIR)/tf.plan $(TERRAFORM_DIR)/plan.json
	find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	rm -f python/*.html python/*.json
