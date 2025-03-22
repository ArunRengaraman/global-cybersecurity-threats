import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
import time

# Cache geocoding results to avoid repeated calls
@st.cache_data
def geocode_countries(countries):
    geolocator = Nominatim(user_agent="cyber_map")
    coords = {}
    for country in countries:
        try:
            location = geolocator.geocode(country)
            if location:
                coords[country] = (location.latitude, location.longitude)
            else:
                coords[country] = (None, None)
            # Respect Nominatim's usage policy: 1 request per second
            time.sleep(1)
        except Exception as e:
            st.warning(f"Geocoding failed for {country}: {str(e)}")
            coords[country] = (None, None)
    return coords

@st.cache_data
def load_data():
    try:
        # Load data from CSV
        df = pd.read_csv('Global_Cybersecurity_Threats_2015-2024.csv', delimiter=",")
        
        # Debug: Print column names to identify potential issues
        st.write("Columns in the DataFrame:", df.columns.tolist())
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Check for required columns
        required_columns = ['Country', 'Year', 'Attack Type', 'Financial Loss (in Million $)', 
                           'Number of Affected Users', 'Incident Resolution Time (in Hours)']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Missing columns in the DataFrame: {', '.join(missing_columns)}")
            st.stop()
        
        # Rename columns for easier access
        df = df.rename(columns={
            'Financial Loss (in Million $)': 'Financial_Loss_Millions',
            'Incident Resolution Time (in Hours)': 'Resolution_Time_Hours'
        })
        
        # Convert numerical columns to appropriate types
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df['Financial_Loss_Millions'] = pd.to_numeric(df['Financial_Loss_Millions'], errors='coerce')
        df['Number of Affected Users'] = pd.to_numeric(df['Number of Affected Users'], errors='coerce')
        df['Resolution_Time_Hours'] = pd.to_numeric(df['Resolution_Time_Hours'], errors='coerce')
        
        # Drop rows with invalid numerical values
        df = df.dropna(subset=['Year', 'Financial_Loss_Millions', 'Number of Affected Users', 'Resolution_Time_Hours'])
        df['Year'] = df['Year'].astype(int)
        
        # Standardize Attack Type
        df['Attack Type'] = df['Attack Type'].str.strip().str.upper()
        
        # Ensure Resolution Time is positive for scatter plot sizing
        df['Resolution_Time_Hours'] = df['Resolution_Time_Hours'].clip(lower=1)
        
        # Geocode countries
        unique_countries = df['Country'].unique()
        coords = geocode_countries(unique_countries)
        
        # Add coordinates to DataFrame
        df['lat'] = df['Country'].map(lambda x: coords[x][0])
        df['lon'] = df['Country'].map(lambda x: coords[x][1])
        
        # Drop rows with invalid coordinates
        df = df.dropna(subset=['lat', 'lon'])
        
        return df
    except FileNotFoundError:
        st.error("The file 'Global_Cybersecurity_Threats_2015-2024.csv' was not found. Please upload the correct file.")
        return pd.DataFrame()
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
    st.write("DataFrame columns:", list(df.columns))
    st.write("DataFrame dtypes:", df.dtypes.to_dict())
    st.write("DataFrame preview:", df.head())
    st.write("Missing values:", df.isnull().sum().to_dict())

# Create tabs for map and analytics
tab1, tab2 = st.tabs(["World Map Visualization", "Dynamic Analytics"])

with tab1:
    st.header("Global Threat Map")
    
    # Check if DataFrame is empty before creating filters
    if not df.empty:
        # Sidebar filters for year range and attack types
        year_range = st.sidebar.slider(
            "Select Year Range",
            min_value=int(df['Year'].min()),
            max_value=int(df['Year'].max()),
            value=(int(df['Year'].min()), int(df['Year'].max()))
        )
        
        attack_types = st.sidebar.multiselect(
            "Select Attack Types",
            options=sorted(df['Attack Type'].unique()),
            default=df['Attack Type'].unique()
        )
        
        # Additional filter: Financial Loss Range
        financial_loss_range = st.sidebar.slider(
            "Select Financial Loss Range (in Million $)",
            min_value=float(df['Financial_Loss_Millions'].min()),
            max_value=float(df['Financial_Loss_Millions'].max()),
            value=(float(df['Financial_Loss_Millions'].min()), float(df['Financial_Loss_Millions'].max()))
        )
        
        # Filter data based on user selections
        filtered_df = df[
            (df['Year'].between(*year_range)) &
            (df['Attack Type'].isin(attack_types)) &
            (df['Financial_Loss_Millions'].between(*financial_loss_range))
        ]
        
        # Display map using Plotly scatter_mapbox for more customization
        if not filtered_df.empty:
            fig_map = px.scatter_mapbox(
                filtered_df,
                lat='lat',
                lon='lon',
                size='Financial_Loss_Millions',
                color='Attack Type',
                hover_data=['Country', 'Year', 'Financial_Loss_Millions', 'Number of Affected Users'],
                title="Global Cybersecurity Incidents",
                zoom=1,
                height=600
            )
            fig_map.update_layout(
                mapbox_style="open-street-map",
                margin={"r":0,"t":50,"l":0,"b":0}
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("No data matching the selected filters.")
    else:
        st.warning("No data available to display the map.")

with tab2:
    st.header("Analytical Visualizations")
    
    if not df.empty:
        try:
            # Use filtered_df to ensure visualizations reflect the same filters as the map
            filtered_df = df[
                (df['Year'].between(*year_range)) &
                (df['Attack Type'].isin(attack_types)) &
                (df['Financial_Loss_Millions'].between(*financial_loss_range))
            ]
            
            if not filtered_df.empty:
                # Visualization 1: Financial Loss by Country
                fig1 = px.bar(
                    filtered_df.groupby('Country', as_index=False)['Financial_Loss_Millions'].sum(),
                    x='Country',
                    y='Financial_Loss_Millions',
                    title="Total Financial Loss by Country (Filtered Data)",
                    labels={'Financial_Loss_Millions': 'Financial Loss (in Million $)'}
                )
                fig1.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig1, use_container_width=True)
                
                # Visualization 2: Financial Loss vs Affected Users
                fig2 = px.scatter(
                    filtered_df,
                    x='Number of Affected Users',
                    y='Financial_Loss_Millions',
                    color='Attack Type',
                    size='Resolution_Time_Hours',
                    hover_data=['Country', 'Year'],
                    title="Financial Impact vs User Affection (Filtered Data)",
                    labels={
                        'Financial_Loss_Millions': 'Financial Loss (in Million $)',
                        'Resolution_Time_Hours': 'Resolution Time (Hours)'
                    }
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("No data matching the selected filters for visualizations.")
        except Exception as e:
            st.error(f"Error creating visualizations: {str(e)}")
    else:
        st.warning("No data available to display visualizations.")

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.info("ℹ️ Use the filters to explore cybersecurity incidents globally.")
