import subprocess
from os import path

import pytest
import testinfra


TUMBLEWEED_CONTAINER = ["registry.opensuse.org/opensuse/tumbleweed:latest"]
LEAP_CONTAINERS = [
    "registry.opensuse.org/opensuse/leap:15.3",
    "registry.opensuse.org/opensuse/leap:15.2",
]
SLE_CONTAINERS = [
    "registry.suse.com/suse/sle15:15.3",
    "registry.suse.com/suse/sle15:15.2",
    "registry.suse.com/suse/sle15:15.1",
    "registry.suse.com/suse/sles12sp5:latest"
]

CONTAINER_IMAGES = TUMBLEWEED_CONTAINER + LEAP_CONTAINERS + SLE_CONTAINERS

CONTAINER_IMAGE_CHOICES = {
    "tumbleweed": TUMBLEWEED_CONTAINER,
    "leap": LEAP_CONTAINERS,
    "sle": SLE_CONTAINERS,
}


def pytest_addoption(parser):
    parser.addoption(
        "--container",
        help="container images to run the tests against",
        nargs="+",
        default=CONTAINER_IMAGES,
    )


def pytest_generate_tests(metafunc):
    if "container" in metafunc.fixturenames:
        containers = metafunc.config.getoption("container")
        images = []
        distros = list(CONTAINER_IMAGE_CHOICES.keys())

        for opt in containers:
            if opt in distros:
                for img in CONTAINER_IMAGE_CHOICES[opt]:
                    images.append(img)
            else:
                images.append(opt)

        metafunc.parametrize("container", images, indirect=True)


@pytest.fixture(scope="session")
def container(request):
    container_url = getattr(request, "param", TUMBLEWEED_CONTAINER[0])
    container_id = (
        subprocess.check_output(
            [
                "podman",
                "run",
                "-d",
                "-it",
                container_url,
                "/bin/sh",
            ]
        )
        .decode()
        .strip()
    )
    subprocess.check_call(
        [
            "podman",
            "cp",
            path.abspath(
                path.join(
                    path.dirname(__file__),
                    "update-ca-certificates",
                )
            ),
            container_id + ":" + "/bin/update-ca-certificates",
        ],
    )

    yield testinfra.get_host(f"podman://{container_id}")

    subprocess.check_call(["podman", "rm", "-f", container_id])
