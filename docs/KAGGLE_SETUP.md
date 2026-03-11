# Kaggle Setup

This is the public setup path for anyone who wants to run WarpLab through Kaggle.

## What You Need

- a Kaggle account
- a Kaggle API token from `https://www.kaggle.com/settings`
- this repo checked out locally
- `uv` installed

## Recommended Auth Method

WarpLab supports Kaggle's modern token-based auth.

Generate a token at:

- `https://www.kaggle.com/settings`

Then choose one of these options.

## Option 1: `.env` In The Repo Root

Copy the example file:

```bash
cp .env.example .env
```

Then edit `.env` and set:

```bash
KAGGLE_API_TOKEN=your-kaggle-api-token
```

This is the easiest path when using WarpLab's Kaggle helpers locally.

## Option 2: Kaggle Access Token File

Create:

- `~/.kaggle/access_token`

and put the token string in that file.

## Option 3: Legacy Kaggle Credentials

WarpLab also supports the legacy Kaggle CLI flow:

- `KAGGLE_USERNAME`
- `KAGGLE_KEY`

or:

- `~/.kaggle/kaggle.json`

Use this only if you already rely on the legacy setup.

## Verify Auth

Run:

```bash
uv run warplab kaggle-doctor
```

Expected result:

- `authenticated: true`
- resolved `username`

## Build A Kaggle Runtime Validation Notebook

```bash
uv run warplab kaggle-package --output-dir build/kaggle-validation
```

The command prints:

- `package_dir`
- `kernel_ref`
- `slug`

## Build A Kaggle Project Notebook

For the verified `saxpy` sample:

```bash
uv run warplab kaggle-project-package \
  --project projects/saxpy \
  --output-dir build/kaggle-saxpy \
  --slug warplab-saxpy-kaggle-run \
  --candidate-count 2 \
  --no-profile
```

Use the smaller smoke-test settings first. Increase the candidate count and re-enable profiling once the basic run is stable in your Kaggle account/runtime.

## Push The Notebook

```bash
set -a && . ./.env && set +a && UV_CACHE_DIR=/tmp/uv-cache uv run kaggle kernels push -p build/kaggle-saxpy
```

If you use `~/.kaggle/access_token` or `~/.kaggle/kaggle.json`, you do not need the `set -a && . ./.env ...` wrapper.

## Check Status

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run kaggle kernels status <your-kaggle-username>/<your-kernel-slug>
```

## Download Output

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run kaggle kernels output <your-kaggle-username>/<your-kernel-slug> -p build/kaggle-output
```

## Notes

- `warplab kaggle-package` and `warplab kaggle-project-package` can resolve the Kaggle username automatically from a valid token.
- `warplab kaggle-doctor` is the first command to run when auth is unclear.
- The public `saxpy` walkthrough lives in `docs/KAGGLE_SAXPY_WALKTHROUGH.md`.
