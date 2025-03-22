import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim

@st.cache_data
def load_data():
    try:
        # Load data from CSV
        df = pd.read_csv('Global_Cybersecurity_Threats_2015-2024.csv', delimiter=";")
        
        # Debug: Print column names to identify potential issues
        st.write("Columns in the DataFrame:", df.columns.tolist())
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Check if 'Country' column exists
        if 'Country' not in df.columns:
            st.error("The 'Country' column is missing. Please check the CSV file for correct column names.")
            st.stop()
        
        # Convert 'Year' to numeric type
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        
        # Geocoding function to get coordinates
        geolocator = Nominatim(user_agent="cyber_map")
        def get_coords(country):
            try:
                location = geolocator.geocode(country)
                return location.latitude, location.longitude if location else (0, 0)
            except:
                return 0, 0
        
        # Add latitude and longitude columns
        df[['lat', 'lon']] = df['Country'].apply(lambda x: pd.Series(get_coords(x)))
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Load and cache data
df = load_data()

# Main app
st.title("Cybersecurity Incident Dashboard 🌐")
st.sidebar.header("Filter Controls")

# Debugging option to show DataFrame structure
if st.checkbox("Show Debug Info"):
    st.write("DataFrame columns:", df.columns)
    st.write("DataFrame preview:", df.head())

# Create tabs for map and analytics
tab1, tab2 = st.tabs(["World Map Visualization", "Dynamic Analytics"])

with tab1:
    st.header("Global Threat Map")
    
    # Sidebar filters for year range and attack types
    year_range = st.sidebar.slider(
        "Select Year Range",
        min_value=int(df['Year'].min()),
        max_value=int(df['Year'].max()),
        value=(int(df['Year'].min()), int(df['Year'].max()))
    )
    
    attack_types = st.sidebar.multiselect(
        "Select Attack Types",
        options=df['Attack Type'].unique() if 'Attack Type' in df.columns else [],
        default=df['Attack Type'].unique() if 'Attack Type' in df.columns else []
    )
    
    # Filter data based on user selections
    filtered_df = df[
        (df['Year'].between(*year_range)) &
        (df['Attack Type'].isin(attack_types))
    ]
    
    # Display map or warning if no data matches filters
    if not filtered_df.empty:
        st.map(filtered_df, latitude='lat', longitude='lon', use_container_width=True)
    else:
        st.warning("No data matching the selected filters.")

with tab2:
    st.header("Analytical Visualizations")
    
    try:
        # Visualization 1: Financial Loss by Country
        fig1 = px.bar(
            df.groupby('Country', as_index=False)['Financial Loss (in Million $)'].sum(),
            x='Country',
            y='Financial Loss (in Million $)',
            title="Total Financial Loss by Country"
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Visualization 2: Financial Loss vs Affected Users
        fig2 = px.scatter(
            df,
            x='Number of Affected Users',
            y='Financial Loss (in Million $)',
            color='Attack Type',
            size='Incident Resolution Time (in Hours)',
            title="Financial Impact vs User Affection"
        )
        st.plotly_chart(fig2, use_container_width=True)
    except KeyError as e:
        st.error(f"Error creating visualizations: {str(e)}. Please check if all required columns are present in the CSV file.")

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.info("ℹ️ Use the filters to explore cybersecurity incidents globally.")
