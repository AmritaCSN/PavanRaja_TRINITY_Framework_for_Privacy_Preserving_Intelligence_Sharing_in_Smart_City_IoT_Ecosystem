#!/usr/bin/env bash
# TRINITY FRAMEWORK — Teardown (clean re-run)
# Usage: bash scripts/teardown.sh [--volumes]

set -euo pipefail

TRINITY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WIPE_VOLUMES="${1:-}"

cd "${TRINITY_ROOT}"

echo "[TRINITY] Stopping all containers..."
docker compose -f nvflare-projects/docker-compose.yml down ${WIPE_VOLUMES:+--volumes} --remove-orphans 2>/dev/null || true

if [ "${WIPE_VOLUMES}" = "--volumes" ]; then
    echo "[TRINITY] Removing crypto material and artifacts..."
    rm -rf fabric-network/crypto-config/
    rm -f  fabric-network/config/genesis.block
    rm -f  fabric-network/config/city-intel-channel.tx
    rm -f  fabric-network/config/CityAMSPanchors.tx
    rm -f  fabric-network/config/CityBMSPanchors.tx
    rm -f  fabric-network/config/CityCMSPanchors.tx
    rm -rf nvflare-projects/fl_project/prod_00/
fi

echo "[TRINITY] Pruning Docker artifacts..."
docker network rm trinity_net 2>/dev/null || true
docker volume prune -f 2>/dev/null || true

echo "[TRINITY] Teardown complete."
