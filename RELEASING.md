# Releasing a NAF package

Use this procedure for package fixes and releases in this workspace. The standing permissions
and merge responsibility are recorded in [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md). The successful framework
[v0.2.2 release](https://github.com/nafphp/framework/releases/tag/v0.2.2) is a reference for the
process and writing style, not a hard-coded starting version for the next release.

## 1. Inspect the current remote state

Work inside the affected package repository. Inspect existing changes before switching
branches; do not stash, reset or commit somebody else's work. Use an isolated checkout when
necessary. GitHub access is available through `gh` and the SSH agent.

```sh
git status --short --branch
git remote -v
git fetch origin --prune --tags
release_repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
gh release list --repo "$release_repo" --limit 10
gh release view --repo "$release_repo" --json tagName,name,body,isDraft,isPrerelease
git tag --sort=-version:refname
git branch -a
git log --oneline -15 origin/main
```

Confirm the repository matches the intended package. Read the latest two or three releases
when needed to establish the style. Choose the next patch for a compatible bug fix; assess
features or breaking changes separately. An RC branch uses the full version, such as
`v0.2.3-rc`, not the literal `v0.2.x-rc`. Never reuse a version that has already been released.

In the examples below, replace `vX.Y.Z` with the chosen next version and `vA.B.C` with its
actual preceding release. These are placeholders, not runnable release names.

```sh
release_tag='vX.Y.Z'
release_branch="${release_tag}-rc"
previous_tag='vA.B.C'
```

## 2. Prepare, verify and push the RC branch

### Coordinate dependent packages and the starter

For a release spanning multiple packages, determine dependency order from each published
`composer.json`. Release prerequisites first and verify each tag and source commit on
Packagist before resolving dependants. Publish `naf/app` last: unlike a library's own lock
file, the starter's `composer.lock` is copied into new projects and used by `create-project`.
A new library release alone does not update that starter lock.

Keep library `require` constraints compatible with the versions they actually need. Raise a
minimum when code depends on a newer API or bug fix; a documentation-only patch does not
require forcing every consumer to that patch. Composer ignores a dependency library's own
lock file when resolving a consuming application's dependencies.

On the starter's RC branch, exclude known-broken dependencies through suitable minimum
constraints, then run `composer update --with-all-dependencies` after the needed releases
are available. Review and commit both `composer.json` and `composer.lock`. Do not add an
explicit package `version`; Composer derives the distributed version from the release tag.

Test the starter with `composer install` and its checked-in lock, then test separately with
latest compatible and minimum supported dependencies. The starter's `composer test` and CI
exercise real HTTP requests. Test in disposable copies so alternate resolutions cannot
replace the lock intended for release. After publishing the starter, run an unversioned
`composer create-project naf/app` in a fresh directory and test it **before any update or
require command**. Confirm its lock contains the intended versions; an update during this
check would hide a stale release. Review installation instructions and remove obsolete
compatibility workarounds only after these checks pass.

### Implement the package change

Create the branch **before editing**. Use the fetched remote base so a stale local `main`
cannot accidentally become the release base:

```sh
git switch --no-track -c "$release_branch" origin/main
```

If this version's branch already exists, inspect it and resume it when it is the intended
work. Do not reset or recreate it. Implement the change and its regression test, then run
the verification described in `AGENT_WORKFLOW.md` and the package README. Check real CLI/HTTP behavior
where relevant. Inspect dependency constraints and any package-specific release requirements.

Review the documentation for every fix, even when the implementation change is small. Correct
or extend the affected pages and examples alongside the code, following the documentation
workflow in `AGENT_WORKFLOW.md`. Prepare version-dependent documentation now and publish it after the
package is available. If the existing documentation remains correct and complete, record that
finding rather than making an unnecessary edit.

Review the diff, stage only your changes, and use the existing commit subject convention:

```text
Preparations for vX.Y.Z - Explain the change - Explain another change - Updated tests
```

Include `Updated tests` only when true. Preserve the configured Git author and use the current
agent's attribution trailer when applicable; do not copy another agent's identity from history.
For Codex the trailer used in this workspace is `Co-Authored-By: Codex <noreply@openai.com>`.

```sh
git diff --cached --check
git diff --cached
# Commit the reviewed changes with the subject and attribution described above.
git push --set-upstream origin "$release_branch"
gh pr list --repo "$release_repo" --head "$release_branch" --state open
```

Report tests and the PR or the comparison URL
`https://github.com/<owner>/<repo>/compare/main...<release-branch>`.
The maintainer merges the package PR through GitHub. Preparing and pushing the branch does not publish
the package. If the current task also authorizes a release, continue after the merge has
actually occurred; otherwise hand over the branch without tagging it.

## 3. Verify the merged commit and CI

For an already prepared release, begin with fresh remote state instead of redoing the fix.
Locate the merged PR and inspect its merge commit:

```sh
git fetch origin --prune --tags
gh pr list --repo "$release_repo" --head "$release_branch" --state merged
# Set pr_number to the PR number verified in that result.
gh pr view "$pr_number" --repo "$release_repo" \
  --json state,baseRefName,headRefName,mergeCommit,mergedAt,url
release_sha=$(gh pr view "$pr_number" --repo "$release_repo" --json mergeCommit --jq '.mergeCommit.oid')
git merge-base --is-ancestor "$release_sha" origin/main
git log --oneline "${previous_tag}..${release_sha}"
git diff --stat "$previous_tag" "$release_sha"
git diff "$previous_tag" "$release_sha"
gh run list --repo "$release_repo" --commit "$release_sha" \
  --json databaseId,workflowName,status,conclusion,headSha,url
```

Confirm the PR is merged into `main` and the ancestry check exits successfully. By default,
`release_sha` is that PR's merge commit, even if `main` has advanced. If the requested release
also includes later commits, review every additional change before selecting a newer SHA;
do not publish unrelated work just because it is newer. For a squash or rebase merge, inspect
the resulting diff instead of relying on RC branch ancestry.

Require the package's relevant CI checks to succeed for the **exact commit being tagged**.
Read failure logs and resolve failures before publishing. An empty run list is not a passing
result; inspect the workflow and run the required checks on that commit if CI is not configured.
If the merged tree differs from the locally tested tree, test the selected release tree too.
Avoid rewriting a shared working copy to do so; use a temporary checkout when needed.

## 4. Write the release notes

Read the full diff since the preceding tag, including relevant changes by other contributors.
Match the previous releases with:

- Title: `vX.Y.Z — Short description of the resulting behavior`.
- English prose explaining the problem, its visible effect, and the corrected behavior.
- A concrete trigger or before/after example when it helps understand the fix.
- Relevant test coverage and any other user-visible changes in the release range.
- Migration instructions when an upgrade requires action.

Keep the notes proportional to the change. Do not paste commit logs, internal conversation
history or unverified test claims. Write the complete notes into a UTF-8 temporary Markdown
file and set `release_notes` to that file's absolute path. Set `release_title` to the reviewed
title. Use `--notes-file` so newlines and literal code survive shell quoting.

## 5. Create the tag and publish

Recheck that neither the tag nor a release of that name already exists. If they do, inspect
them: an already correct release needs no duplicate; a partial previous attempt can be resumed
only when its tag points at the intended SHA. Never move or overwrite an existing release tag.

The framework's preceding tags are lightweight tags. To reproduce that process, create the
tag reference at the exact verified commit using GitHub's API, then publish using that tag:

```sh
gh api "repos/$release_repo/git/refs" --method POST \
  -f ref="refs/tags/$release_tag" -f sha="$release_sha"
gh api "repos/$release_repo/git/ref/tags/$release_tag" --jq '.object'
```

Verify the returned object has `type: commit` and `sha` equal to `release_sha` before continuing.
If another package uses annotated tags, preserve its established tag convention instead.

```sh
gh release create "$release_tag" --repo "$release_repo" \
  --verify-tag --target main --title "$release_title" \
  --notes-file "$release_notes" --latest
```

This is the stable release path: no `--draft` or `--prerelease`. The RC **branch** name does not
make the merged release a prerelease. The recent framework releases have no uploaded assets;
GitHub provides source archives automatically. Use different flags only when the requested
release is actually a draft, prerelease or maintenance release that should not become latest.

If a command fails or its result is uncertain, read GitHub's current state before retrying.
Successful tag creation with failed release creation is a partial release, not permission to
delete and recreate the tag.

## 6. Verify publication and Composer availability

```sh
gh release view "$release_tag" --repo "$release_repo" \
  --json tagName,name,url,body,isDraft,isPrerelease,publishedAt,targetCommitish,assets
gh api "repos/$release_repo/releases/latest" --jq '{tag_name,html_url}'
git fetch origin tag "$release_tag"
git rev-parse "${release_tag}^{commit}"
```

Check the title and notes, public/stable status, latest tag where applicable, and exact commit
SHA. `targetCommitish: main` alone does not prove which commit the tag references.

Read the Composer package name from its manifest and verify Packagist's published metadata:

```sh
composer_package=$(python3 -c 'import json; print(json.load(open("composer.json"))["name"])')
python3 - "$composer_package" "$release_tag" "$release_sha" <<'PY'
import json
import sys
import urllib.request

package, tag, expected_sha = sys.argv[1:]
with urllib.request.urlopen(f"https://repo.packagist.org/p2/{package}.json", timeout=30) as response:
    versions = json.load(response)["packages"][package]
release = next((item for item in versions if item["version"].lstrip("v") == tag.lstrip("v")), None)
if release is None:
    raise SystemExit(f"Packagist has not listed {package} {tag} yet")
if release.get("source", {}).get("reference") != expected_sha:
    raise SystemExit("Packagist source reference does not match the release commit")
print(f"Verified {package} {tag} at {expected_sha}")
PY
```

Allow for propagation delay and recheck when necessary. Until the metadata matches, report
GitHub publication and pending Packagist availability separately.

For installation or bootstrap changes, also install from published packages in a fresh test
directory and run the documented path. For example, `composer create-project naf/app` creates
the starter; a library-only test can use `composer require naf/framework:<version>`. Use an
unused temporary directory or a sibling demo directory, never an existing application. Confirm
the installed version and exercise the affected behavior. Local sibling path repositories
cannot establish that users can install the published release.

## 7. Complete and publish the documentation

After Packagist lists the release, recheck the affected documentation and examples against
the published version. Refresh generated package and function references when affected, and
remove obsolete workarounds only after the updated examples pass. Run the documentation
checks described in `AGENT_WORKFLOW.md` and `README.md` in the docs repository.

The agent is authorized to complete the documentation delivery independently: commit and
push the changes, create or reuse a PR, verify its current CI, merge it into `nafphp/docs`
`main`, and verify the `NAF Docs` deployment and the changed live pages. Do not request a
separate approval or stop after pushing. The package-code merge remains the maintainer's
responsibility as described earlier.

Finish with the release link, version, tested commit, relevant checks, Packagist result and
documentation publication result. Explain the code and documentation changes and why they
were needed, or why no documentation change was necessary. Do not claim completion while
required documentation work or verification is still pending.
