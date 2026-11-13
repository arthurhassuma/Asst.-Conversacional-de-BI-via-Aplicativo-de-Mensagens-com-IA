import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "deploy" / "oracle" / "pac-update.sh"

DOCKER_STUB = """#!/usr/bin/env bash
echo "docker $*" >> "$STUB_DIR/calls.log"
ids="$STUB_DIR/ids"
mkdir -p "$ids"
key() { echo "$1" | tr '/:' '__'; }
case "$1" in
  pull)
    [ "${STUB_PULL_FAIL:-0}" = "1" ] && exit 1
    exit 0 ;;
  image)
    if [[ "$4" == *Labels* ]]; then cat "$STUB_DIR/revision"; exit 0; fi
    f="$ids/$(key "$5")"
    if [ -f "$f" ]; then cat "$f"; exit 0; fi
    exit 1 ;;
  tag)
    cp "$ids/$(key "$2")" "$ids/$(key "$3")" ;;
  compose)
    if [[ " $* " == *" up "* ]] && [ "$(cat "$ids/pac-bi-runtime_local")" = "${STUB_COMPOSE_FAIL_FOR:-none}" ]; then
      exit 1
    fi
    exit 0 ;;
esac
"""

CURL_STUB = """#!/usr/bin/env bash
echo "curl $*" >> "$STUB_DIR/calls.log"
[ "$(cat "$STUB_DIR/ids/pac-bi-runtime_local")" = "${STUB_HEALTH_FAIL_FOR:-none}" ] && exit 22
exit 0
"""


def _bash_works():
    bash = shutil.which("bash")
    if not bash:
        return False
    try:
        out = subprocess.run(
            [bash, "-c", "echo $OSTYPE"], capture_output=True, text=True, timeout=20
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return False
    if os.name == "nt":
        return out in ("msys", "cygwin")
    return out.startswith(("linux", "darwin"))


pytestmark = pytest.mark.skipif(not _bash_works(), reason="bash compatível indisponível")

REMOTE_KEY = "ghcr.io_arthurhassuma_pac-bi-assistant_production"


class Vm:
    def __init__(self, root: Path):
        self.root = root
        self.stub = root / "stub"
        self.bin = root / "bin"
        self.state = root / "state"
        (self.stub / "ids").mkdir(parents=True)
        self.bin.mkdir()
        for name, body in (("docker", DOCKER_STUB), ("curl", CURL_STUB)):
            path = self.bin / name
            path.write_text(body, encoding="utf-8", newline="\n")
            path.chmod(0o755)
        (self.stub / "revision").write_text("abc1234", encoding="utf-8")

    def set_image(self, key: str, image_id: str | None):
        path = self.stub / "ids" / key
        if image_id is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(image_id, encoding="utf-8")

    def image(self, key: str):
        path = self.stub / "ids" / key
        return path.read_text(encoding="utf-8") if path.exists() else None

    def calls(self):
        log = self.stub / "calls.log"
        return log.read_text(encoding="utf-8").splitlines() if log.exists() else []

    def compose_ups(self):
        return [c for c in self.calls() if c.startswith("docker compose") and " up " in c]

    def run(self, **extra):
        env = {
            **os.environ,
            "PATH": f"{self.bin.as_posix()}{os.pathsep}{os.environ['PATH']}",
            "STUB_DIR": self.stub.as_posix(),
            "PAC_STATE_DIR": self.state.as_posix(),
            "PAC_COMPOSE_FILE": (self.root / "compose.yaml").as_posix(),
            **extra,
        }
        return subprocess.run(
            [shutil.which("bash"), SCRIPT.as_posix()],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )


@pytest.fixture
def vm(tmp_path):
    return Vm(tmp_path)


def test_nothing_happens_when_the_promoted_image_is_already_running(vm):
    vm.set_image(REMOTE_KEY, "sha256:same")
    vm.set_image("pac-bi-runtime_local", "sha256:same")
    result = vm.run()
    assert result.returncode == 0
    assert vm.compose_ups() == []


def test_new_healthy_image_is_deployed_and_the_old_one_is_kept_for_rollback(vm):
    vm.set_image(REMOTE_KEY, "sha256:new")
    vm.set_image("pac-bi-runtime_local", "sha256:old")
    result = vm.run()
    assert result.returncode == 0, result.stdout + result.stderr
    assert vm.image("pac-bi-runtime_local") == "sha256:new"
    assert vm.image("pac-bi-runtime_previous") == "sha256:old"
    ups = vm.compose_ups()
    assert (
        len(ups) == 2 and "backend" in ups[0] and "--wait" in ups[0] and ups[1].endswith("polling")
    )
    assert (vm.state / "deployed-revision").read_text(encoding="utf-8").strip() == "abc1234"
    assert not (vm.state / "failed").exists()


def test_unhealthy_image_is_rolled_back_and_not_retried(vm):
    vm.set_image(REMOTE_KEY, "sha256:bad")
    vm.set_image("pac-bi-runtime_local", "sha256:old")
    result = vm.run(STUB_HEALTH_FAIL_FOR="sha256:bad")
    assert result.returncode == 1
    assert vm.image("pac-bi-runtime_local") == "sha256:old"
    assert (vm.state / "failed").read_text(encoding="utf-8").strip() == "sha256:bad"
    assert vm.compose_ups()[-1].endswith("backend polling")
    before = len(vm.compose_ups())
    again = vm.run(STUB_HEALTH_FAIL_FOR="sha256:bad")
    assert again.returncode == 0
    assert len(vm.compose_ups()) == before


def test_failing_compose_up_also_triggers_rollback(vm):
    vm.set_image(REMOTE_KEY, "sha256:bad")
    vm.set_image("pac-bi-runtime_local", "sha256:old")
    result = vm.run(STUB_COMPOSE_FAIL_FOR="sha256:bad")
    assert result.returncode == 1
    assert vm.image("pac-bi-runtime_local") == "sha256:old"


def test_a_fixed_image_is_deployed_after_a_failed_one(vm):
    vm.set_image(REMOTE_KEY, "sha256:bad")
    vm.set_image("pac-bi-runtime_local", "sha256:old")
    assert vm.run(STUB_HEALTH_FAIL_FOR="sha256:bad").returncode == 1
    vm.set_image(REMOTE_KEY, "sha256:fixed")
    result = vm.run(STUB_HEALTH_FAIL_FOR="sha256:bad")
    assert result.returncode == 0
    assert vm.image("pac-bi-runtime_local") == "sha256:fixed"
    assert not (vm.state / "failed").exists()


def test_first_deploy_without_a_local_image_has_no_previous_tag(vm):
    vm.set_image(REMOTE_KEY, "sha256:new")
    result = vm.run()
    assert result.returncode == 0, result.stdout + result.stderr
    assert vm.image("pac-bi-runtime_local") == "sha256:new"
    assert vm.image("pac-bi-runtime_previous") is None


def test_registry_outage_keeps_the_current_version(vm):
    vm.set_image(REMOTE_KEY, "sha256:new")
    vm.set_image("pac-bi-runtime_local", "sha256:old")
    result = vm.run(STUB_PULL_FAIL="1")
    assert result.returncode == 0
    assert vm.image("pac-bi-runtime_local") == "sha256:old"
    assert vm.compose_ups() == []


def test_concurrent_run_is_skipped(vm):
    vm.set_image(REMOTE_KEY, "sha256:new")
    (vm.state / "lock.d").mkdir(parents=True)
    result = vm.run()
    assert result.returncode == 0
    assert vm.calls() == []
