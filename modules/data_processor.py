import pandas as pd
import numpy as np
from fuzzywuzzy import process
from sklearn.ensemble import IsolationForest

class DataProcessor:
    def __init__(self):
        self.required_columns = [
            'units_sold', 'unit_price', 'unit_cost',
            'inventory_days', 'customer_payment_days', 'supplier_payment_days'
        ]
    
    def standardize_columns(self, df):
        """Fuzzy column name matching"""
        standardized = {}
        for col in df.columns:
            match, score = process.extractOne(col.lower(), [x.lower() for x in self.required_columns])
            if score > 70:
                standardized[col] = match
        return df.rename(columns=standardized)
    
    def calculate_metrics(self, df):
        """Compute all business metrics"""
        df['margin_per_unit'] = df['unit_price'] - df['unit_cost']
        df['revenue'] = df['units_sold'] * df['unit_price']
        df['profit'] = df['units_sold'] * df['margin_per_unit']
        df['cash_cycle_days'] = (
            df['inventory_days'] + 
            df['customer_payment_days'] - 
            df['supplier_payment_days']
        )
        df['loops_per_year'] = 365 / df['cash_cycle_days'].clip(lower=1)
        df['revenue_efficiency'] = df['revenue'] / df['cash_cycle_days']
        
        # Anomaly detection
        clf = IsolationForest(contamination=0.1)
        df['anomaly'] = clf.fit_predict(df[self.required_columns])
        
        # Priority scoring
        weights = {
            'revenue_efficiency': 0.4,
            'loops_per_year': 0.3,
            'margin_per_unit': 0.3
        }
        df['priority_score'] = (
            df['revenue_efficiency'] * weights['revenue_efficiency'] +
            df['loops_per_year'] * weights['loops_per_year'] +
            df['margin_per_unit'] * weights['margin_per_unit']
        )
        
        return df