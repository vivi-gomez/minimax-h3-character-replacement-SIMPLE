"""Start this ComfyUI installation with MiniMax H3's stable loading profile.

Place this file beside ComfyUI's main.py. On Linux/macOS, run it with the
Python interpreter from the environment used to run ComfyUI.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Sequence


STABLE_FLAGS = (
    "--disable-fast-disk",
    "--disable-async-offload",
    "--disable-comfy-compiler",
    "--disable-pinned-memory",
    "--use-pytorch-cross-attention",
    "--disable-triton-backend",
)
REQUIRED_FLAGS = ("--disable-fast-disk", "--use-pytorch-cross-attention")
CONFLICTING_FLAGS = (
    "--disable-dynamic-vram",
    "--fast-disk",
    "--async-offload",
    "--force-non-blocking",
    "--use-sage-attention",
    "--use-flash-attention",
    "--use-split-cross-attention",
    "--use-quad-cross-attention",
    "--use-ck-attention",
    "--enable-triton-backend",
)


class LauncherError(ValueError):
    """A startup configuration that cannot use the stable profile."""


@dataclass(frozen=True)
class LaunchPlan:
    root: Path
    command: tuple[str, ...]
    omitted_flags: tuple[str, ...]


def declared_options(cli_args_path: Path) -> set[str]:
    """Read declared flags without importing ComfyUI or initializing a GPU."""
    try:
        tree = ast.parse(cli_args_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise LauncherError(f"Cannot read ComfyUI's startup options: {exc}") from exc
    result = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "add_argument":
            continue
        result.update(
            item.value
            for item in node.args
            if isinstance(item, ast.Constant)
            and isinstance(item.value, str)
            and item.value.startswith("--")
        )
    return result


def reject_conflicting_options(arguments: Sequence[str], supported_options: set[str]) -> None:
    # argparse accepts abbreviated long options, but an exact declared option
    # wins over prefix matches (for example, --fast is distinct from --fast-disk).
    for argument in arguments:
        option = argument.split("=", 1)[0]
        if not option.startswith("--") or option == "--":
            continue
        if option in supported_options and option not in CONFLICTING_FLAGS:
            continue
        conflict = next((flag for flag in CONFLICTING_FLAGS if flag.startswith(option)), None)
        if conflict:
            raise LauncherError(
                f"{argument} conflicts with the stable loading profile ({conflict}). "
                "Remove that option and start again."
            )


def build_launch_plan(
    script_path: Path, executable: str, arguments: Sequence[str]
) -> LaunchPlan:
    root = script_path.resolve().parent
    if not (root / "main.py").is_file() or not (root / "comfy" / "cli_args.py").is_file():
        raise LauncherError(
            "Place h3_studio_start.py and Start-MiniMax-H3-Studio.bat inside the "
            "ComfyUI folder, beside main.py."
        )
    if not executable:
        raise LauncherError("The current Python interpreter could not be identified.")
    supported = declared_options(root / "comfy" / "cli_args.py")
    reject_conflicting_options(arguments, supported)
    for required in REQUIRED_FLAGS:
        if required not in supported:
            raise LauncherError(
                f"This ComfyUI version does not declare {required}, so the "
                "stable loading profile cannot be verified. Use a ComfyUI version "
                "that supports this option. No server was started."
            )
    provided = set()
    for argument in arguments:
        option = argument.split("=", 1)[0]
        if option in supported:
            provided.add(option)
        elif option.startswith("--") and option != "--":
            matches = [flag for flag in supported if flag.startswith(option)]
            if len(matches) == 1:
                provided.add(matches[0])
    added = tuple(flag for flag in STABLE_FLAGS if flag in supported and flag not in provided)
    omitted = tuple(flag for flag in STABLE_FLAGS if flag not in supported)
    command = (executable, "-s", str(root / "main.py"), *added, *arguments)
    return LaunchPlan(root=root, command=command, omitted_flags=omitted)


def main(arguments: Sequence[str] | None = None) -> int:
    try:
        plan = build_launch_plan(
            Path(__file__), sys.executable, sys.argv[1:] if arguments is None else arguments
        )
    except LauncherError as exc:
        print(f"MiniMax H3 Studio could not start: {exc}", file=sys.stderr)
        return 2
    print("MiniMax H3 Studio: stable loading profile (PyTorch attention; fast-disk disabled; ComfyUI memory management preserved).", flush=True)
    print(
        "This profile can use more system RAM and load more slowly. "
        "It does not guarantee that every model or generation will fit or succeed.",
        flush=True,
    )
    if plan.omitted_flags:
        print(
            "This ComfyUI version does not declare these optional settings; omitted: "
            + ", ".join(plan.omitted_flags),
            flush=True,
        )
    try:
        return subprocess.call(plan.command, cwd=plan.root)
    except OSError as exc:
        print(f"Could not start ComfyUI: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
