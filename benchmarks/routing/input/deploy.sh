#!/bin/sh
# Deploy the shop. Usage: ./deploy.sh staging|production
set -e
ENV=$1
[ "$ENV" = staging ] || [ "$ENV" = production ] || { echo "usage: deploy.sh staging|production"; exit 2; }
git diff --quiet || { echo "uncommitted changes"; exit 1; }
make test
docker build -t shop:"$(git rev-parse --short HEAD)" ./shop
if [ "$ENV" = production ]; then
  ./scripts/check_staging_green.sh || { echo "staging is not green"; exit 1; }
  read -p "Deploy to production? [y/N] " ok; [ "$ok" = y ] || exit 1
fi
./scripts/migrate.sh "$ENV"
./scripts/rollout.sh "$ENV" --canary 10
sleep 300
if ./scripts/error_rate.sh "$ENV" --above 1%; then
  ./scripts/rollout.sh "$ENV" --undo
  ./scripts/notify.sh "#deploys" "rollback on $ENV"
  exit 1
fi
./scripts/rollout.sh "$ENV" --full
./scripts/notify.sh "#deploys" "deployed to $ENV"
