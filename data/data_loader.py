"""
Data Loading and Processing Module
Handles data ingestion, preprocessing, and splitting for the power grid environment.
"""

import pandas as pd
import numpy as np
import os
import requests
import logging
from typing import Tuple, Optional, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PowerDataLoader:
    """
    Handles loading, preprocessing, and splitting of power grid load data.
    """

    def __init__(self, config: Dict):
        """
        Initialize the data loader.

        Args:
            config: Configuration dictionary containing data paths and parameters.
        """
        self.config = config['data']
        self.dataset_url = self.config.get('dataset_url', '')
        self.local_path = self.config['local_path']
        self.train_ratio = self.config.get('train_ratio', 0.7)
        self.val_ratio = self.config.get('val_ratio', 0.15)
        self.test_ratio = self.config.get('test_ratio', 0.15)

    def download_data(self) -> None:
        """
        Download the dataset if it does not exist locally.
        Falls back to synthetic data generation if download fails.
        """
        os.makedirs(os.path.dirname(self.local_path), exist_ok=True)

        if os.path.exists(self.local_path):
            logger.info(f"Data file already exists: {self.local_path}")
            return

        logger.info(f"Downloading data from: {self.dataset_url}")
        try:
            response = requests.get(self.dataset_url, timeout=30)
            response.raise_for_status()

            with open(self.local_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Data download complete: {self.local_path}")
        except Exception as e:
            logger.error(f"Data download failed: {e}")
            logger.warning("Falling back to synthetic data generation.")
            self._create_synthetic_data()

    def _create_synthetic_data(self) -> None:
        """
        Generate synthetic load data for testing/fallback purposes.
        Simulates daily and seasonal patterns.
        """
        logger.info("Generating synthetic data...")
        dates = pd.date_range(start='2020-01-01', end='2021-12-31', freq='h')
        n = len(dates)

        # Base load + Daily Pattern + Seasonal Pattern + Random Noise
        base_load = 2500
        daily_pattern = 500 * np.sin(2 * np.pi * dates.hour / 24)
        seasonal_pattern = 1000 * np.sin(2 * np.pi * dates.dayofyear / 365)
        noise = np.random.normal(0, 100, n)

        load = base_load + daily_pattern + seasonal_pattern + noise
        
        # Ensure non-negative load
        load = np.maximum(load, 0)

        df = pd.DataFrame({'timestamp': dates, 'load_mw': load})
        df.to_csv(self.local_path, index=False)
        logger.info(f"Synthetic data saved to {self.local_path}")

    def load_data(self) -> pd.DataFrame:
        """
        Load and preprocess the data.
        
        Returns:
            pd.DataFrame: DataFrame containing 'timestamp' and 'load_mw' columns.
        """
        self.download_data()

        try:
            df = pd.read_csv(self.local_path)
            
            # Standardize column names
            if 'load_mw' not in df.columns:
                # Attempt to identify the load column (assuming single value column for simplicity)
                # In a real scenario, this would be more specific
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    df.rename(columns={numeric_cols[0]: 'load_mw'}, inplace=True)
                else:
                    raise ValueError("Could not identify load column.")

            # Ensure timestamp processing
            if 'timestamp' in df.columns:
                 df['datetime'] = pd.to_datetime(df['timestamp'])
            elif 'Date' in df.columns:
                 df['datetime'] = pd.to_datetime(df['Date'])
            
            # Simple missing value handling
            df['load_mw'] = df['load_mw'].interpolate(method='linear')
            
            # Select and sort
            if 'datetime' in df.columns:
                df = df.sort_values('datetime').reset_index(drop=True)
                logger.info(f"Data loaded successfully. Shape: {df.shape}")
                return df[['datetime', 'load_mw']]
            else:
                raise ValueError("Could not identify datetime column")

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def split_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into training, validation, and test sets.

        Args:
            df: The full dataset DataFrame.

        Returns:
            Tuple containing (train_df, val_df, test_df).
        """
        n = len(df)
        train_end = int(n * self.config['train_ratio'])
        val_end = int(n * (self.config['train_ratio'] + self.config['val_ratio']))

        train_df = df.iloc[:train_end].copy()
        val_df = df.iloc[train_end:val_end].copy()
        test_df = df.iloc[val_end:].copy()

        logger.info(f"Data split - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
        return train_df, val_df, test_df
