# smartmontools, packaged for Debian (welland)

This is [mithro/apt-repo-action](https://github.com/mithro/apt-repo-action)'s
**Set A** layout (`docs/packaging.md`): a GitHub fork of
[smartmontools/smartmontools](https://github.com/smartmontools/smartmontools)
with

- `upstream`: an unmodified copy of upstream's `main`, only ever
  fast-forwarded;
- `packaging` (the default branch): `upstream` plus our changes, `debian/`,
  `packaging/` and `.github/workflows/`.

Nothing here is sent upstream without Tim's explicit approval.

## What is built

Upstream's **git `main`** (pre-8.0), not a release: it has what the release
Debian packages (7.4 in trixie, 7.5 in sid) doesn't:

- `smartd -j/--jsonstate`: a JSON state file per device after each
  successful check, with the same schema as `smartctl -j` (full ATA
  attribute table, SCSI error counters, NVMe health log). This build turns
  it on by default: `/var/lib/smartmontools/smartd-json.MODEL-SERIAL.TYPE.json`.
- NVMe attribute logs (`attrlog.*.nvme.csv`, also in 7.5).
- `-n standby` checks Linux runtime power management before opening a
  device, so a suspended disk isn't woken to ask whether it is asleep.

sensors2mqtt reads the JSON state files; smartd stays the only thing that
sends SMART commands to the disks.

## Where `debian/` comes from

Debian's packaging, from
[salsa.debian.org/debian/smartmontools](https://salsa.debian.org/debian/smartmontools)
at `c0b590e` (7.5-2), imported unchanged with its changelog history, then
adapted in separate commits:

- the quilt patches follow upstream's git layout (`src/`, `lib/`,
  `include/`); `52_remove-pragma.diff` and `automake.patch` are dropped
  (upstream no longer needs them);
- `--with-jsonstate=yes`, `--without-devel`, `--with-build-info`;
- `include/smartmon/version.sh` is generated before `dh_auto_build`
  (see `debian/rules`);
- our `Maintainer:` and `Vcs-*`; Debian's maintainer is kept as
  `XSBC-Original-Maintainer:`. Package names are Debian's, so this replaces
  Debian's `smartmontools` on upgrade.

## Our changes to upstream's code

Each is a commit on `packaging` with an `Upstream:` trailer saying where it
stands upstream. See `git log upstream..packaging -- ':!debian' ':!packaging' ':!.github'`.

## Version

`packaging/deb-version.py` (the shared script doesn't do Set A yet):

    <release>+git<N>.g<sha7>-0+welland<M>[~deb<R>][~pr<P>]

`<release>` is upstream's last release on `main` (its "Release X.Y
RELEASE_X_Y" commit: the svn-imported `RELEASE_*` tags aren't on `main`),
`N` the upstream commits since it, `sha7` the upstream commit built, and `M`
the commits on `packaging` that aren't on `upstream`. For example
`7.5+git583.g06489e0-0+welland4~deb13`: above Debian's 7.5-2, below a
Debian 8.0-1 (which is the signal to merge upstream).

## Updating to a new upstream

`Sync upstream` (`.github/workflows/sync-upstream.yml`) runs weekly: it
fast-forwards `upstream` and opens the pull request "Merge upstream <sha>"
into `packaging`. Merge it with a merge commit, never a rebase. If a quilt
patch no longer applies, the build fails; refresh it on the pull request's
branch. By hand:

```sh
git fetch https://github.com/smartmontools/smartmontools.git main
git push origin FETCH_HEAD:refs/heads/upstream
git checkout -b sync/upstream origin/packaging
git merge --no-ff origin/upstream
```

## Install

```sh
sudo install -d -m0755 /etc/apt/keyrings
curl -fsSL https://mith.ro/smartmontools/smartmontools.gpg | sudo tee /etc/apt/keyrings/smartmontools.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/smartmontools.gpg] https://mith.ro/smartmontools/trixie/ ./" \
  | sudo tee /etc/apt/sources.list.d/smartmontools.list
sudo apt update
```

Put your suite in place of `trixie`: `trixie`, `forky`, `sid`,
`raspbian-trixie` or `raspbian-forky`.

The repository's signing key fingerprint is
`BA73 6533 F208 1C67 909B  D3CC 6B00 F679 0FF6 4E12`.
