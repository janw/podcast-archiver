#!/bin/sh

TMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'tmpdir')

export FORCE_COLOR="1"
export COLUMNS="120"
export CREATED_FILES="created.txt"
export DELETED_FILES="deleted.txt"
export NO_CONFIRM="true"
export SKIP_GIT_CHECKS="true"
export CLEAN_IMG_PATHS='./assets/*.svg'
export CI=1
export FORCE_INTERACTIVE=1
export PODCAST_ARCHIVER_ARCHIVE_DIRECTORY="$TMPDIR"
export PODCAST_ARCHIVER_IGNORE_DATABASE=true

# shellcheck disable=SC2064
trap "rm -rf '$TMPDIR'" EXIT

exec poetry run rich-codex --terminal-width $COLUMNS --notrim
