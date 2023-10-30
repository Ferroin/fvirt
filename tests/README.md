# Testing fvirt

fvirt uses [pytest](https://docs.pytest.org/) for testing. Configuration for pytest is in the `pyproject.toml`
file in the root of the repository, and all the testing dependencies, including pytest itself, are included in
the development environment that will be installed by Poetry.

This means that once you have a local development environment set up for fvirt, all you need to do to run tests is:

```
poetry run pytest
```

## Test timeouts.

All tests intentionally have a hard 30-second timeout. Any test which exceeds this time limit will be terminated
and counted as a failure.

This policy was instituted because it’s possible for Python code interacting with libvirt to trigger situations
in libvirt where the process simply hangs, and any such situations that are caused by fvirt code are treated as
critical bugs.

The timeout may be selectively extended on tests that truly do require more time, such as tests that work with
live domains running actual guest operating systems, but such tests should both be marked as slow _and_ still have
a hard timeout to make sure they don’t hang.

## Test concurrency.

In our CI environment, tests are run concurrently using pytest-xdist. This means that all tests _must_
be concurrency-clean for a PR to pass CI. The pytest-xdist plugin is included by default in the development
environment, and the tests will also run concurrently locally by default unless you explicitly override this behavior.

Tests must also be safe against reordering of test cases, and we internally utilize the pytest-randomize plugin to force reordering

## Tests with external dependencies.

A number of our tests uses `qemu:///session` URIs. This means those tests have a functional dependency on virtqemud
and possibly on a working qemu-system emulator.

By default, the test suite will check for these external dependencies and skip any tests that require them if they
are not found. You can make these tests fail instead of being skipped by setting `FVIRT_FAIL_NON_RUNNABLE_TESTS`
to a non-empty string in the test environment.

Developers who want to confirm that tests are skipped by this logic can force it to skip all tests that it would
skip by setting `FVIRT_TEST_SKIP_TESTS` to a non-empty string.

## Code coverage

fvirt uses `coverage` and the `pytest-cov` plugin to check code coverage. Modules should target at least 80%
coverage whenever possible. Code coverage data can be generated with the following command:

`poetry run pytest --cov=fvirt`

Once coverage data is generated, it can be inspected using

`poetry run coverage report`

Our code coverage metrics are computed using both statement and branch coverage analysis.
