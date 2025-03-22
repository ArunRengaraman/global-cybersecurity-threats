import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim

# Sample Data
data = pd.read_csv('Global_Cybersecurity_Threats_2015-2024.csv', delimiter=";")

@st.cache_data
def load_data():
    df = pd.DataFrame(data)
    
    # Geocoding function to get coordinates
    geolocator = Nominatim(user_agent="cyber_map")
    def get_coords(country):
        try:
            location = geolocator.geocode(country)
            return location.latitude, location.longitude
        except:
            return 0, 0  # Default coordinates
    
    df[['lat', 'lon']] = df['Country'].apply(
        lambda x: pd.Series(get_coords(x))
    )
    return df

# Load and cache data
df = load_data()

# Main app
st.title("Cybersecurity Incident Dashboard 🌐")
st.sidebar.header("Filter Controls")

# Create tabs
tab1, tab2 = st.tabs(["World Map Visualization", "Dynamic Analytics"])

with tab1:
    st.header("Global Threat Map")
    
    # Map filters
    year_range = st.sidebar.slider(
        "Select Year Range",
        min_value=2017,
        max_value=2024,
        value=(2017, 2024)
    )
    
    attack_types = st.sidebar.multiselect(
        "Select Attack Types",
        options=df['Attack Type'].unique(),
        default=df['Attack Type'].unique()
    )
    
    # Filter data
    filtered_df = df[
        (df['Year'].between(*year_range)) &
        (df['Attack Type'].isin(attack_types))
    ]
    
    # Display map
    if not filtered_df.empty:
        st.map(filtered_df,
               latitude='lat',
               longitude='lon',
               size='Financial Loss (in Million $)',
               color='#FF0000',
               use_container_width=True)
    else:
        st.warning("No data matching the selected filters")

with tab2:
    st.header("Analytical Visualizations")
    
    # Visualization 1: Financial Loss by Country
    fig1 = px.bar(
        df.groupby('Country', as_index=False)['Financial Loss (in Million $)'].sum(),
        x='Country',
        y='Financial Loss (in Million $)',
        title="Total Financial Loss by Country"
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Visualization 2: Loss vs Affected Users
    fig2 = px.scatter(
        df,
        x='Number of Affected Users',
        y='Financial Loss (in Million $)',
        color='Attack Type',
        size='Incident Resolution Time (in Hours)',
        title="Financial Impact vs User Affection"
    )
    st.plotly_chart(fig2, use_container_width=True)

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.info("ℹ️ Use the filters to explore cybersecurity incidents globally")

