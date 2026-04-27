import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from .cloud_client import BrowserUseCloudClient, BrowserUseCloudError
from .local_cli import BrowserUseLocalCliError, run_local_debug, write_debug_result
from .prompt_builder import (
    build_agent_session_payload,
    build_browser_session_payload,
    build_browser_workflow_payload,
    build_multi_source_browser_workflow_payload,
    write_payload,
)
from .sites import site_choices


def main(argv: list = None) -> int:
    parser = argparse.ArgumentParser(description="Japan real estate data retriever Browser Use runner.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser(
        "build-task",
        help="Build the primary browser-only Cloud Browser payload and workflow context.",
    )
    _add_cloud_browser_workflow_arguments(build_parser)
    build_parser.add_argument("--out", type=Path, required=True, help="Output JSON payload path.")

    run_parser = subparsers.add_parser(
        "run",
        help="Create a primary browser-only Cloud Browser session and workflow context.",
    )
    _add_cloud_browser_workflow_arguments(run_parser)
    run_parser.add_argument("--out", type=Path, help="Write browser connection and workflow context JSON to this path.")
    run_parser.add_argument("--dry-run", action="store_true", help="Print payload without calling API.")

    run_all_parser = subparsers.add_parser(
        "run-all",
        help="Create one isolated Cloud Browser session per source for browser-only execution.",
    )
    _add_multi_source_browser_workflow_arguments(run_all_parser)
    run_all_parser.add_argument("--out", type=Path, help="Write all browser connections and workflow contexts to this path.")
    run_all_parser.add_argument("--dry-run", action="store_true", help="Print payload without calling API.")

    agent_parser = subparsers.add_parser(
        "run-agent",
        help="Run Browser Use Cloud Agent v3 as a fallback or repair path.",
    )
    _add_cloud_agent_arguments(agent_parser)
    agent_parser.add_argument("--out", type=Path, help="Write session result JSON to this path.")
    agent_parser.add_argument("--dry-run", action="store_true", help="Print payload without calling API.")
    agent_parser.add_argument("--poll-interval", type=float, default=5.0)
    agent_parser.add_argument("--timeout-seconds", type=int, default=900)

    browser_parser = subparsers.add_parser(
        "create-browser",
        help="Create a raw standalone Cloud Browser session for diagnostics.",
    )
    _add_cloud_browser_arguments(browser_parser)
    browser_parser.add_argument("--out", type=Path, help="Write browser connection JSON to this path.")
    browser_parser.add_argument("--dry-run", action="store_true", help="Print payload without calling API.")

    stop_parser = subparsers.add_parser("stop-browser", help="Stop one or more Cloud Browser sessions.")
    stop_parser.add_argument("--browser-id", nargs="+", required=True, help="Browser session id returned by run, run-all, or create-browser.")
    stop_parser.add_argument("--out", type=Path, help="Write stopped browser result JSON to this path.")

    stop_session_parser = subparsers.add_parser("stop-session", help="Stop a Cloud Agent session.")
    stop_session_parser.add_argument("--session-id", required=True, help="Session id returned by run.")
    stop_session_parser.add_argument("--strategy", choices=("session", "task"), default="session")
    stop_session_parser.add_argument("--out", type=Path, help="Write stopped session result JSON to this path.")

    debug_parser = subparsers.add_parser(
        "debug-local",
        help="Debug site workflow with the local browser-use CLI and local browser.",
    )
    _add_site_query_arguments(debug_parser)
    debug_parser.add_argument(
        "--browser-use-cli",
        help="Path to the browser-use executable. Defaults to BROWSER_USE_CLI, PATH, or ~/.browser-use-env/bin/browser-use.",
    )
    debug_parser.add_argument("--session", default="japan-real-estate-debug")
    debug_parser.add_argument("--headless", action="store_true", help="Do not pass --headed to browser-use.")
    debug_parser.add_argument("--profile", help="Chrome profile name to pass to browser-use --profile.")
    debug_parser.add_argument("--no-open", action="store_true", help="Print debug plan without opening the browser.")
    debug_parser.add_argument("--state", action="store_true", help="Run browser-use state after opening the site.")
    debug_parser.add_argument("--screenshot", type=Path, help="Capture a screenshot to this path.")
    debug_parser.add_argument("--out", type=Path, help="Write local debug result JSON to this path.")

    args = parser.parse_args(argv)

    if args.command == "build-task":
        query = _read_json(args.query_file)
        payload = _build_cloud_browser_workflow_payload(args, query)
        write_payload(args.out, payload)
        print(str(args.out))
        return 0

    if args.command == "run":
        query = _read_json(args.query_file)
        payload = _build_cloud_browser_workflow_payload(args, query)
        if args.dry_run:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        client = BrowserUseCloudClient()
        try:
            browser = client.create_browser(payload["browserPayload"])
        except BrowserUseCloudError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        result = {
            "browser": browser,
            "workflow": payload["workflow"],
        }
        if args.out:
            write_payload(args.out, result)
            print(str(args.out))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "run-all":
        query = _read_json(args.query_file)
        sources = _resolve_sources(args.sources, query)
        payload = _build_multi_source_cloud_browser_workflow_payload(args, sources, query)
        if args.dry_run:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        client = BrowserUseCloudClient()
        result = {
            "executionMode": "browser_only_primary",
            "sessionIsolation": payload["sessionIsolation"],
            "sources": {},
            "errors": [],
        }
        for source, source_payload in payload["sources"].items():
            try:
                browser = client.create_browser(source_payload["browserPayload"])
            except BrowserUseCloudError as exc:
                result["errors"].append({"source": source, "message": str(exc)})
                continue
            result["sources"][source] = {
                "browser": browser,
                "workflow": source_payload["workflow"],
            }

        if result["errors"]:
            print(json.dumps(result["errors"], ensure_ascii=False), file=sys.stderr)

        if args.out:
            write_payload(args.out, result)
            print(str(args.out))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result["errors"] and not result["sources"] else 0

    if args.command == "run-agent":
        query = _read_json(args.query_file)
        payload = _build_cloud_agent_payload(args, query)
        if args.dry_run:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        client = BrowserUseCloudClient(
            poll_interval=args.poll_interval,
            timeout_seconds=args.timeout_seconds,
        )
        try:
            result = client.run_task(payload)
        except BrowserUseCloudError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        if args.out:
            write_payload(args.out, result)
            print(str(args.out))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "create-browser":
        payload = _build_cloud_browser_payload(args)
        if args.dry_run:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        client = BrowserUseCloudClient()
        try:
            result = client.create_browser(payload)
        except BrowserUseCloudError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        if args.out:
            write_payload(args.out, result)
            print(str(args.out))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "stop-browser":
        client = BrowserUseCloudClient()
        results = []
        had_error = False
        for browser_id in args.browser_id:
            try:
                results.append(client.stop_browser(browser_id))
            except BrowserUseCloudError as exc:
                had_error = True
                results.append({"id": browser_id, "error": str(exc)})

        if args.out:
            write_payload(args.out, {"browsers": results})
            print(str(args.out))
        else:
            print(json.dumps({"browsers": results}, ensure_ascii=False, indent=2))
        return 1 if had_error else 0

    if args.command == "stop-session":
        client = BrowserUseCloudClient()
        try:
            result = client.stop_session(args.session_id, strategy=args.strategy)
        except BrowserUseCloudError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        if args.out:
            write_payload(args.out, result)
            print(str(args.out))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "debug-local":
        query = _read_json(args.query_file)
        try:
            result = run_local_debug(
                source=args.site,
                query=query,
                browser_use_cli=args.browser_use_cli,
                session=args.session,
                headed=not args.headless,
                profile=args.profile,
                open_browser=not args.no_open,
                include_state=args.state,
                screenshot_path=args.screenshot,
            )
        except BrowserUseLocalCliError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        if args.out:
            write_debug_result(args.out, result)
            print(str(args.out))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    parser.error("Unsupported command.")
    return 2


def _add_site_query_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--site", choices=site_choices(), required=True)
    parser.add_argument("--query-file", type=Path, required=True)


def _add_cloud_browser_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timeout-minutes", type=int, default=60)
    parser.add_argument("--profile-id", help="Browser Use profile id for persistent cookies/storage.")
    parser.add_argument("--enable-recording", action="store_true")
    parser.add_argument("--browser-screen-width", type=int, default=1440)
    parser.add_argument("--browser-screen-height", type=int, default=1000)
    parser.add_argument("--allow-resizing", action="store_true")


def _add_cloud_browser_workflow_arguments(parser: argparse.ArgumentParser) -> None:
    _add_site_query_arguments(parser)
    _add_cloud_browser_arguments(parser)


def _add_multi_source_browser_workflow_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--query-file", type=Path, required=True)
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=site_choices(),
        help="Sources to run. Defaults to query.sources when present, otherwise all supported sources.",
    )
    _add_cloud_browser_arguments(parser)


def _add_cloud_agent_arguments(parser: argparse.ArgumentParser) -> None:
    _add_site_query_arguments(parser)
    parser.add_argument("--model", default="bu-mini")
    parser.add_argument("--max-cost-usd", type=float, default=2.0)
    parser.add_argument("--keep-alive", action="store_true")
    parser.add_argument("--profile-id", help="Browser Use profile id for persistent cookies/storage.")
    parser.add_argument("--workspace-id", help="Browser Use workspace id for persistent files.")
    parser.add_argument("--enable-recording", action="store_true")
    parser.add_argument("--disable-skills", action="store_true")
    parser.add_argument("--enable-agentmail", action="store_true")
    parser.add_argument("--cache-script", action="store_true")


def _build_cloud_agent_payload(args: argparse.Namespace, query: Dict[str, Any]) -> Dict[str, Any]:
    return build_agent_session_payload(
        source=args.site,
        query=query,
        model=args.model,
        max_cost_usd=args.max_cost_usd,
        keep_alive=args.keep_alive,
        profile_id=args.profile_id,
        workspace_id=args.workspace_id,
        enable_recording=args.enable_recording,
        skills=not args.disable_skills,
        agentmail=args.enable_agentmail,
        cache_script=args.cache_script,
    )


def _build_cloud_browser_workflow_payload(args: argparse.Namespace, query: Dict[str, Any]) -> Dict[str, Any]:
    return build_browser_workflow_payload(
        source=args.site,
        query=query,
        timeout_minutes=args.timeout_minutes,
        profile_id=args.profile_id,
        enable_recording=args.enable_recording,
        browser_screen_width=args.browser_screen_width,
        browser_screen_height=args.browser_screen_height,
        allow_resizing=args.allow_resizing,
    )


def _build_multi_source_cloud_browser_workflow_payload(
    args: argparse.Namespace,
    sources: list,
    query: Dict[str, Any],
) -> Dict[str, Any]:
    return build_multi_source_browser_workflow_payload(
        sources=sources,
        query=query,
        timeout_minutes=args.timeout_minutes,
        profile_id=args.profile_id,
        enable_recording=args.enable_recording,
        browser_screen_width=args.browser_screen_width,
        browser_screen_height=args.browser_screen_height,
        allow_resizing=args.allow_resizing,
    )


def _build_cloud_browser_payload(args: argparse.Namespace) -> Dict[str, Any]:
    return build_browser_session_payload(
        timeout_minutes=args.timeout_minutes,
        profile_id=args.profile_id,
        enable_recording=args.enable_recording,
        browser_screen_width=args.browser_screen_width,
        browser_screen_height=args.browser_screen_height,
        allow_resizing=args.allow_resizing,
    )


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _resolve_sources(cli_sources: Any, query: Dict[str, Any]) -> list:
    if cli_sources:
        return list(cli_sources)
    query_sources = query.get("sources")
    if isinstance(query_sources, list) and query_sources:
        return [str(source) for source in query_sources]
    return list(site_choices())


if __name__ == "__main__":
    raise SystemExit(main())
