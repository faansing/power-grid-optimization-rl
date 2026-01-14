"""
数据预处理模块 - 特征工程和数据增强
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class PowerDataPreprocessor:
    """电力数据预处理器"""
    
    def __init__(self, window_size: int = 24):
        """
        初始化预处理器
        
        Args:
            window_size: 历史窗口大小（小时）
        """
        self.window_size = window_size
        self.scaler = StandardScaler()
        self.load_mean = None
        self.load_std = None
        
    def extract_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        提取时间相关特征
        
        Args:
            df: 输入DataFrame（必须包含datetime列）
            
        Returns:
            添加了时间特征的DataFrame
        """
        df = df.copy()
        
        # 基础时间特征
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.dayofweek
        df['day_of_month'] = df['datetime'].dt.day
        df['month'] = df['datetime'].dt.month
        df['quarter'] = df['datetime'].dt.quarter
        
        # 周期性编码（使用sin/cos避免突变）
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # 布尔特征
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_peak_hour'] = ((df['hour'] >= 9) & (df['hour'] <= 21)).astype(int)
        df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
        
        # 季节（简化版）
        df['is_summer'] = ((df['month'] >= 6) & (df['month'] <= 8)).astype(int)
        df['is_winter'] = ((df['month'] == 12) | (df['month'] <= 2)).astype(int)
        
        return df
    
    def extract_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        提取统计特征
        
        Args:
            df: 输入DataFrame
            
        Returns:
            添加了统计特征的DataFrame
        """
        df = df.copy()
        
        # 滚动统计特征
        for window in [24, 168]:  # 24小时、7天
            df[f'load_ma_{window}'] = df['load_mw'].rolling(window=window, min_periods=1).mean()
            df[f'load_std_{window}'] = df['load_mw'].rolling(window=window, min_periods=1).std()
            df[f'load_min_{window}'] = df['load_mw'].rolling(window=window, min_periods=1).min()
            df[f'load_max_{window}'] = df['load_mw'].rolling(window=window, min_periods=1).max()
        
        # 填充初始NaN（使用全局统计）
        for col in df.columns:
            if df[col].isna().any():
                df[col] = df[col].fillna(df[col].mean())
        
        # 趋势特征
        df['load_diff_1h'] = df['load_mw'].diff(1).fillna(0)
        df['load_diff_24h'] = df['load_mw'].diff(24).fillna(0)
        
        # 相对位置特征
        df['load_vs_daily_avg'] = df['load_mw'] / (df['load_ma_24'] + 1e-6)
        df['load_vs_weekly_avg'] = df['load_mw'] / (df['load_ma_168'] + 1e-6)
        
        return df
    
    def create_forecast_features(self, df: pd.DataFrame, horizon: int = 4) -> pd.DataFrame:
        """
        创建预测特征（历史窗口）
        
        Args:
            df: 输入DataFrame
            horizon: 预测视野（小时）
            
        Returns:
            添加了预测特征的DataFrame
        """
        df = df.copy()
        
        # 历史负荷特征
        for lag in [1, 2, 4, 24, 168]:
            df[f'load_lag_{lag}'] = df['load_mw'].shift(lag)
        
        # 填充初始NaN
        df = df.bfill()
        
        return df
    
    def normalize_data(self, df: pd.DataFrame, fit: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """
        数据标准化
        
        Args:
            df: 输入DataFrame
            fit: 是否fit scaler（训练集为True，验证/测试集为False）
            
        Returns:
            (标准化后的DataFrame, 标准化参数字典)
        """
        df = df.copy()
        
        if fit:
            self.load_mean = df['load_mw'].mean()
            self.load_std = df['load_mw'].std()
        
        # 保存标准化参数
        norm_params = {
            'load_mean': self.load_mean,
            'load_std': self.load_std
        }
        
        return df, norm_params
    
    def process(self, df: pd.DataFrame, fit: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """
        完整的预处理流程
        
        Args:
            df: 输入DataFrame
            fit: 是否为训练集
            
        Returns:
            (处理后的DataFrame, 元数据)
        """
        logger.info(f"Starting data preprocessing (fit={fit})...")
        
        # 1. 提取时间特征
        df = self.extract_time_features(df)
        logger.info(f"  Time feature extraction complete")
        
        # 2. 提取统计特征
        df = self.extract_statistical_features(df)
        logger.info(f"  Statistical feature extraction complete")
        
        # 3. 创建预测特征
        df = self.create_forecast_features(df)
        logger.info(f"  Forecast feature creation complete")
        
        # 4. 标准化
        df, norm_params = self.normalize_data(df, fit=fit)
        logger.info(f"  Data normalization complete")
        
        logger.info(f"Preprocessing complete: {len(df)} records, {len(df.columns)} features")
        
        return df, norm_params


def prepare_data_for_environment(df: pd.DataFrame, start_idx: int, episode_length: int) -> np.ndarray:
    """
    为强化学习环境准备episode数据
    
    Args:
        df: 预处理后的完整DataFrame
        start_idx: episode起始索引
        episode_length: episode长度（小时）
        
    Returns:
        episode的负荷序列 (numpy array)
    """
    end_idx = min(start_idx + episode_length, len(df))
    episode_data = df.iloc[start_idx:end_idx]['load_mw'].values
    
    # 如果不足episode_length，用最后一个值填充
    if len(episode_data) < episode_length:
        padding = np.full(episode_length - len(episode_data), episode_data[-1])
        episode_data = np.concatenate([episode_data, padding])
    
    return episode_data


if __name__ == "__main__":
    # 测试代码
    import yaml
    from data_loader import PowerDataLoader
    
    with open('../config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 加载数据
    loader = PowerDataLoader(config)
    df = loader.load_data()
    train_df, val_df, test_df = loader.split_data(df)
    
    # 预处理
    preprocessor = PowerDataPreprocessor()
    train_processed, norm_params = preprocessor.process(train_df, fit=True)
    
    print("\nFeatures after preprocessing:")
    print(train_processed.columns.tolist())
    print(f"\nData shape: {train_processed.shape}")
    print(f"\nFirst 5 rows:")
    print(train_processed.head())
    
    print("\nData preprocessing test complete!")
