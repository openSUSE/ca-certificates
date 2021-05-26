import pytest


HOOKSDIR1 = "/etc/ca-certificates/update.d"
HOOKSDIR2 = "/usr/lib/ca-certificates/update.d"

HOOK_ARGS_PATH = "/hook_args"
LISTENER_SCRIPT_DEST = HOOKSDIR2 + "/foo.run"

LISTENER_SCRIPT = (
    r"""#!/bin/bash
echo "\$@" > """
    + HOOK_ARGS_PATH
)

BAR_HOOK = "bar.run"


def copy_listener_script(container_connection):
    if container_connection.file(HOOK_ARGS_PATH).exists:
        container_connection.run_expect([0], "rm " + HOOK_ARGS_PATH)

    if not container_connection.file(LISTENER_SCRIPT_DEST).exists:
        container_connection.run_expect(
            [0],
            "\n".join(
                (
                    "cat << EOF > " + LISTENER_SCRIPT_DEST,
                    LISTENER_SCRIPT,
                    "EOF",
                )
            ),
        )
        container_connection.run_expect(
            [0], "chmod +x " + LISTENER_SCRIPT_DEST
        )


def test_does_nothing_under_transactional_update(container):
    container.run_expect([0], "echo foo > /etc/pki/trust/.updated")
    container.run_expect(
        [0], "TRANSACTIONAL_UPDATE=1 /bin/update-ca-certificates"
    )

    assert container.file("/etc/pki/trust/.updated").exists
    assert container.file("/etc/pki/trust/.updated").content_string == ""


def test_prints_help(container):
    assert (
        container.run_expect([0], "/bin/update-ca-certificates --help").stdout
        == """USAGE: /bin/update-ca-certificates [OPTIONS]
OPTIONS:
  --verbose, -v     verbose output
  --fresh, -f       start from scratch
  --help, -h        this screen
"""
    )


def test_reports_invalid_options(container):
    res = container.run_expect([1], "/bin/update-ca-certificates --foobar")
    assert res.stdout == ""
    assert res.stderr == "invalid option: --foobar\n"


@pytest.mark.parametrize(
    "flag",
    [
        "",
        "-f",
        "-v",
        "-v -f",
        "-f -v",
    ],
)
def test_runs_the_hooks_in_hookdirs(container, flag):
    copy_listener_script(container)
    res = container.run_expect([0], "/bin/update-ca-certificates " + flag)
    if "-v" in flag:
        assert "running " + LISTENER_SCRIPT_DEST + " .." in res.stdout

    passed_flags = (
        " ".join(
            filter(None, (f if f in flag else None for f in ("-f", "-v")))
        )
        + "\n"
    )
    assert container.file(HOOK_ARGS_PATH).content_string == passed_flags
    assert not container.file("/etc/pki/trust/.updated").exists


def test_prefers_hooks_in_etc(container):
    for hookdir in (HOOKSDIR1, HOOKSDIR2):
        dest = hookdir + "/" + BAR_HOOK
        container.run_expect([0], 'echo "#!/bin/bash" >' + dest)
        container.run_expect([0], "chmod +x " + dest)

    res = container.run_expect([0], "/bin/update-ca-certificates -v")
    assert "running " + HOOKSDIR1 + "/" + BAR_HOOK + " .." in res.stdout
    assert "running " + HOOKSDIR2 + "/" + BAR_HOOK + " .." not in res.stdout

    for hookdir in (HOOKSDIR1, HOOKSDIR2):
        container.run_expect([0], "rm " + hookdir + "/" + BAR_HOOK)


@pytest.mark.parametrize("hookdir", [HOOKSDIR1, HOOKSDIR2])
def test_ignores_directories(container, hookdir):
    dest = hookdir + "/" + BAR_HOOK
    container.run_expect([0], "mkdir " + dest)

    res = container.run_expect([0], "/bin/update-ca-certificates -v")
    assert "running " + dest + " .." not in res.stdout

    container.run_expect([0], "rmdir " + dest)


@pytest.mark.parametrize("hookdir", [HOOKSDIR1, HOOKSDIR2])
def test_does_not_execute_files_not_called_dot_run(container, hookdir):
    dest = hookdir + "/" + "run"
    container.run_expect([0], "touch " + dest)

    res = container.run_expect([0], "/bin/update-ca-certificates -v")
    assert "running " + dest + " .." not in res.stdout

    container.run_expect([0], "rm " + dest)


@pytest.mark.parametrize("hookdir", [HOOKSDIR1, HOOKSDIR2])
def test_ignores_hooks_in_subdirectories(container, hookdir):
    subdir = hookdir + "/" + "test"
    dest = subdir + "/" + BAR_HOOK
    container.run_expect([0], "mkdir " + subdir)
    container.run_expect([0], 'echo "#!/bin/bash" >' + dest)
    container.run_expect([0], "chmod +x " + dest)
    container.run_expect([0], dest)

    res = container.run_expect([0], "/bin/update-ca-certificates -v")
    assert "running " + dest + " .." not in res.stdout

    container.run_expect([0], "rm -rf " + subdir)


def test_runs_hooks_in_sorted_order(container):
    hooks = [HOOKSDIR1 + "/" + hook for hook in ("10foo.run", "20bar.run")]
    for hook in hooks:
        container.run_expect([0], 'echo "#!/bin/bash" >' + hook)
        container.run_expect([0], "chmod +x " + hook)
        container.run_expect([0], hook)

    res = container.run_expect([0], "/bin/update-ca-certificates -v")

    for hook in hooks:
        assert "running " + hook + " .." in res.stdout
        container.run_expect([0], "rm " + hook)

    assert res.stdout.index(hooks[0]) < res.stdout.index(hooks[1])


def test_skips_hooks_symlinked_to_dev_null(container):
    HOOK = HOOKSDIR1 + "/50foobar.run"
    container.run_expect([0], "ln -sf /dev/null " + HOOK)
    res = container.run_expect([0], "/bin/update-ca-certificates -v")
    assert "skipping " + HOOK in res.stdout
