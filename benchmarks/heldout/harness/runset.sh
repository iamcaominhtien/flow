#!/bin/sh
# Usage: runset.sh LABEL PLUGIN_DIR ID...  -- runs the given held-out briefs, one after another.
LABEL=$1
PLUGIN=$2
shift 2
SET=/home/user/flow/benchmarks/heldout
OUT=/tmp/claude-0/-home-user-flow/5fb04f72-c6de-5efb-87ee-7bcf899e8920/scratchpad/heldout/$LABEL
for ID in "$@"; do
  WORK=$OUT/$ID/work
  mkdir -p "$WORK"
  if [ -d "$SET/$ID/input" ]; then cp -R "$SET/$ID/input" "$WORK/input"; fi
  cd "$WORK" || exit 1
  claude -p --model sonnet --plugin-dir "$PLUGIN" \
    --permission-mode acceptEdits \
    --allowedTools "Read" "Write" "Edit" "Glob" "Grep" "Skill" "Bash(python3:*)" "Bash(node:*)" \
      "Bash(ls:*)" "Bash(find:*)" "Bash(grep:*)" "Bash(wc:*)" "Bash(head:*)" "Bash(cat:*)" "Bash(mkdir:*)" \
    --max-turns 150 --output-format stream-json --verbose \
    "$(cat "$SET/$ID/request.md")" > "$OUT/$ID/log.jsonl" 2> "$OUT/$ID/err.txt"
  echo "$LABEL $ID exit $?"
done
