# JupyterLite site in the lonboard docs

**Date:** 2026-10-01
**Branch:** `kyle/jupyterlite`
**Issue:** #1319
**Status:** Approved

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

Agreed in conversation on 2026-09-30 and 2026-10-01:

- **Alongside, not embedded.** The docs link to a JupyterLite site. No notebook
  is embedded in a docs page.
- **Deployed once**, at `https://developmentseed.org/lonboard/jupyterlite/`, as a
  `jupyterlite/` folder at the root of the `gh-pages` branch, not inside each
  docs version.
- **Latest lonboard only.** The notebook runs `%pip install lonboard` with no
  pin, so it always gets the newest release from PyPI.
- **Deployed with the docs** on stable release tags, plus a manual trigger.
- **Ships with 0.17.0.** The release moves from 2026-10-01 to 2026-10-02.
- **Bundle the anywidget wheel** that matches the anywidget frontend the site
  bundles, so the two halves always match (see Build). ipywidgets comes from
  PyPI.
- **Serve the notebook read-only.**
  - Visitors can still edit and run it, but their edits aren't saved over the
    deployed copy, so every visit starts from the latest deploy.
  - File > Save As keeps a visitor's own version.
  - A writable notebook would keep edits across reloads, but the visitor's
    saved copy would then hide every later deploy for them.
- **Dependabot ignores minor and major updates** of
  `jupyterlite-pyodide-kernel`, which can move the site to a new Pyodide ABI.
- **Rehearse both workflows before tagging,** using a `dry_run` input on the new
  one. Otherwise their first real run is the tag push.

## What we know

Checked on 2026-10-01 with throwaway builds, Chrome, a Node replay of the
Pyodide kernel, the GitHub API and mike's source. "Tested" means it was run.
"From source" means it was read in the code but not reproduced.

- **mike leaves the folder alone** (from source, mike 2.2.0). Each deploy builds
  its commit on the current `gh-pages` tip and deletes only its own version
  folder(s). It then rewrites `versions.json` and `.nojekyll`, and pushes
  without force.
- **The design works** (tested). A prototype of this build was served under
  `/lonboard/jupyterlite/`. It used jupyterlite-core 0.8.5 and
  jupyterlite-pyodide-kernel 0.8.6, which gives Pyodide 314.0.6 and Python 3.14,
  bundled anywidget 0.11.0, and served the notebook read-only. It also bundled
  ipywidgets 8.1.9; the design takes ipywidgets from PyPI instead, as the earlier
  spike build did, and it rendered too. Results:
  - It rendered the map with lonboard 0.17.0b1.
  - anywidget loaded only from the site's own index.
  - A notebook cell edited in the read-only build ran with the edit.
  - The notebook showed a read-only badge, Save was disabled, and nothing was
    autosaved after 130 s. Save As made a writable copy.
- **Where everything comes from at runtime** (tested):
  - jsDelivr serves Pyodide and its builds of numpy, pandas, pyarrow, pyproj,
    shapely, geopandas and fiona, plus parquet-wasm and the data.
  - PyPI serves lonboard and the `cp314-pyemscripten_2026_0` wheels of arro3
    and geoarrow-rust-core.
  - CARTO serves the basemap.
  - A first visit downloads about 65 MB. The map appears about 8 s after Run
    All, on a fast machine and connection.
- **Before 0.17.0 is on PyPI the notebook fails** (tested). `%pip install
  lonboard` resolves 0.16.0, which pins `anywidget~=0.9.0`. The site serves
  anywidget 0.11.0, so the first cell fails with "Can't find a pure Python 3
  wheel for 'anywidget~=0.9.0'". Without bundling, 0.16.0 would install and
  then fail at `viz()` with "can't start new thread", which #1204 fixed.
- **Saved copies hide redeploys** (tested). JupyterLite autosaves a run,
  writable notebook after 120 s. From then on that visitor sees their browser
  copy, not the deployed file.
- **anywidget's frontend has to match** (from source). anywidget's Python side
  asks for frontend `~{major}.{minor}.*`, and #1282 dropped lonboard's anywidget
  cap. Without bundling, a new anywidget minor release would stop the map from
  rendering until `uv.lock` is bumped and the site redeployed. No anywidget 0.12
  exists to test this with.
- **A bundled wheel is the only source for its package** (tested). `%pip` never
  falls back to PyPI for a name the site's index has.
- **Storage is named by site path** (tested), as
  `JupyterLite Storage - /lonboard/jupyterlite/`. Other sites on
  developmentseed.org don't share it.
- **Kernel selection** (tested). A `python3` kernelspec, which is what
  `normalize-notebook` writes, still starts the Pyodide kernel, through
  JupyterLab's fallback on `language_info.name`. Without `language_info`, every
  visitor gets a "Select Kernel" dialog.
- **CI's uv is new enough** (tested). CI pins `setup-uv` to `0.4.x`, which is uv
  0.4.30. It supports `uv run --locked --only-group`, and that installs only
  the group. This matters because the build bundles every JupyterLab extension
  in its environment, so the dev group has to stay out.
- **Size** (tested). With `no_sourcemaps` the site is about 22 MB in about 550
  files; with source maps it is 72 MB. Each deploy replaces the folder, so the
  published site doesn't grow per release. Branch history grows by about
  6.5 MB, compressed, per deploy that changes the assets.
- **Publish step** (tested locally). A simulation against a partial-clone remote
  confirmed:
  - Other folders are untouched, and deleted files are removed.
  - A first deploy works, and an unchanged rebuild is a no-op.
  - A non-fast-forward push is rejected cleanly.

  actionlint passes drafts of all three workflow changes.
- **Release timing** (observed on past releases). PyPI has the wheel about 1 min
  after the tag push, and the docs push lands about 1 min after it. The two
  workflows are independent, so that order is usual, not guaranteed.

## Design

### Files

- **New:**
  - `jupyterlite/jupyter_lite_config.json`
  - `jupyterlite/content/getting-started.ipynb`. Force-add it: `.gitignore`
    has `*.ipynb`.
  - `scripts/build_jupyterlite.py`
  - `.github/workflows/deploy-jupyterlite.yml`
- **Changed:** `.github/workflows/deploy-mkdocs.yml`,
  `.github/workflows/test.yml`, `.github/dependabot.yml`, `pyproject.toml`,
  `uv.lock`, `.pre-commit-config.yaml`, `.gitignore`, `docs/ecosystem/pyodide.md`,
  `examples/index.md` (served as `docs/examples/index.md`, which is a symlink),
  `README.md` and `DEVELOP.md`.
- **Replaced:** `assets/lonboard-jupyterlite.png` (2.1 MB, used only by the
  Pyodide page) becomes a compressed JPEG of the new notebook, used by both the
  Pyodide page and the examples card. Every docs version gets its own copy of
  `assets/`, so it should be small.

### The notebook

Copied from developmentseed/jupyterlite's `lonboard-0.17.ipynb`, with these
changes:

- **Install line:** `%pip install lonboard geopandas requests pyarrow`, with no
  pin. pyarrow is listed because only lonboard imports it, so the kernel can't
  detect that it's needed.
- **Data:** loaded from a geodatasets tag (`@2026.5.1`, which jsDelivr caches
  as immutable) instead of `@main`.
- **Reprojection:** `.to_crs(4326)` before `viz`, so there's no reprojection
  warning.
- **Cleanup:** a short intro, and outputs cleared.
- **Metadata:** kernelspec `python` / "Python (Pyodide)", and
  `language_info.name` `python`.

Two lint changes go with it:

- **Ruff:** add `"jupyterlite/*" = ["S108", "S113"]` to the ruff
  per-file-ignores. Extracting to `/tmp` is deliberate: the working directory,
  `/drive`, syncs into the visitor's browser storage. And leaving out a request
  timeout keeps the demo short.
- **Pre-commit:** the `normalize-notebook` hook gets `exclude: ^jupyterlite/`.
  CI runs pre-commit on all files, and the hook would rewrite the kernelspec.
  The build script takes over its checks for these notebooks.

### Build

`uv run --locked --only-group jupyterlite python scripts/build_jupyterlite.py
[--output-dir DIR]` runs these steps. The default output is
`jupyterlite/_output`.

1. **Checks each notebook** in `jupyterlite/content/`: no outputs, the Pyodide
   kernelspec, and `language_info.name == "python"`.
2. **Deletes the build cache** (`jupyterlite/.jupyterlite.doit.db`) and the
   output directory, so every build is a full build (about 5 s). It deletes the
   output directory only if it holds an earlier JupyterLite build. Without this,
   JupyterLite's cache can keep a stale `"writable": true` or stale wheels.
3. **Makes read-only copies** of `content/` in a temporary directory and builds
   from those. jupyter-server then lists the notebooks as `"writable": false`,
   and the source files are never touched.
4. **Bundles the matching anywidget wheel.** It looks up the `py3-none-any`
   wheel of the anywidget version installed in the build environment, using
   PyPI's JSON API with only the standard library. It passes the URL as
   `--piplite-wheels`.
5. **Runs `jupyter lite build`** with `jupyterlite/` as the working directory.
6. **Fails unless the output is right:** each notebook is in `<output>/files/`
   with `"writable": false` in `api/contents/all.json`, and `pypi/all.json` lists
   only anywidget.

**Why bundle anywidget.** anywidget's Python side only works with a frontend of
the same minor version. The frontend is bundled at build time, while `%pip`
would install the newest anywidget from PyPI at runtime. Serving the matching
wheel keeps the two halves at the same version. `uv.lock` has one anywidget for
the whole project, so a tag's bundle always satisfies that release.

The trade-offs:

- The site can't install older lonboard releases.
- A beta that raises the anywidget floor needs a deploy from `main` before
  `--pre` works there.
- ipywidgets comes from PyPI: the bundled widgets frontend (jupyterlab_widgets 3)
  works with every ipywidgets 8.x.

**Why read-only.** Otherwise a visitor's autosaved copy hides every later
deploy. Visitors can still edit and run the notebook, and File > Save As keeps
a copy.

**Lock file.** Regenerate `uv.lock` with a current uv. uv 0.4.30 would rewrite it
in an older format.

- **The PR check builds with `--locked`,** so a stale lock fails the PR instead
  of building from versions nobody reviewed.
- **The deploy builds with `--frozen`.** `uv.lock` also records lonboard's own
  version, and a release that bumps it without re-locking mustn't block the
  tag's deploy. Bump versions with `uv version <version>`, which updates both
  files.

### Deploy

**New `.github/workflows/deploy-jupyterlite.yml`.** It's a separate workflow so
that the site can be redeployed without redeploying the docs.

- **Triggers:** `workflow_call`, from deploy-mkdocs, and `workflow_dispatch`
  with a boolean `dry_run` input. Called runs always publish.
- **Permissions and guard:** `permissions: contents: read`. The job only runs
  from `refs/heads/main` or a `refs/tags/v*` tag, so a manual run from a feature
  branch can't publish that branch's notebook by accident. Such a run is
  skipped.
- **Steps, in order:**
  1. Check out the triggering ref: the release tag when called on a release,
     or the chosen branch or tag when run by hand.
  2. Run `setup-uv` with `0.4.x`.
  3. Build into `$RUNNER_TEMP`.
  4. Mint the app token with `actions/create-github-app-token`, from
     `DS_RELEASE_BOT_ID` and `DS_RELEASE_BOT_PRIVATE_KEY` (org secrets, passed
     by `secrets: inherit`) and with `permission-contents: write`.
  5. Check out `refs/heads/gh-pages` into `gh-pages/`, with
     `sparse-checkout: jupyterlite` and the app token. The branch is about
     945 MB.
  6. Run `rm -rf jupyterlite`, `cp -R` the build in its place, and
     `git add -A`. Don't use rsync: its size+mtime check can skip changed files.
  7. If nothing changed, stop.
  8. Commit as `CI <ci-bot@example.com>`, the docs job's identity, setting both
     `GIT_AUTHOR_*` and `GIT_COMMITTER_*`. The message is "Deployed <sha> to
     jupyterlite".
  9. Run `git push` without `--force`, or `git push --dry-run` when `dry_run`
     is set.
- **Why the app token:** it's what the docs job uses (#1161). It is minted
  after the build, so the third-party build code only ever runs with the
  read-only `GITHUB_TOKEN`.

**Changes to `.github/workflows/deploy-mkdocs.yml`:**

- **Expose whether it deployed.** Add `id: deploy` to the "Deploy docs" step.
  Inside the existing stable-tag `if`, after `mike deploy`, add
  `echo "deployed=true" >> "$GITHUB_OUTPUT"`. Add
  `outputs: deployed: ${{ steps.deploy.outputs.deployed }}` to the `build` job.
- **Add a `jupyterlite` job:** `needs: build`,
  `if: needs.build.outputs.deployed == 'true'`,
  `uses: ./.github/workflows/deploy-jupyterlite.yml`, `secrets: inherit` and
  `permissions: contents: read`.
- **Effects:**
  - Beta tags skip the site.
  - A manual docs run that resolves to a stable tag republishes both the docs
    and the site, from the ref it was started on.

**No concurrency group.** `needs:` orders a release's two pushes. Any other
writer can only make a non-forced push fail, and re-running fixes it: a manual
run, a second tag, or a hand edit of `gh-pages`. A shared group on the calling
job would deadlock.

### PR check

A new `jupyterlite` job in `test.yml`: checkout, `setup-uv` `0.4.x`, then the
build script into `$RUNNER_TEMP`. It needs no Node, because the JupyterLite app
ships prebuilt in the jupyterlite-core wheel. The job runs the script's checks
on every PR, Dependabot bumps included.

### Dependency updates

- **The `jupyterlite` group:** `jupyterlite-core[contents]>=0.8.5`,
  `jupyterlite-pyodide-kernel>=0.8.6,<0.9`, `anywidget` and `ipywidgets`.
  - anywidget and ipywidgets are there for their frontends, which the build
    bundles.
  - The `[contents]` extra brings jupyter-server, which the build needs for
    notebooks.
  - The lower bounds matter: 0.7.x kernels can't install lonboard.
- **Kernel upgrades are manual.** The kernel package picks the Pyodide version.
  A minor bump can move to a new Pyodide ABI, and `%pip install lonboard` then
  fails until arro3 and geoarrow-rust-core publish wasm wheels for it. Dependabot
  raises caps inside its grouped PR (as in #1261), so `.github/dependabot.yml`
  also ignores minor and major updates of `jupyterlite-pyodide-kernel`. Such
  upgrades are done by hand and checked in a browser. Patch updates stay on the
  same ABI and still flow.

### Docs

- **`docs/ecosystem/pyodide.md`:** rewritten.
  - A "Try it in your browser" button linking to
    `https://developmentseed.org/lonboard/jupyterlite/lab/index.html?path=getting-started.ipynb`,
    the new screenshot, and the notebook's code.
  - What to expect:
    - The first run downloads about 65 MB and takes tens of seconds.
    - The notebook is read-only. Edits are lost on reload, and the browser
      warns before you leave. To keep them, use File > Save As, then choose
      Discard when asked about `getting-started.ipynb`.
  - Use `%pip install --pre lonboard` to try a beta.
  - Don't use `-U` or `--upgrade`: piplite silently skips the whole line.
  - Keep the note about memory limits, and remove the advice to load arro3
    wheels by hand.
- **`examples/index.md`:** a "Lonboard in your browser" card with the same
  image, linking to `../ecosystem/pyodide/`.
- **`README.md`:** a plain Markdown link. The README is also the docs home page
  and the PyPI description, so it can't use mkdocs-only syntax. The link goes
  live on GitHub at merge, before the site exists, so merge close to tagging.
- **Links:** all use the absolute `https://` URL. The Pages site doesn't
  enforce HTTPS, and service workers need it.

### Developer notes

Add a short "JupyterLite site" section to `DEVELOP.md`:

- **Build and preview:**
  `uv run --locked --only-group jupyterlite python scripts/build_jupyterlite.py --output-dir /tmp/lite/lonboard/jupyterlite`,
  then `python -m http.server -d /tmp/lite 8000`, then open
  `http://127.0.0.1:8000/lonboard/jupyterlite/lab/index.html?path=getting-started.ipynb`.
- **Expected warnings:** the build always prints two, about translations and
  libarchive-c.
- **Constraints:**
  - lonboard's lower bounds must stay at or below Pyodide's versions (for
    example traitlets 5.14.3, numpy 2.4.6, pyproj 3.7.2).
  - A new required dependency must be pure Python, in Pyodide's lock, or
    published as a `pyemscripten` wheel.
  - Kernel minor upgrades are manual.

### Release-notes edits

Outside this PR: the 0.17 `CHANGELOG.md` section and the blog post exist only
in the maintainer's checkout.

- **`CHANGELOG.md`:** date to 2026-10-02, and add this PR.
- **The blog post:** it says it was written entirely by a human, so the
  maintainer makes these edits: the date, and optionally a link to the site in
  the "Emscripten support" section.

## Testing

- **CI:** the PR check, plus ruff and pre-commit on the notebook.
- **Before merging:**
  1. Run actionlint on the three workflow files.
  2. Build locally, serve the output, and run the notebook with lonboard built
     from `main`. If 0.17.0b2 has been cut, use `%pip install --pre lonboard`.
     Otherwise run `pnpm run build && uv build --wheel`, serve the wheel, and use
     `%pip install <wheel URL> geopandas requests pyarrow`.
  3. Check that the map renders.
  4. Check that anywidget comes from the site's `/lonboard/jupyterlite/pypi/`.
     Use `importlib.metadata.distribution("anywidget").read_text("PYODIDE_URL")`
     or the Network panel; `micropip.list()` says "pypi" either way.
  5. Check that the notebook is read-only.
- **After merging, before tagging:**
  1. Run deploy-mkdocs from `main`. The newest tag is a beta, so nothing
     deploys, but GitHub has to accept both workflow files and the call between
     them.
  2. Run deploy-jupyterlite from `main` with `dry_run`. That exercises the
     build, the token, the sparse checkout, the commit and a
     `git push --dry-run`.
- **After the release:** in a fresh private window, open the docs link, run the
  notebook unchanged, and check that `import lonboard; lonboard.__version__`
  returns `0.17.0`.

## Release sequence

1. **Merge the release-notes changes and this PR.** Tag-triggered runs read the
   workflow files from the tagged commit.
2. **Rehearse** the two workflows (see Testing). Don't publish the site for real
   before 0.17.0 is on PyPI: the notebook would fail at install.
3. **Tag `v0.17.0`.** The PyPI upload and the docs deploy start in parallel. The
   site's job then runs inside the "Publish docs via GitHub Pages" run, after
   the docs job. Each push starts a Pages build of about 2-4 min.
4. **Check the live site** (see Testing). If the first cell fails with the
   `anywidget~=0.9.0` error, either the browser cached PyPI's old index (for up
   to 10 min) or the PyPI upload failed. Once PyPI has 0.17.0 the site works,
   with no redeploy.
5. **Recover from failures:**
   - A transient failure: use "Re-run failed jobs".
   - A failure that needs a fix: fix it on `main`, then run deploy-jupyterlite
     from `main`.
   - The docs job failed, so the site job was skipped: fix it, then run
     deploy-mkdocs from `main`. After the tag, `git describe` resolves to
     v0.17.0, so that run publishes both.
   - GitHub rejected the run at startup because of a broken workflow file, so
     neither was published: same as the previous case.

**Fallback:** if this PR isn't ready when 0.17.0 is due, tag anyway. Then merge
it and run deploy-mkdocs from `main`. That redeploys the v0.17 docs and the site,
which is fine as long as nothing else has merged since the tag.

**Rollback:**

- **Revert a deploy:** in a sparse clone of `gh-pages`, revert the deploy
  commit and push without force.
- **Take the site down:** `git rm -r jupyterlite` on `gh-pages`.
- **Fix forward:** fix it on `main` and run deploy-jupyterlite from `main`.

## Risks

- **Runtime services:** jsDelivr, PyPI and CARTO. The kernel also installs
  `comm` from PyPI at startup. An outage of any of them breaks the demo.
- **Compiled wasm wheels:** arro3's and geoarrow-rust-core's are built for one
  Pyodide ABI, and neither project tests them at runtime.
  - geoarrow-rust-core has wasm wheels only for 0.6.3.
  - arro3-io 0.8.3 was yanked without one, so visitors get 0.8.2.
- **The PyPI upload:** if it fails on release day, the site fails at install
  until it's fixed, because the two workflows don't depend on each other.
- **ipywidgets 9:** it would need the same treatment as anywidget. Until the
  site is rebuilt with a matching widgets frontend, maps wouldn't render.
- **Service workers:** JupyterLite unregisters every service worker on the
  origin on a browser's first visit and on each JupyterLite version change. No
  other developmentseed.org page registers one today.
- **Moving the site** to another path would orphan visitors' Save As copies,
  because storage is named by path.
- **Rewriting `gh-pages`:** a rewrite like the one on 2026-09-30 would delete
  `jupyterlite/` unless it is kept explicitly.

## Follow-ups

Each one has an issue:

- **A Pyodide smoke test in CI** (#1321), for example a Node replay of the
  kernel bootstrap, about 20 s. It should resolve through the built site's
  `pypi/all.json` first, as the site does.
- **developmentseed/jupyterlite** (#1322):
  - Add `content/lonboard/data-filter-extension.ipynb` that links to the new
    site. That repairs the link in every old docs version without touching
    `gh-pages`.
  - Point its README links at the new site.
- **gh-pages size** (#1323). It will be about 1.11 GB once v0.17 and the site
  deploy, over GitHub's documented 1 GB limit. That limit hasn't been enforced
  so far. Prune old minors with `mike delete --push`, which keeps
  `jupyterlite/`.
- **HTTPS** (#1324). Enforce HTTPS for the Pages site (an admin setting).
- **Commit identity** (#1325). Commits by `ci-bot@example.com` show on GitHub as
  an unrelated user, so switch both deploys to the app's bot identity. In the
  same change, move off `create-github-app-token`'s deprecated `app-id` to
  `client-id`.
