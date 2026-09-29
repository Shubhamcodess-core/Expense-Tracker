#!/usr/bin/env python3
"""
Demo script for ML Expense Analyzer
Shows basic functionality of the ML pipeline
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def main():
    print("=" * 60)
    print("ML Expense Analyzer - Demo")
    print("=" * 60)

    # Check if we have the sample data
    sample_data_path = Path("data/sample_expenses.csv")
    if not sample_data_path.exists():
        print("Sample data not found. Please ensure data/sample_expenses.csv exists.")
        return

    print(f"Found sample data: {sample_data_path}")
    print(f"File size: {sample_data_path.stat().st_size} bytes")

    # Show first few lines of the sample data
    print("\nFirst 5 rows of sample data:")
    with open(sample_data_path, 'r') as f:
        lines = [next(f) for _ in range(5)]
        for i, line in enumerate(lines, 1):
            print(f"{i}: {line.strip()}")

    print("\n" + "=" * 60)
    print("To run the full ML pipeline, execute:")
    print("  python main.py --data data/sample_expenses.csv")
    print("=" * 60)
    print("\nThis will:")
    print("  1. Preprocess the expense data")
    print("  2. Engineer features (time, amount, text, categorical)")
    print("  3. Train multiple ML models (classification, regression, clustering, anomaly detection)")
    print("  4. Evaluate model performance")
    print("  5. Generate comprehensive reports and visualizations")
    print("  6. Save trained models for future use")
    print("\nThe project implements a complete machine learning workflow")
    print("suitable for a 'Machine Learning Major Project' as specified.")
    print("=" * 60)

if __name__ == "__main__":
    main()