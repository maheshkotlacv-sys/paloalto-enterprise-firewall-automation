# Palo Alto Enterprise Firewall Automation

[![CI](https://github.com/maheshkotlacv-sys/paloalto-enterprise-firewall-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/maheshkotlacv-sys/paloalto-enterprise-firewall-automation/actions/workflows/ci.yml)
[![Compliance Scan](https://github.com/maheshkotlacv-sys/paloalto-enterprise-firewall-automation/actions/workflows/compliance-scan.yml/badge.svg)](https://github.com/maheshkotlacv-sys/paloalto-enterprise-firewall-automation/actions/workflows/compliance-scan.yml)
[![Terraform](https://img.shields.io/badge/Terraform-1.8+-7B42BC?style=flat&logo=terraform)](https://www.terraform.io/)
[![Ansible](https://img.shields.io/badge/Ansible-2.15+-EE0000?style=flat&logo=ansible)](https://www.ansible.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Production-grade automation framework for Palo Alto VM-Series firewalls on AWS, managed through Panorama, with DC-to-AWS hybrid cloud VPN — covering infrastructure provisioning, configuration management, Day-2 operations, and continuous compliance.

---

## What this project covers

Most firewall automation repositories demonstrate basic connectivity. This one is built around how enterprise network security teams actually operate Palo Alto at scale:

- Infrastructure is **provisioned by Terraform** — VM-Series on AWS with S3 bootstrap, IAM roles, and security groups
- Configuration is **managed by Ansible** — Panorama device groups, security policies, NAT, IPsec VPN, HA, threat prevention profiles
- Day-2 operations are **automated by Python** — config backup, rule auditing, threat intel EDL sync, CIS compliance reporting, log analysis
- Every change is **gated by CI/CD** — ansible-lint, terraform validate, tfsec, OPA policy checks, and unit tests run before anything touches a device

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Enterprise Network                            │
│                                                                       │
│  On-Premises Data Centre                  AWS (us-east-1)            │
│  ─────────────────────                    ──────────────             │
│  ┌──────────────────┐                    ┌──────────────────────┐   │
│  │  Corporate LAN    │                    │   Security VPC        │   │
│  │  10.0.0.0/8       │                    │   100.64.0.0/16       │   │
│  │                   │                    │                       │   │
│  │  ┌─────────────┐ │   IPsec/IKEv2      │  ┌────────────────┐  │   │
│  │  │  DC Firewall │◄├────VPN Tunnel──────┤► │  VM-Series     │  │   │
│  │  │  (Physical)  │ │   (BGP over VPN)   │  │  (AWS EC2)     │  │   │
│  │  └─────────────┘ │                    │  └───────┬────────┘  │   │
│  └──────────────────┘                    │          │            │   │
│                                           │  ┌───────▼────────┐  │   │
│  ┌──────────────────┐                    │  │  Spoke VPCs     │  │   │
│  │  Panorama         │◄───Management──────┤  │  App workloads  │  │   │
│  │  (On-Prem/Cloud)  │    (HTTPS/API)     │  └────────────────┘  │   │
│  │                   │                    └──────────────────────┘   │
│  │  Device Groups:   │                                               │
│  │  - aws-vmseries   │    Automation Stack                           │
│  │  - dc-perimeter   │    ────────────────                           │
│  └──────────────────┘    Terraform  → Provision VM-Series + VPC     │
│                            Ansible   → Configure via Panorama API    │
│                            Python    → Day-2 ops + compliance        │
│                            CI/CD     → Gate every change             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Repository structure

```text
.
├── .github/workflows/
│   ├── ci.yml                          # PR gate: lint → validate → scan → test
│   └── compliance-scan.yml             # Nightly CIS compliance check
├── terraform/                          # VM-Series infrastructure on AWS
│   ├── main.tf / variables.tf / ...
│   └── modules/
│       ├── vm_series/                  # PA VM-Series EC2 + interfaces
│       ├── bootstrap_s3/               # S3 bootstrap bucket + IAM
│       └── security_groups/            # Management + dataplane SGs
├── ansible/
│   ├── inventory/                      # Device inventory + group vars
│   ├── roles/
│   │   ├── panos_baseline/             # Device hardening + system config
│   │   ├── panos_security_policy/      # Zone-based security rules
│   │   ├── panos_nat_policy/           # NAT rules (source + destination)
│   │   ├── panos_vpn/                  # IKEv2 + IPsec DC-to-AWS tunnel
│   │   ├── panos_ha/                   # Active/Passive HA
│   │   ├── panos_threat_profiles/      # AV, IPS, URL, WildFire profiles
│   │   ├── panos_logging/              # Syslog + Panorama log forwarding
│   │   └── panorama_push/              # Commit and push via Panorama
│   └── playbooks/                      # Orchestration playbooks
├── python/
│   ├── pan_config_backup.py            # XML config backup to S3
│   ├── pan_rule_audit.py               # Unused/shadowed/permissive rules
│   ├── pan_threat_intel_sync.py        # IOC feed → External Dynamic List
│   ├── pan_compliance_report.py        # CIS PAN-OS benchmark report
│   ├── pan_bulk_address_objects.py     # Bulk address/group management
│   ├── pan_log_analyzer.py             # Threat log parsing + alerting
│   └── utils/                          # API connector + report helpers
├── bootstrap/                          # PAN-OS S3 bootstrap package
├── policies/
│   ├── opa/firewall_policy.rego        # OPA rule hygiene enforcement
│   └── compliance/cis_panos_checks.yml # CIS benchmark definitions
├── docs/
│   ├── architecture.md
│   ├── threat-model.md
│   ├── demo-commands.md
│   └── runbooks/                       # Operational runbooks
├── tests/                              # pytest unit tests
├── Makefile
└── ...
```

---

## Quick start

```bash
git clone https://github.com/maheshkotlacv-sys/paloalto-enterprise-firewall-automation.git
cd paloalto-enterprise-firewall-automation

# Install Python dependencies
pip install -r python/requirements.txt

# Install Ansible collection
ansible-galaxy collection install paloaltonetworks.panos

# Install pre-commit hooks
pip install pre-commit && pre-commit install

# Provision VM-Series on AWS
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
make tf-init && make tf-plan

# Configure devices via Panorama
cp ansible/inventory/group_vars/all.yml.example ansible/inventory/group_vars/all.yml
make ansible-check

# Run compliance report
make compliance
```

---

## Automation layers

| Layer | Tool | Scope |
|-------|------|-------|
| Provision | Terraform | VM-Series EC2, S3 bootstrap, security groups, IAM |
| Configure | Ansible + Panorama API | Security policy, NAT, VPN, HA, threat profiles |
| Day-2 Ops | Python (pan-os-python) | Backup, audit, EDL sync, compliance, log analysis |
| Pipeline | GitHub Actions | Lint, validate, scan, policy check, unit tests |
| Compliance | Python + OPA | CIS PAN-OS benchmark, nightly scheduled scan |

---

## Makefile targets

```bash
make tf-init          # terraform init
make tf-validate      # terraform fmt + validate
make tf-plan          # terraform plan
make ansible-lint     # run ansible-lint on all playbooks
make ansible-check    # dry-run all playbooks (check mode)
make compliance       # run CIS compliance report
make backup           # run config backup for all devices
make rule-audit       # run security rule audit report
make threat-sync      # sync threat intel to EDL
make test             # run pytest unit tests
make scan             # tfsec + ansible-lint + OPA
make help             # list all targets
```

---

## Scope note

All IP addresses, credentials, device serial numbers, and account IDs are placeholders. No real infrastructure identifiers are committed. Credentials are consumed from environment variables or AWS Secrets Manager — never from files in this repository.

---

## License

MIT — see `LICENSE`.
