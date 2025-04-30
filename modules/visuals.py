import plotly.express as px #quick charts, minimal config
import plotly.graph_objects as go #more flexible for bar charts and lines
from plotly.subplots import make_subplots #Combining multiple charts into one layout

class Visualizations:
    
    #See how product categories contribute to revenue + where cash is stuck
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
        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0)) #removes excess margina nd padding
        return fig
    
    #Rank SKUs visually by revenue, profit margin, and capital efficiency
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
        fig.update_traces( #adds a dark border around each bubble
            marker=dict(line=dict(width=1, color='DarkSlateGrey')),
            selector=dict(mode='markers')
        )
        return fig
    
    #Compare your business vs. industry averages for inventory, payment gap, and loops
    @staticmethod
    def benchmark_comparison(df, industry):
        fig = make_subplots(rows=1, cols=3, subplot_titles=(
            'Inventory Days', 'Payment Gap', 'Capital Loops'
        ))
        
        # Inventory Days comparison
        fig.add_trace( #Plots each SKU’s inventory days
            go.Bar(
                x=df['sku'],
                y=df['inventory_days'],
                name='Your Business'
            ),
            row=1, col=1
        )
        fig.add_hline( #Draws a dotted horizontal line representing the industry average
            y=industry['inventory_days'],
            line_dash='dot',
            row=1, col=1
        )
        
        # Payment Gap comparison
        #Plots how long it takes each SKU to collect money after paying suppliers
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
        # Shows how many times per year your capital is being reinvested per SKU
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
        
        #Final layout keeps things compact and removes legend (each bar already labeled by SKU)
        fig.update_layout(height=400, showlegend=False)
        return fig