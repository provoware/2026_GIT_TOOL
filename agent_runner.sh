#!/bin/bash

AGENTS_FILE="AGENTS.md"
DONE_FILE="done.log"
PROGRESS_FILE="progress.json"

NEXT_AGENT=$(grep -n "^## AGENT_" "$AGENTS_FILE" | \
  while read -r line; do
    num=$(echo "$line" | cut -d: -f1)
    status=$(sed -n "$((num+1))p" "$AGENTS_FILE")
    if echo "$status" | grep -q "Status: open"; then
      echo "$line" | awk '{print $2}'
      exit 0
    fi
  done)

if [ -z "$NEXT_AGENT" ]; then
  echo "Alle Agenten erledigt."
  exit 0
fi

echo "Starte $NEXT_AGENT"

sed -i "/## $NEXT_AGENT/,/---/s/Status: open/Status: done/" "$AGENTS_FILE"

echo "$(date -Iseconds) $NEXT_AGENT erledigt" >> "$DONE_FILE"

TOTAL=$(grep -c "^## AGENT_" "$AGENTS_FILE")
DONE=$(grep -c "Status: done" "$AGENTS_FILE")
PERCENT=$((100 * DONE / TOTAL))

echo "{ \"total\": $TOTAL, \"done\": $DONE, \"percent\": $PERCENT }" > "$PROGRESS_FILE"

echo "$NEXT_AGENT abgeschlossen ($PERCENT%)"
