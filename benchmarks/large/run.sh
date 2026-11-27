#!/bin/sh
# Usage: run.sh LABEL PLUGIN_DIR BRIEF_ID  -- one Sonnet run of the author skill on a frozen brief.
LABEL=$1
PLUGIN=$2
ID=$3
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${LARGE_OUT:-/tmp/large}/$LABEL/$ID
rm -rf "$OUT"
mkdir -p "$OUT/work"
cp "$HERE/$ID/brief.md" "$OUT/work/brief.md"
cd "$OUT/work" || exit 1
claude -p "Use the flow plugin's author skill to draw the diagram described in brief.md, for reading on a screen. Draw all of its content. Put the files in the folder diagrams/. Look at the picture and improve it before you finish." \
  --model sonnet --plugin-dir "$PLUGIN" --permission-mode acceptEdits \
  --allowedTools Read Write Edit Glob Grep Skill "Bash(python3:*)" "Bash(node:*)" "Bash(ls:*)" "Bash(mkdir:*)" "Bash(cat:*)" "Bash(head:*)" \
  --disallowedTools Agent Task --max-turns 200 --output-format stream-json --verbose \
  > "$OUT/log.jsonl" 2> "$OUT/err.txt"
echo "$LABEL $ID exit $?"
