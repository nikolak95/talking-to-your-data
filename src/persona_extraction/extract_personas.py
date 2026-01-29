#!/usr/bin/env python3
"""
LifeSnaps Persona Extraction Pipeline

This script extracts representative 14-day windows from the LifeSnaps dataset
for three distinct health personas:
  - Persona A: Sleep-deprived with weekend recovery pattern
  - Persona B: Active lifestyle with irregular stress-causing routine
  - Persona C: Active senior with moderate activity, fragmented sleep, slow recovery

The pipeline:
  1. Extracts all viable time windows from the dataset
  2. Scores each window against persona profiles
  3. Identifies top candidates for each persona
  4. Randomly selects one viable candidate per persona
  5. Generates JSON files and comparison visualizations

Usage:
    python extract_personas.py <path_to_lifesnaps_daily.csv> [options]

    Options:
        --top-k N           Selection pool size (default: 1 = best candidate)
                            top-k > 1: randomly select from top k candidates
        --seed S            Random seed for reproducibility (default: None)
        --window-days N     Window size in days (default: 14)
        --min-days N        Minimum days with valid data (default: 12)
        --output-dir DIR    Output directory (default: current directory)
        --plot              Generate comparison plot

Examples:
    python extract_personas.py daily.csv
    python extract_personas.py daily.csv --top-k 5 --seed 42 --plot
    python extract_personas.py daily.csv --top-k 10 --seed 123
"""

import sys
import json
import argparse
from pathlib import Path

import pandas as pd

from window_extraction import (
    extract_candidates,
    select_top_candidates,
    select_random_from_viable,
    extract_window_data
)
from visualization import (
    print_candidate_summary,
    window_to_json,
    plot_comparison
)


def main():
    parser = argparse.ArgumentParser(
        description="Extract representative personas from LifeSnaps health dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1]
    )

    parser.add_argument(
        "csv_path",
        help="Path to daily.csv file"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=1,
        help="Selection pool size: top-k=1 picks best, top-k>1 picks randomly from top k (default: 1)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: None)"
    )
    parser.add_argument(
        "--window-days",
        type=int,
        default=14,
        help="Window size in days (default: 14)"
    )
    parser.add_argument(
        "--min-days",
        type=int,
        default=12,
        help="Minimum days with valid data (default: 12)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate comparison plot"
    )

    args = parser.parse_args()

    # Validate arguments
    if not Path(args.csv_path).exists():
        print(f"Error: File not found: {args.csv_path}", file=sys.stderr)
        sys.exit(1)

    if args.top_k < 1:
        print(f"Error: top-k must be at least 1", file=sys.stderr)
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("LifeSnaps Persona Extraction Pipeline")
    print("=" * 80)
    print(f"Input file: {args.csv_path}")
    print(f"Output directory: {args.output_dir}")
    print(f"Window size: {args.window_days} days")
    print(f"Minimum data coverage: {args.min_days} days")
    print(f"Selection pool size (top-k): {args.top_k}")
    print(f"Random seed: {args.seed if args.seed is not None else 'None (random)'}")
    print()

    # Load data
    print("Loading dataset...")
    try:
        df = pd.read_csv(args.csv_path)
        print(f"Loaded {len(df)} rows from {len(df['id'].unique())} participants")
    except Exception as e:
        print(f"Error loading CSV: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract all candidates
    print(f"\nExtracting viable {args.window_days}-day windows...")
    candidates = extract_candidates(
        df,
        window_days=args.window_days,
        min_present_days=args.min_days
    )
    print(f"Found {len(candidates)} viable windows ({len(candidates)//3} unique windows)")

    # Select top candidates
    top_a, top_b, top_c = select_top_candidates(candidates, top_k=args.top_k)

    print_candidate_summary(top_a, "A", args.top_k)
    print_candidate_summary(top_b, "B", args.top_k)
    print_candidate_summary(top_c, "C", args.top_k)

    # Random selection
    print(f"\n{'='*80}")
    if args.top_k == 1:
        print(f"Selection: Best candidate (top-k=1, deterministic)")
    else:
        print(f"Random Selection (top-k={args.top_k}, seed={args.seed})")
    print(f"{'='*80}")

    try:
        # Select randomly from the top-k candidates (no threshold filter needed)
        selected_a = select_random_from_viable(top_a, threshold=0.0, seed=args.seed)
        print(f"\nPersona A Selected:")
        print(f"  ID:         {selected_a.participant_id}")
        print(f"  Start Date: {selected_a.start_date.date()}")
        print(f"  Fit Score:  {selected_a.fit_score:.4f}")
        if args.top_k > 1:
            print(f"  (Randomly selected from top {args.top_k} candidates)")

        selected_b = select_random_from_viable(top_b, threshold=0.0, seed=args.seed)
        print(f"\nPersona B Selected:")
        print(f"  ID:         {selected_b.participant_id}")
        print(f"  Start Date: {selected_b.start_date.date()}")
        print(f"  Fit Score:  {selected_b.fit_score:.4f}")
        if args.top_k > 1:
            print(f"  (Randomly selected from top {args.top_k} candidates)")

        selected_c = select_random_from_viable(top_c, threshold=0.0, seed=args.seed)
        print(f"\nPersona C Selected:")
        print(f"  ID:         {selected_c.participant_id}")
        print(f"  Start Date: {selected_c.start_date.date()}")
        print(f"  Fit Score:  {selected_c.fit_score:.4f}")
        if args.top_k > 1:
            print(f"  (Randomly selected from top {args.top_k} candidates)")

    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        print(f"Try increasing --top-k value", file=sys.stderr)
        sys.exit(1)

    # Extract window data
    print(f"\n{'='*80}")
    print("Extracting Selected Windows")
    print(f"{'='*80}")

    window_a = extract_window_data(
        df,
        selected_a.participant_id,
        selected_a.start_date.strftime("%Y-%m-%d"),
        window_days=args.window_days
    )

    window_b = extract_window_data(
        df,
        selected_b.participant_id,
        selected_b.start_date.strftime("%Y-%m-%d"),
        window_days=args.window_days
    )

    window_c = extract_window_data(
        df,
        selected_c.participant_id,
        selected_c.start_date.strftime("%Y-%m-%d"),
        window_days=args.window_days
    )

    print(f"✓ Extracted Persona A window: {len(window_a)} days")
    print(f"✓ Extracted Persona B window: {len(window_b)} days")
    print(f"✓ Extracted Persona C window: {len(window_c)} days")

    # Generate JSON files
    print(f"\nGenerating JSON files...")

    json_a = window_to_json(window_a, "A", selected_a.participant_id)
    json_b = window_to_json(window_b, "B", selected_b.participant_id)
    json_c = window_to_json(window_c, "C", selected_c.participant_id)

    output_a = args.output_dir / "persona_a.json"
    output_b = args.output_dir / "persona_b.json"
    output_c = args.output_dir / "persona_c.json"

    with open(output_a, "w", encoding="utf-8") as f:
        json.dump(json_a, f, indent=2)

    with open(output_b, "w", encoding="utf-8") as f:
        json.dump(json_b, f, indent=2)

    with open(output_c, "w", encoding="utf-8") as f:
        json.dump(json_c, f, indent=2)

    print(f"✓ Saved {output_a}")
    print(f"✓ Saved {output_b}")
    print(f"✓ Saved {output_c}")

    # Generate plot if requested
    if args.plot:
        print(f"\nGenerating comparison plot...")
        plot_path = args.output_dir / "persona_comparison.png"
        plot_comparison(
            window_a,
            window_b,
            window_c=window_c,
            title_a=f"Persona A (id={selected_a.participant_id}, score={selected_a.fit_score:.3f})",
            title_b=f"Persona B (id={selected_b.participant_id}, score={selected_b.fit_score:.3f})",
            title_c=f"Persona C (id={selected_c.participant_id}, score={selected_c.fit_score:.3f})",
            output_path=str(plot_path)
        )

    # Summary
    print(f"\n{'='*80}")
    print("Pipeline Complete!")
    print(f"{'='*80}")
    print(f"\nOutput files:")
    print(f"  • {output_a}")
    print(f"  • {output_b}")
    print(f"  • {output_c}")
    if args.plot:
        print(f"  • {plot_path}")

    print(f"\nSelection details:")
    print(f"  • Selection pool: Top {args.top_k} candidate(s)")
    if args.top_k == 1:
        print(f"  • Method: Best candidate (deterministic)")
    else:
        print(f"  • Method: Random selection (uniform)")
        print(f"  • Random seed: {args.seed if args.seed is not None else 'None (random)'}")
    print()


if __name__ == "__main__":
    main()
