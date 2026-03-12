# Demo Commands

## Terraform

```bash
# Provision VM-Series on AWS
export TF_VAR_panorama_vm_auth_key="your-auth-key"
export TF_VAR_panorama_username="svc-terraform"
export TF_VAR_panorama_password="..."
export TF_VAR_vpn_pre_shared_key="..."

make tf-init
make tf-validate
make tf-plan
terraform -chdir=terraform apply -var-file=terraform.tfvars

# View outputs
terraform -chdir=terraform output
```

## Ansible — deploy full configuration

```bash
# Export credentials
export PANOS_USERNAME="svc-ansible"
export PANOS_PASSWORD="..."
export PANORAMA_USERNAME="svc-ansible"
export PANORAMA_PASSWORD="..."
export VPN_PRE_SHARED_KEY="..."
export DC_VPN_PEER_IP="203.0.113.1"

# Check mode (dry run — no changes)
make ansible-check

# Full deployment
ansible-playbook ansible/playbooks/site.yml -i ansible/inventory/hosts.yml

# Deploy security policy only
make deploy-policy

# Deploy VPN only
make deploy-vpn

# Onboard a new device
ansible-playbook ansible/playbooks/onboard_device.yml \
  -i ansible/inventory/hosts.yml \
  -e "target_host=vmseries-aws-03"
```

## Python Day-2 operations

```bash
# Security rule audit
export PANOS_USERNAME="svc-audit"
export PANOS_PASSWORD="..."
export VMSERIES_01_MGMT_IP="10.0.1.10"

python3 python/pan_rule_audit.py \
  --device $VMSERIES_01_MGMT_IP \
  --days 90 \
  --output rule-audit-$(date +%Y%m%d).html

# Configuration backup
python3 python/pan_config_backup.py \
  --inventory ansible/inventory/hosts.yml \
  --bucket my-panos-backup-bucket

# Threat intel sync
python3 python/pan_threat_intel_sync.py \
  --bucket my-edl-bucket

# CIS compliance report
python3 python/pan_compliance_report.py \
  --device $VMSERIES_01_MGMT_IP \
  --output compliance-$(date +%Y%m%d).html

# Threat log analysis (last 24 hours, high+ severity)
python3 python/pan_log_analyzer.py \
  --device $VMSERIES_01_MGMT_IP \
  --severity high --hours 24
```

## VPN verification

```bash
# Check IKE SA status on VM-Series (via Ansible)
ansible -i ansible/inventory/hosts.yml aws_vmseries \
  -m paloaltonetworks.panos.panos_op \
  -a "provider={{ panos_provider }} cmd='show vpn ike-sa'"

# Check IPsec tunnel state
ansible -i ansible/inventory/hosts.yml aws_vmseries \
  -m paloaltonetworks.panos.panos_op \
  -a "provider={{ panos_provider }} cmd='show vpn ipsec-sa'"
```
