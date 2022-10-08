#!/bin/bash --login

set +euo pipefail
conda activate cilroy
set -euo pipefail

exec "$@"
