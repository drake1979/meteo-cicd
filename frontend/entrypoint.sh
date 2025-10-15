#!/bin/sh

find /app -type f | xargs sed -i \
 -e 's,%REACT_APP_API_URL%,'"$REACT_APP_API_URL"',g' \
 -e 's,%REACT_APP_ODIN_URL%,'"$REACT_APP_ODIN_URL"',g'

exec "$@"