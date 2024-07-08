import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from scipy.stats import gaussian_kde
from sklearn.cluster import DBSCAN

class SupportResistanceIdentifier:
    def __init__(self, params):
        self.window = int(params.get('window', 20))
        self.touch_threshold = params.get('price_threshold', 0.001)
        self.kde_bandwidth = params.get('kde_bandwidth', 0.01)
        self.eps = params.get('eps', 0.01)
        self.min_samples = params.get('min_samples', 3)
        self.support_levels = {}
        self.resistance_levels = {}
        self.last_processed_index = 0
        self.dbscan_interval = params.get('dbscan_interval', 100)
        self.kde_interval = params.get('kde_interval', 500)
        self.df = None

    def initialize_with_historical_data(self, historical_df):
        """
        Initialize the identifier with historical data.
        This method should be called once with the full historical dataset.
        """
        self.df = historical_df
        chunk_size = 1000  # Process data in chunks to avoid memory issues
        
        for start in range(0, len(self.df), chunk_size):
            end = min(start + chunk_size, len(self.df))
            self._vectorized_process(start, end)
            
            if end % self.dbscan_interval == 0:
                self._apply_dbscan()
            if end % self.kde_interval == 0:
                self._apply_kde()
        
        self.last_processed_index = len(self.df)
        return self.support_levels, self.resistance_levels

    def identify_levels(self, new_data=None):
        """
        Identify levels based on new data or update existing levels.
        If new_data is provided, it's treated as incremental data.
        If new_data is None, it processes any unprocessed data in the existing dataframe.
        """
        if new_data is not None:
            self.df = pd.concat([self.df, new_data])
        
        start_index = self.last_processed_index
        end_index = len(self.df)
        
        if end_index > start_index:
            self._vectorized_process(start_index, end_index)
            
            if end_index % self.dbscan_interval == 0:
                self._apply_dbscan()
            if end_index % self.kde_interval == 0:
                self._apply_kde()
            
            self.last_processed_index = end_index
        
        return self.support_levels, self.resistance_levels

    def _vectorized_process(self, start_index, end_index):
        if end_index - start_index < self.window:
            return  # Not enough new data

        # Create rolling window views
        high_rolling = self.df['High'].rolling(window=self.window)
        low_rolling = self.df['Low'].rolling(window=self.window)

        # Identify local extrema
        highs = high_rolling.apply(lambda x: x.iloc[-1] == x.max())
        lows = low_rolling.apply(lambda x: x.iloc[-1] == x.min())

        # Get the prices of the extrema
        high_prices = self.df.loc[highs & (self.df.index >= start_index), 'High']
        low_prices = self.df.loc[lows & (self.df.index >= start_index), 'Low']

        # Process support levels
        self._process_levels(low_prices, self.support_levels, is_support=True)

        # Process resistance levels
        self._process_levels(high_prices, self.resistance_levels, is_support=False)

    def _process_levels(self, prices, levels, is_support):
        for index, price in prices.iteritems():
            if price not in levels:
                levels[price] = {'touches': 1, 'breaks': 0, 'last_touch': index}
            else:
                current_price = self.df.loc[index, 'Close']
                if is_support:
                    if current_price < price * (1 - self.touch_threshold):
                        levels[price]['breaks'] += 1
                    elif price * (1 - self.touch_threshold) <= current_price <= price:
                        levels[price]['touches'] += 1
                        levels[price]['last_touch'] = index
                else:
                    if current_price > price * (1 + self.touch_threshold):
                        levels[price]['breaks'] += 1
                    elif price <= current_price <= price * (1 + self.touch_threshold):
                        levels[price]['touches'] += 1
                        levels[price]['last_touch'] = index

    # ... (rest of the methods remain the same: _apply_dbscan, _cluster_levels, _apply_kde, _smooth_levels, get_active_levels)
