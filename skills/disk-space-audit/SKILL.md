---
name: disk-space-audit
description: Audit and safely clean disk usage across filesystems, Docker images/containers/volumes, logs, databases, caches, build outputs, and ML model stores. Use whenever the user asks what is consuming disk, wants Docker or model cleanup, mentions a full partition, or asks to move large data off the home SSD. On this host, actively check both ~/hroot service trees and /mnt/store-ext4/models. Read-only first; never delete, prune, or move data without explicit confirmation.
disable-model-invocation: true
---

# Disk-space audit and cleanup

Start read-only. Report exact paths, physical-size caveats, and what is safe to rebuild before proposing changes.

## Host storage map

Inspect these locations explicitly rather than relying on a single `du` traversal:

| Area | Paths | Look for |
|---|---|---|
| Filesystems | `/`, `/home`, `/mnt/store-ext4` | Capacity, mount boundaries, unexpectedly full partitions |
| Service state | `/home/ankit/hroot/devserver`, `/home/ankit/hroot/homeserver` | Compose services, bind-mounted volumes, logs, databases, backups |
| Docker data | `/home/ankit/docker_root` | Inspect through Docker commands; never edit overlay/container storage manually |
| Projects | `/home/ankit/hroot/projects` or `/projects` | Build trees, venvs, `node_modules`, generated artifacts, checked-out model assets |
| Shared models | `/mnt/store-ext4/models` | Canonical location for container model weights and Hugging Face caches |
| User caches | `/home/ankit/.cache`, `/home/ankit/.local/share`, language/package-manager caches | Rebuildable downloads, wheels, browser caches, tool state |
| Durable user data | `/home/ankit/hroot/allplace`, databases, uploads | Review only; never classify as junk merely because it is large |
| System logs | `/var/log`, systemd journal, deleted-open files | Retention, stale logs, space not visible to ordinary `du` |

The two primary Compose sources are:

- `/home/ankit/hroot/devserver/docker-compose.yml`
- `/home/ankit/hroot/homeserver/docker-compose.yaml`

Also check Compose overrides and profile files in those directories.

## Read-only inventory

### 1. Establish filesystem boundaries

Use:

```text
df -hT PATH
findmnt -T PATH
du -xhd1 PATH | sort -hr
```

Run `du` separately for nested mounts such as `/mnt/store-ext4`; `du -x` intentionally does not cross filesystems. Do not sum overlapping parent and child totals.

### 2. Drill down large trees

Prioritize:

- `devserver/volumes`, `homeserver/volumes`, and their `logs/` directories
- SQLite/Postgres data, request logs, audio caches, uploads, and backups
- project build output, virtual environments, package caches, and dependency trees
- large regular files sorted descending
- `journalctl --disk-usage` and `lsof +L1` when available

Label database sizes as allocated physical size when relevant. SQLite deletion does not shrink a file without compaction; mention that before suggesting retention changes.

### 3. Audit Docker without pruning

Collect:

```text
docker ps -a
docker image ls
docker system df -v
docker volume ls
```

Cross-reference container Compose labels with the current Compose service lists. Classify objects as:

- running and Compose-defined
- stopped but Compose-defined, possibly an intentional cold/spare service
- orphaned because its service was removed
- unreferenced tagged image
- dangling build/intermediate image still referenced by a failed container

Do not sum virtual image sizes. Prefer `UNIQUE SIZE` plus writable container layers, and state when shared layers make immediate reclaim smaller than the displayed image size. Never run broad `docker system prune` as part of an audit.

Do not inspect or print container environments because they can contain credentials. Mounts, labels, image IDs, status, health, and non-secret commands are sufficient.

### 4. Audit ML model placement

Container model data belongs under `/mnt/store-ext4/models`, not under `~/hroot` service volumes.

Inspect every container mount whose destination resembles:

- `/models`
- Hugging Face or Transformers caches
- Ollama storage
- Whisper, embedding, ASR, TTS, or image-generation caches

Search current Compose files and service volumes for:

- `*.gguf`, `*.safetensors`, `*.onnx`, `*.nemo`, `*.pt`, `*.pth`, `*.ckpt`, and `*.tflite`
- Hugging Face cache trees and extensionless Ollama blobs
- application-managed local model caches such as Open WebUI Whisper models

Distinguish model weights from small reference audio, generated speech, tokenizers, and repository fixtures. If a tracked repository asset is required for builds, preserve it in the repository but point the runtime container at a verified central copy.

## Cleanup workflow

Only proceed after the user explicitly approves the named candidates.

1. Record baseline filesystem and Docker usage.
2. Stop or remove only the approved containers.
3. For model moves across filesystems:
   - copy with metadata-preserving `rsync`
   - compare source and destination with a dry-run `rsync --delete`
   - delete the source only when the comparison is empty
   - use a symlink only when local tooling still needs the old path
4. Update Compose bind mounts and remove retired service definitions.
5. Remove obsolete service-specific routes, recipes, and rendered/template config when retirement is intentional.
6. Remove images only after verifying no retained container needs them.
7. Delete named volumes only when the user has explicitly approved deleting their data.
8. Validate Compose and proxy configuration, recreate only affected services, and check health.
9. Re-run filesystem, Docker, mount, and large-model scans to measure the result.

Respect intentionally retained cold services. A stopped container is not automatically junk.

## Candidate labels

- **Rebuildable:** package cache, compiler output, `node_modules`, venv, downloaded image
- **Movable:** model weights or caches currently on the wrong filesystem
- **Review:** logs, databases, archives, backups, uploads, stopped Compose services
- **Do not blindly remove:** source trees, durable user data, active databases, Docker volumes, tracked repository assets

## Report format

```text
# Disk-space report

## Current state
- Filesystem capacity / used / free
- Docker image / container / volume usage
- Mount and hardlink caveats

## Highest-priority candidates
| Reclaimable | Path or Docker object | Type | Evidence | Recommended action |

## Model placement
| Size | Current path | Runtime consumer | Canonical destination | Status |

## Retained intentionally
- Running services and cold/spare services that should remain

## Suggested order
1. Safest/highest-confidence action
2. Data-preserving moves
3. Items requiring a policy decision

No changes made.
```

After approved cleanup, replace the final line with measured reclaimed space, changed files/services, validation results, preserved data locations, and any residual stale integration references.
