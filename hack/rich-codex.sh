#!/bin/sh

export FORCE_COLOR="1"
export TERMINAL_WIDTH="140"
export TERMINAL_THEME=MONOKAI
export CREATED_FILES="created.txt"
export DELETED_FILES="deleted.txt"
export NO_CONFIRM="true"
export SKIP_GIT_CHECKS="true"
export CLEAN_IMG_PATHS='./assets/*.svg'
export CI=1

exec poetry run rich-codex
