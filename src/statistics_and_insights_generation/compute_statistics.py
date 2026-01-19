#!/usr/bin/env python3
"""
Compute statistics from extracted persona JSON files.

This script computes correlations, trends, and summary statistics from
persona_a.json and persona_b.json files. LLM-based insights are optional
and can be added separately.

Usage:
    python compute_statistics.py persona_a.json
    python compute_statistics.py persona_a.json persona_b.json
    python compute_statistics.py persona_a.json --output stats_a.json

Examples:
    # Compute stats for one persona
    python compute_statistics.py persona_a.json

    # Compute stats for both personas
    python compute_statistics.py persona_a.json persona_b.json

    # Save to specific output file
    python compute_statistics.py persona_a.json --output precomputed_a.json
"""

import argparse
import json
import sys
from pathlib import Path

from statistics import compute_all_statistics, format_statistics_summary


def main():
    parser = argparse.ArgumentParser(
        description="Compute statistics from persona JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "input_files",
        nargs="+",
        help="Input persona JSON file(s)"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output JSON file (default: precomputed_<persona>.json)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress console output"
    )

    args = parser.parse_args()

    for input_file in args.input_files:
        input_path = Path(input_file)

        if not input_path.exists():
            print(f"Error: File not found: {input_file}", file=sys.stderr)
            sys.exit(1)

        # Load persona data
        if not args.quiet:
            print(f"\nLoading {input_path}...")

        with open(input_path, 'r', encoding='utf-8') as f:
            persona_data = json.load(f)

        # Compute statistics
        if not args.quiet:
            print("Computing statistics...")

        stats = compute_all_statistics(persona_data)

        # Print summary
        if not args.quiet:
            print(format_statistics_summary(stats))

        # Determine output path
        if args.output and len(args.input_files) == 1:
            output_path = args.output_dir / args.output
        else:
            persona = persona_data.get('persona', 'x').lower()
            output_path = args.output_dir / f"precomputed_{persona}.json"

        # Save statistics
        args.output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        if not args.quiet:
            print(f"\nSaved statistics to: {output_path}")

    if not args.quiet:
        print("\nDone!")


if __name__ == "__main__":
    main()
