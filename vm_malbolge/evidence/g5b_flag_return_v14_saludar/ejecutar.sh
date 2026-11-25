#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root=${MALBOLGE_MB_DATABASE_ROOT:-$here/../../..}
exec "$root/../Malbolge-PureEpoch/build/olmstead" "$here/run02/saludar.mb"
