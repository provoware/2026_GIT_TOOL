#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

export BOOTSTRAP_PROJECT_ROOT="$project_root"

source "$project_root/scripts/bootstrap/bootstrap.lib.sh"

bootstrap_main "$@"
