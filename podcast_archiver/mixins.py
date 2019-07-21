class InfoKeyMixin:
    INFO_KEYS = []

    def __init__(self, *args, **kwargs):
        for key, datum in kwargs.items():
            if key not in self.INFO_KEYS:
                raise ValueError(f"Got unexpected metadatum {key}")

            setattr(self, key, datum)
