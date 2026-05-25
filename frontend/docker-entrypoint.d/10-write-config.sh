#!/bin/sh
set -eu

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

api_base_url="$(json_escape "${API_BASE_URL:-http://127.0.0.1:8000}")"

cat > /usr/share/nginx/html/config.js <<EOF
window.__PROCTORING_CONFIG__ = {
  API_BASE_URL: "$api_base_url"
};
EOF
