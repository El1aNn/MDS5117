import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Page Configuration
st.set_page_config(
    page_title="Global Soybean Trade Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .metric-label {
        font-size: 14px;
        color: #555;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #003f5c;
    }
    .metric-delta {
        font-size: 14px;
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 5px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Load Data
@st.cache_data
def load_data():
    df = pd.read_csv('data/dashboard_data.csv')
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Data file 'dashboard_data.csv' not found. Please run 'prepare_dashboard_data.py' first.")
    st.stop()

# Coordinates for Map (Approximate Centers)
COORDINATES = {
    # Core Exporters
    'Brazil': {'lat': -14.2350, 'lon': -51.9253},
    'USA': {'lat': 37.0902, 'lon': -95.7129},
    'Argentina': {'lat': -38.4161, 'lon': -63.6167},
    'Paraguay': {'lat': -23.4425, 'lon': -58.4438},
    'Canada': {'lat': 56.1304, 'lon': -106.3468},
    
    # Core Importers
    'China': {'lat': 35.8617, 'lon': 104.1954},
    'Japan': {'lat': 36.2048, 'lon': 138.2529},
    'Mexico': {'lat': 23.6345, 'lon': -102.5528},
    'Thailand': {'lat': 15.8700, 'lon': 100.9925},
    'Turkey': {'lat': 38.9637, 'lon': 35.2433},
    'Egypt': {'lat': 26.8206, 'lon': 30.8025},
    
    # Groups
    'European Union': {'lat': 50.8503, 'lon': 4.3517}, # Brussels
    'Rest of Africa': {'lat': -8.7832, 'lon': 34.5085}, # Central/South East Africa approx
    'Other ASEAN': {'lat': -0.7893, 'lon': 113.9213}, # Indonesia approx
    'Middle East': {'lat': 23.8859, 'lon': 45.0792}, # Saudi Arabia approx
    'Central America & Caribbean': {'lat': 15.0000, 'lon': -85.0000},
    'Rest of World': {'lat': 0.0, 'lon': 0.0} # Equator/Prime Meridian
}

# Entity Colors & ISO Codes for Map Styling
ENTITY_COLORS = {
    'Brazil': '#2ca02c',    # Green
    'USA': '#1f77b4',       # Blue
    'Argentina': '#ff7f0e', # Orange
    'Paraguay': '#9467bd',  # Purple
    'Canada': '#8c564b',    # Brown
    'China': '#d62728',     # Red
    'European Union': '#e377c2', # Pink
    'Japan': '#17becf',     # Cyan
    'Mexico': '#bcbd22',    # Olive
    'Thailand': '#17becf',  # Cyan
    'Turkey': '#7f7f7f',    # Gray
    'Egypt': '#7f7f7f',     # Gray
}

ENTITY_ISOS = {
    'Brazil': ['BRA'],
    'USA': ['USA'],
    'Argentina': ['ARG'],
    'Paraguay': ['PRY'],
    'Canada': ['CAN'],
    'China': ['CHN'],
    'Japan': ['JPN'],
    'Mexico': ['MEX'],
    'Thailand': ['THA'],
    'Turkey': ['TUR'],
    'Egypt': ['EGY'],
    'European Union': ['AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE']
}

def get_color(name):
    return ENTITY_COLORS.get(name, '#7f7f7f')

def get_isos(name):
    return ENTITY_ISOS.get(name, [])

# Helper to get coords
def get_coords(name):
    return COORDINATES.get(name, {'lat': 0, 'lon': 0})

# ==========================================
# Top Layout: Title & Overview
# ==========================================
st.title("🌱 Global Soybean Trade")
st.markdown("Interactive analysis of trade flows, prices, and market dynamics.")

# Helper Functions (Global)
def format_currency(val):
    if val >= 1e9:
        return f"${val/1e9:.1f}B"
    elif val >= 1e6:
        return f"${val/1e6:.1f}M"
    else:
        return f"${val:,.0f}"

def format_volume(val):
    if val >= 1e6:
        return f"{val/1e6:.1f}M Tons"
    else:
        return f"{val:,.0f} Tons"

# Overview: Stacked Bar Chart (All Years) - REMOVED per user request
# st.markdown("### 📈 Trade Volume Evolution")
# ...

st.markdown("---")

# ==========================================
# 2. Main Analysis Tabs
# ==========================================
tab_map, tab_rank, tab_country, tab_multi = st.tabs([
    "🌏 Trade Flows & Network", 
    "🏆 Competition & Rankings", 
    "🔍 Country Profile & Balance",
    "🕸️ Multi-Route Analysis"
])

# --- TAB 1: Trade Flows (Map & Sankey) ---
with tab_map:
    # Local Year Control & KPIs
    col_ctrl, col_kpi = st.columns([1, 3])
    
    with col_ctrl:
        min_year = int(df['year'].min())
        max_year = int(df['year'].max())
        years = list(range(min_year, max_year + 1))
        
        # Use a range slider to allow single year or period analysis
        selected_years = st.select_slider(
            "📅 Select Analysis Period",
            options=years,
            value=(max_year, max_year),
            help="Select a single year or a range of years to aggregate data."
        )
    
    # Handle Range Selection
    if isinstance(selected_years, tuple):
        start_year, end_year = selected_years
    else:
        start_year = end_year = selected_years

    # Filter Data for Period
    df_year = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    
    # KPIs
    total_trade_value = df_year['v'].sum()
    total_trade_volume = df_year['q'].sum()
    
    # Logic for Growth/Comparison
    if start_year == end_year:
        # Single Year Mode: Compare to previous year
        df_prev = df[df['year'] == (start_year - 1)]
        prev_val = df_prev['v'].sum() if not df_prev.empty else 0
        if prev_val > 0:
            delta = (total_trade_value - prev_val) / prev_val * 100
            delta_str = f"{delta:.1f}% YoY"
        else:
            delta_str = None
        period_label = f"({start_year})"
    else:
        # Range Mode: No direct YoY comparison (or compare to previous same-length period, but let's keep it simple)
        delta_str = None
        period_label = f"({start_year}-{end_year})"

    if not df_year.empty:
        # For Top Route, we sum up if it's a range
        route_agg = df_year.groupby(['exporter_group', 'importer_group'])['v'].sum().reset_index()
        top_route_row = route_agg.sort_values('v', ascending=False).iloc[0]
        top_route_name = f"{top_route_row['exporter_group']} ➝ {top_route_row['importer_group']}"
        top_route_val = top_route_row['v']
    else:
        top_route_name = "N/A"
        top_route_val = 0
        
    with col_kpi:
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Trade Value", format_currency(total_trade_value), delta_str)
        k2.metric("Total Volume", format_volume(total_trade_volume))
        k3.metric("Top Route", top_route_name, format_currency(top_route_val))

    # Unified Layout: Controls and Charts in one section
    st.markdown("###") 
    
    view_type = st.radio("Select View", ["Geographic Map", "Sankey Diagram (Flow Logic)"], horizontal=True, label_visibility="collapsed")
    
    if view_type == "Geographic Map":
        row2_col1, row2_col2 = st.columns([3, 2])
        
        with row2_col1:
            # Prepare Map Data
            # Aggregate by Exporter Group -> Importer Group
            map_df = df_year.groupby(['exporter_group', 'importer_group'])['v'].sum().reset_index()
            
            # Filter out "Rest" groups as requested
            map_df = map_df[
                (~map_df['exporter_group'].str.contains('Rest')) & 
                (~map_df['importer_group'].str.contains('Rest'))
            ]
            
            map_df = map_df.sort_values('v', ascending=False).head(20) # Top 20 routes
            
            # Create Plotly Map
            fig_map = go.Figure()
            
            # 1. Add Choropleth Layers (Coloring Countries)
            # Collect all unique entities involved in the map
            active_entities = set(map_df['exporter_group'].unique()) | set(map_df['importer_group'].unique())
            
            for entity in active_entities:
                isos = get_isos(entity)
                if isos:
                    color = get_color(entity)
                    fig_map.add_trace(go.Choropleth(
                        locations=isos,
                        z=[1]*len(isos), # Dummy value
                        colorscale=[[0, color], [1, color]],
                        showscale=False,
                        marker_line_color='white',
                        marker_line_width=0.5,
                        hoverinfo='text',
                        text=entity,
                        name=entity
                    ))

            # 2. Add Lines and Markers
            for _, row in map_df.iterrows():
                exp = row['exporter_group']
                imp = row['importer_group']
                val = row['v']
                
                start_coords = get_coords(exp)
                end_coords = get_coords(imp)
                
                # Line width based on value
                width = max(1, val / total_trade_value * 50) 
                
                # Color based on Exporter
                color = get_color(exp)
                
                # Draw Line
                fig_map.add_trace(go.Scattergeo(
                    lon = [start_coords['lon'], end_coords['lon']],
                    lat = [start_coords['lat'], end_coords['lat']],
                    mode = 'lines',
                    line = dict(width=width, color=color),
                    opacity = 0.6,
                    hoverinfo = 'text',
                    text = f"{exp} ➝ {imp}: {format_currency(val)}"
                ))
                
                # Add Source Marker (Small Circle)
                fig_map.add_trace(go.Scattergeo(
                    lon = [start_coords['lon']],
                    lat = [start_coords['lat']],
                    mode = 'markers',
                    marker = dict(size=5, color=color, symbol='circle'),
                    hoverinfo = 'text',
                    text = f"Source: {exp}"
                ))
                
                # Add Destination Marker (Arrow/Triangle to indicate flow)
                fig_map.add_trace(go.Scattergeo(
                    lon = [end_coords['lon']],
                    lat = [end_coords['lat']],
                    mode = 'markers',
                    marker = dict(size=8, color='red', symbol='triangle-down'), # Using triangle as arrow-head proxy
                    hoverinfo = 'text',
                    text = f"Dest: {imp}"
                ))

            fig_map.update_layout(
                title_text=f"Global Trade Flows {period_label}",
                showlegend=False,
                geo = dict(
                    projection_type="equirectangular",
                    showland = True,
                    landcolor = "rgb(243, 243, 243)",
                    countrycolor = "rgb(204, 204, 204)",
                    showcountries=True,
                ),
                margin=dict(l=0, r=0, t=30, b=0),
                height=500
            )
            st.plotly_chart(fig_map, use_container_width=True)

        with row2_col2:
            st.markdown("#### Market Share Composition")
            
            subtab1, subtab2 = st.tabs(["Exporters", "Importers"])
            
            with subtab1:
                # Exporter Treemap
                exp_share = df_year.groupby('exporter_group')['v'].sum().reset_index()
                fig_tree_exp = px.treemap(
                    exp_share, 
                    path=['exporter_group'], 
                    values='v',
                    color='exporter_group',
                    color_discrete_map=ENTITY_COLORS, # Use consistent colors
                    title=f"Export Market Share {period_label}"
                )
                # Reduce top margin to bring title closer to chart and reduce gap above
                fig_tree_exp.update_layout(margin=dict(t=30, l=10, r=10, b=10))
                st.plotly_chart(fig_tree_exp, use_container_width=True)
                
            with subtab2:
                # Importer Treemap
                imp_share = df_year.groupby('importer_group')['v'].sum().reset_index()
                fig_tree_imp = px.treemap(
                    imp_share, 
                    path=['importer_group'], 
                    values='v',
                    color='importer_group',
                    color_discrete_map=ENTITY_COLORS, # Use consistent colors
                    title=f"Import Market Share {period_label}"
                )
                # Reduce top margin to bring title closer to chart and reduce gap above
                fig_tree_imp.update_layout(margin=dict(t=30, l=10, r=10, b=10))
                st.plotly_chart(fig_tree_imp, use_container_width=True)

    else: # Sankey Diagram
        # Prepare Sankey Data
        sankey_df = df_year.groupby(['exporter_group', 'importer_group'])['v'].sum().reset_index()
        # Filter small flows to avoid clutter
        threshold = sankey_df['v'].sum() * 0.01 # 1% threshold
        sankey_df = sankey_df[sankey_df['v'] > threshold]
        
        # Create node list
        all_nodes = list(pd.concat([sankey_df['exporter_group'], sankey_df['importer_group']]).unique())
        node_map = {node: i for i, node in enumerate(all_nodes)}
        
        source_indices = sankey_df['exporter_group'].map(node_map).tolist()
        target_indices = sankey_df['importer_group'].map(node_map).tolist()
        values = sankey_df['v'].tolist()
        
        fig_sankey = go.Figure(data=[go.Sankey(
            node = dict(
                pad = 15,
                thickness = 20,
                line = dict(color = "black", width = 0.5),
                label = all_nodes,
                color = "blue"
            ),
            link = dict(
                source = source_indices,
                target = target_indices,
                value = values
            )
        )])
        
        fig_sankey.update_layout(title_text=f"Global Trade Flows (Sankey Diagram) - {period_label}", font_size=10)
        st.plotly_chart(fig_sankey, use_container_width=True)

# --- TAB 2: Competition (Rankings) ---
with tab_rank:
    st.subheader("🏆 Market Leadership Evolution (Bump Chart)")
    
    # Calculate Rankings over time for Exporters
    rank_df = df.groupby(['year', 'exporter_group'])['v'].sum().reset_index()
    rank_df['rank'] = rank_df.groupby('year')['v'].rank(ascending=False, method='first')
    
    # Filter top 10 countries ever to avoid clutter
    top_countries = rank_df.groupby('exporter_group')['v'].sum().nlargest(10).index
    rank_df_filtered = rank_df[rank_df['exporter_group'].isin(top_countries)]
    
    # Only show top 10 ranks
    rank_df_filtered = rank_df_filtered[rank_df_filtered['rank'] <= 10]
    
    fig_bump = px.line(
        rank_df_filtered,
        x='year',
        y='rank',
        color='exporter_group',
        title="Top Exporters Ranking History",
        markers=True
    )
    
    # Invert Y axis so Rank 1 is at top
    fig_bump.update_yaxes(autorange="reversed")
    
    st.plotly_chart(fig_bump, use_container_width=True)

# --- TAB 4: Country Profile ---
with tab_country:
    st.subheader("🔍 Country-Specific Analysis")
    
    col_sel1, col_sel2 = st.columns(2)
    all_entities = sorted(list(set(df['exporter_group'].unique()) | set(df['importer_group'].unique())))
    
    with col_sel1:
        selected_country = st.selectbox("Select Country/Region", all_entities, index=all_entities.index('China') if 'China' in all_entities else 0)
    
    # 1. Butterfly Chart (Balance)
    st.markdown(f"#### ⚖️ Trade Balance: {selected_country}")
    
    # Get total exports and imports for this country over time
    country_exp = df[df['exporter_group'] == selected_country].groupby('year')['v'].sum().reset_index().rename(columns={'v': 'Exports'})
    country_imp = df[df['importer_group'] == selected_country].groupby('year')['v'].sum().reset_index().rename(columns={'v': 'Imports'})
    
    balance_df = pd.merge(country_exp, country_imp, on='year', how='outer').fillna(0)
    
    # For butterfly chart, make Imports negative
    balance_df['Imports_Neg'] = -balance_df['Imports']
    
    fig_butterfly = go.Figure()
    
    fig_butterfly.add_trace(go.Bar(
        x=balance_df['year'],
        y=balance_df['Exports'],
        name='Exports',
        marker_color='green'
    ))
    
    fig_butterfly.add_trace(go.Bar(
        x=balance_df['year'],
        y=balance_df['Imports_Neg'],
        name='Imports',
        marker_color='red',
        customdata=balance_df['Imports'], # For hover
        hovertemplate='%{customdata:.2s}'
    ))
    
    fig_butterfly.update_layout(
        title=f"Export (Green) vs Import (Red) Balance for {selected_country}",
        barmode='relative',
        yaxis_title="Trade Value ($)",
        xaxis_title="Year"
    )
    
    st.plotly_chart(fig_butterfly, use_container_width=True)
    
    # 2. Heatmap Matrix
    st.markdown("#### 🔥 Global Trade Heatmap (Top 10 Partners)")
    
    # Determine if this country is primarily an exporter or importer to choose partners
    total_exp = balance_df['Exports'].sum()
    total_imp = balance_df['Imports'].sum()
    
    if total_exp > total_imp:
        # Show who buys from them
        role_label = "Importers (Destinations)"
        heatmap_data = df[df['exporter_group'] == selected_country]
        y_field = 'importer_group'
    else:
        # Show who sells to them
        role_label = "Exporters (Sources)"
        heatmap_data = df[df['importer_group'] == selected_country]
        y_field = 'exporter_group'
        
    # Aggregate by Year and Partner
    hm_agg = heatmap_data.groupby(['year', y_field])['v'].sum().reset_index()
    
    # Filter Top 10 partners overall
    top_partners = hm_agg.groupby(y_field)['v'].sum().nlargest(10).index
    hm_agg_filtered = hm_agg[hm_agg[y_field].isin(top_partners)]
    
    fig_heatmap = px.density_heatmap(
        hm_agg_filtered,
        x='year',
        y=y_field,
        z='v',
        title=f"Trade Intensity with Top {role_label}",
        color_continuous_scale='Viridis'
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("---")

# --- TAB 4: Multi-Route Analysis ---
with tab_multi:
    st.subheader("🕸️ Multi-Route Trade Analysis")
    st.markdown("Compare trade flows between multiple exporters and importers to identify shifts in market dynamics (e.g., USA vs Brazil exports to China).")

    col_sel_exp, col_sel_imp = st.columns(2)
    all_exporters = sorted(df['exporter_group'].unique())
    all_importers = sorted(df['importer_group'].unique())

    with col_sel_exp:
        sel_exporters = st.multiselect("Select Exporters", all_exporters, default=['USA', 'Brazil'])
    with col_sel_imp:
        sel_importers = st.multiselect("Select Importers", all_importers, default=['China'])

    if sel_exporters and sel_importers:
        # Filter
        route_df = df[
            (df['exporter_group'].isin(sel_exporters)) & 
            (df['importer_group'].isin(sel_importers))
        ].groupby(['year', 'exporter_group', 'importer_group'])[['v', 'q']].sum().reset_index()
        
        route_df['route'] = route_df['exporter_group'] + " ➝ " + route_df['importer_group']
        
        # 1. Trend Line Chart
        fig_trend = px.line(
            route_df, 
            x='year', 
            y='v', 
            color='route', 
            markers=True,
            title="Trade Volume Trends Comparison",
            labels={'v': 'Trade Value ($)'}
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        col_viz1, col_viz2 = st.columns(2)
        
        with col_viz1:
            # 2. Market Share (if 1 importer selected, show exporter share)
            if len(sel_importers) == 1:
                # Normalize to 100%
                fig_share = px.area(
                    route_df,
                    x='year',
                    y='v',
                    color='exporter_group',
                    groupnorm='percent',
                    title=f"Market Share Evolution in {sel_importers[0]}",
                    labels={'v': 'Market Share (%)'}
                )
                st.plotly_chart(fig_share, use_container_width=True)
            else:
                 # Stacked Bar of Total Volume by Route
                 fig_stack = px.bar(
                     route_df,
                     x='year',
                     y='v',
                     color='route',
                     title="Total Trade Volume Composition",
                     barmode='stack'
                 )
                 st.plotly_chart(fig_stack, use_container_width=True)

        with col_viz2:
            # 3. Unit Price Comparison
            route_df['unit_price'] = route_df['v'] / route_df['q']
            
            fig_price = px.line(
                route_df,
                x='year',
                y='unit_price',
                color='route',
                markers=True,
                title="Unit Price Comparison ($/Ton)",
                labels={'unit_price': 'Price ($/Ton)'}
            )
            st.plotly_chart(fig_price, use_container_width=True)

    else:
        st.info("Please select at least one exporter and one importer.")

