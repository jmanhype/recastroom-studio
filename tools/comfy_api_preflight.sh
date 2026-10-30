#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMFY_CLI_VERSION="${COMFY_CLI_VERSION:-1.24.0}"
COMFY_CLI=(uvx --from "comfy-cli==${COMFY_CLI_VERSION}" comfy)

"${COMFY_CLI[@]}" --json build validate deploy/comfy --custom-nodes-dir custom_nodes
"${COMFY_CLI[@]}" --json build push deploy/comfy --dry-run --custom-nodes-dir custom_nodes
