import sys

if sys.version_info >= (3, 11):  # pragma: no-cover-lt-311
    from datetime import UTC
else:  # pragma: no-cover-gte-311
    from datetime import timezone

    UTC = timezone.utc
