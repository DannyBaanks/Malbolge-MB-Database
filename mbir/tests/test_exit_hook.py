from mbir import run_with_exit_hook


def test_exit_hook_translates_integer_system_exit():
    def stop():
        raise SystemExit(7)

    result = run_with_exit_hook(stop)
    assert (result.status, result.exit_code) == ("EXIT", 7)


def test_exit_hook_preserves_normal_return():
    result = run_with_exit_hook(lambda: "MBIR")
    assert (result.status, result.exit_code, result.stdout) == (
        "RETURNED", 0, b"MBIR"
    )
