# Runbook: Emergency Configuration Rollback

## Option 1 — Ansible rollback playbook
```bash
ansible-playbook ansible/playbooks/rollback.yml \
  -e "target_host=<device-name>"
```
This reverts uncommitted candidate config to last committed state.

## Option 2 — Panorama revert
1. Log into Panorama
2. Navigate to: Device > Config Audit
3. Select the previous good config version
4. Click Revert > Commit and Push

## Option 3 — PAN-OS CLI
```
> revert config from running-config.xml
> commit description "Emergency rollback"
```

## Post-rollback verification
1. Verify VPN tunnels are up: `show vpn ike-sa`
2. Verify security policy is as expected: `show running security-policy`
3. Run compliance check: `python3 python/pan_compliance_report.py --device <ip>`
4. Document incident in change management system
