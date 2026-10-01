# JupyterLite site in the lonboard docs

**Date:** 2026-10-01
**Branch:** `kyle/jupyterlite`
**Issue:** #1319
**Status:** Draft, awaiting review

## Problem

Lonboard 0.17 runs in JupyterLite with a plain `%pip install lonboard`. Earlier
versions needed hand-built wheels (the old demo installs `lonboard==0.10.0b2`
plus arro3 and geoarrow-rust-core wheels for emscripten 3.1.58 from S3). The docs
don't show this:

- `docs/ecosystem/pyodide.md` links to
  `jupyterlite.ds.io/lab/index.html?path=lonboard%2Fdata-filter-extension.ipynb`,
  which is broken: developmentseed/jupyterlite renamed that folder to
  `lonboard_example/`.
- The same page tells readers to load arro3 wheels by hand.
- The demo lives in another repo, so it drifts: its newest notebook pins
  `lonboard==0.17.0-beta.1`.

## Decisions

Agreed in conversation on 2026-09-30 and 2026-10-01.

- **Alongside, not embedded.** The docs link to a JupyterLite site. No notebook
  is embedded in a docs page.
- **Deployed once**, at `https://developmentseed.org/lonboard/jupyterlite/`, as a
  `jupyterlite/` folder at the root of the `gh-pages` branch, not inside each
  docs version.
- **Latest lonboard only.** The notebook runs `%pip install lonboard` with no
  pin, so it always gets the newest release from PyPI.
- **Deployed with the docs** on stable release tags, plus a manual trigger.
- **Ships with 0.17.0.** The release moves from 2026-10-01 to 2026-10-02.

## Verified facts

Checked on 2026-10-01 with throwaway builds, a real browser, and the GitHub API.

- **mike leaves the folder alone.** Each `mike deploy` commit starts from the
  current `gh-pages` tip and deletes only its own version folder(s), then
  rewrites `versions.json` and `.nojekyll`. A root `jupyterlite/` folder
  survives docs releases.
- **The stack works.** The planned build (jupyterlite-core 0.8.5,
  jupyterlite-pyodide-kernel 0.8.6, Pyodide 314.0.6, Python 3.14), served under
  `/lonboard/jupyterlite/`, renders the notebook's map with lonboard 0.17.0b1.
  The relative URLs and the service worker scope both work under that subpath,
  and GitHub Pages needs no COOP/COEP headers. jupyterlite.ds.io, on Pyodide
  314.0.0, renders it too.
- **What comes from where at runtime:**
  - Pyodide, and its builds of numpy, pandas, pyarrow, pyproj, shapely,
    geopandas and fiona, come from jsDelivr.
  - lonboard comes from PyPI.
  - arro3-core, arro3-compute, arro3-io and geoarrow-rust-core come from PyPI
    as `cp314-pyemscripten_2026_0` wheels.
  - The basemap comes from CARTO.
  - geopandas reads the shapefile with fiona; pyogrio isn't available in
    Pyodide.
  - A first visit downloads about 45-65 MB. On a fast machine the map appears
    about 8 s after Run All.
- **0.16.0 doesn't work there.** Until 0.17.0 is on PyPI, `%pip install
  lonboard` installs 0.16.0, which fails at `viz()` with "can't start new
  thread" (fixed in #1204). 0.16.0 also pins `anywidget~=0.9.0`, which the
  site's anywidget 0.11 frontend can't render.
- **anywidget's two halves must match.** anywidget's Python side asks for a
  frontend `~{major}.{minor}.*`. The site bundles the frontend from its build
  environment, while `%pip` installs anywidget from PyPI. 0.17.0 drops the
  anywidget cap (#1282). So without a fix, an anywidget 0.12 release would stop
  the map from rendering until the site is rebuilt.
- **A bundled wheel beats PyPI.** When the site bundles a wheel (piplite index),
  `%pip install` takes that package only from the bundle, whatever PyPI has.
- **Saved copies hide redeploys.** JupyterLite autosaves an opened, run notebook
  into the browser after about 120 s. From then on that copy hides every later
  deploy. A notebook whose file is read-only at build time is served with
  `"writable": false`: it can't be saved in place, so visitors always see the
  deployed version, and Save As still works.
- **Storage is per path.** Browser storage is named per site path
  (`JupyterLite Storage - /lonboard/jupyterlite/`), so it doesn't collide with
  other sites on developmentseed.org.
- **Kernel selection.** A notebook with kernelspec `python3` (what
  `normalize-notebook` writes) still starts the Pyodide kernel, but only through
  JupyterLab's fallback on `language_info.name`. Without `language_info` a
  "Select Kernel" dialog appears.
- **uv 0.4.30 is enough.** CI's `setup-uv` pin `0.4.x` gives uv 0.4.30, which
  supports `uv run --only-group` (added in 0.4.27). That installs only the group:
  not lonboard, its dependencies, or the dev group. This matters because the
  build bundles every JupyterLab extension in its environment.
- **Size.** Built with `no_sourcemaps`, the site is about 21.5 MB in 550 files.
  With source maps it's 72 MB. Each deploy replaces the folder, so it doesn't
  grow per release.
- **Release timing.** On a `v*` tag, PyPI has the wheel about 1 min after the
  push. The docs deploy runs in parallel, and the JupyterLite job runs after it,
  so the site goes live after PyPI has the release.

## Design

### Repository layout

- `jupyterlite/jupyter_lite_config.json`:
  `{"LiteBuildConfig": {"contents": ["content"], "no_sourcemaps": true}}`. Leave
  `output_dir` out: a relative one resolves against the current directory, not
  this folder.
- `jupyterlite/content/getting-started.ipynb`: the notebook from
  developmentseed/jupyterlite (`content/lonboard_example/lonboard-0.17.ipynb`),
  with these changes:
  - `%pip install lonboard geopandas requests pyarrow`, with no pin.
  - Outputs cleared and imports sorted.
  - kernelspec stays `python` / "Python (Pyodide)", and `language_info.name`
    stays `python`.
  - A short Markdown intro.

  It's force-added, because `.gitignore` has `*.ipynb`.
- `scripts/build_jupyterlite.py`: the build, shared by both workflows and by
  local builds (see Build).
- `pyproject.toml`: a new `jupyterlite` dependency group,
  `jupyterlite-core[contents]>=0.8.5,<0.9`,
  `jupyterlite-pyodide-kernel>=0.8.6,<0.9`, `anywidget` and `ipywidgets`. The
  `[contents]` extra pulls in jupyter-server, which the build needs to add
  notebooks. The `<0.9` caps make a move to a new Pyodide ABI a deliberate,
  reviewed change. Regenerate `uv.lock` with the maintainer's uv, not 0.4.30:
  0.4.30 rewrites the lock in its older format.
- `pyproject.toml` ruff config: a per-file-ignores entry for `jupyterlite/`,
  like the one `examples/*` already has, for S113 (`requests` without timeout)
  and S108 (`/tmp` paths). The plan checks with `ruff check` that the glob
  matches the notebook.
- `.pre-commit-config.yaml`: `exclude: ^jupyterlite/` on `normalize-notebook`.
  CI runs pre-commit with `--all-files`, and the hook would otherwise rewrite the
  kernelspec to `python3`.
- `.gitignore`: `jupyterlite/_output` and `.jupyterlite.doit.db`.

### Build

`uv run --only-group jupyterlite python scripts/build_jupyterlite.py [--output-dir DIR]`
does the following:

1. **Bundles the matching anywidget and ipywidgets wheels.** It reads the
   anywidget and ipywidgets versions installed in the build environment, looks
   up their `py3-none-any` wheels with PyPI's JSON API
   (`https://pypi.org/pypi/<name>/<version>/json`), and passes the wheel URLs to
   the build as `--piplite-wheels`. The site then serves `%pip` the same
   versions as the frontends it bundles: anywidget's, and jupyterlab_widgets'
   for ipywidgets. Since `uv.lock` resolves one anywidget for the whole project,
   the bundled version always satisfies the lonboard release that deploys it.
2. **Makes the notebooks read-only** (`chmod a-w`) for the build and restores
   them afterwards, so that saved browser copies can't hide later deploys.
3. **Runs `jupyter lite build`** with `jupyterlite/` as the working directory,
   so `.jupyterlite.doit.db` and the default `_output/` stay in that folder. It
   first resolves `--output-dir` against the directory the script was run from.
4. **Fails if the notebook is missing** from `<output>/files/`. If the config
   isn't read, the build exits 0 without the notebook.

The site does not bundle a lonboard wheel. A bundled wheel would freeze the site
on that version.

### Deploy

**New `.github/workflows/deploy-jupyterlite.yml`**, triggered by
`workflow_call` and `workflow_dispatch`:

- **Permissions and guard.** `permissions: contents: read`. The job runs only
  when `github.ref` is `refs/heads/main` or a `refs/tags/v*` tag, so nobody can
  publish a branch's notebook.
- **Its own token.** It mints its own token with
  `actions/create-github-app-token`, from `DS_RELEASE_BOT_ID` and
  `DS_RELEASE_BOT_PRIVATE_KEY` (org secrets, passed with `secrets: inherit`). A
  token can't be handed over from the docs job, and `GITHUB_TOKEN` is read-only
  in this repo.
- **Build steps:**
  1. Check out the repo at the caller's ref (the release tag when called).
  2. Run `setup-uv` with `0.4.x`.
  3. Run the build script into `$RUNNER_TEMP/jupyterlite-site`.
- **Publish steps:**
  1. Check out `gh-pages` into `gh-pages/` with `sparse-checkout: jupyterlite`
     and the app token. The branch is about 945 MB, so a full checkout would be
     wasteful.
  2. Run `rm -rf jupyterlite`, `cp -R` the build into its place, and
     `git add -A jupyterlite`. Don't use rsync: its size+mtime check can skip
     changed files.
  3. Skip the commit if `git diff --cached --quiet` reports no changes.
  4. Commit as `CI <ci-bot@example.com>`, the docs job's identity. Set both
     `GIT_AUTHOR_*` and `GIT_COMMITTER_*`.
  5. Push without `--force`. If `gh-pages` moved in the meantime, the push is
     rejected, and re-running the job starts again from the new tip.

**Changes to `.github/workflows/deploy-mkdocs.yml`:**

- **Expose whether it deployed.** Add `id: deploy` to the "Deploy docs" step,
  and `echo "deployed=true" >> "$GITHUB_OUTPUT"` after `mike deploy`, inside the
  existing stable-tag `if`. Add `outputs: deployed:` to the `build` job.
- **Add a `jupyterlite` job:**
  ```yaml
  jupyterlite:
    needs: build
    if: needs.build.outputs.deployed == 'true'
    uses: ./.github/workflows/deploy-jupyterlite.yml
    secrets: inherit
    permissions:
      contents: read
  ```
  Beta tags don't deploy docs, so they don't deploy the site either.

**No concurrency group.** `needs:` already orders a release's two pushes. The
only other writer is a manual run, and a collision there only rejects a
non-forced push. A shared group would have to stay off the calling job, or it
deadlocks.

### PR check

A new `jupyterlite` job in `.github/workflows/test.yml`, with no matrix: checkout,
`setup-uv` `0.4.x`, then the build script into `$RUNNER_TEMP`. It needs no Node:
the JupyterLite app ships prebuilt in the jupyterlite-core wheel. Dependabot's
existing uv entry already updates the new group, and this job builds each bump.

### Docs

- **`docs/ecosystem/pyodide.md`:** rewritten.
  - A "Try it in your browser" button linking to
    `https://developmentseed.org/lonboard/jupyterlite/lab/index.html?path=getting-started.ipynb`,
    a new screenshot, and the notebook's code.
  - What to expect: the first run downloads about 50 MB, and the notebook can't
    be saved in place, so use File > Save As to keep changes.
  - Use `%pip install --pre lonboard` to try a beta, and avoid `-U`, which
    piplite silently ignores.
  - Keep the note about memory limits, and remove the advice to load arro3
    wheels by hand.
- **`docs/examples/index.md`:** a "Lonboard in your browser" card linking to that
  page.
- **`README.md`:** one "Try it in your browser" link.
- **Links:** all of them use the absolute `https://` URL. The Pages site doesn't
  enforce HTTPS, and service workers need it.

### Developer notes

Add a "JupyterLite site" section to `DEVELOP.md`:

- How to build and preview locally: run the script, then serve the output under
  `/lonboard/jupyterlite/`.
- How to test a pre-release: `%pip install --pre lonboard` in the browser.
- Three constraints:
  - lonboard's dependency lower bounds must stay at or below Pyodide's versions
    (for example traitlets 5.14.3, numpy 2.4.6, pyproj 3.7.2).
  - A jupyterlite-pyodide-kernel minor bump can mean a new Pyodide ABI.
  - A new ABI needs arro3 and geoarrow-rust-core wasm wheels before
    `%pip install lonboard` works.

### Release-notes edits

These go in the release notes, not this PR. The 0.17 `CHANGELOG.md` section and
`docs/blog/posts/lonboard-0.17.md` aren't on `main` yet.

- Change both dates to 2026-10-02.
- Link the site from the blog post's "Emscripten support" section.
- List this PR in the changelog.

## Testing

- **CI:** the PR check builds the site; ruff and pre-commit pass on the notebook.
- **Before merging, by hand:**
  1. Build with the script and serve the output under `/lonboard/jupyterlite/`.
  2. Open the notebook, change the install line to `%pip install --pre lonboard`
     (0.17.0 isn't on PyPI yet), and run all.
  3. Check that the map renders.
  4. Check that `micropip.list()` shows anywidget and ipywidgets from the
     bundled index.
  5. Check that the notebook is read-only (Save is disabled).
- **After the release:** open the live link and run the notebook unchanged. It
  should install lonboard 0.17.0 and render the map.
- **Not automated in this PR:** running the notebook in Pyodide. See follow-ups.

## Release sequence

1. Merge this PR. Tag-triggered runs read the workflow files from the tagged
   commit, so both workflow changes must be on `main` before tagging.
2. Don't run `deploy-jupyterlite` by hand before 0.17.0 is on PyPI. The site
   would install 0.16.0, which fails.
3. Tag `v0.17.0`. PyPI, then the docs, then the JupyterLite job. Each push starts
   its own Pages deployment, which takes about 2-4 min.
4. Check the live link (see Testing).
5. If the JupyterLite job fails, fix it on `main` and run `deploy-jupyterlite`
   from `main` with "Run workflow".

## Risks and known limitations

- **Runtime services.** The site depends on jsDelivr (Pyodide, its packages,
  the NYC data), PyPI (lonboard and the compiled wheels; the kernel also
  installs `comm` from PyPI at startup) and CARTO. An outage of any of them
  breaks the demo.
- **The compiled wheels are the weak link.** The arro3 and geoarrow-rust-core
  wasm wheels are built for one Pyodide ABI, and neither project tests them at
  runtime. A broken wasm release would reach every visitor.
  - geoarrow-rust-core has wasm wheels only for 0.6.3.
  - arro3-io 0.8.3 was yanked with no wasm wheel, so visitors get 0.8.2.
- **Service workers.** JupyterLite unregisters every service worker on the origin
  when its version changes, which can affect other developmentseed.org sites.
  They re-register on their next visit.
- **Moving the site** to another path would orphan visitors' saved files
  ("Save As" copies), because storage is named by path.

## Out of scope and follow-ups

- **A Pyodide smoke test in CI.** For example, replay the kernel bootstrap with
  `pyodide@314.0.6` under Node, about 20 s. It would catch upstream wheel
  breakage and too-high lower bounds between releases.
- **developmentseed/jupyterlite:** remove or redirect its lonboard notebooks and
  fix its README badge.
- **gh-pages size.** It is 945 MB, and the 0.17 docs take it to about 1.09 GB,
  over GitHub's documented 1 GB limit, which isn't enforced yet. Prune old
  minors.
- **HTTPS.** Enforce HTTPS for the Pages site (an admin setting).
- **Commit identity.** Commits by `ci-bot@example.com` show on GitHub as an
  unrelated user. Switch both deploys to the app's bot identity.
- **`app-id`** is deprecated in `create-github-app-token` in favour of
  `client-id`.
