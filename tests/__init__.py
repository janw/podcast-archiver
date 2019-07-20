from os import path


FIXTURES_DIR = path.join(path.dirname(path.realpath(__file__)), "fixtures", "")


def fixturefile(filename):
    return path.join(FIXTURES_DIR, filename)
