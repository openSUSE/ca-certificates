# Testsuite

`update-ca-certificates` has a simple container based test suite implemented in
Python using [pytest](https://pytest.org) and
[testinfra](https://testinfra.readthedocs.io/).


## Prerequisites

- Python >= 3.6.2
- [pytest](https://docs.pytest.org/en/stable/), ideally with xdist
- [testinfra](https://testinfra.readthedocs.io/).
- [Podman](https://podman.io/)


## Running the tests

Install dependencies (e.g. in a virtualenv), then run the tests:

```ShellSession
$ pytest -vv -n $(nproc)
$ # only run the tests on Leap:
$ pytest -vv -n $(nproc) --container leap
$ # run only a certain test function
$ pytest -vv -k prints_help -n $(nproc)
```


## Writing tests

Tests are implemented as python functions using `testinfra` with a bit of pytest
magic sprinkled on top of them:
```python
def test_runs_in_container(container):
    container.run("touch /foobar")
    assert container.file("/foobar").exists
```

The parameter `container` is a pytest fixture defined in `conftest.py`. It
starts a container (by default openSUSE Tumbleweed) at the start of the test
suite run, copies the `update-ca-certificates` script into the container to
`/bin/update-ca-certificates`, gives each test a connection to the container and
destroys it after the run.

Additionally the `pytest_generate_tests` function in `conftest.py` ensures that
each test is automagically run for all available containers (Tumbleweed, Leap
and SLE). This can be toggled via the `--container` flag passed to
pytest. E.g. `pytest --container leap sle` will only run the tests on Leap and
SLE containers, whereas `pytest --container
my.registry.name/path/to/my/image:42` will run the tests only inside the
container image available under `my.registry.name/path/to/my/image:42`.

Note, that for efficiency, the container connection is shared by all test
function that use the same image. This means that if you **must** undo any
mutation that you performed during your tests, to not cause failures in
subsequent tests.
