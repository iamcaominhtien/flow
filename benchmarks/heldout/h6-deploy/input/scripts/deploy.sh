#!/bin/sh
# Usage: deploy.sh ENV TAG
set -e
ENV=$1; TAG=$2
kubectl --context "$ENV" set image deploy/api api="registry.example.com/shop/api:$TAG"
if kubectl --context "$ENV" rollout status deploy/api --timeout=300s; then
  echo "$TAG" > ".last_good_$ENV"
else
  kubectl --context "$ENV" rollout undo deploy/api
  exit 1
fi
