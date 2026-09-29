#!/usr/bin/env python3
"""Set A version for mithro/smartmontools (apt-repo-action docs/packaging.md).

    <tag>+git<N>.g<sha7>-0+welland<M>[~deb<R>][~pr<P>]

- <tag>: the newest upstream release in the build's history. Upstream's git
  history came from svn, and its RELEASE_X_Y tags point at commits outside
  the main line, so the release is found by the main line's own
  "Release X.Y RELEASE_X_Y" commit instead of by `git describe`.
- N, sha7: upstream commits since that release, and the upstream commit
  built: the merge-base of HEAD and the `upstream` branch.
- M: commits on `packaging` that aren't on `upstream`.
- ~deb<R>, ~pr<P>: from $SUITE and $PR, which build-deb passes into the
  build container.

With --write-changelog, adds this build's entry on top of the committed
debian/changelog (Debian's history is kept: docs/packaging.md, "The
changelog").
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHANGELOG = REPO / "debian" / "changelog"
SOURCE = "smartmontools"
OWNER_TAG = "welland"
GITHUB_REPO = "mithro/smartmontools"
MAINTAINER = "Tim 'mithro' Ansell <me@mith.ro>"
SUITE_RELEASE = {"bookworm": 12, "trixie": 13, "forky": 14}
UPSTREAM_REFS = ("origin/upstream", "upstream")
RELEASE_SUBJECT = re.compile(r"^Release (\d+(?:\.\d+)+) RELEASE_\d+(?:_\d+)+$")


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def fail(msg: str) -> None:
    print(f"deb-version.py: {msg}", file=sys.stderr)
    sys.exit(1)


def upstream_commit() -> str:
    for ref in UPSTREAM_REFS:
        try:
            git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        except subprocess.CalledProcessError:
            continue
        return git("merge-base", "HEAD", ref)
    fail(f"none of {', '.join(UPSTREAM_REFS)} exists: fetch with full history")


def last_release(commit: str) -> tuple[str, str]:
    for line in git("log", "--format=%H %s", "--grep=^Release [0-9]", commit).splitlines():
        sha, subject = line.split(" ", 1)
        m = RELEASE_SUBJECT.match(subject)
        if m:
            return m.group(1), sha
    fail(f"no 'Release X.Y RELEASE_X_Y' commit in the history of {commit}")


def suite_suffix(suite: str) -> str:
    codename = suite.removeprefix("raspbian-")
    if codename == "sid":
        return ""
    if codename not in SUITE_RELEASE:
        fail(f"unknown suite {suite!r}")
    return f"~deb{SUITE_RELEASE[codename]}"


def version(suite: str | None, pr: str | None) -> str:
    up = upstream_commit()
    tag, release = last_release(up)
    n = git("rev-list", "--count", f"{release}..{up}")
    sha7 = git("rev-parse", "--short=7", up)
    m = git("rev-list", "--count", f"{up}..HEAD")
    v = f"{tag}+git{n}.g{sha7}-0+{OWNER_TAG}{m}"
    if suite:
        v += suite_suffix(suite)
    if pr:
        v += f"~pr{pr}"
    return v


def write_changelog(suite: str, pr: str | None) -> None:
    head = git("rev-parse", "HEAD")
    date = git("log", "-1", "--format=%cd", "--date=rfc2822", "HEAD")
    entry = (
        f"{SOURCE} ({version(suite, pr)}) {suite}; urgency=medium\n\n"
        f"  * Built from {GITHUB_REPO}@{head}\n\n"
        f" -- {MAINTAINER}  {date}\n\n"
    )
    CHANGELOG.write_text(entry + CHANGELOG.read_text())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--suite", default=os.environ.get("SUITE") or None)
    ap.add_argument("--pr", default=os.environ.get("PR") or None)
    ap.add_argument("--write-changelog", action="store_true")
    a = ap.parse_args()
    if a.write_changelog:
        if not a.suite:
            fail("--write-changelog needs --suite (or $SUITE)")
        write_changelog(a.suite, a.pr)
    else:
        print(version(a.suite, a.pr))


if __name__ == "__main__":
    main()
