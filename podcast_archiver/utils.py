from os import path, W_OK, access
from argparse import Action, ArgumentTypeError


class writeable_dir(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not path.isdir(prospective_dir):
            raise ArgumentTypeError("%s is not a valid path" % prospective_dir)
        if access(prospective_dir, W_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise ArgumentTypeError("%s is not a writeable dir" % prospective_dir)
