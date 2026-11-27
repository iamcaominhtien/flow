#!/bin/sh
# Usage: smoke.sh ENV ; three checks, any failure fails the step
set -e
BASE="https://$1.shop.example.com"
curl -fsS "$BASE/health" > /dev/null
curl -fsS "$BASE/api/products?limit=1" > /dev/null
curl -fsS -X POST "$BASE/api/cart/dry-run" > /dev/null
