# Release Checklist

Use this before publishing a new public WarpLab release.

## Positioning

- confirm the release is framed as `early beta`, `open beta`, or `experimental` unless the full GPU sample flow has been revalidated
- make sure the README status section matches current reality
- make sure docs do not claim any sample-project path is stable unless it has been rerun recently

## Repo Hygiene

- review `git status`
- confirm `.env` is not tracked
- confirm `.env.example` is current
- confirm generated local artifacts under `build/`, `runs/`, `reports/`, and `db/` are not accidentally staged for release unless intentionally included

## Local Verification

- run `uv sync --dev`
- run `uv run pytest -q`
- run `uv run warplab --help`
- run `uv run warplab doctor`
- run `uv run warplab kaggle-doctor` if Kaggle support is part of the release story

## Docs Verification

- read `README.md`
- read `docs/README.md`
- read `docs/KAGGLE_SETUP.md`
- read `docs/KAGGLE_SAXPY_WALKTHROUGH.md`
- confirm commands match the current CLI
- confirm all referenced docs/files exist

## GPU Workflow Verification

- rerun the Kaggle runtime validation notebook if Kaggle is mentioned in the release notes
- rerun the smoke-test Kaggle `saxpy` package:
  - `uv run warplab kaggle-project-package --project projects/saxpy --output-dir build/kaggle-saxpy --slug warplab-saxpy-kaggle-run --candidate-count 2 --no-profile`
- confirm the downloaded Kaggle output includes:
  - runtime diagnostics JSON
  - WarpLab CLI JSON summary
  - report path or summary path
- if the smoke test fails, do not claim end-to-end sample-project stability

## Release Assets

- update `docs/OPEN_SOURCE_GAPS_AND_NEXT_STEPS.md` if the gap list changed
- update the release post draft if the release story changed
- prepare a short changelog with:
  - user-facing additions
  - fixes
  - known limitations

## Publish

- tag the release only after the verification steps above pass
- publish the repo with the release framing consistent across:
  - GitHub description
  - README
  - release notes
  - release post
