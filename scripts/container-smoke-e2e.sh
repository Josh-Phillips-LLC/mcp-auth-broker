#!/usr/bin/env bash
set -euo pipefail

image_tag="mcp-auth-broker:smoke"

docker build -t "$image_tag" .
docker run --rm "$image_tag" python -m mcp_auth_broker.cli smoke-e2e
