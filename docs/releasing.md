# Releasing

This project uses numeric release versions and tags without a leading `v`.
The automated release workflows build and validate artifacts from commits on
`main`; publishing is a separate, manually dispatched operation.

## Prepare a release

1. Set `VERSION` and `intervalues/__version__.py` to the same release version.
2. Move the approved changelog entries under a dated heading such as
   `## [0.4.0] - 2026-10-14`, leaving `[Unreleased]` for later changes.
3. Merge the release commit to `main` and confirm the regular CI and artifact
   validation checks pass.
4. Create and push the matching numeric tag, for example:

   ```shell
   git tag -a 0.4.0 -m "0.4.0"
   git push origin 0.4.0
   ```

The `Release build` workflow verifies that the tag matches `VERSION`, the
runtime version, and the dated changelog heading, and that the tagged commit
is reachable from `main`. It builds and validates the source distribution and
Linux wheels, then stores the artifacts. It does not publish them.
The existing GitHub-to-GitLab sync workflow also mirrors pushed tags to
GitLab.

## Publish to TestPyPI

Before the first upload, configure a TestPyPI trusted publisher with:

- GitHub owner: `debruijn`
- Repository: `intervalues`
- Workflow: `publish-release.yml`
- GitHub environment: `testpypi`

Create the `testpypi` GitHub environment, restrict deployments to `main`, and
require reviewer approval.
Do not configure or store an API token; the workflow uses OIDC.

After a matching numeric tag exists, manually run **Publish release** from
`main` with that tag, choose `testpypi`, enable **Confirm upload to TestPyPI**,
and approve the environment deployment. The workflow builds, validates, and
uploads the validated artifact set. Record the successful workflow run ID;
production promotion will download that exact artifact from the same run.

Inspect the uploaded files and metadata on TestPyPI, then install the package
in a clean environment and run a smoke test before enabling production
publishing. For example, from outside the repository checkout:

```shell
python -m venv /tmp/intervalues-testpypi
/tmp/intervalues-testpypi/bin/python -m pip install \
  --index-url https://test.pypi.org/simple \
  intervalues==0.4.0
cd /tmp
/tmp/intervalues-testpypi/bin/python -c \
  "import importlib.metadata, intervalues; assert intervalues.__version__ == importlib.metadata.version('intervalues') == '0.4.0'"
```

## Enable production publishing

Only after the TestPyPI upload and installation have been reviewed:

1. Configure PyPI's trusted publisher for owner `debruijn`, repository
   `intervalues`, workflow `publish-release.yml`, and GitHub environment
   `pypi`.
2. Create the `pypi` GitHub environment, restrict deployments to `main`, and
   require reviewer approval.
3. Set the repository variable `PRODUCTION_PUBLISHING_ENABLED` to `true`.

Without that variable, the workflow rejects production publication even if
the production destination is selected. To promote, manually run **Publish
release** for the same numeric tag, choose `pypi`, provide the successful
TestPyPI workflow run ID, enable **Confirm upload to production PyPI**, and
approve the protected environment. The production job verifies that the
source run successfully published to TestPyPI, checks the artifact manifest
against the selected tag and source commit, revalidates the artifacts, and
uploads those same files without rebuilding. Production publication is never
triggered automatically by pushing a tag.

Published versions cannot be overwritten. Check the tag, version, changelog,
trusted-publisher configuration, and selected destination carefully before
approving either upload.
