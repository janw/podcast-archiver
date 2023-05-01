from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import types

if TYPE_CHECKING:
    from pydantic import BaseSettings
    from pydantic.fields import ModelField


class readable_file(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_file = Path(values)
        if not prospective_file.is_file():
            raise argparse.ArgumentTypeError(f"{prospective_file} does not exist")
        setattr(namespace, self.dest, prospective_file)


class writeable_config_file(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_file = Path(values)
        if prospective_file.suffix not in {".yml", ".yaml"}:
            raise argparse.ArgumentTypeError(f"{prospective_file} must end in '.yml' or '.yaml'")
        if not prospective_file.parent.is_dir():
            raise argparse.ArgumentTypeError(f"{prospective_file.parent} does not exist")
        if prospective_file.is_file():
            raise argparse.ArgumentTypeError(f"{prospective_file} must not exist yet")
        setattr(namespace, self.dest, prospective_file)


def _convert_field_type(field: ModelField):
    if field.type_ in {types.DirectoryPath, types.FilePath}:
        return str
    return field.type_


def get_parser(settings_class: type[BaseSettings]):
    parser = argparse.ArgumentParser(prog="podcast-archiver")
    for name, field in settings_class.__fields__.items():
        if not (flags := field.field_info.extra.get("flags")):
            continue

        added_args = {}
        if action := field.field_info.extra.get("argparse_action"):
            added_args["action"] = action
        elif field.default is False:
            added_args["action"] = "store_true"
        elif field.default is True:
            added_args["action"] = "store_false"
        else:
            added_args["type"] = _convert_field_type(field)

        if metavar := field.field_info.extra.get("argparse_metavar"):
            added_args["metavar"] = metavar

        parser.add_argument(
            *flags,
            dest=name,
            default=field.default,
            help=field.field_info.description,
            **added_args,
        )

    parser.add_argument(
        "--config",
        action=readable_file,
        help=(
            "Provide a path to a config file. Additional command line"
            " arguments will override the settings found in this file."
        ),
        metavar="CONFIG_FILE",
    )
    parser.add_argument(
        "--config-generate",
        action=writeable_config_file,
        help="Generate an example YAML config file at the given location and exit. Must end in '.yml' or '.yaml'.",
        metavar="CONFIG_FILE",
    )
    parser.add_argument("-V", "--version", action="store_true", help="Print version and exit.")

    return parser
