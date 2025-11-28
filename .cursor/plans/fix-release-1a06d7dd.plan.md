<!-- 1a06d7dd-4a75-48f9-bfbc-3f519efb8ab4 ef2b0c02-e3f4-4ef8-a29c-dff386ef332d -->
# Fix Release Versioning

## Changes Required

### 1. Update Makefile

Modify the `release` target in [`Makefile`](Makefile) to:

- Remove automatic "v" prefix addition (lines 46-50)
- Accept version WITH "v" prefix from user
- Update help message to show example with "v" prefix: `make release version=v0.1.0`

**Current code** (adds "v" automatically):

```makefile
git tag -a "v$(version)" -m "Release v$(version)"
git push origin "v$(version)"
```

**New code** (uses version as-is):

```makefile
git tag -a "$(version)" -m "Release $(version)"
git push origin "$(version)"
```

### 2. Delete Incorrect Tag

- Delete `vv0.1.0` tag locally: `git tag -d vv0.1.0`
- Delete `vv0.1.0` tag from remote: `git push origin :refs/tags/vv0.1.0`

### 3. Create Correct Release

Run: `make release version=v0.1.0`

This will create and push the `v0.1.0` tag correctly.

### To-dos

- [ ] Update Makefile release target to not add 'v' prefix and update help
- [ ] Delete vv0.1.0 tag locally and from remote
- [ ] Create new v0.1.0 release