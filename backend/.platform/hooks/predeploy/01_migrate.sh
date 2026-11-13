#!/bin/bash
set -euo pipefail

echo "Running TaskFlow database migrations..."
python -m alembic upgrade head
echo "TaskFlow database migrations completed successfully."
