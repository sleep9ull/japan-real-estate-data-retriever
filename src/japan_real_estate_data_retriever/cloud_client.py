import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

from .paths import PROJECT_ROOT


TERMINAL_STATUSES = {"idle", "stopped", "timed_out", "error"}
BASE_URL_V3 = "https://api.browser-use.com/api/v3"
CLOUD_BACKENDS = {"cloud", "rest"}


class BrowserUseCloudError(RuntimeError):
    pass


class BrowserUseCloudClient:
    def __init__(
        self,
        backend: str = "cloud",
        api_key: Optional[str] = None,
        poll_interval: float = 5.0,
        timeout_seconds: int = 900,
    ) -> None:
        self.backend = _normalize_backend(backend)
        self.api_key = api_key or _load_api_key()
        self.poll_interval = poll_interval
        self.timeout_seconds = timeout_seconds

    def create_session(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        session = self._request("POST", "/sessions", payload)
        if not session.get("id"):
            raise BrowserUseCloudError("Browser Use response did not include a session id.")
        return session

    def get_session(self, session_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/sessions/{session_id}")

    def stop_session(self, session_id: str, strategy: str = "session") -> Dict[str, Any]:
        return self._request("POST", f"/sessions/{session_id}/stop", {"strategy": strategy})

    def run_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        session = self.create_session(payload)
        session_id = session["id"]
        if session.get("status") in TERMINAL_STATUSES:
            return session

        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            session = self.get_session(session_id)
            status = session.get("status")
            if status in TERMINAL_STATUSES:
                return session
            time.sleep(self.poll_interval)

        raise BrowserUseCloudError(f"Timed out waiting for Browser Use session {session_id}.")

    def create_browser(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        browser = self._request("POST", "/browsers", payload)
        if not browser.get("id"):
            raise BrowserUseCloudError("Browser Use response did not include a browser session id.")
        if not browser.get("cdpUrl"):
            raise BrowserUseCloudError("Browser Use response did not include a CDP URL.")
        return browser

    def get_browser(self, browser_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/browsers/{browser_id}")

    def stop_browser(self, browser_id: str) -> Dict[str, Any]:
        return self._request("PATCH", f"/browsers/{browser_id}", {"action": "stop"})

    def raw_get(self, path: str) -> Dict[str, Any]:
        if not path.startswith("/"):
            path = "/" + path
        return self._request("GET", path)

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._rest_request(method, path, payload)

    def _rest_request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise BrowserUseCloudError(
                "Browser Use API key is required. Set BROWSER_USE_API_KEY or ~/.jreretrieve/config.toml."
            )

        data = None
        headers = {
            "X-Browser-Use-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        request = urllib.request.Request(
            BASE_URL_V3 + path,
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise BrowserUseCloudError(
                f"Browser Use REST request failed with HTTP {exc.code}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise BrowserUseCloudError(f"Browser Use REST request failed: {exc}") from exc

        return _parse_json_output(body)


def _parse_json_output(output: str) -> Dict[str, Any]:
    text = output.strip()
    if not text:
        raise BrowserUseCloudError("Empty JSON response from Browser Use.")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise BrowserUseCloudError(f"Invalid JSON response from Browser Use: {text}") from exc


def _normalize_backend(backend: str) -> str:
    if backend not in CLOUD_BACKENDS:
        choices = ", ".join(sorted(CLOUD_BACKENDS))
        raise ValueError(f"backend must be one of: {choices}")
    if backend == "cloud":
        return "rest"
    return backend


def _load_api_key() -> Optional[str]:
    value, _source = _load_env_value_with_source("BROWSER_USE_API_KEY")
    return value


def get_auth_status() -> Dict[str, Any]:
    _value, source = _load_env_value_with_source("BROWSER_USE_API_KEY")
    return {
        "available": source != "missing",
        "source": source,
        "env_var": "BROWSER_USE_API_KEY",
        "config_path": str(_user_config_path()),
    }


def _load_env_value(name: str) -> Optional[str]:
    value, _source = _load_env_value_with_source(name)
    return value


def _load_env_value_with_source(name: str) -> Tuple[Optional[str], str]:
    env_value = os.environ.get(name)
    if env_value:
        return env_value, "env"

    config_value = _load_config_value(name)
    if config_value:
        return config_value, "config"

    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None, "missing"

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == name:
            loaded = value.strip().strip('"').strip("'") or None
            return loaded, "project_env" if loaded else "missing"
    return None, "missing"


def _user_config_path() -> Any:
    return os.path.expanduser("~/.jreretrieve/config.toml")


def _load_config_value(name: str) -> Optional[str]:
    path = _user_config_path()
    if not os.path.exists(path):
        return None

    key_aliases = {name, name.lower(), name.lower().replace("_", "-")}
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            normalized_key = key.strip().strip('"').strip("'")
            if normalized_key in key_aliases:
                loaded = value.strip().strip('"').strip("'")
                return loaded or None
    return None
