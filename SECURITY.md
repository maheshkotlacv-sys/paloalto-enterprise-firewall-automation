# Security Policy

This repository contains automation code for enterprise firewall infrastructure. No real credentials, device serial numbers, or production IPs are committed.

## Reporting security issues

Open a GitHub issue labelled `security` for architecture or code-level findings.
For sensitive disclosures, contact the repository owner directly before public disclosure.

## Credential policy

All credentials are consumed via environment variables:
- `PANOS_USERNAME` / `PANOS_PASSWORD` — direct device access
- `PANORAMA_USERNAME` / `PANORAMA_PASSWORD` — Panorama access
- `TF_VAR_panorama_vm_auth_key` — bootstrap auth key
- `TF_VAR_vpn_pre_shared_key` — VPN PSK

Never commit credentials to this repository. The `.gitignore` excludes `terraform.tfvars` and `.env` files.
