# ✅ Production Release Checklist

Use this checklist to release v1.0.0

---

## Phase 1: Verification (30 minutes)

### Testing
- [ ] Install test dependencies: `pip install -r requirements.txt`
- [ ] Run all tests: `pytest tests/ -v`
- [ ] Check coverage: `pytest tests/ --cov=exttester --cov-report=html`
- [ ] Open coverage report: `start htmlcov/index.html`
- [ ] Verify coverage is 60%+ (target: 65-80%)

### Build
- [ ] Install build tools: `pip install build`
- [ ] Build package: `python -m build`
- [ ] Verify dist/ contains:
  - [ ] `exttester-1.0.0-py3-none-any.whl`
  - [ ] `exttester-1.0.0.tar.gz`

### Local Testing
- [ ] Create test environment: `python -m venv test_env`
- [ ] Activate: `test_env\Scripts\activate`
- [ ] Install from wheel: `pip install dist/exttester-1.0.0-py3-none-any.whl`
- [ ] Test CLI: `python main.py --help`
- [ ] Deactivate: `deactivate`

---

## Phase 2: Documentation (20 minutes)

### Update Files
- [ ] Update `CHANGELOG.md` with v1.0.0 release notes
- [ ] Update `README.md` badges (see BADGES_UPDATE.md)
- [ ] Verify `VERSION` file contains `1.0.0`
- [ ] Update `exttester/__version__.py` if needed

### Review Documentation
- [ ] Read through README.md for accuracy
- [ ] Check all links work
- [ ] Verify installation instructions
- [ ] Check feature list matches reality

---

## Phase 3: Git & GitHub (15 minutes)

### Commit Changes
```bash
git add .
git commit -m "Production upgrade: pytest, CI/CD, packaging, v1.0.0"
git push origin main
```

### Verify CI
- [ ] Go to: https://github.com/Subhan-Haider/EXTENSION-TESTER/actions
- [ ] Wait for CI to complete
- [ ] Verify all jobs pass:
  - [ ] Test job (Ubuntu + Windows, Python 3.9-3.12)
  - [ ] Lint job
  - [ ] Security job
  - [ ] Build job
- [ ] Check coverage report uploaded

### Fix Any CI Failures
If CI fails:
- [ ] Read error messages
- [ ] Fix issues locally
- [ ] Re-run tests locally
- [ ] Commit and push fixes
- [ ] Wait for CI to pass

---

## Phase 4: Create Release (10 minutes)

### Tag Release
```bash
# Create annotated tag
git tag -a v1.0.0 -m "Version 1.0.0 - Production Release

Major Features:
- Real browser automation with Playwright
- Comprehensive scoring engine
- CVE vulnerability scanning
- PDF report generation
- Professional test suite (pytest)
- Multi-platform CI/CD
- pip installable package

See CHANGELOG.md for full details."

# Push tag
git push origin v1.0.0
```

### Monitor Release Build
- [ ] Go to: https://github.com/Subhan-Haider/EXTENSION-TESTER/actions
- [ ] Watch "Release" workflow run
- [ ] Verify jobs complete:
  - [ ] create-release
  - [ ] build-windows-exe
  - [ ] build-python-package
  - [ ] update-changelog

### Verify Release Created
- [ ] Go to: https://github.com/Subhan-Haider/EXTENSION-TESTER/releases
- [ ] Verify v1.0.0 release exists
- [ ] Check assets uploaded:
  - [ ] ExtensionTester.exe
  - [ ] ExtensionTester.exe.sha256
  - [ ] exttester-1.0.0-py3-none-any.whl
  - [ ] exttester-1.0.0.tar.gz
  - [ ] checksums.txt

---

## Phase 5: Post-Release (20 minutes)

### Test Release
- [ ] Download ExtensionTester.exe from release
- [ ] Run on clean Windows machine
- [ ] Verify it works

### Download Python Package
- [ ] Download .whl from release
- [ ] Create fresh venv
- [ ] Install: `pip install exttester-1.0.0-py3-none-any.whl`
- [ ] Test: `exttester --help`

### Update README Badges
- [ ] Add CI badge (should show passing)
- [ ] Add coverage badge
- [ ] Add release badge
- [ ] Commit and push

### Announce
- [ ] Write release announcement
- [ ] Share on relevant platforms:
  - [ ] GitHub Discussions
  - [ ] Reddit (r/Python, r/webdev)
  - [ ] Twitter/X
  - [ ] Dev.to
  - [ ] LinkedIn

---

## Phase 6: Optional - PyPI Publishing (30 minutes)

### Setup PyPI Account
- [ ] Create account at https://pypi.org
- [ ] Verify email
- [ ] Enable 2FA
- [ ] Create API token
- [ ] Add token to GitHub secrets as `PYPI_API_TOKEN`

### Test on TestPyPI First
```bash
# Install twine
pip install twine

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ exttester
```

### Publish to PyPI
```bash
# Upload to PyPI
twine upload dist/*

# Test install
pip install exttester
```

### Update Release Workflow
- [ ] Uncomment PyPI publishing section in `.github/workflows/release.yml`
- [ ] Commit and push
- [ ] Future releases will auto-publish to PyPI

---

## Troubleshooting

### CI Fails
**Problem:** Tests fail in CI but pass locally  
**Solution:** 
- Check Python version differences
- Check OS-specific issues (Windows vs Linux)
- Review CI logs carefully
- Add `print()` statements for debugging

### Build Fails
**Problem:** `python -m build` fails  
**Solution:**
- Ensure `setup.py` and `pyproject.toml` are correct
- Check all imports work
- Verify `exttester/__version__.py` exists

### Release Not Created
**Problem:** Tag pushed but no release  
**Solution:**
- Check tag format is `v*.*.*` (e.g., v1.0.0)
- Verify `.github/workflows/release.yml` exists
- Check GitHub Actions permissions
- Look for errors in Actions tab

### .exe Doesn't Run
**Problem:** ExtensionTester.exe fails to run  
**Solution:**
- Check `ExtensionTester.spec` configuration
- Verify all dependencies included
- Test on clean Windows machine
- Check antivirus didn't block it

---

## Success Criteria

### ✅ Release is successful when:
- [ ] All CI tests pass
- [ ] GitHub release created with all assets
- [ ] .exe runs on Windows
- [ ] Python package installs via pip
- [ ] CLI commands work
- [ ] Coverage is 60%+
- [ ] No critical bugs reported

### 🎉 You're done when:
- [ ] v1.0.0 tag exists
- [ ] GitHub release is live
- [ ] All assets downloadable
- [ ] README updated
- [ ] Announcement posted

---

## Next Steps After v1.0

### v1.1 Planning
- [ ] Review PRODUCTION_UPGRADE_PLAN.md
- [ ] Prioritize next features
- [ ] Create GitHub issues
- [ ] Set milestone for v1.1

### Community Building
- [ ] Respond to issues
- [ ] Review pull requests
- [ ] Update documentation
- [ ] Create video tutorials

### Continuous Improvement
- [ ] Monitor CI for flaky tests
- [ ] Improve test coverage (target 80%+)
- [ ] Add more examples
- [ ] Write blog posts

---

**Current Status:** Ready to execute  
**Estimated Time:** 1.5-2 hours  
**Difficulty:** Easy (everything is automated)

**Let's ship v1.0! 🚀**
