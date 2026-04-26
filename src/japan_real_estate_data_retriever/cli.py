import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from .cloud_client import BrowserUseCloudClient, BrowserUseCloudError
from .local_cli import BrowserUseLocalCliError, run_local_debug, write_debug_result
from .prompt_builder import build_session_payload, write_payload
from .sites import site_choices


def main(argv: list = None) -> int:
    parser = argparse.ArgumentParser(description="Japan real estate data retriever Browser Use runner.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build-task", help="Build a Browser Use session payload.")
    _add_cloud_task_arguments(build_parser)
    build_parser.add_argument("--out", type=Path, required=True, help="Output JSON payload path.")

    run_parser = subparsers.add_parser("run", help="Run a production Browser Use Cloud session.")
    _add_cloud_task_arguments(run_parser)
    run_parser.add_argument("--out", type=Path, help="Write session result JSON to this path.")
    run_parser.add_argument("--dry-run", action="store_true", help="Print payload without calling API.")
    run_parser.add_argument("--poll-interval", type=float, default=5.0)
    run_parser.add_argument("--timeout-seconds", type=int, default=900)

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
        payload = build_session_payload(args.site, query, args.model, args.max_cost_usd)
        write_payload(args.out, payload)
        print(str(args.out))
        return 0

    if args.command == "run":
        query = _read_json(args.query_file)
        payload = build_session_payload(args.site, query, args.model, args.max_cost_usd)
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


def _add_cloud_task_arguments(parser: argparse.ArgumentParser) -> None:
    _add_site_query_arguments(parser)
    parser.add_argument("--model", default="bu-mini")
    parser.add_argument("--max-cost-usd", type=float, default=2.0)


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


if __name__ == "__main__":
    raise SystemExit(main())
