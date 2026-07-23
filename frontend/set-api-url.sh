#!/usr/bin/env bash
# ---------------------------------------------------------------
#  Netlify build step.
#  Writes the Cloud Run address from the API_BASE environment
#  variable into assets/js/config.js, so the deployed site talks
#  to your backend without the URL being committed to git.
#
#  Set it in Netlify:
#    Site configuration -> Environment variables -> API_BASE
# ---------------------------------------------------------------
set -e

TARGET="assets/js/config.js"

if [ ! -f "$TARGET" ]; then
  echo "ERROR: $TARGET not found. Is the Netlify base directory set to 'frontend'?"
  exit 1
fi

if [ -n "$API_BASE" ]; then
  CLEAN="${API_BASE%/}"                       # drop any trailing slash
  sed -i.bak "s|^const PRODUCTION_API = .*|const PRODUCTION_API = \"$CLEAN\";|" "$TARGET"
  rm -f "$TARGET.bak"
  echo "config.js now points at: $CLEAN"
else
  echo "WARNING: API_BASE is not set in Netlify."
  echo "         The site will use whatever is committed in config.js:"
  grep "^const PRODUCTION_API" "$TARGET" || true
  echo "         Set it under Site configuration -> Environment variables."
fi

echo "Build step finished."
