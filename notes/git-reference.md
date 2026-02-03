# Git Reference

## Check Status

```bash
git status          # Compare local files against last commit (doesn't contact GitHub)
git fetch           # Download latest info from GitHub (doesn't change your files)
git fetch && git status   # Accurate comparison against GitHub
```

## What Status Tells You

- **"up to date with origin/main"** = your branch matches GitHub
- **"ahead by X commits"** = you have unpushed commits
- **"behind by X commits"** = GitHub has commits you don't have
- **"working tree clean"** = no uncommitted changes

## View Commits

```bash
git log -1                          # Last commit
git log -1 --oneline                # Last commit (short)
git log origin/main -1              # Latest commit on GitHub
git show origin/main                # Latest GitHub commit with diff
git log origin/main..HEAD --oneline # Your unpushed commits
```

## Pull vs Fetch

| Command | Downloads info | Changes your files |
|---------|---------------|-------------------|
| `git fetch` | ✓ | ✗ |
| `git pull` | ✓ | ✓ |

`git pull` = `git fetch` + `git merge`

## Common Workflow

```bash
# Check if synced with GitHub
git fetch && git status

# Push local changes
git add <file>
git commit -m "message"
git push

# Get changes from GitHub
git pull
```
