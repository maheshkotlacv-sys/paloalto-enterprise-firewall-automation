# Runbook: New VM-Series Device Onboarding

## Prerequisites
- Terraform has provisioned the EC2 instance and bootstrap S3 content
- Device has registered with Panorama (verify in Panorama > Managed Devices)
- Device IP is reachable from the Ansible control host on port 443

## Steps

1. Add the device to `ansible/inventory/hosts.yml` under `aws_vmseries`
2. Set the correct `ansible_host`, `device_group`, and `template_stack` values
3. Run the onboarding playbook:
   ```bash
   ansible-playbook ansible/playbooks/onboard_device.yml \
     -i ansible/inventory/hosts.yml \
     -e "target_host=<new-device-name>"
   ```
4. Verify the device appears in Panorama > Managed Devices as connected
5. Verify the security policy is pushed: check Panorama > Push > Status
6. Run a compliance check on the new device:
   ```bash
   python3 python/pan_compliance_report.py --device <device-ip>
   ```

## Rollback
If onboarding fails, run:
```bash
ansible-playbook ansible/playbooks/rollback.yml -e "target_host=<new-device-name>"
```
