from __future__ import annotations

import argparse
import json
from typing import Sequence

from .server import MCPAuthBrokerServer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mcp-auth-broker")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run", "health", "ready", "tools"],
        help="Command to execute",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    server = MCPAuthBrokerServer()

    if args.command == "health":
        print(json.dumps(server.health(), sort_keys=True))
        return

    if args.command == "ready":
        print(json.dumps(server.readiness(), sort_keys=True))
        return

    if args.command == "tools":
        print(json.dumps(server.discover_tools(), sort_keys=True))
        return

    payload = {
        "status": "started",
        "service": server.config.service_name,
        "environment": server.config.environment,
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
