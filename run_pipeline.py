"""
RazorShield — run_pipeline.py
=================================
Convenience script to run the complete ML pipeline end-to-end.

Usage:
    python run_pipeline.py
    python run_pipeline.py --skip-data   # if data already generated
    python run_pipeline.py --eval-test   # also evaluate on held-out test
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(description="RazorShield ML Pipeline")
    parser.add_argument("--skip-data", action="store_true",
                        help="Skip data generation if CSV already exists")
    parser.add_argument("--eval-test", action="store_true",
                        help="Run final evaluation on held-out test set")
    args = parser.parse_args()

    import yaml
    with open(ROOT_DIR / "config" / "config.yaml") as f:
        config = yaml.safe_load(f)

    # ── Step 1: Generate data ──────────────────────────────────────────────
    raw_path = ROOT_DIR / config["data"]["output_path"]
    if args.skip_data and raw_path.exists():
        print(f"[pipeline] Skipping data generation — {raw_path} exists.")
    else:
        print("\n" + "="*60)
        print(" Step 1/4  Generate Synthetic Dataset")
        print("="*60)
        t0 = time.time()
        from data_generator import generate_and_save
        generate_and_save(config)
        print(f"[pipeline] Done in {time.time()-t0:.1f}s")

    # ── Step 2: Train ──────────────────────────────────────────────────────
    print("\n" + "="*60)
    print(" Step 2/4  Train Models (LR + RF + LightGBM)")
    print("="*60)
    t0 = time.time()
    from train_v2 import train_all_models
    train_all_models(config)
    print(f"[pipeline] Done in {time.time()-t0:.1f}s")

    # ── Step 3: Evaluate on validation ────────────────────────────────────
    print("\n" + "="*60)
    print(" Step 3/4  Evaluate on Validation Set")
    print("="*60)
    t0 = time.time()
    from evaluate import evaluate_on_split
    evaluate_on_split("validation", config)
    print(f"[pipeline] Done in {time.time()-t0:.1f}s")

    # ── Step 4 (optional): Evaluate on test ───────────────────────────────
    if args.eval_test:
        print("\n" + "="*60)
        print(" Step 4/4  Evaluate on Held-out Test Set  <- FINAL METRICS")
        print("="*60)
        t0 = time.time()
        evaluate_on_split("test", config)
        print(f"[pipeline] Done in {time.time()-t0:.1f}s")

    print("\nPipeline complete! Run the dashboard with:")
    print("   streamlit run app/streamlit_app.py\n")


if __name__ == "__main__":
    main()
