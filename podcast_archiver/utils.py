import re
import unicodedata


def slugify(filename):
    filename = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore")
    filename = re.sub(r"[^\w\s\-\.]", "", filename.decode("ascii")).strip()
    filename = re.sub(r"[-\s]+", "-", filename)

    return filename
