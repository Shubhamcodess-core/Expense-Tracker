#!/usr/bin/env python3
"""
Main execution script for ML Expense Analyzer
Orchestrates the complete machine learning pipeline
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from utils.logger import setup_logging
from utils.config import load_config
from data.preprocess import ExpenseDataPreprocessor
from features.engineer import FeatureEngineer
from models.trainer import ModelTrainer
from models.evaluator import ModelEvaluator
from reports.generator import ReportGenerator

def setup_directories():
    """Create necessary directory structure"""
    directories = [
        "data/raw",
        "data/processed",
        "data/external",
        "models",
        "notebooks",
        "reports",
        "reports/plots",
        "reports/predictions",
        "logs"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def main():
    """Main function to run the ML pipeline"""
    parser = argparse.ArgumentParser(description="ML Expense Analyzer Pipeline")
    parser.add_argument(
        "--skip-preprocess",
        action="store_true",
        help="Skip data preprocessing step"
    )
    parser.add_argument(
        "--skip-training",
        action="store_true",
        help="Skip model training step"
    )
    parser.add_argument(
        "--skip-evaluation",
        action="store_true",
        help="Skip model evaluation step"
    )
    parser.add_argument(
        "--skip-reporting",
        action="store_true",
        help="Skip report generation step"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--data",
        type=str,
        help="Path to input expense data CSV file"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting ML Expense Analyzer Pipeline")

    try:
        # Load configuration
        config = load_config(args.config)
        logger.info(f"Loaded configuration from {args.config}")

        # Setup directories
        setup_directories()

        # Step 1: Data Preprocessing
        if not args.skip_preprocess:
            logger.info("Step 1: Data Preprocessing")
            preprocessor = ExpenseDataPreprocessor(config)

            if args.data:
                logger.info(f"Loading data from {args.data}")
                raw_data = preprocessor.load_data(args.data)
            else:
                logger.info("Generating sample expense data for demonstration")
                raw_data = preprocessor.generate_sample_data()

            processed_data = preprocessor.preprocess(raw_data)
            preprocessor.save_processed_data(processed_data)
            logger.info("Data preprocessing completed")
        else:
            logger.info("Skipping data preprocessing")
            # Load existing processed data
            preprocessor = ExpenseDataPreprocessor(config)
            processed_data = preprocessor.load_processed_data()

        # Step 2: Feature Engineering
        logger.info("Step 2: Feature Engineering")
        feature_engineer = FeatureEngineer(config)
        featured_data = feature_engineer.engineer_features(processed_data)
        feature_engineer.save_featured_data(featured_data)
        logger.info("Feature engineering completed")

        # Step 3: Model Training
        if not args.skip_training:
            logger.info("Step 3: Model Training")
            trainer = ModelTrainer(config)
            trained_models = trainer.train_all_models(featured_data)
            trainer.save_models(trained_models)
            logger.info("Model training completed")
        else:
            logger.info("Skipping model training")
            # Load existing models
            trainer = ModelTrainer(config)
            trained_models = trainer.load_models()

        # Step 4: Model Evaluation
        if not args.skip_evaluation:
            logger.info("Step 4: Model Evaluation")
            evaluator = ModelEvaluator(config)
            evaluation_results = evaluator.evaluate_models(trained_models, featured_data)
            evaluator.save_evaluation_results(evaluation_results)
            logger.info("Model evaluation completed")
        else:
            logger.info("Skipping model evaluation")
            evaluator = ModelEvaluator(config)
            evaluation_results = evaluator.load_evaluation_results()

        # Step 5: Report Generation
        if not args.skip_reporting:
            logger.info("Step 5: Report Generation")
            report_generator = ReportGenerator(config)
            report_generator.generate_comprehensive_report(
                processed_data,
                featured_data,
                trained_models,
                evaluation_results
            )
            logger.info("Report generation completed")
        else:
            logger.info("Skipping report generation")

        logger.info("ML Expense Analyzer Pipeline completed successfully!")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()