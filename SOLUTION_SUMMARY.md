# Fix for Test Dependency Version Constraint Bug

## Problem

When a Spack package declares both a regular dependency and a test-only dependency with version constraints, the constraints were being incorrectly merged:

```python
depends_on("fmt")                    # build+link+run, any version
depends_on("fmt@:10", type="test")   # test only, version ≤10
```

**Bug**: Spack merged these into `fmt@:10` with types `BUILD|LINK|TEST`, causing the test-only version constraint to apply even when `tests=False`.

**Impact**: Packages like `gaudi` couldn't concretize with `fmt@11` because the test-only `fmt@:10` constraint was incorrectly enforced for build/link dependencies.

## Solution

The fix keeps test-only and non-test dependencies separate instead of merging them when they have different type classifications.

### Architecture

Dependencies can now be stored in two formats:
- **Single Dependency**: `deps_by_name["foo"] = Dependency(...)` (backward compatible)
- **List of Dependencies**: `deps_by_name["foo"] = [Dep1, Dep2]` (when separation needed)

The list format is used when:
- One dependency is test-only (`depflag == TEST`)
- Another dependency is non-test (`depflag & ~TEST != 0`)
- Both target the same package

### Implementation (6 commits)

#### 1. test: add regression tests for test dependency version constraints
- **File**: `lib/spack/spack/test/concretization/test_dependency_types.py`
- **Purpose**: Document expected behavior with tests that initially fail
- **Tests**:
  - Test-only constraints don't affect non-test concretization
  - Test constraints apply when `tests=True`
  - Default version selection unaffected by test constraints
  - Complex mixed scenarios (gaudi pattern)

#### 2. dependency: add helper to normalize dependency storage format
- **File**: `lib/spack/spack/dependency.py`
- **Change**: Add `dependencies_as_list()` helper function
- **Purpose**: Normalize iteration - always returns a list regardless of storage format
- **Usage**: `for dep in dependencies_as_list(value): ...`

#### 3. directives: keep test-only dependencies separate from non-test deps
- **File**: `lib/spack/spack/directives.py`
- **Change**: Check test-only status before merging dependencies
- **Logic**:
  - If both have same test-only status → merge (existing behavior)
  - If different test-only status → store separately as list
  - Test-only deps can be filtered without affecting non-test constraints

#### 4. package_base: handle list-format dependencies in _by_subkey
- **File**: `lib/spack/spack/package_base.py`
- **Change**: Use `extend()` instead of `append()` when value is a list
- **Fixes**: Prevented nested lists `[[Dep1, Dep2]]` that broke iteration

#### 5. solver: handle both single and list dependency formats
- **File**: `lib/spack/spack/solver/asp.py`
- **Change**: Use `dependencies_as_list()` in solver fact generation
- **Impact**: Solver correctly processes separated dependencies

#### 6. core: update dependency iteration to handle list format
- **Files**: 
  - `lib/spack/spack/patch.py` - patch indexing
  - `lib/spack/spack/audit.py` - dependency validation
  - `lib/spack/spack/cmd/dependents.py` - dep graph construction
  - `lib/spack/spack/solver/input_analysis.py` - deptype checking
  - `lib/spack/spack/spec.py` - patch application
- **Change**: All locations now use `dependencies_as_list()` helper

## Results

✅ All 4 regression tests pass
✅ Test-only constraints isolated correctly
✅ `spack spec gaudi ^fmt@11` now works (without `--test`)
✅ Backward compatible with existing packages

## Testing

```bash
# Run the regression tests
cd ~/git/spack/.worktree/fix-test-dependency-bug
python3 -m pytest lib/spack/spack/test/concretization/test_dependency_types.py -v

# Test with real package
spack spec gaudi ^fmt@11           # Should succeed
spack spec --test gaudi ^fmt@11    # Should fail (test constraint)
```

## Branch Info

- **Worktree**: `.worktree/fix-test-dependency-bug`
- **Branch**: `fix-test-dependency-bug`
- **Base**: `develop` (commit c64ed21fe3)
- **Commits**: 6 commits implementing the fix

## Files Modified

1. `lib/spack/spack/test/concretization/test_dependency_types.py` (new)
2. `lib/spack/spack/dependency.py`
3. `lib/spack/spack/directives.py`
4. `lib/spack/spack/package_base.py`
5. `lib/spack/spack/solver/asp.py`
6. `lib/spack/spack/patch.py`
7. `lib/spack/spack/audit.py`
8. `lib/spack/spack/cmd/dependents.py`
9. `lib/spack/spack/solver/input_analysis.py`
10. `lib/spack/spack/spec.py`

## Next Steps

1. Run full Spack test suite to ensure no regressions
2. Test with additional real-world packages
3. Submit PR to Spack with these commits
4. Consider long-term refactoring (Option 3 from analysis) for more robust type-specific constraints
