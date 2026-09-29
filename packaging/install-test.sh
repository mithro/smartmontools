#!/bin/sh
# Smoke test run by mithro/apt-repo-action's install test, as root in a
# clean container of the suite, after the built packages are installed.
set -eu

smartctl --version
smartd --version

# smartd was configured --with-jsonstate=yes: it writes JSON state files
# by default, and says where.
smartd --help > /tmp/smartd-help.txt 2>&1 || true
if ! grep -q 'smartd-json\.' /tmp/smartd-help.txt; then
  echo "smartd has no default JSON state file prefix:" >&2
  cat /tmp/smartd-help.txt >&2
  exit 1
fi

# The Debian packaging's systemd unit and defaults are in place.
test -f /usr/lib/systemd/system/smartmontools.service
test -f /etc/default/smartmontools
test -d /var/lib/smartmontools

echo "install test passed"
