#!/usr/bin/env bash
# Atualiza backend e polling para a imagem promovida no GHCR e volta à anterior se o /health falhar.
# Roda na VM como root, disparado pelo pac-update.timer. Não usa SSH: a VM só busca (pull).
set -euo pipefail

IMAGE="${PAC_REGISTRY_IMAGE:-ghcr.io/arthurhassuma/pac-bi-assistant}"
TAG="${PAC_TRACK_TAG:-production}"
PROJECT="${PAC_COMPOSE_PROJECT:-pac-bi-24h}"
COMPOSE_FILE="${PAC_COMPOSE_FILE:?defina PAC_COMPOSE_FILE com o caminho do compose.yaml da VM}"
HEALTH_URL="${PAC_HEALTH_URL:-http://127.0.0.1:8000/health}"
STATE_DIR="${PAC_STATE_DIR:-/var/lib/pac-update}"
LOCAL_IMAGE="pac-bi-runtime:local"
PREVIOUS_IMAGE="pac-bi-runtime:previous"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
compose() { docker compose -p "$PROJECT" -f "$COMPOSE_FILE" "$@"; }
image_id() { docker image inspect --format '{{.Id}}' "$1" 2>/dev/null || true; }

mkdir -p "$STATE_DIR"
LOCK="$STATE_DIR/lock.d"
if ! mkdir "$LOCK" 2>/dev/null; then
  log "outra atualização em andamento; nada a fazer"
  exit 0
fi
trap 'rmdir "$LOCK"' EXIT

if ! docker pull --quiet "$IMAGE:$TAG" >/dev/null; then
  log "não foi possível baixar $IMAGE:$TAG; mantendo a versão atual"
  exit 0
fi

new_id="$(image_id "$IMAGE:$TAG")"
current_id="$(image_id "$LOCAL_IMAGE")"
if [ "$new_id" = "$current_id" ]; then
  exit 0
fi
if [ -f "$STATE_DIR/failed" ] && [ "$(cat "$STATE_DIR/failed")" = "$new_id" ]; then
  exit 0
fi

revision="$(docker image inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$IMAGE:$TAG" 2>/dev/null || true)"
log "nova imagem (revisão ${revision:-desconhecida}); atualizando"

if [ -n "$current_id" ]; then
  docker tag "$LOCAL_IMAGE" "$PREVIOUS_IMAGE"
fi
docker tag "$IMAGE:$TAG" "$LOCAL_IMAGE"

deployed() {
  compose up -d --wait --wait-timeout 120 backend &&
    compose up -d polling &&
    curl --fail --silent --max-time 5 "$HEALTH_URL" >/dev/null
}

if deployed; then
  printf '%s\n' "${revision:-desconhecida}" >"$STATE_DIR/deployed-revision"
  rm -f "$STATE_DIR/failed"
  log "atualização concluída (revisão ${revision:-desconhecida})"
  exit 0
fi

log "falha na atualização (revisão ${revision:-desconhecida}); voltando à versão anterior"
printf '%s\n' "$new_id" >"$STATE_DIR/failed"
if [ -n "$current_id" ]; then
  docker tag "$PREVIOUS_IMAGE" "$LOCAL_IMAGE"
  compose up -d backend polling || log "a reversão também falhou; verifique a VM manualmente"
fi
exit 1
