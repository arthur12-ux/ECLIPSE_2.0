#!/bin/bash
# Double-click in Finder to open the ECLIPSE interface on the current git branch.
# Serves this folder on http://localhost:8000 and opens ScenarioIndex.html?branch=<current branch>.
# Close this Terminal window (or press Ctrl+C) to stop the server.

cd "$(dirname "$0")" || exit 1

PORT=8000
BRANCH="$(git branch --show-current 2>/dev/null)"
if [ -z "$BRANCH" ]; then
  echo "Could not detect the current git branch. Using main."
  BRANCH="main"
fi

while lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; do
  PORT=$((PORT + 1))
done

URL="http://localhost:${PORT}/ScenarioIndex.html?branch=${BRANCH}"

echo "Branch : ${BRANCH}"
echo "URL    : ${URL}"
echo
if [ "$BRANCH" = "main" ]; then
  echo "WARNING: you are on main. Uploads, CAD, graph and DES runs will be written to main."
else
  echo "Uploads, CAD, graph and DES runs will be written to the '${BRANCH}' branch on GitHub."
fi
echo "Close this window or press Ctrl+C to stop the server."
echo

(sleep 1 && open "$URL") &
exec python3 -m http.server "$PORT" --bind 127.0.0.1
