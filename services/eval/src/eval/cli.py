"""Eval CLI: split, run, compare, gate (implemented in P3)."""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    """Define the CLI described in the LLD."""
    parser = argparse.ArgumentParser(prog="python -m eval")
    commands = parser.add_subparsers(dest="command", required=True)
    split = commands.add_parser("split", help="write eval/splits.json (once)")
    split.add_argument("--seed", type=int, default=42)
    run = commands.add_parser("run", help="score profiles on a split")
    run.add_argument("--profiles", default="full")
    run.add_argument("--split", choices=["tune", "test", "all"], default="all")
    run.add_argument("--concurrency", type=int, default=4)
    run.add_argument("--no-ragas", action="store_true")
    run.add_argument("--resume")
    compare = commands.add_parser("compare", help="overall and per-category deltas")
    compare.add_argument("run_a")
    compare.add_argument("run_b")
    gate = commands.add_parser("gate", help="check a run against config/gates.yaml")
    gate.add_argument("run_id")
    gate.add_argument("--phase")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch; commands arrive in P3."""
    args = build_parser().parse_args(argv)
    print(f"eval {args.command}: not implemented until P3", file=sys.stderr)
    return 2
