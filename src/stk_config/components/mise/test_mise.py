import subprocess

from stk.helpers.mise import mise_executable


def test_mise_runs() -> None:
    completed = subprocess.run(
        [str(mise_executable()), "--version"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert completed.stdout.strip()


def test_mise_never_builds_from_source() -> None:
    def setting(key: str) -> str:
        return subprocess.run(
            [str(mise_executable()), "settings", "get", key],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    assert setting("node.compile") == "false"
    assert "asdf" in setting("disable_backends")
