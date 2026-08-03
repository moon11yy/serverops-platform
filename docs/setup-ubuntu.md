# Ubuntu VM Setup

## Recommended VM profile

- Ubuntu Server 24.04 LTS, amd64
- 6 virtual CPUs
- 16 GB RAM
- 100 GB dynamically allocated disk
- NAT networking
- OpenSSH server enabled during installation

This allocation is intentionally larger than the Docker Compose MVP requires because the
same VM will later run k3s, Prometheus, Grafana, and Argo CD.

## Base packages

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl ca-certificates make jq openssh-server
sudo systemctl enable --now ssh
```

## Install Docker Engine and the Compose plugin

Run:

```bash
chmod +x scripts/install-docker-ubuntu.sh
./scripts/install-docker-ubuntu.sh
```

Then log out and log back in so Docker group membership is applied.

## Verify

```bash
docker --version
docker compose version
docker run --rm hello-world
```

## Clone and start

```bash
git clone <your-repository-url>
cd serverops-platform
cp .env.example .env
nano .env
docker compose up --build -d
docker compose ps
```
