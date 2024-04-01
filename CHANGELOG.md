## v1.3.1 (2024-04-01)

### Refactor

- Improve config file parsing (#124)

## v1.3.0 (2024-02-09)

### Feat

- Add --write-info-json option (#59, #8)

## v1.2.1 (2024-01-29)

### Fix

- Publish using PyPI trusted publisher

## v1.2.0 (2024-01-21)

### Feat

- Add episode.original_filename template variable (#57)

### Fix

- Restore missing first progress line (#58)

## v1.1.0 (2024-01-20)

### Feat

- Add episode.original_filename template variable (#57)

## v1.0.1 (2024-01-20)

### Fix

- Parse unknown/missing file extensions properly (#56)
- Handle download failures gracefully (#55)

## v1.0.0 (2024-01-17)

### Feat

- Completely refactor processing logic (#50)
- Integrate click for cli and config-parsing
- Allow configuration of config envvar
- Add config file support

### Fix

- Completion message shows as human-readable string (#53)
- Remnant build-backend adjusted to poetry
- Update user-agent URL

### Refactor

- Use requests lib for all requests

## v0.5.1 (2023-04-26)

### Fix

- Package entrypoint moved

## v0.5.0 (2023-04-26)

### Fix

- Propagate package version where needed

## v0.4.3 (2023-04-22)

## v0.4.2 (2023-04-22)

## v0.4.1 (2023-04-21)

### Fix

- Restore slugify functionality
- PyPI references improvements

## v0.4.0 (2023-04-21)

### Fix

- Restore argparse error handling
- Restore progress bar functionality
- Make script callable properly via main func

### Refactor

- Pay down complexity tech debt
