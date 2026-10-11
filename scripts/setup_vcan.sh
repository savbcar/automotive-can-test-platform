#!/usr/bin/env bash
set -euo pipefail

INTERFACE="${1:-vcan0}"

if ! command -v ip >/dev/null 2>&1; then
  echo "ERROR: iproute2 is required" >&2
  exit 1
fi

if ip link show "$INTERFACE" >/dev/null 2>&1; then
  sudo ip link set "$INTERFACE" up
  echo "$INTERFACE already exists and is up"
  exit 0
fi

sudo modprobe vcan 2>/dev/null || true
sudo ip link add dev "$INTERFACE" type vcan
sudo ip link set "$INTERFACE" up
ip -details link show "$INTERFACE"
