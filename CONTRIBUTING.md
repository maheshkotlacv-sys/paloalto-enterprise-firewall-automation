# Contributing

## Branch naming
- `feat/<description>` — new features
- `fix/<description>` — bug fixes
- `docs/<description>` — documentation updates
- `refactor/<description>` — code restructuring

## Pull request checklist
- [ ] `make tf-validate` passes
- [ ] `make ansible-lint` passes
- [ ] `make test` passes
- [ ] `make scan` passes (no HIGH/CRITICAL findings)
- [ ] Documentation updated if architecture changed
- [ ] New variables have descriptions and validation blocks
- [ ] No credentials or real IPs committed

## Commit message format
```
feat(vpn): add tunnel monitoring with failover
fix(ansible): correct zone assignment for trust interface
docs(threat-model): add EDL poisoning threat
```
