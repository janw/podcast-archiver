## v2.0.2 (2025-01-01)

### Fix

- Restore printing archived during progress (#227)

## v2.0.1 (2025-01-01)

### Fix

- Restore console output in non-interactive mode (#226)

## v2.0.0 (2024-12-30)

### BREAKING CHANGE

- the --update option ('update_archive' in settings) has
been removed. Feeds are now always processed in full (unless running in
continuous mode).

### Feat

- Improve progress display and episodes report (#215)
- Improve progress display and episodes report (#213)
- Remove --update option (#211)
- Allow downloading republished episodes (#208)

### Fix

- Refine pretty-printing of episode ranges (#221)

### Refactor

- Move models into package (#214)

## v1.7.2 (2024-12-03)

### Fix

- Don't add episode to DB if they failed downloading (#209, #210)

## v1.7.1 (2024-10-27)

### Fix

- Mark --update deprecated (#194)

## v1.7.0 (2024-10-27)

### Feat

- Add continuous mode with --sleep-seconds (#192)

## v1.6.2 (2024-10-20)

### Fix

- Improve failure handling and logging (#189)

## v1.6.1 (2024-10-12)

### Fix

- Fix docker minor version tagging

## v1.6.0 (2024-09-22)

### Feat

- Add support for file url scheme (#183)

## v1.5.2 (2024-09-22)

### Fix

- Ignore unused link length (#182)

## v1.5.1 (2024-09-22)

### Fix

- Demote problems to debug logging (#180)

## v1.5.0 (2024-08-17)

### Feat

- Replace rich with tqdm for progress bars (#174)

## v1.4.4 (2024-06-08)

### Fix

- Remove unnecessary parsing of feed link (#159)

## v1.4.3 (2024-06-08)

### Fix

- Maintain order of feeds as passed in (#157)

## v1.4.2 (2024-06-08)

### Fix

- Avoid parsing links unless it's the enclosure (#156)

## v1.4.1 (2024-06-08)

### Fix

- Replace slashes in slugify (#153)

## v1.4.0 (2024-04-17)

### Feat

- Add episodes database (#117) (#119)

## v1.3.3 (2024-04-07)

### Fix

- Restore docker entrypoint, update dockerfile (#127, #125)

## v1.3.2 (2024-04-07)

### Fix

- restore config envvar as PODCAST_ARCHIVER_CONFIG (#126)

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
