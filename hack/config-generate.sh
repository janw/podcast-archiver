#!/bin/sh

export CI=1

{
  poetry run podcast-archiver --config-generate
  echo
  echo '# vim:syntax=yaml'
} > config.yaml.example
