import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    HF_API_KEY = os.getenv('HF_API_KEY')
    PLOTLY_USERNAME = os.getenv('PLOTLY_USERNAME')
    PLOTLY_API_KEY = os.getenv('PLOTLY_API_KEY')
    
    # Industry benchmarks
    INDUSTRY_BENCHMARKS = {
        'retail': {
            'inventory_days': 45,
            'payment_gap': 15,
            'loops_per_year': 8
        },
        'manufacturing': {
            'inventory_days': 60,
            'payment_gap': 30,
            'loops_per_year': 6
        }
    }