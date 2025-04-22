import streamlit as st
from prophet import Prophet
import pandas as pd

class InsightsEngine:
    def __init__(self, df):
        self.df = df
    
    def generate_insights(self):
        insights = []
        for _, row in self.df.iterrows():
            insight = {
                'sku': row['sku'],
                'category': row['category'],
                'priority': self._get_priority_level(row['priority_score']),
                'actions': self._generate_actions(row)
            }
            insights.append(insight)
        return insights
    
    def _get_priority_level(self, score):
        if score > 0.7:
            return 'High'
        elif score > 0.4:
            return 'Medium'
        return 'Low'
    
    def _generate_actions(self, row):
        actions = []
        
        # Inventory actions
        if row['inventory_days'] > 45:
            actions.append({
                'type': 'inventory',
                'severity': 'high',
                'action': f"Reduce inventory days from {row['inventory_days']} to under 45",
                'steps': [
                    "Implement just-in-time ordering",
                    "Run promotional campaigns",
                    "Optimize reorder points"
                ]
            })
        
        # Margin actions
        if row['margin_per_unit'] < 1:
            actions.append({
                'type': 'margin',
                'severity': 'critical',
                'action': f"Increase margin from ${row['margin_per_unit']:.2f} to >$1.00",
                'steps': [
                    "Negotiate with suppliers",
                    "Bundle with higher-margin items",
                    "Implement value-added features"
                ]
            })
        
        # Payment gap actions
        payment_gap = row['customer_payment_days'] - row['supplier_payment_days']
        if payment_gap > 20:
            actions.append({
                'type': 'payments',
                'severity': 'medium',
                'action': f"Reduce payment gap from {payment_gap} days to <20",
                'steps': [
                    "Offer early payment discounts",
                    "Extend supplier terms",
                    "Consider invoice factoring"
                ]
            })
        
        return actions
    
    def generate_cash_flow_forecast(self):
        try:
            # Prepare data for Prophet
            df_prophet = pd.DataFrame({
                'ds': pd.date_range(start='2023-01-01', periods=12, freq='M'),
                'y': np.linspace(
                    self.df['revenue'].sum() / 12,
                    self.df['revenue'].sum() / 12 * 1.2,
                    12
                )
            })
            
            model = Prophet()
            model.fit(df_prophet)
            future = model.make_future_dataframe(periods=6, freq='M')
            forecast = model.predict(future)
            
            return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        except Exception as e:
            st.error(f"Forecast failed: {str(e)}")
            return None