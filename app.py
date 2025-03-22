import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Predefined dictionary of country coordinates
COUNTRY_COORDINATES = {
    'China': (35.8617, 104.1954),
    'India': (20.5937, 78.9629),
    'UK': (55.3781, -3.4360),
    'Germany': (51.1657, 10.4515),
    'France': (46.6034, 1.8883),
    'Australia': (-25.2744, 133.7751),
    'Russia': (61.5240, 105.3188),
    'Brazil': (-14.2350, -51.9253),
    'Japan': (36.2048, 138.2529),
    'USA': (37.0902, -95.7129)
}

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
        required_columns = [
            'Country', 'Year', 'Attack Type', 'Target Industry', 'Financial Loss (in Million $)',
            'Number of Affected Users', 'Attack Source', 'Security Vulnerability Type',
            'Defense Mechanism Used', 'Incident Resolution Time (in Hours)'
        ]
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
        
        # Add coordinates using predefined dictionary
        df['lat'] = df['Country'].map(lambda x: COUNTRY_COORDINATES.get(x, (None, None))[0])
        df['lon'] = df['Country'].map(lambda x: COUNTRY_COORDINATES.get(x, (None, None))[1])
        
        # Drop rows with invalid coordinates
        initial_len = len(df)
        df = df.dropna(subset=['lat', 'lon'])
        if len(df) < initial_len:
            st.warning(f"Dropped {initial_len - len(df)} rows due to missing coordinates for some countries. "
                       f"Supported countries: {', '.join(COUNTRY_COORDINATES.keys())}")
        
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
        
        # Map style selection
        map_style = st.selectbox(
            "Select Map Style",
            options=["open-street-map", "carto-positron", "carto-darkmatter", "stamen-terrain"],
            index=0
        )
        
        # Display map using Plotly scatter_mapbox
        if not filtered_df.empty:
            fig_map = px.scatter_mapbox(
                filtered_df,
                lat='lat',
                lon='lon',
                size='Financial_Loss_Millions',
                color='Attack Type',
                hover_data={
                    'Country': True,
                    'Year': True,
                    'Attack Type': True,
                    'Target Industry': True,
                    'Financial_Loss_Millions': True,
                    'Number of Affected Users': True,
                    'Resolution_Time_Hours': True
                },
                title="Global Cybersecurity Incidents",
                zoom=1,
                height=800  # Increased height for a larger map
            )
            fig_map.update_layout(
                mapbox_style=map_style,
                margin={"r":0, "t":50, "l":0, "b":0},
                mapbox=dict(
                    center=dict(lat=20, lon=0),  # Center the map for better global view
                    zoom=1
                )
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("No data matching the selected filters.")
    else:
        st.warning("No data available to display the map. This may be due to missing coordinates or data loading issues.")

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
                # Section 1: Financial Loss and User Impact
                st.subheader("Financial Loss and User Impact")
                
                # Visualization 1: Financial Loss by Country (Bar Chart)
                fig1 = px.bar(
                    filtered_df.groupby('Country', as_index=False)['Financial_Loss_Millions'].sum(),
                    x='Country',
                    y='Financial_Loss_Millions',
                    title="Total Financial Loss by Country (Filtered Data)",
                    labels={'Financial_Loss_Millions': 'Financial Loss (in Million $)'}
                )
                fig1.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig1, use_container_width=True)
                
                # Visualization 2: Financial Loss vs Affected Users (Scatter Plot)
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
                
                # Section 2: Trends Over Time
                st.subheader("Trends Over Time")
                
                # Visualization 3: Financial Loss Over Time (Line Plot)
                fig3 = px.line(
                    filtered_df.groupby(['Year', 'Country'], as_index=False)['Financial_Loss_Millions'].sum(),
                    x='Year',
                    y='Financial_Loss_Millions',
                    color='Country',
                    title="Financial Loss Over Time by Country (Filtered Data)",
                    labels={'Financial_Loss_Millions': 'Financial Loss (in Million $)'},
                    markers=True
                )
                st.plotly_chart(fig3, use_container_width=True)
                
                # Section 3: Distribution of Attacks
                st.subheader("Distribution of Attacks")
                
                # Visualization 4: Distribution of Attack Types (Pie Chart)
                fig4 = px.pie(
                    filtered_df,
                    names='Attack Type',
                    title="Distribution of Attack Types (Filtered Data)",
                    hole=0.3  # Donut chart style
                )
                st.plotly_chart(fig4, use_container_width=True)
                
                # Visualization 5: Distribution of Target Industries (Pie Chart)
                fig5 = px.pie(
                    filtered_df,
                    names='Target Industry',
                    title="Distribution of Target Industries (Filtered Data)",
                    hole=0.3
                )
                st.plotly_chart(fig5, use_container_width=True)
                
                # Section 4: Attack Patterns
                st.subheader("Attack Patterns")
                
                # Visualization 6: Heatmap of Attack Types by Country
                heatmap_data = filtered_df.groupby(['Country', 'Attack Type']).size().reset_index(name='Count')
                fig6 = px.density_heatmap(
                    heatmap_data,
                    x='Country',
                    y='Attack Type',
                    z='Count',
                    title="Heatmap of Attack Types by Country (Filtered Data)",
                    color_continuous_scale='Viridis'
                )
                fig6.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig6, use_container_width=True)
                
                # Section 5: Distribution Analysis
                st.subheader("Distribution Analysis")
                
                # Visualization 7: Box Plot of Financial Loss by Attack Type
                fig7 = px.box(
                    filtered_df,
                    x='Attack Type',
                    y='Financial_Loss_Millions',
                    title="Distribution of Financial Loss by Attack Type (Filtered Data)",
                    labels={'Financial_Loss_Millions': 'Financial Loss (in Million $)'}
                )
                fig7.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig7, use_container_width=True)
                
                # Visualization 8: Box Plot of Resolution Time by Target Industry
                fig8 = px.box(
                    filtered_df,
                    x='Target Industry',
                    y='Resolution_Time_Hours',
                    title="Distribution of Resolution Time by Target Industry (Filtered Data)",
                    labels={'Resolution_Time_Hours': 'Resolution Time (Hours)'}
                )
                fig8.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig8, use_container_width=True)
            else:
                st.warning("No data matching the selected filters for visualizations.")
        except Exception as e:
            st.error(f"Error creating visualizations: {str(e)}")
    else:
        st.warning("No data available to display visualizations.")

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.info("ℹ️ Use the filters to explore cybersecurity incidents globally.")
