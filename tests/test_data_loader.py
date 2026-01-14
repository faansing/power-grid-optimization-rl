"""
Unit tests for Data Loader
"""
import pytest
import numpy as np
import pandas as pd
import os
import yaml
from data.data_loader import PowerDataLoader


@pytest.fixture
def config():
    """Load configuration"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def loader(config):
    """Create data loader instance"""
    return PowerDataLoader(config)


class TestDataLoading:
    """Test data loading functionality"""
    
    def test_loader_initialization(self, loader):
        """Test loader initializes correctly"""
        assert loader is not None
        assert hasattr(loader, 'local_path')
        assert hasattr(loader, 'train_ratio')
    
    def test_load_data_returns_dataframe(self, loader):
        """Test load_data returns DataFrame"""
        df = loader.load_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
    
    def test_data_has_required_columns(self, loader):
        """Test loaded data has required columns"""
        df = loader.load_data()
        assert 'datetime' in df.columns
        assert 'load_mw' in df.columns
    
    def test_data_no_missing_values(self, loader):
        """Test no missing values in critical columns"""
        df = loader.load_data()
        assert df['load_mw'].isna().sum() == 0
    
    def test_data_sorted_by_time(self, loader):
        """Test data is sorted chronologically"""
        df = loader.load_data()
        assert df['datetime'].is_monotonic_increasing


class TestDataSplitting:
    """Test data splitting functionality"""
    
    def test_split_returns_three_sets(self, loader):
        """Test split returns train, val, test"""
        df = loader.load_data()
        train, val, test = loader.split_data(df)
        
        assert isinstance(train, pd.DataFrame)
        assert isinstance(val, pd.DataFrame)
        assert isinstance(test, pd.DataFrame)
    
    def test_split_ratios(self, loader):
        """Test split maintains correct ratios"""
        df = loader.load_data()
        train, val, test = loader.split_data(df)
        
        total = len(train) + len(val) + len(test)
        train_ratio = len(train) / total
        val_ratio = len(val) / total
        test_ratio = len(test) / total
        
        assert abs(train_ratio - loader.train_ratio) < 0.01
        assert abs(val_ratio - loader.val_ratio) < 0.01
        assert abs(test_ratio - loader.test_ratio) < 0.01
    
    def test_splits_non_overlapping(self, loader):
        """Test train/val/test sets don't overlap"""
        df = loader.load_data()
        train, val, test = loader.split_data(df)
        
        # Check timestamps don't overlap
        assert train['datetime'].max() < val['datetime'].min()
        assert val['datetime'].max() < test['datetime'].min()
    
    def test_split_maintains_order(self, loader):
        """Test each split is time-ordered"""
        df = loader.load_data()
        train, val, test = loader.split_data(df)
        
        assert train['datetime'].is_monotonic_increasing
        assert val['datetime'].is_monotonic_increasing
        assert test['datetime'].is_monotonic_increasing


class TestDataQuality:
    """Test data quality checks"""
    
    def test_load_values_positive(self, loader):
        """Test all load values are positive"""
        df = loader.load_data()
        assert (df['load_mw'] > 0).all()
    
    def test_load_values_reasonable(self, loader):
        """Test load values are in reasonable range"""
        df = loader.load_data()
        # Should be between 100-2000 MW for typical systems
        assert df['load_mw'].min() >= 100
        assert df['load_mw'].max() <= 2000
    
    def test_no_duplicate_timestamps(self, loader):
        """Test no duplicate timestamps"""
        df = loader.load_data()
        assert not df['datetime'].duplicated().any()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
