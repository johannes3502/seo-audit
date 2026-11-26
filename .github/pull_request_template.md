## What changed

<!-- One paragraph. Link the rule ID or issue if there is one. -->

## Why

<!-- The false positive, missed case or workflow problem this fixes. -->

## Verification

- [ ] `python scripts/validate_skill.py .`
- [ ] `python -m py_compile scripts/*.py`
- [ ] `python -m unittest discover -s tests -v`
- [ ] Added or updated a fixture
- [ ] Added a false-positive case (for a new or changed rule)

## Scope check

- [ ] Generic: no customer domain, keyword, route name or private data
- [ ] Rule IDs are unchanged or new
- [ ] `CHANGELOG.md` updated
- [ ] `README.md` updated if public behavior changed
