#!/usr/bin/env python3
"""
Generate statistics and observer prompt from health data.

This script takes raw health data JSON and user profile information,
computes statistics, and generates a filled observer prompt ready for LLM use.

Usage:
    python generate_prompt.py persona_a.json --age 28 --gender male
    python generate_prompt.py persona_a.json --age "late 20s" --gender female --output-dir ./output

Outputs:
    1. precomputed_<persona>.json - Computed statistics
    2. prompt_<persona>.txt - Filled observer prompt ready for LLM

Examples:
    # Basic usage
    python generate_prompt.py persona_a.json --age 28 --gender male

    # Specify output directory
    python generate_prompt.py persona_a.json --age 28 --gender male --output-dir ./generated

    # Process multiple files
    python generate_prompt.py persona_a.json persona_b.json --age 25 --gender female
"""

import argparse
import json
import sys
from pathlib import Path

from statistics import compute_all_statistics, format_statistics_summary
from prompt_builder import build_observer_prompt


def main():
    parser = argparse.ArgumentParser(
        description="Generate statistics and observer prompt from health data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "input_files",
        nargs="+",
        help="Input persona JSON file(s) with health data"
    )
    parser.add_argument(
        "--age",
        required=True,
        help="User's age (e.g., '28' or 'late 20s')"
    )
    parser.add_argument(
        "--gender",
        required=True,
        help="User's gender (e.g., 'male', 'female', 'non-binary')"
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
            print(f"\nProcessing {input_path}...")

        with open(input_path, 'r', encoding='utf-8') as f:
            persona_data = json.load(f)

        # Compute statistics
        if not args.quiet:
            print("Computing statistics...")

        stats = compute_all_statistics(persona_data)

        # Print summary
        if not args.quiet:
            print(format_statistics_summary(stats))

        # Build observer prompt
        if not args.quiet:
            print("Building observer prompt...")

        prompt = build_observer_prompt(
            persona_data=persona_data,
            statistics=stats,
            user_age=args.age,
            user_gender=args.gender
        )

        # Determine output paths
        persona = persona_data.get('persona', 'x').lower()
        args.output_dir.mkdir(parents=True, exist_ok=True)

        stats_path = args.output_dir / f"precomputed_{persona}.json"
        prompt_path = args.output_dir / f"prompt_{persona}.txt"

        # Save statistics JSON
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        if not args.quiet:
            print(f"Saved statistics to: {stats_path}")

        # Save filled prompt
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt)

        if not args.quiet:
            print(f"Saved prompt to: {prompt_path}")

    if not args.quiet:
        print("\nDone!")
        print("\nNext steps:")
        print("  1. Use the generated prompt with your preferred LLM")
        print("  2. The LLM should return a JSON array of 5 insights")
        print("  3. Each insight has: insight, explanation, confidence_score (0-10)")


if __name__ == "__main__":
    main()
