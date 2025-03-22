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

# Custom CSS for a cleaner UI
st.markdown(
    """
    <style>
    .main-title {
        font-size: 36px;
        font-weight: bold;
        color: #1E90FF;
        text-align: center;
        margin-bottom: 20px;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
        padding: 20px;
    }
    .sidebar-header {
        font-size: 24px;
        font-weight: bold;
        color: #333;
        margin-bottom: 20px;
    }
    .section-header {
        font-size: 22px;
        font-weight: bold;
        color: #2E8B57;
        margin-top: 30px;
        margin-bottom: 10px;
    }
    .warning-box {
        background-color: #FFF3CD;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .error-box {
        background-color: #F8D7DA;
        color: #721C24;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .footer {
        text-align: center;
        font-size: 14px;
        color: #666;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #ddd;
    }
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_data
def load_data():
    try:
        # Load data from CSV
        df = pd.read_csv('Global_Cybersecurity_Threats_2015-2024.csv', delimiter=",")
        
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
            st.markdown(f'<div class="error-box">Missing columns in the DataFrame: {", ".join(missing_columns)}</div>', unsafe_allow_html=True)
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
            st.markdown(
                f'<div class="warning-box">Dropped {initial_len - len(df)} rows due to missing coordinates for some countries. '
                f'Supported countries: {", ".join(COUNTRY_COORDINATES.keys())}</div>',
                unsafe_allow_html=True
            )
        
        return df
    except FileNotFoundError:
        st.markdown('<div class="error-box">The file "Global_Cybersecurity_Threats_2015-2024.csv" was not found. Please upload the correct file.</div>', unsafe_allow_html=True)
        return pd.DataFrame()
    except Exception as e:
        st.markdown(f'<div class="error-box">Error loading data: {str(e)}</div>', unsafe_allow_html=True)
        return pd.DataFrame()

# Load and cache data
df = load_data()

# Main app
st.markdown('<div class="main-title">Cybersecurity Incident Dashboard 🌐</div>', unsafe_allow_html=True)
st.markdown("Explore global cybersecurity incidents from 2015 to 2024 with interactive maps and detailed analytics.", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown('<div class="sidebar-header">Filter Controls</div>', unsafe_allow_html=True)

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
        
        # Map type selection (2D or 3D)
        map_type = st.selectbox("Select Map Type", options=["2D Map", "3D Globe"], index=0)
        
        # Map style selection (only for 2D map)
        map_style = None
        if map_type == "2D Map":
            map_style = st.selectbox(
                "Select Map Style",
                options=["open-street-map", "carto-positron", "carto-darkmatter", "stamen-terrain"],
                index=0
            )
        
        # Define marker symbols for each attack type
        unique_attack_types = filtered_df['Attack Type'].unique()
        marker_symbols = ['circle', 'square', 'diamond', 'cross', 'x', 'triangle-up', 'triangle-down', 'pentagon', 'hexagon']
        # Map each attack type to a symbol (cycle through symbols if there are more attack types than symbols)
        attack_type_to_symbol = {attack: marker_symbols[i % len(marker_symbols)] for i, attack in enumerate(unique_attack_types)}
        filtered_df['Marker Symbol'] = filtered_df['Attack Type'].map(attack_type_to_symbol)
        
        # Validate data before plotting
        if not filtered_df.empty:
            # Ensure required columns have valid data
            required_plot_columns = ['lat', 'lon', 'Financial_Loss_Millions', 'Attack Type', 'Marker Symbol']
            for col in required_plot_columns:
                if filtered_df[col].isnull().any():
                    st.markdown(f'<div class="error-box">Error: Column "{col}" contains missing values.</div>', unsafe_allow_html=True)
                    st.stop()
            
            # Ensure lat and lon are numeric
            filtered_df['lat'] = pd.to_numeric(filtered_df['lat'], errors='coerce')
            filtered_df['lon'] = pd.to_numeric(filtered_df['lon'], errors='coerce')
            filtered_df = filtered_df.dropna(subset=['lat', 'lon'])
            
            # Ensure Financial_Loss_Millions is numeric and positive
            filtered_df['Financial_Loss_Millions'] = pd.to_numeric(filtered_df['Financial_Loss_Millions'], errors='coerce')
            filtered_df = filtered_df[filtered_df['Financial_Loss_Millions'] > 0]
            
            # Ensure Marker Symbol contains valid symbols
            valid_symbols = set(marker_symbols)
            if not filtered_df['Marker Symbol'].isin(valid_symbols).all():
                st.markdown(
                    f'<div class="error-box">Error: Invalid marker symbols in "Marker Symbol" column. '
                    f'Valid symbols are: {", ".join(valid_symbols)}</div>',
                    unsafe_allow_html=True
                )
                st.stop()
            
            # Display map based on user selection
            if map_type == "2D Map":
                # 2D Map with scatter_mapbox
                fig_map = px.scatter_mapbox(
                    filtered_df,
                    lat='lat',
                    lon='lon',
                    size='Financial_Loss_Millions',
                    color='Attack Type',
                    symbol='Marker Symbol',  # Differentiate attack types with symbols
                    hover_data={
                        'Country': True,
                        'Year': True,
                        'Attack Type': True,
                        'Target Industry': True,
                        'Financial_Loss_Millions': True,
                        'Number of Affected Users': True,
                        'Resolution_Time_Hours': True
                    },
                    title="Global Cybersecurity Incidents (2D Map)",
                    zoom=1,
                    height=800
                )
                fig_map.update_layout(
                    mapbox_style=map_style,
                    margin={"r":0, "t":50, "l":0, "b":0},
                    mapbox=dict(
                        center=dict(lat=20, lon=0),
                        zoom=1
                    ),
                    legend=dict(
                        title="Attack Type",
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    )
                )
                st.plotly_chart(fig_map, use_container_width=True)
            
            else:
                # 3D Globe with scatter_geo
                fig_globe = px.scatter_geo(
                    filtered_df,
                    lat='lat',
                    lon='lon',
                    size='Financial_Loss_Millions',
                    color='Attack Type',
                    symbol='Marker Symbol',  # Differentiate attack types with symbols
                    hover_data={
                        'Country': True,
                        'Year': True,
                        'Attack Type': True,
                        'Target Industry': True,
                        'Financial_Loss_Millions': True,
                        'Number of Affected Users': True,
                        'Resolution_Time_Hours': True
                    },
                    title="Global Cybersecurity Incidents (3D Globe)",
                    projection='orthographic',
                    height=800
                )
                fig_globe.update_layout(
                    margin={"r":0, "t":50, "l":0, "b":0},
                    legend=dict(
                        title="Attack Type",
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    ),
                    geo=dict(
                        showland=True,
                        landcolor="rgb(243, 243, 243)",
                        showocean=True,
                        oceancolor="rgb(200, 230, 255)",
                        showcountries=True,
                        countrycolor="rgb(204, 204, 204)"
                    )
                )
                st.plotly_chart(fig_globe, use_container_width=True)
        else:
            st.markdown('<div class="warning-box">No data matching the selected filters.</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="warning-box">No data available to display the map. This may be due to missing coordinates or data loading issues.</div>',
            unsafe_allow_html=True
        )

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
                st.markdown('<div class="section-header">Financial Loss and User Impact</div>', unsafe_allow_html=True)
                
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
                st.markdown('<div class="section-header">Trends Over Time</div>', unsafe_allow_html=True)
                
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
                st.markdown('<div class="section-header">Distribution of Attacks</div>', unsafe_allow_html=True)
                
                # Visualization 4: Distribution of Attack Types (Pie Chart)
                fig4 = px.pie(
                    filtered_df,
                    names='Attack Type',
                    title="Distribution of Attack Types (Filtered Data)",
                    hole=0.3
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
                st.markdown('<div class="section-header">Attack Patterns</div>', unsafe_allow_html=True)
                
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
                st.markdown('<div class="section-header">Distribution Analysis</div>', unsafe_allow_html=True)
                
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
                st.markdown('<div class="warning-box">No data matching the selected filters for visualizations.</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="error-box">Error creating visualizations: {str(e)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="warning-box">No data available to display visualizations.</div>', unsafe_allow_html=True)

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.info("ℹ️ Use the filters to explore cybersecurity incidents globally.")

# Footer
st.markdown(
    '<div class="footer">Cybersecurity Incident Dashboard | Data Source: Global Cybersecurity Threats 2015-2024</div>',
    unsafe_allow_html=True
)
