import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import PROJECT_ROOT
from .sites import get_site


LOCAL_ENV_FILENAME = ".env.local"


class BrowserUseLocalCliError(RuntimeError):
    pass


def run_local_debug(
    source: str,
    query: Dict[str, Any],
    browser_use_cli: Optional[str] = None,
    session: str = "japan-real-estate-debug",
    headed: bool = True,
    profile: Optional[str] = None,
    open_browser: bool = True,
    include_state: bool = False,
    screenshot_path: Optional[Path] = None,
) -> Dict[str, Any]:
    site = get_site(source)
    cli = resolve_browser_use_cli(browser_use_cli)
    if not cli:
        raise BrowserUseLocalCliError(
            "browser-use CLI was not found. Install it with "
            "`curl -fsSL https://browser-use.com/cli/install.sh | bash`, then run "
            "`source ~/.zshrc`, set BROWSER_USE_CLI, or pass --browser-use-cli."
        )

    result: Dict[str, Any] = {
        "mode": "local-browser-cli",
        "source": site.source,
        "source_site_name": site.display_name,
        "start_url": site.base_url,
        "query": query,
        "commands": [],
        "notes": [
            "This mode uses local browser-use CLI browser commands only.",
            "It is for local workflow debugging and does not produce canonical schema output.",
            "Use `run` to create the production Cloud Browser session and workflow context.",
        ],
        "suggested_next_commands": _suggested_commands(cli, session, site.base_url),
    }

    if open_browser:
        result["commands"].append(
            _run_browser_use_command(cli, session, headed, profile, ["open", site.base_url])
        )

    if include_state:
        result["commands"].append(
            _run_browser_use_command(cli, session, headed, profile, ["state"])
        )

    if screenshot_path:
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        result["commands"].append(
            _run_browser_use_command(
                cli,
                session,
                headed,
                profile,
                ["screenshot", str(screenshot_path)],
            )
        )
        result["screenshot_path"] = str(screenshot_path)

    return result


def resolve_browser_use_cli(explicit_path: Optional[str] = None) -> Optional[str]:
    candidates = [
        explicit_path,
        _load_env_value("BROWSER_USE_CLI"),
        shutil.which("browser-use"),
        str(Path.home() / ".browser-use-env" / "bin" / "browser-use"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        expanded = os.path.expanduser(candidate)
        resolved = shutil.which(expanded) if os.sep not in expanded else expanded
        if resolved and os.path.isfile(resolved) and os.access(resolved, os.X_OK):
            return resolved
    return None


def _run_browser_use_command(
    cli: str,
    session: str,
    headed: bool,
    profile: Optional[str],
    command_args: List[str],
) -> Dict[str, Any]:
    command = [cli, "--session", session]
    if headed:
        command.append("--headed")
    if profile is not None:
        command.extend(["--profile", profile])
    command.extend(command_args)

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _suggested_commands(cli: str, session: str, start_url: str) -> List[str]:
    return [
        f"{cli} --session {session} --headed open {start_url}",
        f"{cli} --session {session} state",
        f"{cli} --session {session} screenshot data/raw/local-debug.png",
        f"{cli} --session {session} close",
    ]


def _load_env_value(name: str) -> Optional[str]:
    env_value = os.environ.get(name)
    if env_value:
        return env_value

    env_path = PROJECT_ROOT / LOCAL_ENV_FILENAME
    if not env_path.exists():
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"').strip("'") or None
    return None


def write_debug_result(path: Path, result: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
