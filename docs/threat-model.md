# Threat Model

STRIDE-based threat model for the Palo Alto VM-Series deployment on AWS with DC-to-AWS VPN.

## Assets

| Asset | Sensitivity |
|-------|------------|
| VM-Series firewall instances | Critical — compromise means inspection bypass |
| Panorama management plane | Critical — controls all device policy |
| VPN pre-shared key | Critical — compromise exposes DC-to-AWS tunnel |
| S3 bootstrap bucket | High — contains Panorama auth key and init config |
| IAM role for VM-Series | High — grants S3 access at bootstrap |
| Threat intelligence EDL | Medium — poisoning causes false block or miss |
| Config backup S3 bucket | Medium — contains device configuration XML |

## STRIDE threats and mitigations

### Spoofing
- **Threat**: Attacker impersonates a managed device to Panorama using a stolen VM auth key.
- **Mitigation**: VM auth keys are single-use and time-limited. Bootstrap S3 bucket is encrypted, private, and accessible only via instance IAM role. Auth key is passed as a sensitive Terraform variable and never stored in state plaintext.

### Tampering
- **Threat**: Attacker modifies firewall policy by directly accessing the PAN-OS management interface.
- **Mitigation**: Management security group restricts HTTPS and SSH to corporate IP space only (10.0.0.0/8). IMDSv2 is enforced on EC2 instances. All policy changes go through Panorama with commit audit logging.

- **Threat**: S3 bootstrap content is modified to inject malicious init-cfg.
- **Mitigation**: S3 bucket has public access blocked, versioning enabled, and access restricted to the specific instance IAM role. S3 object integrity is verified by the bootstrap process.

### Repudiation
- **Threat**: Administrator claims they did not make a policy change.
- **Mitigation**: Panorama maintains a full commit history with username, timestamp, and diff. AWS CloudTrail records all API calls to EC2 and S3. Git history records all Ansible and Terraform changes.

### Information Disclosure
- **Threat**: VPN pre-shared key is exposed via Terraform state.
- **Mitigation**: PSK is passed as a sensitive variable (`TF_VAR_vpn_pre_shared_key`) and marked sensitive in Terraform. Remote state should be stored in S3 with encryption and restricted IAM access. Rotate PSK on a defined schedule.

- **Threat**: Config backup XML exposes address objects, credentials, or network topology.
- **Mitigation**: Backup bucket uses SSE-KMS encryption. Access restricted to the backup automation IAM role. Credentials are not stored in PAN-OS config XML in modern deployments.

### Denial of Service
- **Threat**: VM-Series instance is terminated by an attacker with AWS console access.
- **Mitigation**: EC2 termination protection should be enabled. IAM policy restricts who can terminate firewall instances. HA pair ensures continuity on single-instance failure.

- **Threat**: Threat intel EDL is poisoned with corporate IP ranges, causing legitimate traffic to be blocked.
- **Mitigation**: EDL feed validation rejects non-routable and RFC1918 addresses. Feed sources are pinned to known trusted providers. EDL changes are archived in S3 for rollback.

### Elevation of Privilege
- **Threat**: Compromised EC2 workload in a spoke VPC uses the VM-Series trust interface to pivot.
- **Mitigation**: Trust security group only accepts traffic from RFC1918 ranges. PAN-OS zone-based policy enforces application allow-listing. WildFire and IPS profiles inspect all allowed traffic.

## Residual risks

1. **Panorama compromise** — If Panorama is compromised, an attacker can push malicious policy to all managed devices. Panorama access should be protected with MFA, role-based access control, and network segmentation.
2. **IKEv2 implementation vulnerabilities** — Depends on PAN-OS IKEv2 implementation correctness. Mitigated by keeping PAN-OS patched and using strong crypto profiles.
3. **EDL polling reliability** — If S3 becomes unreachable, firewalls continue using the last cached EDL. This is a known PAN-OS behaviour and is acceptable for this threat model.
