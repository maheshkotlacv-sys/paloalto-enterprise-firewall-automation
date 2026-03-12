# Architecture Overview

## Design intent
This project automates the lifecycle of Palo Alto VM-Series firewalls deployed in AWS as part of a hybrid cloud security architecture. The on-premises data centre connects to AWS via an IKEv2 IPsec VPN tunnel, and all traffic between DC workloads and AWS workloads passes through the VM-Series firewall for centralized inspection.

Panorama serves as the single management plane for all firewalls — configuration is pushed from Panorama to device groups rather than managing each device directly. This ensures policy consistency and provides a single audit trail.

## Component roles

**Terraform** provisions the AWS infrastructure: VM-Series EC2 instances, network interfaces, EIPs, security groups, and the S3 bootstrap bucket. The bootstrap bucket contains `init-cfg.txt` which directs each VM-Series to register with Panorama on first boot, pulling its template and device group configuration automatically.

**Ansible** manages configuration state via the `paloaltonetworks.panos` collection. Playbooks are structured as roles for separation of concerns: baseline hardening, security policy, NAT, VPN, HA, threat profiles, and logging. All changes are pushed through Panorama using commit-and-push rather than direct device commits.

**Python scripts** handle Day-2 operations that are operational rather than declarative:
- `pan_config_backup.py` — exports running XML config and uploads to S3 nightly
- `pan_rule_audit.py` — identifies unused, permissive, shadowed, and unlogged rules
- `pan_threat_intel_sync.py` — pulls IOC feeds and publishes EDL files to S3
- `pan_compliance_report.py` — CIS PAN-OS benchmark checks with HTML reporting
- `pan_log_analyzer.py` — queries threat logs and generates event summary reports

## VPN architecture (DC-to-AWS)

The IKEv2/IPsec tunnel uses the following design:
- IKE crypto profile: AES-256-GCM, SHA-384, DH Group 20 (384-bit ECC)
- IPsec crypto profile: AES-256-GCM, PFS Group 20, 1-hour rekey
- Tunnel monitoring enabled — detects failure and triggers failover
- BGP is not used — static routes are configured on both ends pointing to remote networks via the tunnel interface
- Appliance mode is not applicable to VM-Series direct VPN (it applies to TGW-attached inspection)

## High Availability

VM-Series is deployed as an Active/Passive HA pair across two Availability Zones. HA1 uses the management interface for heartbeat and hello. HA2 uses a dedicated ENI for state synchronisation. On failover, the passive device becomes active and EIPs are remapped to its interfaces via the AWS HA helper or lambda-based failover.

## Security zones

| Zone | Interface | Connected to |
|------|-----------|-------------|
| untrust | ethernet1/1 | Internet / WAN / VPN peer |
| trust | ethernet1/2 | AWS internal workload VPCs |
| vpn-tunnel | tunnel.1 | DC networks via IPsec |
| mgmt | (out-of-band) | Panorama + admin access |

All security policy is zone-based. No inter-zone traffic is permitted by default — rules explicitly allow specific App-IDs between zones.
