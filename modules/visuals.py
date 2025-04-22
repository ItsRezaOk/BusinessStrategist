import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class Visualizations:
    @staticmethod
    def cash_cycle_sunburst(df):
        fig = px.sunburst(
            df,
            path=['category', 'sku'],
            values='revenue',
            color='cash_cycle_days',
            hover_data=['profit', 'loops_per_year'],
            color_continuous_scale='RdYlGn_r'
        )
        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
        return fig
    
    @staticmethod
    def priority_matrix(df):
        fig = px.scatter(
            df,
            x='loops_per_year',
            y='margin_per_unit',
            size='revenue',
            color='priority_score',
            hover_name='sku',
            labels={
                'loops_per_year': 'Capital Velocity (Loops/Year)',
                'margin_per_unit': 'Unit Margin ($)'
            },
            title='Portfolio Priority Matrix'
        )
        fig.update_traces(
            marker=dict(line=dict(width=1, color='DarkSlateGrey')),
            selector=dict(mode='markers')
        )
        return fig
    
    @staticmethod
    def benchmark_comparison(df, industry):
        fig = make_subplots(rows=1, cols=3, subplot_titles=(
            'Inventory Days', 'Payment Gap', 'Capital Loops'
        ))
        
        # Inventory Days comparison
        fig.add_trace(
            go.Bar(
                x=df['sku'],
                y=df['inventory_days'],
                name='Your Business'
            ),
            row=1, col=1
        )
        fig.add_hline(
            y=industry['inventory_days'],
            line_dash='dot',
            row=1, col=1
        )
        
        # Payment Gap comparison
        payment_gap = df['customer_payment_days'] - df['supplier_payment_days']
        fig.add_trace(
            go.Bar(
                x=df['sku'],
                y=payment_gap,
                name='Payment Gap'
            ),
            row=1, col=2
        )
        fig.add_hline(
            y=industry['payment_gap'],
            line_dash='dot',
            row=1, col=2
        )
        
        # Loops comparison
        fig.add_trace(
            go.Bar(
                x=df['sku'],
                y=df['loops_per_year'],
                name='Capital Loops'
            ),
            row=1, col=3
        )
        fig.add_hline(
            y=industry['loops_per_year'],
            line_dash='dot',
            row=1, col=3
        )
        
        fig.update_layout(height=400, showlegend=False)
        return fig