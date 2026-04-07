# Release Process

`trajrl` is published to [PyPI](https://pypi.org/project/trajrl/) automatically by GitHub Actions ([.github/workflows/publish.yml](.github/workflows/publish.yml)) whenever a `v*` tag is pushed.

## Cutting a release

1. Bump the version in [pyproject.toml](pyproject.toml) (follow [SemVer](https://semver.org/)) and commit:
   ```
   git commit -am "release: vX.Y.Z"
   git push
   ```
2. Tag and push:
   ```
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
3. Watch the run:
   ```
   gh run watch --repo trajectoryRL/trajrl
   ```

The workflow will:
- Build sdist + wheel with `python -m build`
- Publish to PyPI via [trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC, no tokens)
- Create a GitHub Release with auto-generated notes and the built artifacts attached

## Release notes

GitHub auto-generates release notes from PRs merged since the previous tag, grouped by label per [.github/release.yml](.github/release.yml):

| Label                   | Section            |
|-------------------------|--------------------|
| `breaking`              | Breaking Changes   |
| `feature`, `enhancement`| New Features       |
| `bug`, `fix`            | Bug Fixes          |
| `documentation`, `docs` | Documentation      |
| `ci`, `build`           | CI / Build         |
| (anything else)         | Other Changes      |
| `ignore-for-release`    | Excluded           |

Apply labels on the PR before merging to get clean grouping.

## Trusted publishing setup (one-time, already configured)

- PyPI project: https://pypi.org/project/trajrl/
- Trusted publisher: `trajectoryRL/trajrl`, workflow `publish.yml`, environment `pypi`
- GitHub environment: `pypi` (no protection rules)

If trusted publishing breaks, the fallback is `PYPI_API_TOKEN` as a repo secret — but trusted publishing is preferred.

## Backfilling a release

If a tag was pushed before the release workflow existed (or the publish step succeeded but the release-creation step didn't run), create the release manually:

```
gh release create vX.Y.Z --repo trajectoryRL/trajrl --title vX.Y.Z --generate-notes
```
