import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# Set page configuration to use the full width of the page
st.set_page_config(layout="wide")

# Load the dataset
file_path = "app_traffic_traffic_202502061131.csv"
df = pd.read_csv(file_path)

# Convert date column to datetime and extract hour
df['date'] = pd.to_datetime(df['date'])
df['hour'] = df['date'].dt.hour

def main():
    # Calculate first and last day of the current month
    today = datetime.date.today()
    first_day_of_month = today.replace(day=1)
    if today.month == 12:
        last_day_of_month = today.replace(day=31)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
        last_day_of_month = next_month - datetime.timedelta(days=1)
    
    # Determine dataset's date range
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    
    # Set default date range to the current month (within dataset's limits)
    default_start = max(first_day_of_month, min_date)
    default_end = min(last_day_of_month, max_date)
    
    # Create a top row with two columns: one for title and one for the date filter
    col_title, col_filter = st.columns([3, 1])
    with col_title:
        st.title("Website Traffic Dashboard")
    with col_filter:
        date_range = st.date_input(
            "Select date range", 
            value=[default_start, default_end],
            min_value=min_date, 
            max_value=max_date
        )
    
    # Validate the date input: if a single date is selected, show an error.
    if len(date_range) == 2:
        start_date, end_date = date_range
        st.session_state.last_valid_range = date_range
        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
        filtered_df = df.loc[mask]
        valid_view = True
    elif len(date_range) == 1:
        st.error("Invalid date range. Please select two dates.")
        valid_view = False
    else:
        filtered_df = df.copy()
        valid_view = True
    
    if valid_view:
        # Calculate current period metrics
        current_total_traffic = filtered_df.shape[0]
        current_total_visitors = filtered_df['session_key'].nunique()
        
        # Calculate the period length (number of days) and determine the previous period
        delta_days = (end_date - start_date).days + 1  # inclusive
        prev_start = start_date - datetime.timedelta(days=delta_days)
        prev_end = start_date - datetime.timedelta(days=1)
        mask_prev = (df['date'].dt.date >= prev_start) & (df['date'].dt.date <= prev_end)
        prev_df = df.loc[mask_prev]
        prev_total_traffic = prev_df.shape[0]
        prev_total_visitors = prev_df['session_key'].nunique()
        
        # Compute delta differences
        delta_traffic = current_total_traffic - prev_total_traffic
        delta_visitors = current_total_visitors - prev_total_visitors
        
        # Layout with two main columns and show st.metric with delta values
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Traffics", current_total_traffic, delta=delta_traffic)
            
            # Traffic by Date
            traffic_by_date = filtered_df.groupby(filtered_df['date'].dt.date).size().reset_index(name='Traffic')
            fig = px.line(traffic_by_date, x='date', y='Traffic', title='Traffic by Date', 
                          markers=True, hover_data={'Traffic': True})
            st.plotly_chart(fig, use_container_width=True)
            
            # Traffic by Hour
            traffic_by_hour = filtered_df.groupby('hour').size().reset_index(name='Traffic')
            fig = px.line(traffic_by_hour, x='hour', y='Traffic', title='Traffic by Hour', 
                          markers=True, hover_data={'Traffic': True})
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.metric("Total Visitors", current_total_visitors, delta=delta_visitors)
            
            # Traffic by Category (ordered descending)
            traffic_category = filtered_df['uri_lvl_0'].value_counts().reset_index()
            traffic_category.columns = ['Category', 'Count']
            traffic_category = traffic_category.sort_values(by='Count', ascending=False)
            fig = px.pie(traffic_category, names='Category', values='Count', title='Traffic by Category', 
                         hover_data=['Count'])
            st.plotly_chart(fig, use_container_width=True)
        
            # Top 10 Pages (ordered descending, then sorted ascending for horizontal bar chart)
            top_pages = filtered_df['uri_title'].value_counts().nlargest(10).reset_index()
            top_pages.columns = ['Page', 'Traffic']
            top_pages = top_pages.sort_values(by='Traffic', ascending=True)
            fig = px.bar(top_pages, x='Traffic', y='Page', orientation='h', title='Top 10 Pages', 
                         hover_data=['Traffic'])
            st.plotly_chart(fig, use_container_width=True)
        
if __name__ == "__main__":
    main()
