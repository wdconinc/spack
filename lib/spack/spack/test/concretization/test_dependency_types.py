# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
"""Tests for dependency type handling, particularly test dependencies."""
import pytest

import spack.concretize
import spack.repo
import spack.solver.asp
from spack.spec import Spec
from spack.test.conftest import RepoBuilder


@pytest.mark.regression("test-dependency-version-constraint")
@pytest.mark.usefixtures("config")
def test_test_dependency_version_constraint_not_enforced_without_tests(repo_builder: RepoBuilder):
    """Test-only version constraints should not apply to non-test concretization.
    
    When a package has:
        depends_on("foo")
        depends_on("foo@:1.0", type="test")
    
    The version constraint @:1.0 should ONLY apply when tests=True.
    Without tests, foo should be unconstrained (any version allowed).
    
    This is a regression test for a bug where Spack merged dependencies
    and applied test-only version constraints to build/link dependencies.
    """
    # Create a base package "foo" (template includes versions 1.0, 2.0, 3.0)
    repo_builder.add_package("foo")
    
    # Create package "bar" that depends on foo, with a test-only version constraint
    repo_builder.add_package(
        "bar",
        dependencies=[
            ("foo", None, None),
            ("foo@:1.0", "test", None),
        ],
    )
    
    with spack.repo.use_repositories(repo_builder.root):
        # Without tests=True, should be able to use foo@2.0
        # The test-only constraint foo@:1.0 should NOT be enforced
        spec = Spec("bar ^foo@2.0")
        concrete = spack.concretize.concretize_one(spec, tests=False)
        
        assert concrete["foo"].satisfies("@2.0"), (
            "foo@2.0 should be allowed when tests=False. "
            "Test-only constraint foo@:1.0 was incorrectly enforced."
        )


@pytest.mark.regression("test-dependency-version-constraint")
@pytest.mark.usefixtures("config")
def test_test_dependency_version_constraint_enforced_with_tests(repo_builder: RepoBuilder):
    """Test-only version constraints SHOULD apply when tests=True.
    
    When tests are enabled, the test dependency constraints must be respected.
    """
    # Create packages (template includes versions 1.0, 2.0, 3.0)
    repo_builder.add_package("foo")
    
    repo_builder.add_package(
        "bar",
        dependencies=[
            ("foo", None, None),
            ("foo@:1.0", "test", None),
        ],
    )
    
    with spack.repo.use_repositories(repo_builder.root):
        # With tests=True, foo@2.0 should NOT be allowed
        spec = Spec("bar ^foo@2.0")
        
        with pytest.raises(Exception):  # Should fail concretization
            concrete = spack.concretize.concretize_one(spec, tests=True)


@pytest.mark.regression("test-dependency-version-constraint")
@pytest.mark.usefixtures("config")
def test_test_dependency_version_constraint_without_explicit_request(repo_builder: RepoBuilder):
    """Without explicitly requesting a version, test constraints should not affect default.
    
    When concretizing without tests and without an explicit version request,
    the solver should choose the latest version, not be constrained by test deps.
    """
    # Create packages (template includes versions 1.0, 2.0, 3.0)
    repo_builder.add_package("foo")
    
    repo_builder.add_package(
        "bar",
        dependencies=[
            ("foo", None, None),
            ("foo@:1.0", "test", None),
        ],
    )
    
    with spack.repo.use_repositories(repo_builder.root):
        # Without tests and without explicit version, should get latest (3.0)
        spec = Spec("bar")
        concrete = spack.concretize.concretize_one(spec, tests=False)
        
        # Should prefer the latest version since test constraint doesn't apply
        assert concrete["foo"].satisfies("@3.0"), (
            "Without tests=True, should get latest foo version. "
            f"Got {concrete['foo'].version} instead of 3.0"
        )


@pytest.mark.regression("test-dependency-version-constraint")
@pytest.mark.usefixtures("config")
def test_mixed_dependency_types_with_constraints(repo_builder: RepoBuilder):
    """Test that version constraints are properly scoped to their dependency types.
    
    Tests the specific pattern from the gaudi package:
        depends_on("fmt")
        depends_on("fmt@:8", when="@:36.9")
        depends_on("fmt@:10", when="@:38")
        depends_on("fmt@:11", when="@:39")
        depends_on("fmt@:10", type="test")
        
    The template provides versions 1.0, 2.0, 3.0 so we'll test with those.
    """
    repo_builder.add_package("fmt")
    
    repo_builder.add_package(
        "mypkg",
        dependencies=[
            ("fmt", None, None),
            ("fmt@:1.0", None, "@:1.5"),  # Like fmt@:8 when @:36.9
            ("fmt@:2.0", None, "@:2.5"),  # Like fmt@:10 when @:38
            ("fmt@:2.0", "test", None),   # Test constraint same as @:2.5 constraint
        ],
    )
    
    with spack.repo.use_repositories(repo_builder.root):
        # mypkg@3.0 should allow fmt@3.0 without tests (no when= constraints apply)
        spec = Spec("mypkg@3.0 ^fmt@3.0")
        concrete = spack.concretize.concretize_one(spec, tests=False)
        assert concrete["fmt"].satisfies("@3.0"), \
            "mypkg@3.0 should allow fmt@3.0 without tests"
        
        # mypkg@2.0 should allow fmt@2.0 (within @:2.0 constraint from when=@:2.5)
        spec = Spec("mypkg@2.0 ^fmt@2.0")
        concrete = spack.concretize.concretize_one(spec, tests=False)
        assert concrete["fmt"].satisfies("@2.0"), \
            "mypkg@2.0 should allow fmt@2.0 (matches when= constraint)"
