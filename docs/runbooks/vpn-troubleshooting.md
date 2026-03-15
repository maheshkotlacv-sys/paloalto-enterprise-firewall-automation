# Runbook: DC-to-AWS VPN Troubleshooting

## Check IKE phase 1
```
> show vpn ike-sa
```
Expected: State = active, DH group = 20, Cipher = AES-256-GCM

## Check IPsec phase 2
```
> show vpn ipsec-sa
```
Expected: Active tunnels shown with byte counters incrementing

## Check tunnel interface
```
> show interface tunnel.1
```
Expected: State = up, traffic counters incrementing

## Common causes of tunnel failure

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| IKE SA not established | PSK mismatch | Verify PSK matches on both ends |
| IKE SA up, IPsec SA missing | Crypto profile mismatch | Verify DH group and encryption match |
| Both SAs up, no traffic | Routing issue | Check static routes on both ends |
| Intermittent drops | MTU issue | Enable TCP MSS clamping on tunnel interface |
