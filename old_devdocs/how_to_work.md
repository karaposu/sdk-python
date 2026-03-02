# Developer Workflow Guide

This guide explains how to work on the Bright Data Python SDK as a developer, including branching strategy, PR process, and best practices.

## Table of Contents
1. [Two Ways to Contribute](#two-ways-to-contribute)
2. [Quick Start](#quick-start)
3. [Branching Strategy](#branching-strategy)
4. [Types of Changes](#types-of-changes)
5. [Development Workflow](#development-workflow)
6. [Pull Request Process](#pull-request-process)
7. [Testing Requirements](#testing-requirements)
8. [Code Review](#code-review)
9. [Release Process](#release-process)

---

## Two Ways to Contribute

There are **two workflows** depending on your access level:

### Option 1: Direct Repository Access (Team Members)

**You have this if:** You can push branches directly to the main repository

```bash
# Push directly to the repository
git push origin fix/chatgpt-batch-timeout
```

**When to use:** You're a team member with write access to the repository

### Option 2: Fork-Based Workflow (External Contributors or Limited Access)

**You have this if:** You need to fork the repository first

```bash
# Push to your fork
git push origin fix/chatgpt-batch-timeout  # (origin = your fork)
```

**When to use:**
- You don't have write access to the main repository
- You're an external contributor
- You're a team member without push permissions (yet)

**Visual explanation:**

```
Direct Access Workflow:
┌────────────────────────────────────┐
│  brightdata/sdk-python (main repo) │
│                                    │
│  main ← fix/my-fix (you push here)│
└────────────────────────────────────┘

Fork-Based Workflow:
┌────────────────────────────────────┐
│  brightdata/sdk-python (upstream)  │
│                                    │
│  main (you CANNOT push here)       │
└──────────────┬─────────────────────┘
               │
               │ (fork)
               ↓
┌────────────────────────────────────┐
│  YOUR-USERNAME/sdk-python (origin) │
│                                    │
│  main ← fix/my-fix (you push here) │
└────────────────────────────────────┘
               │
               │ (Pull Request)
               ↓
┌────────────────────────────────────┐
│  Reviewer merges your PR into      │
│  brightdata/sdk-python main        │
└────────────────────────────────────┘
```

**Key difference:**
- **Direct access**: You push branches directly to `brightdata/sdk-python`
- **Fork-based**: You push branches to `YOUR-USERNAME/sdk-python`, then create PR

---

## Quick Start

### If You Have Direct Repository Access

```bash
# 1. Make sure you're on main and up to date
git checkout main
git pull origin main

# 2. Create a feature/fix branch
git checkout -b fix/chatgpt-batch-timeout

# 3. Make your changes
# ... edit files ...

# 4. Run tests
python -m pytest tests/
python probe_tests/test_08_chatgpt.py

# 5. Commit and push
git add .
git commit -m "fix: Increase fetch timeout for large batch responses"
git push origin fix/chatgpt-batch-timeout

# 6. Create PR on GitHub
# Go to GitHub and create a Pull Request
```

### If You're Using a Fork

```bash
# 1. Fork the repository on GitHub
# Click "Fork" button on https://github.com/brightdata/sdk-python

# 2. Clone YOUR fork
git clone https://github.com/YOUR-USERNAME/sdk-python.git
cd sdk-python

# 3. Add upstream remote (the main repository)
git remote add upstream https://github.com/brightdata/sdk-python.git

# 4. Verify remotes
git remote -v
# origin    https://github.com/YOUR-USERNAME/sdk-python.git (your fork)
# upstream  https://github.com/brightdata/sdk-python.git (main repo)

# 5. Keep your fork's main up to date
git checkout main
git fetch upstream
git merge upstream/main
git push origin main

# 6. Create a feature/fix branch
git checkout -b fix/chatgpt-batch-timeout

# 7. Make your changes
# ... edit files ...

# 8. Run tests
python -m pytest tests/
python probe_tests/test_08_chatgpt.py

# 9. Commit and push TO YOUR FORK
git add .
git commit -m "fix: Increase fetch timeout for large batch responses"
git push origin fix/chatgpt-batch-timeout

# 10. Create PR on GitHub
# Go to YOUR FORK on GitHub
# Click "Compare & pull request"
# This will create a PR from your fork to the main repository
```

---

## Branching Strategy

### Main Branch
- **`main`** - Production-ready code
  - Always deployable
  - Protected branch (requires PR + review)
  - All releases are tagged from main
  - Never commit directly to main

### Working Branches

Create a new branch for **each improvement/fix/feature**. Use this naming convention:

```
<type>/<short-description>
```

**Types:**
- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `refactor/` - Code refactoring (no behavior change)
- `test/` - Adding or updating tests
- `perf/` - Performance improvements
- `chore/` - Maintenance tasks (deps, CI, etc.)

**Examples:**
```bash
git checkout -b feat/add-serp-bing-support
git checkout -b fix/chatgpt-batch-timeout
git checkout -b docs/improve-readme-examples
git checkout -b refactor/consolidate-scrapers
git checkout -b test/add-concurrency-tests
git checkout -b perf/optimize-polling-logic
git checkout -b chore/update-dependencies
```

### Branch Naming Best Practices

✅ **Good:**
```
feat/instagram-stories-scraper
fix/amazon-price-parsing
docs/api-reference-cleanup
test/google-search-concurrency
```

❌ **Bad:**
```
my-changes
update
fix-bug
john-dev
temp
```

### Do We Need a `dev` Branch?

**No, we don't use a `dev` branch.** Here's why:

**Our workflow:**
```
main (production)
  ↑
  PR from fix/chatgpt-batch-timeout
  PR from feat/bing-search
  PR from docs/update-examples
```

**Why no dev branch:**
1. **Simplicity** - Fewer branches to manage
2. **Faster iteration** - Changes go directly to main after review
3. **CI/CD friendly** - Every PR is tested against main
4. **Clear history** - main reflects actual production state

**When you might use a dev branch:**
- If you're working on a **major version** (v2.0) that takes months
- If you need to **coordinate multiple large features** before release
- If you have a **release schedule** (e.g., monthly releases)

For this SDK, **feature branches → main** is sufficient.

---

## Types of Changes

Different types of changes have different requirements:

### 1. Bug Fixes (`fix/`)

**When:** Something is broken or not working as expected

**Process:**
1. Create issue documenting the bug (optional but recommended)
2. Create `fix/descriptive-name` branch
3. Write/update test that reproduces the bug
4. Fix the bug
5. Verify test passes
6. Create PR with "Fixes #123" in description

**Testing requirements:**
- ✅ Add test that reproduces the bug
- ✅ Verify all existing tests still pass
- ✅ Run relevant probe tests

**Example:**
```bash
git checkout -b fix/chatgpt-batch-timeout

# 1. Write test that fails
# probe_tests/async/test_17_chatgpt_batch_debug.py

# 2. Fix the bug
# Edit src/brightdata/scrapers/api_client.py

# 3. Verify test passes
python probe_tests/async/test_17_chatgpt_batch_debug.py

# 4. Commit
git commit -m "fix: Increase fetch timeout for large batch responses

- Add fetch_timeout parameter to api_client.fetch_result()
- Default timeout increased from 30s to 120s
- Fixes ChatGPT batch prompts with 3+ items
- Fixes batch prompts with web_search enabled

Fixes #45"
```

### 2. New Features (`feat/`)

**When:** Adding new functionality

**Process:**
1. Document the feature (optional: in `devdocs/features/`)
2. Create `feat/descriptive-name` branch
3. Implement feature
4. Write comprehensive tests
5. Update documentation
6. Create PR

**Testing requirements:**
- ✅ Unit tests for new code
- ✅ Integration tests (probe tests)
- ✅ Update README if user-facing
- ✅ Add examples if applicable

**Example:**
```bash
git checkout -b feat/bing-search-serp

# 1. Implement feature
# src/brightdata/services/serp/bing.py
# src/brightdata/services/serp/service.py

# 2. Write tests
# tests/unit/test_bing_search.py
# probe_tests/test_09_bing_search.py

# 3. Update docs
# README.md - add Bing example
# docs/serp.md - document Bing API

# 4. Commit
git commit -m "feat: Add Bing search support to SERP API

- Implement BingSearch class
- Add client.search.bing_async() method
- Support all Bing search parameters
- Add comprehensive tests and examples"
```

### 3. Documentation (`docs/`)

**When:** Updating documentation only (no code changes)

**Process:**
1. Create `docs/descriptive-name` branch
2. Update documentation
3. Create PR

**Testing requirements:**
- ✅ Verify examples actually work
- ✅ Check for typos and broken links
- ❌ No unit tests needed (docs only)

**Example:**
```bash
git checkout -b docs/improve-chatgpt-examples

# Edit README.md, docs/*.md

git commit -m "docs: Improve ChatGPT usage examples

- Add batch prompts example
- Add web search example
- Fix typos in API reference
- Update code snippets to latest API"
```

### 4. Refactoring (`refactor/`)

**When:** Improving code structure without changing behavior

**Process:**
1. Create `refactor/descriptive-name` branch
2. Refactor code
3. **Verify all tests still pass** (critical!)
4. Create PR

**Testing requirements:**
- ✅✅✅ All existing tests MUST pass
- ✅ No new tests needed (behavior unchanged)
- ✅ Performance tests if applicable

**Example:**
```bash
git checkout -b refactor/consolidate-scraper-base

# Refactor code
# src/brightdata/scrapers/base.py

# CRITICAL: Verify nothing broke
python -m pytest tests/
python probe_tests/test_08_chatgpt.py
python probe_tests/async/test_10_concurrency_google_search.py

git commit -m "refactor: Consolidate scraper base class methods

- Move common polling logic to base class
- Reduce code duplication across scrapers
- No behavior changes"
```

### 5. Tests (`test/`)

**When:** Adding or improving tests only

**Process:**
1. Create `test/descriptive-name` branch
2. Add/improve tests
3. Verify tests pass
4. Create PR

**Example:**
```bash
git checkout -b test/add-linkedin-concurrency-tests

# Add tests
# probe_tests/async/test_18_linkedin_concurrency.py

git commit -m "test: Add concurrency tests for LinkedIn scraper

- Test 10 concurrent profile scrapes
- Test 5 concurrent post scrapes
- Verify no connector errors"
```

### 6. Performance (`perf/`)

**When:** Improving performance

**Process:**
1. Benchmark current performance
2. Create `perf/descriptive-name` branch
3. Implement improvement
4. Benchmark new performance
5. Document improvement in commit message
6. Create PR

**Example:**
```bash
git checkout -b perf/optimize-polling-interval

git commit -m "perf: Optimize polling interval based on dataset type

- Reduce polling interval for SERP (5s instead of 10s)
- Increase polling interval for scraping (15s instead of 10s)
- Reduces API calls by ~30% for typical workloads
- Benchmarks: Amazon scraping 15% faster"
```

---

## Development Workflow

### Step-by-Step Process

#### 1. Before You Start

```bash
# Always start from latest main
git checkout main
git pull origin main

# Make sure environment is clean
python -m pytest tests/  # Should all pass
```

#### 2. Create Your Branch

```bash
# Create and switch to new branch
git checkout -b fix/chatgpt-batch-timeout

# Verify you're on the right branch
git branch
# * fix/chatgpt-batch-timeout
#   main
```

#### 3. Make Your Changes

```bash
# Edit files
# Use your IDE or text editor

# Check what you changed
git status
git diff
```

#### 4. Test Your Changes

```bash
# Run unit tests
python -m pytest tests/

# Run relevant probe tests
python probe_tests/test_08_chatgpt.py

# For concurrency changes
python probe_tests/async/test_17_chatgpt_batch_debug.py

# Lint (if you have linters set up)
black src/
flake8 src/
```

#### 5. Commit Your Changes

```bash
# Stage files
git add src/brightdata/scrapers/api_client.py
git add src/brightdata/utils/polling.py

# Or stage all changes
git add .

# Commit with descriptive message
git commit -m "fix: Increase fetch timeout for large batch responses"

# Or use multi-line commit message
git commit -m "fix: Increase fetch timeout for large batch responses

- Add fetch_timeout parameter to api_client.fetch_result()
- Default timeout increased from 30s to 120s for fetch operations
- Fixes ChatGPT batch prompts with 3+ items
- Fixes batch prompts with web_search enabled

The issue was that large JSON responses took longer than 30s to download,
causing TimeoutError during the fetch phase. Poll timeout controls how long
we wait for the job to complete, but fetch timeout controls how long we wait
to download the results.

Fixes #45"
```

#### 6. Push Your Branch

```bash
# Push to GitHub (first time)
git push -u origin fix/chatgpt-batch-timeout

# Subsequent pushes (if you make more commits)
git push
```

#### 7. Create Pull Request

Go to GitHub:
1. Navigate to `https://github.com/anthropics/sdk-python` (or your org's repo)
2. Click "Compare & pull request" button
3. Fill in PR details (see [Pull Request Process](#pull-request-process))
4. Click "Create pull request"

#### 8. Address Review Feedback

```bash
# Make requested changes
# Edit files...

# Commit changes
git add .
git commit -m "Address review feedback: add type hints"

# Push (PR updates automatically)
git push
```

#### 9. After PR is Merged

```bash
# Switch back to main
git checkout main

# Pull the merged changes
git pull origin main

# Delete your local branch (optional, keeps things clean)
git branch -d fix/chatgpt-batch-timeout

# Delete remote branch (optional, GitHub can do this automatically)
git push origin --delete fix/chatgpt-batch-timeout
```

---

## Pull Request Process

### PR Title Format

Use conventional commit format:

```
<type>: <short description>
```

**Examples:**
```
fix: Increase fetch timeout for large batch responses
feat: Add Bing search support to SERP API
docs: Improve ChatGPT usage examples
refactor: Consolidate scraper base class methods
test: Add concurrency tests for LinkedIn scraper
perf: Optimize polling interval based on dataset type
```

### PR Description Template

```markdown
## What
Brief description of what this PR does

## Why
Why is this change needed? What problem does it solve?

## How
How does this PR solve the problem?

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests (probe tests) run successfully
- [ ] Manual testing performed
- [ ] No regressions in existing functionality

## Related Issues
Fixes #45
Related to #67

## Screenshots (if applicable)
[Before/after screenshots for UI changes]

## Checklist
- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated (if needed)
- [ ] No breaking changes (or documented in PR)
```

### Example PR Description

```markdown
## What
Fixes ChatGPT batch prompts timeout issue for large batches (3+ prompts) and web search batches.

## Why
ChatGPT batch prompts were failing with error "Failed to fetch results: " when:
- Batch contains 3+ prompts
- Web search is enabled (larger responses)

Root cause: HTTP fetch timeout was 30s, but large JSON responses take 30-60s to download.

## How
- Added `fetch_timeout` parameter to `api_client.fetch_result()` (default: 120s)
- Threaded `fetch_timeout` through `polling.py` and `workflow.py`
- Separated fetch timeout from poll timeout (different concerns)
- Backwards compatible: all new parameters have defaults

See `devdocs/fixes/chatgpt_batch_timeout_fix.md` for detailed analysis.

## Testing
- [x] Unit tests pass
- [x] `probe_tests/test_08_chatgpt.py` - all tests pass (was failing)
- [x] `probe_tests/async/test_17_chatgpt_batch_debug.py` - verbose debug shows fetch now succeeds
- [x] Tested batches of 1, 2, 3, 5 prompts - all work
- [x] Tested with web_search enabled - works
- [x] No regressions in other scrapers

**Before:**
```
3 prompts: ❌ Failed: Failed to fetch results:
web_search: ❌ Failed: Failed to fetch results:
```

**After:**
```
3 prompts: ✅ SUCCESS
web_search: ✅ SUCCESS
```

## Related Issues
Fixes #45

## Checklist
- [x] Code follows project style guidelines
- [x] Tests pass locally
- [x] Documentation updated (devdocs)
- [x] Backwards compatible (no breaking changes)
```

---

## Testing Requirements

### Before Creating PR

**All PRs must:**
1. ✅ Pass all existing unit tests
2. ✅ Pass relevant integration tests (probe tests)
3. ✅ Include new tests for new code
4. ✅ Not break existing functionality

### Running Tests

```bash
# Quick check - unit tests only
python -m pytest tests/ -v

# Full check - all tests
python -m pytest tests/
python probe_tests/test_*.py

# Specific test
python probe_tests/test_08_chatgpt.py

# Concurrency tests
python probe_tests/async/test_10_concurrency_google_search.py
python probe_tests/async/test_11_concurrency_amazon_search.py
```

### Test Coverage by Change Type

| Change Type | Unit Tests | Integration Tests | Documentation |
|-------------|-----------|------------------|---------------|
| Bug Fix     | ✅ Required | ✅ Required | Optional |
| New Feature | ✅ Required | ✅ Required | ✅ Required |
| Docs Only   | ❌ N/A | ❌ N/A | ✅ Verify examples work |
| Refactor    | ✅ Must pass all | ✅ Must pass all | Optional |
| Perf        | ✅ Must pass all | ✅ Benchmarks | ✅ Document gains |
| Tests       | ✅ New tests | ✅ New tests | Optional |

---

## Code Review

### What Reviewers Look For

1. **Correctness**
   - Does it solve the problem?
   - Are there edge cases not handled?
   - Is the logic sound?

2. **Testing**
   - Are there tests for new code?
   - Do tests actually test the right thing?
   - Any regressions?

3. **Code Quality**
   - Follows Python best practices?
   - Clear variable names?
   - Appropriate comments?
   - No unnecessary complexity?

4. **Backwards Compatibility**
   - Will this break existing users?
   - Are new parameters optional with sensible defaults?
   - Is deprecated functionality clearly marked?

5. **Documentation**
   - Are docstrings updated?
   - Is README updated (if user-facing)?
   - Are examples clear and correct?

### How to Be a Good Reviewer

**✅ Good Reviews:**
```
"Nice fix! Could you add a test case for when timeout=0?
That edge case might cause issues."

"The logic looks good, but I think we can simplify lines 45-52
by using a dictionary instead of nested if statements."

"Excellent documentation! One typo on line 23: 'recieve' → 'receive'"
```

**❌ Bad Reviews:**
```
"This is wrong" (not helpful - explain why)
"Just use a different approach" (what approach?)
"LGTM" (without actually reviewing)
```

### How to Respond to Review Feedback

**✅ Good Responses:**
```
"Good catch! Fixed in commit abc123"

"I considered that approach, but it won't work when X happens.
What do you think about Y instead?"

"You're right, I missed that edge case. Adding test now."
```

**❌ Bad Responses:**
```
"It works on my machine" (doesn't address the issue)
"That's not important" (dismissive)
[No response] (acknowledge feedback!)
```

---

## Release Process

### Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

1.2.3
│ │ │
│ │ └─ Patch: Bug fixes, no breaking changes
│ └─── Minor: New features, backwards compatible
└───── Major: Breaking changes
```

**Examples:**
- `1.0.0` → `1.0.1` - Bug fix release
- `1.0.1` → `1.1.0` - New feature (ChatGPT scraper added)
- `1.1.0` → `2.0.0` - Breaking change (API redesign)

### When to Release

**Patch release (1.0.x):** After bug fixes
**Minor release (1.x.0):** After new features
**Major release (x.0.0):** After breaking changes

### Release Checklist

(For maintainers with release permissions)

```bash
# 1. Make sure main is clean
git checkout main
git pull origin main

# 2. Update version in setup.py, pyproject.toml, __init__.py
# Version: 1.2.3 → 1.2.4 (for patch)

# 3. Update CHANGELOG.md
# Document all changes since last release

# 4. Commit version bump
git add .
git commit -m "chore: Bump version to 1.2.4"

# 5. Tag release
git tag -a v1.2.4 -m "Release v1.2.4"

# 6. Push
git push origin main
git push origin v1.2.4

# 7. Build and publish to PyPI
python -m build
python -m twine upload dist/*

# 8. Create GitHub Release
# Go to GitHub → Releases → Draft new release
# Select tag v1.2.4
# Copy from CHANGELOG.md
# Publish release
```

---

## Best Practices

### Commits

**✅ Good commits:**
```bash
git commit -m "fix: Handle None values in price parsing"
git commit -m "feat: Add support for Instagram stories"
git commit -m "docs: Update ChatGPT examples with web search"
```

**❌ Bad commits:**
```bash
git commit -m "update"
git commit -m "fix bug"
git commit -m "asdfasdf"
git commit -m "WIP"  # Don't push WIP commits
```

### Branch Hygiene

**Do:**
- Create new branch for each feature/fix
- Keep branches focused (one thing per branch)
- Delete branches after merge
- Rebase on main if branch gets stale

**Don't:**
- Commit directly to main
- Reuse old branches for new work
- Let branches live forever
- Mix unrelated changes in one branch

### Communication

**Do:**
- Document your changes clearly
- Respond to review comments promptly
- Ask questions if requirements unclear
- Update the team on blockers

**Don't:**
- Go silent during review
- Merge without approval
- Ignore review feedback
- Make breaking changes without discussion

---

## Common Scenarios

### Scenario 1: I Need to Fix a Bug

```bash
# 1. Create fix branch
git checkout main
git pull origin main
git checkout -b fix/price-parsing-none-values

# 2. Write test that reproduces bug
# tests/test_price_parsing.py

# 3. Fix the bug
# src/brightdata/scrapers/amazon/scraper.py

# 4. Verify fix
python -m pytest tests/test_price_parsing.py

# 5. Commit and push
git add .
git commit -m "fix: Handle None values in price parsing"
git push -u origin fix/price-parsing-none-values

# 6. Create PR on GitHub
```

### Scenario 2: I'm Adding a New Feature

```bash
# 1. Create feature branch
git checkout main
git pull origin main
git checkout -b feat/instagram-stories

# 2. Implement feature
# src/brightdata/scrapers/instagram/scraper.py

# 3. Write tests
# tests/test_instagram_stories.py
# probe_tests/test_11_instagram_stories.py

# 4. Update docs
# README.md
# docs/instagram.md

# 5. Verify everything works
python -m pytest tests/
python probe_tests/test_11_instagram_stories.py

# 6. Commit and push
git add .
git commit -m "feat: Add Instagram stories scraping support"
git push -u origin feat/instagram-stories

# 7. Create PR with detailed description
```

### Scenario 3: My Branch is Behind Main

```bash
# Option 1: Rebase (cleaner history)
git checkout fix/my-fix
git fetch origin
git rebase origin/main

# If conflicts, resolve them
# Then: git rebase --continue

git push --force-with-lease

# Option 2: Merge (preserves history)
git checkout fix/my-fix
git merge main
git push
```

### Scenario 4: I Made a Mistake in My Last Commit

```bash
# If you haven't pushed yet
git commit --amend -m "fix: Correct commit message"

# If you already pushed (be careful!)
git commit --amend -m "fix: Correct commit message"
git push --force-with-lease  # Only if no one else is using this branch!

# To add forgotten files to last commit
git add forgotten_file.py
git commit --amend --no-edit
```

### Scenario 5: I Want to Test Someone's PR

```bash
# Option 1: Checkout their branch
git fetch origin
git checkout fix/their-fix

# Option 2: Pull their branch
git checkout -b test-their-pr
git pull origin fix/their-fix

# Test it
python probe_tests/test_08_chatgpt.py

# Leave feedback in PR comments
```

### Scenario 6: I'm Using a Fork - Keep It Updated

```bash
# Sync your fork's main with upstream (do this regularly!)
git checkout main
git fetch upstream
git merge upstream/main
git push origin main

# Update your feature branch with latest changes from upstream
git checkout fix/my-fix
git fetch upstream
git rebase upstream/main
git push --force-with-lease  # Force push to your fork
```

### Scenario 7: I'm Using a Fork - Create PR

```bash
# 1. Make sure you're on your feature branch
git checkout fix/chatgpt-batch-timeout

# 2. Push to YOUR fork
git push origin fix/chatgpt-batch-timeout

# 3. Go to GitHub - YOUR fork page
# https://github.com/YOUR-USERNAME/sdk-python

# 4. You'll see a banner: "Compare & pull request"
# Click it

# 5. The PR will be FROM your fork TO the main repository:
# base repository: brightdata/sdk-python  base: main
# head repository: YOUR-USERNAME/sdk-python  compare: fix/chatgpt-batch-timeout

# 6. Fill in PR details and create
```

### Scenario 8: I'm Using a Fork - My Fork is Behind

```bash
# Your fork's main is behind the upstream main

# Option 1: Update via command line (recommended)
git checkout main
git fetch upstream
git merge upstream/main  # Fast-forward merge
git push origin main     # Update your fork on GitHub

# Option 2: Update via GitHub UI
# 1. Go to your fork on GitHub
# 2. Click "Sync fork" button
# 3. Click "Update branch"
# 4. Then locally: git checkout main && git pull origin main
```

### Scenario 9: Understanding Remotes with Fork

```bash
# Check your remotes
git remote -v

# You should see:
# origin    https://github.com/YOUR-USERNAME/sdk-python.git (fetch)
# origin    https://github.com/YOUR-USERNAME/sdk-python.git (push)
# upstream  https://github.com/brightdata/sdk-python.git (fetch)
# upstream  https://github.com/brightdata/sdk-python.git (push)

# origin = YOUR fork (you can push here)
# upstream = main repository (you can only fetch/pull from here)

# Fetch from upstream (main repo)
git fetch upstream

# Push to origin (your fork)
git push origin fix/my-fix

# NEVER try to push to upstream (will fail if you don't have access)
git push upstream fix/my-fix  # ❌ Will fail
```

---

## Quick Reference

### Common Commands (Direct Access)

```bash
# Start new work
git checkout main && git pull origin main && git checkout -b feat/my-feature

# Check status
git status
git diff

# Commit
git add .
git commit -m "feat: My feature"

# Push
git push -u origin feat/my-feature  # First time
git push                             # Subsequent times

# Update branch with latest main
git fetch origin
git rebase origin/main

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# See commit history
git log --oneline

# Switch branches
git checkout main
git checkout fix/my-fix

# Delete branch
git branch -d feat/my-feature        # Local
git push origin --delete feat/my-feature  # Remote
```

### Common Commands (Fork-Based)

```bash
# Set up fork (one time)
git clone https://github.com/YOUR-USERNAME/sdk-python.git
cd sdk-python
git remote add upstream https://github.com/brightdata/sdk-python.git

# Start new work (sync with upstream first)
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
git checkout -b feat/my-feature

# Check status
git status
git diff

# Commit
git add .
git commit -m "feat: My feature"

# Push to YOUR fork
git push -u origin feat/my-feature  # First time
git push                             # Subsequent times

# Sync your feature branch with latest upstream
git fetch upstream
git rebase upstream/main
git push --force-with-lease  # Force push to your fork

# Update fork's main branch regularly
git checkout main
git fetch upstream
git merge upstream/main
git push origin main

# Delete branch
git branch -d feat/my-feature        # Local
git push origin --delete feat/my-feature  # On your fork
```

### Commit Message Types

| Type | When to Use |
|------|-------------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code restructuring, no behavior change |
| `test:` | Adding/updating tests |
| `perf:` | Performance improvement |
| `chore:` | Maintenance (deps, CI, build) |
| `style:` | Code formatting (no logic change) |

---

## Questions?

If you're unsure about anything:

1. **Check this guide** - Most common scenarios covered
2. **Look at recent PRs** - See how others do it
3. **Ask the team** - Better to ask than guess
4. **Document new patterns** - Update this guide if you discover something new

Happy coding! 🚀
