#!/bin/sh
set -eu

cat > /usr/share/nginx/html/config.js <<EOF
window.__API_BASE_URL__ = "${API_BASE_URL:-}";
EOF
