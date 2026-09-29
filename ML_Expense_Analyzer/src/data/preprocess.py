import pandas as pd
import numpy as np
import yaml
import os
from pathlib import Path
from typing import Tuple, Optional
import logging
from datetime import datetime
import re


class ExpenseDataPreprocessor:
    """
    Handles loading, cleaning, and preprocessing of expense data
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.required_columns = config['data']['required_columns']
        self.optional_columns = config['data']['optional_columns']
        self.date_format = config['data']['date_format']

    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        Load expense data from CSV file
        """
        self.logger.info(f"Loading data from {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")

        # Try to read CSV with different encodings
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding='latin-1')
            except Exception as e:
                raise RuntimeError(f"Failed to read CSV file {file_path}: {e}")

        self.logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
        return df

    def generate_sample_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """
        Generate sample expense data for demonstration purposes
        """
        self.logger.info(f"Generating {n_samples} sample expense records")

        np.random.seed(42)

        # Generate dates over the past year
        end_date = datetime.now()
        start_date = end_date.replace(year=end_date.year - 1)
        date_strings = pd.date_range(start=start_date, end=end_date, freq='D').strftime('%Y-%m-%d').tolist()

        # Categories and their typical amount ranges
        categories = {
            'Food': (5, 50),
            'Transport': (10, 100),
            'Entertainment': (15, 200),
            'Shopping': (20, 300),
            'Education': (50, 500),
            'Bills': (50, 400),
            'Health': (10, 500),
            'Travel': (100, 1000),
            'Other': (5, 150)
        }

        # Generate some realistic descriptions
        descriptions = {
            'Food': ['Groceries', 'Restaurant', 'Coffee shop', 'Fast food', 'Supermarket'],
            'Transport': ['Gas', 'Public transport', 'Taxi', 'Parking', 'Vehicle maintenance'],
            'Entertainment': ['Movie', 'Concert', 'Streaming service', 'Games', 'Books'],
            'Shopping': ['Clothing', 'Electronics', 'Home goods', 'Online shopping', 'Department store'],
            'Education': ['Courses', 'Books', 'Supplies', 'Online learning', 'Workshop'],
            'Bills': ['Electricity', 'Water', 'Internet', 'Phone', 'Rent'],
            'Health': ['Pharmacy', 'Doctor visit', 'Dentist', 'Gym', 'Insurance'],
            'Travel': ['Flight', 'Hotel', 'Car rental', 'Vacation', 'Travel insurance'],
            'Other': ['Gift', 'Donation', 'Miscellaneous', 'Fees', 'Subscription']
        }

        # Generate data
        data = []
        for _ in range(n_samples):
            category = np.random.choice(list(categories.keys()))
            min_amt, max_amt = categories[category]
            amount = round(np.random.uniform(min_amt, max_amt), 2)
            description = np.random.choice(descriptions[category])
            data.append({
                'date': np.random.choice(date_strings),
                'amount': amount,
                'category': category,
                'description': description,
                'currency': 'USD',
                'payment_method': np.random.choice(['Credit Card', 'Debit Card', 'Cash', 'Bank Transfer'])
            })

        df = pd.DataFrame(data)
        self.logger.info(f"Generated sample data with {len(df)} records")
        return df

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the expense data
        """
        self.logger.info("Starting data preprocessing")

        # Create a copy to avoid modifying original data
        processed_df = df.copy()

        # Validate required columns
        missing_columns = set(self.required_columns) - set(processed_df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Convert date column to datetime
        try:
            processed_df['date'] = pd.to_datetime(processed_df['date'], format=self.date_format)
        except Exception as e:
            self.logger.warning(f"Failed to parse dates with format {self.date_format}: {e}")
            # Try inferring format
            processed_df['date'] = pd.to_datetime(processed_df['date'], infer_datetime_format=True)

        # Ensure amount is numeric
        processed_df['amount'] = pd.to_numeric(processed_df['amount'], errors='coerce')

        # Remove rows with invalid amounts
        initial_count = len(processed_df)
        processed_df = processed_df.dropna(subset=['amount'])
        processed_df = processed_df[processed_df['amount'] >= 0]  # No negative amounts
        removed_count = initial_count - len(processed_df)
        if removed_count > 0:
            self.logger.warning(f"Removed {removed_count} rows with invalid amounts")

        # Clean category column (remove whitespace, standardize)
        if 'category' in processed_df.columns:
            processed_df['category'] = processed_df['category'].astype(str).str.strip()
            # Standardize category names (title case)
            processed_df['category'] = processed_df['category'].str.title()

        # Clean description column
        if 'description' in processed_df.columns:
            processed_df['description'] = processed_df['description'].astype(str).str.strip()
            # Fill empty descriptions
            processed_df['description'] = processed_df['description'].replace('nan', 'No description')

        # Handle currency column
        if 'currency' in processed_df.columns:
            processed_df['currency'] = processed_df['currency'].astype(str).str.strip().str.upper()
            processed_df['currency'] = processed_df['currency'].replace('NAN', 'USD')
            processed_df['currency'] = processed_df['currency'].fillna('USD')

        # Handle payment_method column
        if 'payment_method' in processed_df.columns:
            processed_df['payment_method'] = processed_df['payment_method'].astype(str).str.strip()
            processed_df['payment_method'] = processed_df['payment_method'].replace('nan', 'Unknown')

        # Remove duplicate rows
        initial_count = len(processed_df)
        processed_df = processed_df.drop_duplicates()
        removed_count = initial_count - len(processed_df)
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} duplicate rows")

        # Sort by date
        processed_df = processed_df.sort_values('date').reset_index(drop=True)

        self.logger.info(f"Preprocessing completed. Final dataset: {len(processed_df)} rows")
        return processed_df

    def save_processed_data(self, df: pd.DataFrame, filename: str = "processed_expenses.csv"):
        """
        Save processed data to CSV file
        """
        processed_path = Path(self.config['data']['processed_path'])
        processed_path.mkdir(parents=True, exist_ok=True)

        file_path = processed_path / filename
        df.to_csv(file_path, index=False)
        self.logger.info(f"Saved processed data to {file_path}")

    def load_processed_data(self, filename: str = "processed_expenses.csv") -> pd.DataFrame:
        """
        Load previously processed data
        """
        file_path = Path(self.config['data']['processed_path']) / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Processed data file not found: {file_path}")

        df = pd.read_csv(file_path)
        # Convert date column back to datetime
        df['date'] = pd.to_datetime(df['date'])
        self.logger.info(f"Loaded processed data from {file_path}")
        return df

    def get_data_info(self, df: pd.DataFrame) -> dict:
        """
        Get basic information about the dataset
        """
        info = {
            'shape': df.shape,
            'columns': list(df.columns),
            'data_types': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'date_range': {
                'min': df['date'].min().strftime('%Y-%m-%d') if 'date' in df.columns else None,
                'max': df['date'].max().strftime('%Y-%m-%d') if 'date' in df.columns else None
            },
            'category_distribution': df['category'].value_counts().to_dict() if 'category' in df.columns else {},
            'amount_stats': {
                'mean': df['amount'].mean(),
                'median': df['amount'].median(),
                'std': df['amount'].std(),
                'min': df['amount'].min(),
                'max': df['amount'].max()
            } if 'amount' in df.columns else {}
        }
        return info