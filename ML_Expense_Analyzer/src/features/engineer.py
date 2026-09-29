import pandas as pd
import numpy as np
import yaml
import os
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import logging
from datetime import datetime
import re
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib


class FeatureEngineer:
    """
    Handles feature engineering for expense data
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.feature_config = config['features']
        self.label_encoders = {}
        self.onehot_encoders = {}
        self.scalers = {}
        self.text_vectorizers = {}

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform feature engineering on the expense data
        """
        self.logger.info("Starting feature engineering")

        # Create a copy to avoid modifying original data
        featured_df = df.copy()

        # Ensure date column is datetime
        if 'date' in featured_df.columns and not pd.api.types.is_datetime64_any_dtype(featured_df['date']):
            featured_df['date'] = pd.to_datetime(featured_df['date'])

        # Time-based features
        if 'date' in featured_df.columns:
            featured_df = self._extract_time_features(featured_df)

        # Amount-based features
        if 'amount' in featured_df.columns:
            featured_df = self._extract_amount_features(featured_df)

        # Text-based features (from description)
        if 'description' in featured_df.columns:
            featured_df = self._extract_text_features(featured_df)

        # Categorical features
        categorical_columns = ['category', 'currency', 'payment_method']
        for col in categorical_columns:
            if col in featured_df.columns:
                featured_df = self._encode_categorical_feature(featured_df, col)

        # Interaction features
        featured_df = self._create_interaction_features(featured_df)

        # Remove original columns that were transformed (optional)
        # Keep them for interpretability, but we can mark which are engineered

        self.logger.info(f"Feature engineering completed. Features: {len(featured_df.columns)} columns")
        return featured_df

    def _extract_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract time-based features from date column
        """
        self.logger.info("Extracting time-based features")

        if 'date' not in df.columns:
            return df

        # Basic time features
        df['hour'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.dayofweek  # Monday=0, Sunday=6
        df['day_of_month'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['year'] = df['date'].dt.year

        # Boolean features
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
        df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
        df['is_quarter_start'] = df['date'].dt.is_quarter_start.astype(int)
        df['is_quarter_end'] = df['date'].dt.is_quarter_end.astype(int)

        # Cyclical encoding for periodic features
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

        return df

    def _extract_amount_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract amount-based features
        """
        self.logger.info("Extracting amount-based features")

        if 'amount' not in df.columns:
            return df

        # Log transformation (handles skewness)
        df['log_amount'] = np.log1p(df['amount'])  # log(1+x) to handle zeros

        # Z-score normalization
        amount_mean = df['amount'].mean()
        amount_std = df['amount'].std()
        if amount_std > 0:
            df['amount_zscore'] = (df['amount'] - amount_mean) / amount_std
        else:
            df['amount_zscore'] = 0

        # Rolling statistics (if we have enough data and sorted by date)
        if len(df) >= 7 and 'date' in df.columns:
            df_sorted = df.sort_values('date')
            df['rolling_mean_7d'] = df_sorted['amount'].rolling(window=7, min_periods=1).mean()
            df['rolling_std_7d'] = df_sorted['amount'].rolling(window=7, min_periods=1).std().fillna(0)

        # Expense ratio features (would need income data, placeholder for now)
        # df['expense_ratio_to_income'] = df['amount'] / income_amount  # if income data available

        return df

    def _extract_text_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract text-based features from description column
        """
        self.logger.info("Extracting text-based features")

        if 'description' not in df.columns:
            return df

        # Fill missing descriptions
        df['description'] = df['description'].fillna('').astype(str)

        # Basic text features
        df['description_length'] = df['description'].str.len()
        df['word_count'] = df['description'].str.split().str.len()
        df['has_numbers'] = df['description'].str.contains(r'\d').astype(int)
        df['has_uppercase'] = df['description'].str.contains(r'[A-Z]').astype(int)

        # Sentiment-like features (simple approach)
        positive_words = ['good', 'great', 'excellent', 'happy', 'nice', 'best', 'love', 'like']
        negative_words = ['bad', 'poor', 'terrible', 'hate', 'dislike', 'worst', 'expensive', 'costly']

        df['positive_word_count'] = df['description'].str.lower().apply(
            lambda x: sum(word in x for word in positive_words)
        )
        df['negative_word_count'] = df['description'].str.lower().apply(
            lambda x: sum(word in x for word in negative_words)
        )
        df['sentiment_score'] = df['positive_word_count'] - df['negative_word_count']

        # TF-IDF features (for more advanced text analysis)
        try:
            tfidf_params = {
                'max_features': 100,
                'stop_words': 'english',
                'ngram_range': (1, 2),
                'min_df': 2
            }

            # Only fit TF-IDF if we have sufficient data
            if len(df['description'].unique()) >= 2:
                tfidf_matrix = TfidfVectorizer(**tfidf_params).fit_transform(df['description'])
                tfidf_feature_names = [f'tfidf_{i}' for i in range(tfidf_matrix.shape[1])]
                tfidf_df = pd.DataFrame(
                    tfidf_matrix.toarray(),
                    columns=tfidf_feature_names,
                    index=df.index
                )
                # Concatenate with original dataframe
                df = pd.concat([df, tfidf_df], axis=1)
                self.logger.info(f"Added {tfidf_matrix.shape[1]} TF-IDF features")
            else:
                self.logger.warning("Not enough unique descriptions for TF-IDF vectorization")
        except Exception as e:
            self.logger.warning(f"Failed to create TF-IDF features: {e}")

        return df

    def _encode_categorical_feature(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        Encode categorical features
        """
        self.logger.info(f"Encoding categorical feature: {column}")

        if column not in df.columns:
            return df

        # Fill missing values
        df[column] = df[column].fillna('Unknown').astype(str)

        # Label encoding
        if column not in self.label_encoders:
            self.label_encoders[column] = LabelEncoder()
            df[f'{column}_encoded'] = self.label_encoders[column].fit_transform(df[column])
        else:
            # Handle unseen categories in transform
            unique_values = set(df[column].unique())
            known_values = set(self.label_encoders[column].classes_)
            unknown_values = unique_values - known_values

            if unknown_values:
                # Temporarily add unknown values to encoder
                self.logger.warning(f"Found unknown values in {column}: {unknown_values}")
                # For simplicity, we'll map unknown values to the most frequent class
                # In production, you might want a different strategy
                most_frequent = self.label_encoders[column].classes_[0]
                df[column] = df[column].apply(lambda x: x if x in known_values else most_frequent)

            df[f'{column}_encoded'] = self.label_encoders[column].transform(df[column])

        # One-hot encoding (for tree-based models, label encoding is often sufficient)
        # But we'll create both options
        try:
            if column not in self.onehot_encoders or len(self.onehot_encoders[column].categories_[0]) < 10:
                # Only one-hot encode if cardinality is reasonable
                unique_count = df[column].nunique()
                if unique_count <= 10:  # Threshold for one-hot encoding
                    if column not in self.onehot_encoders:
                        self.onehot_encoders[column] = OneHotEncoder(sparse_output=False, drop='first')
                        encoded_array = self.onehot_encoders[column].fit_transform(df[[column]])
                    else:
                        encoded_array = self.onehot_encoders[column].transform(df[[column]])

                    # Create column names
                    categories = self.onehot_encoders[column].categories_[0]
                    if len(categories) > 1:  # drop_first=True means we drop first category
                        categories = categories[1:]
                    else:
                        categories = []

                    feature_names = [f'{column}_oh_{cat}' for cat in categories]
                    encoded_df = pd.DataFrame(encoded_array, columns=feature_names, index=df.index)
                    df = pd.concat([df, encoded_df], axis=1)
                    self.logger.info(f"Added {len(feature_names)} one-hot encoded features for {column}")
        except Exception as e:
            self.logger.warning(f"Failed to create one-hot encoding for {column}: {e}")

        return df

    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create interaction features between important variables
        """
        self.logger.info("Creating interaction features")

        # Amount and time interactions
        if 'amount' in df.columns and 'month' in df.columns:
            df['amount_month_interaction'] = df['amount'] * df['month']

        if 'amount_zscore' in df.columns and 'is_weekend' in df.columns:
            df['amount_weekend_interaction'] = df['amount_zscore'] * df['is_weekend']

        # Category and amount interactions (if we have encoded category)
        if 'category_encoded' in df.columns and 'amount' in df.columns:
            df['category_amount_interaction'] = df['category_encoded'] * df['amount']

        return df

    def save_featured_data(self, df: pd.DataFrame, filename: str = "featured_expenses.csv"):
        """
        Save featured data to CSV file
        """
        processed_path = Path(self.config['data']['processed_path'])
        processed_path.mkdir(parents=True, exist_ok=True)

        file_path = processed_path / filename
        df.to_csv(file_path, index=False)
        self.logger.info(f"Saved featured data to {file_path}")

    def load_featured_data(self, filename: str = "featured_expenses.csv") -> pd.DataFrame:
        """
        Load previously featured data
        """
        file_path = Path(self.config['data']['processed_path']) / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Featured data file not found: {file_path}")

        df = pd.read_csv(file_path)
        # Convert date column back to datetime if it exists
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        self.logger.info(f"Loaded featured data from {file_path}")
        return df

    def save_encoders(self, filepath: str = "models/encoders.joblib"):
        """
        Save fitted encoders for later use
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        encoders_dict = {
            'label_encoders': self.label_encoders,
            'onehot_encoders': self.onehot_encoders,
            'scalers': self.scalers,
            'text_vectorizers': self.text_vectorizers
        }
        joblib.dump(encoders_dict, filepath)
        self.logger.info(f"Saved encoders to {filepath}")

    def load_encoders(self, filepath: str = "models/encoders.joblib"):
        """
        Load previously fitted encoders
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Encoders file not found: {filepath}")

        encoders_dict = joblib.load(filepath)
        self.label_encoders = encoders_dict['label_encoders']
        self.onehot_encoders = encoders_dict['onehot_encoders']
        self.scalers = encoders_dict['scalers']
        self.text_vectorizers = encoders_dict['text_vectorizers']
        self.logger.info(f"Loaded encoders from {filepath}")

    def get_feature_importance_names(self) -> List[str]:
        """
        Get list of engineered feature names for importance tracking
        """
        # This would typically be computed after feature engineering
        # For now, return common engineered feature names
        engineered_features = [
            'hour', 'day_of_week', 'day_of_month', 'month', 'quarter', 'year',
            'is_weekend', 'is_month_start', 'is_month_end', 'is_quarter_start', 'is_quarter_end',
            'day_of_week_sin', 'day_of_week_cos', 'month_sin', 'month_cos',
            'log_amount', 'amount_zscore', 'rolling_mean_7d', 'rolling_std_7d',
            'description_length', 'word_count', 'has_numbers', 'has_uppercase',
            'positive_word_count', 'negative_word_count', 'sentiment_score'
        ]
        # Add TF-IDF features if they exist
        tfidf_features = [f'tfidf_{i}' for i in range(100)]  # placeholder
        engineered_features.extend(tfidf_features)
        # Add encoded categorical features
        encoded_features = ['category_encoded', 'currency_encoded', 'payment_method_encoded']
        engineered_features.extend(encoded_features)
        # Add one-hot encoded features
        onehot_features = [f'{col}_oh_{cat}' for col in ['category', 'currency', 'payment_method'] for cat in ['A', 'B', 'C']]  # placeholder
        engineered_features.extend(onehot_features)
        # Add interaction features
        interaction_features = [
            'amount_month_interaction', 'amount_weekend_interaction', 'category_amount_interaction'
        ]
        engineered_features.extend(interaction_features)

        return engineered_features