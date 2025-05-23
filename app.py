import streamlit as st #Main Streamlit app
import pandas as pd  #Read uploads to CSV- Store, pass, clean data
import numpy as np #np.linspace for forecasting
from datetime import datetime
from config import Config
from modules.data_processor import DataProcessor
from modules.visuals import Visualizations
from modules.insights_engine import InsightsEngine
import requests
import io
import json

# Initialize configuration
config = Config()

# Set page config
st.set_page_config(
    page_title="ProductVelocity - Capital Flow Optimizer", 
    layout="wide",
    page_icon="🚀"
)

# Initialize session state
if 'data' not in st.session_state: #App cached
    st.session_state.data = None
if 'industry' not in st.session_state:
    st.session_state.industry = 'retail'

# Initialize modules
data_processor = DataProcessor() #Business logic
visuals = Visualizations() #Chart Tools

# --- UI Components ---
def show_onboarding_tour():
    tour_steps = [
        {"title": "Welcome", "content": "This tool helps optimize your capital flow through data analysis"},
        {"title": "Data Input", "content": "Upload your data or generate sample data"},
        {"title": "Analysis", "content": "View key metrics and visualizations"},
        {"title": "Insights", "content": "Get actionable recommendations"}
    ]

    if st.checkbox("Show onboarding tour", True):
        with st.expander("Getting Started Tour"):
            for step in tour_steps:
                st.subheader(step['title'])
                st.write(step['content'])
                st.write("---")

def normalize_columns(df):
    # First pass normalization
    df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns] #Help organize columns
    
    # Specific column mappings
    column_mappings = {
        'sku': 'sku',
        'category': 'category',
        'inventorydays': 'inventory_days',
        'unitssold': 'units_sold',
        'unitcost': 'unit_cost',
        'unitprice': 'unit_price',
        'customerpaymentdays': 'customer_payment_days',
        'supplierpaymentdays': 'supplier_payment_days'
    }
    
    # Apply specific mappings
    for original, new in column_mappings.items():
        if original in df.columns and new not in df.columns:
            df.rename(columns={original: new}, inplace=True)
    
    return df

def data_upload_section():
    st.header("Data Input")

    col1, col2 = st.columns(2) #creates 2 columns

    with col1:
        st.subheader("Upload Your Data")
        uploaded_file = st.file_uploader(
            "Upload CSV file", 
            type="csv",
            help="Upload your business data in CSV format"
        )

        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                df = normalize_columns(df)  #Lowercase and consistent columns
                df = data_processor.standardize_columns(df)
                df = data_processor.calculate_metrics(df)
                st.session_state.data = df
                st.success("Data processed successfully!")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

                

    with col2:
        st.subheader("Generate Sample Data") # Generated with Mixtral-8x7B (from Hugging Face)
        business_idea = st.text_input(
            "Describe your business",
            placeholder="e.g., Organic Coffee Roastery"
        )

        if st.button("Generate with AI") and business_idea: #button pressed and business_data is populated
            with st.spinner("Generating sample data..."):
                try:
                    headers = {"Authorization": f"Bearer {config.HF_API_KEY}"}
                    payload = {
                       #MAIN PROMPT
                       #Models output CSV, avoids getting unnessary text from the LLM, column asked are only what is expected
                        "inputs": f"Generate 5 sample product rows for a {business_idea} business with: sku, category, inventory_days, units_sold, unit_cost, unit_price, customer_payment_days, supplier_payment_days. Return only CSV."
                    }
                    #Call Hugging Face API - send POST with prompt and auth
                    #points to Mixtral endpoint
                    response = requests.post(
                        "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
                        headers=headers,
                        json=payload
                    )

                    if response.status_code == 200: #if success
                        result = response.json() #load json
                        
                        #Ensures data is in the format we want and Mixtral didnt give like a sentence
                        if isinstance(result, list) and 'generated_text' in result[0]: #no empty {} json
                            result = result[0]['generated_text'] #API needs to return a list
                        else:
                            st.error("AI model returned unexpected format.")
                            st.stop()

                        st.subheader("Raw AI Output")
                        st.text_area("Check if the result is valid CSV:", result, height=200)
                        

                        #Result trimming, add more if needed or if more efficient
                        result = result.strip() 
                        if result.startswith("Generate"):
                            result = result[result.find("\n")+1:]

                        df_sample = pd.read_csv(io.StringIO(result)) #Converts result to an in-memory file, reads with pandas
                        df_sample = normalize_columns(df_sample)

                        numeric_cols = ['inventory_days', 'units_sold', 'unit_cost', 'unit_price', 'customer_payment_days', 'supplier_payment_days']
                        for col in numeric_cols: #Columns must be numbers and not strings
                            if col in df_sample.columns:
                                df_sample[col] = pd.to_numeric(df_sample[col], errors='coerce') #takes a col, tries to convert to int/fl using pandas, stores back in col
                        
                        #Finalizes AI data to match uploaded
                        df_sample = data_processor.standardize_columns(df_sample)
                        df_sample = data_processor.calculate_metrics(df_sample)

                        st.session_state.data = df_sample #Store result in memory
                        st.success("Sample data generated!")
                        st.dataframe(df_sample.head())
                    else:
                        st.error(f"Failed to generate data. Status code: {response.status_code}")
                        st.text_area("Raw API response", response.text, height=200)
                        st.stop()
                except Exception as e:
                    st.error(f"Generation error: {str(e)}")



def analysis_dashboard():
    if st.session_state.data is None: #dont proceed unless data exists
        st.warning("Upload or generate data to begin analysis")
        return

    df = st.session_state.data #df - generated or uploaded data

    required_columns = {'category', 'inventory_days', 'units_sold', 'unit_cost', 
                       'unit_price', 'customer_payment_days', 'supplier_payment_days'}
    missing = required_columns - set(df.columns.str.lower()) #check if we have the right amount of columns
    if missing:
        st.error(f"Missing required columns: {missing}") #since every metric depends on all these columns, if missing -> error
        st.write("Current columns:", df.columns.tolist())
        return

    st.header("Analysis Dashboard")

    # Industry selection
    st.session_state.industry = st.selectbox( # dropdown list for industries
        "Select your industry for benchmarking",
        options=list(config.INDUSTRY_BENCHMARKS.keys()) #Industry benchmarks are just benchmarks for now but will be changed with professional data later

    )

    # Key metrics
    st.subheader("Key Metrics")
    col1, col2, col3 = st.columns(3) #Horizontal boxes for metric display
    with col1:
        st.metric("Total Revenue", f"${df['revenue'].sum():,.2f}")
    with col2:
        st.metric("Avg Cash Cycle", f"{df['cash_cycle_days'].mean():.1f} days")
    with col3:
        st.metric("Capital Loops/Year", f"{df['loops_per_year'].mean():.1f}x")

    # Visualizations
    st.subheader("Portfolio Analysis")
    tab1, tab2, tab3 = st.tabs(["Sunburst View", "Priority Matrix", "Benchmarks"])


    # See which products/categories contribute the most revenue and which are bottlenecks
    with tab1:
        st.plotly_chart( #uses plotly sunburst to show Outer: SKU, inner: category, Color: cash_cycle_days, Size: revanue
            visuals.cash_cycle_sunburst(df),
            use_container_width=True
        )

    #What is most worth your attention?
    with tab2:
        st.plotly_chart( #uses plotly bubble chart to 
            visuals.priority_matrix(df),
            use_container_width=True
        )


    #chart compares your actual metrics to the industry benchmark
    with tab3:
        st.plotly_chart( #inverntory days, Payment gaps, Capital loops/year
            visuals.benchmark_comparison(
                df,
                config.INDUSTRY_BENCHMARKS[st.session_state.industry]
            ),
            use_container_width=True
        )

    # Scenario modeling 
    #What IF you Improve
    st.subheader("Scenario Modeling")
    with st.expander("Adjust Parameters"):
        col1, col2 = st.columns(2)
        
        #inv_reduction = 5 means: simulate optimizing your supply chain so inventory sits for 5 fewer days
        #payment_improvement = 5 means: simulate customers paying 5 days faster
        with col1:
            inv_reduction = st.slider("Reduce Inventory Days By", 0, 30, 5, help="Simulate inventory optimization")
        with col2:
            payment_improvement = st.slider("Improve Customer Payment Days By",0, 30, 5,help="Simulate better payment terms")

        # Apply scenario
        scenario_df = df.copy()

        # Ensure these columns (with new changes) are numeric
        scenario_df['inventory_days'] = pd.to_numeric(scenario_df['inventory_days'], errors='coerce')
        scenario_df['customer_payment_days'] = pd.to_numeric(scenario_df['customer_payment_days'], errors='coerce')

        scenario_df['inventory_days'] = scenario_df['inventory_days'] - inv_reduction
        scenario_df['customer_payment_days'] = scenario_df['customer_payment_days'] - payment_improvement

        scenario_df = data_processor.calculate_metrics(scenario_df)

        delta_revenue = scenario_df['revenue'].sum() - df['revenue'].sum()
        delta_loops = scenario_df['loops_per_year'].mean() - df['loops_per_year'].mean()


        #Compare results
        st.metric("Projected Revenue Impact", 
                 f"${scenario_df['revenue'].sum():,.2f}",
                 f"{delta_revenue:,.2f}")
        st.metric("Projected Capital Velocity",
                 f"{scenario_df['loops_per_year'].mean():.1f}x",
                 f"{delta_loops:.1f}x")

def insights_section():
    if st.session_state.data is None:
        return

    df = st.session_state.data
    insights_engine = InsightsEngine(df) #Takes a data frame and collect insights by creating a dictionay(organized)

    st.header("Insights")

    # Generate and display insights
    insights = insights_engine.generate_insights()

    for insight in insights:
        with st.expander(f"{insight['sku']} ({insight['category']}) - Priority: {insight['priority']}"):
            if not insight['actions']:
                st.info("No critical issues detected for this SKU")
                continue

            for action in insight['actions']:
                if action['severity'] == 'critical':
                    container = st.error
                elif action['severity'] == 'high':
                    container = st.warning
                else:
                    container = st.info

                container(f"**{action['action']}**")
                st.write("**Steps:**")
                for step in action['steps']:
                    st.write(f"- {step}")

    # Cash flow forecast
    st.subheader("Cash Flow Forecast")
    forecast = insights_engine.generate_cash_flow_forecast()
    if forecast is not None:
        import plotly.express as px
        fig = px.line(
            forecast,
            x='ds',
            y='yhat',
            title="6-Month Revenue Forecast",
            labels={'ds': 'Date', 'yhat': 'Revenue'}
        )
        fig.add_scatter(
            x=forecast['ds'],
            y=forecast['yhat_upper'],
            mode='lines',
            line=dict(color='gray', dash='dash'),
            name='Upper Bound'
        )
        fig.add_scatter(
            x=forecast['ds'],
            y=forecast['yhat_lower'],
            mode='lines',
            line=dict(color='gray', dash='dash'),
            name='Lower Bound'
        )
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
