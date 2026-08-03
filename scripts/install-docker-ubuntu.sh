#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -eq 0 ]]; then
  echo "Run this script as a regular user with sudo access, not as root." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y ca-certificates curl git make jq

conflicting_packages=(docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc)
for package in "${conflicting_packages[@]}"; do
  sudo apt-get remove -y "$package" 2>/dev/null || true
done

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

sudo docker run --rm hello-world
sudo docker compose version

echo "Docker installation completed. Log out and log back in before running Docker without sudo."
