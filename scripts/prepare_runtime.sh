#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_URL="https://github.com/rh-hideout/pokeemerald-expansion.git"
UPSTREAM_REF="75b806a3ab57a81ff1eb6179288981f0b3cc3050"
RUNTIME_DIR="${GOLD_RUNTIME_DIR:-$ROOT_DIR/build/pokeemerald-expansion}"

mkdir -p "$(dirname "$RUNTIME_DIR")"

if [[ ! -d "$RUNTIME_DIR/.git" ]]; then
    git clone "$UPSTREAM_URL" "$RUNTIME_DIR"
fi

git -C "$RUNTIME_DIR" fetch --tags origin
git -C "$RUNTIME_DIR" checkout --detach "$UPSTREAM_REF"
git -C "$RUNTIME_DIR" reset --hard "$UPSTREAM_REF"
git -C "$RUNTIME_DIR" clean -fdx

while IFS= read -r patch; do
    [[ -z "$patch" ]] && continue
    patch_path="$ROOT_DIR/patches/pokeemerald-expansion/$patch"
    echo "Applying $patch"
    git -C "$RUNTIME_DIR" apply --check "$patch_path"
    git -C "$RUNTIME_DIR" apply "$patch_path"
done < "$ROOT_DIR/patches/pokeemerald-expansion/series"

python3 "$ROOT_DIR/tools/check_pokeemerald_capacity.py" --expect-phase1 "$RUNTIME_DIR"

echo "Prepared GOLD runtime at: $RUNTIME_DIR"
echo "Upstream ref: $(git -C "$RUNTIME_DIR" rev-parse HEAD)"
