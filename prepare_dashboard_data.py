import pandas as pd
import numpy as np
from pathlib import Path
from glob import glob
import os

# Configuration
BASE_DIR = Path('/home/elian/cuhksz/term3/dv/final_project/data')
OUTPUT_FILE = 'data/dashboard_data.csv'
PRODUCT_CODES = [120110, 120190]  # Soybeans (Seed and Other)

# Country Groups Definition
CORE_EXPORTERS = ['Brazil', 'USA', 'Argentina', 'Paraguay', 'Canada']
CORE_IMPORTERS = ['China', 'Japan', 'Mexico', 'Thailand', 'Turkey', 'Egypt']
CORE_COUNTRIES = set(CORE_EXPORTERS + CORE_IMPORTERS)

EU27_ISO3 = [
    'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 
    'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE'
]

ASEAN_ISO3 = [
    'BRN', 'KHM', 'IDN', 'LAO', 'MYS', 'MMR', 'PHL', 'SGP', 'VNM' 
    # Thailand (THA) is in Core
]

MIDDLE_EAST_ISO3 = [
    'BHR', 'IRN', 'IRQ', 'ISR', 'JOR', 'KWT', 'LBN', 'OMN', 'PSE', 'QAT', 'SAU', 'SYR', 'ARE', 'YEM'
    # Turkey (TUR) and Egypt (EGY) are in Core
]

CENTRAL_AMERICA_CARIBBEAN_ISO3 = [
    'BLZ', 'CRI', 'SLV', 'GTM', 'HND', 'NIC', 'PAN', # Central America
    'ATG', 'BHS', 'BRB', 'CUB', 'DMA', 'DOM', 'GRD', 'HTI', 'JAM', 'KNA', 'LCA', 'VCT', 'TTO' # Caribbean
]

# We need a way to identify Africa. We can use a list of African ISO3 codes.
# Since I don't have a full list handy, I'll rely on the country_codes file if it has region info, 
# but it doesn't. I'll add a comprehensive list of African ISO3s.
AFRICA_ISO3 = [
    'DZA', 'AGO', 'BEN', 'BWA', 'BFA', 'BDI', 'CPV', 'CMR', 'CAF', 'TCD', 'COM', 'COG', 'COD', 'CIV', 'DJI', 
    'GNQ', 'ERI', 'ETH', 'GAB', 'GMB', 'GHA', 'GIN', 'GNB', 'KEN', 'LSO', 'LBR', 'LBY', 'MDG', 'MWI', 'MLI', 
    'MRT', 'MUS', 'MAR', 'MOZ', 'NAM', 'NER', 'NGA', 'RWA', 'STP', 'SEN', 'SYC', 'SLE', 'SOM', 'ZAF', 'SSD', 
    'SDN', 'SWZ', 'TZA', 'TGO', 'TUN', 'UGA', 'ZMB', 'ZWE'
    # Egypt (EGY) is in Core
]

def get_group(name, iso3):
    # 1. Core Players
    if name in CORE_COUNTRIES:
        return name
    
    # 2. EU-27
    if iso3 in EU27_ISO3:
        return "European Union"
    
    # 3. Regions
    if iso3 in ASEAN_ISO3:
        return "Other ASEAN"
    
    if iso3 in MIDDLE_EAST_ISO3:
        return "Middle East"
    
    if iso3 in CENTRAL_AMERICA_CARIBBEAN_ISO3:
        return "Central America & Caribbean"
    
    if iso3 in AFRICA_ISO3:
        if name == 'Egypt': # Should be caught by Core, but just in case
            return name
        return "Rest of Africa"
        
    # 4. Rest of World
    return "Rest of World"

def main():
    print("Loading country codes...")
    try:
        country_df = pd.read_csv(BASE_DIR / 'country_codes_V202501.csv')
    except FileNotFoundError:
        print("Error: country_codes_V202501.csv not found in ../dataset")
        return

    # Create a mapping from code to info
    code_to_info = country_df.set_index('country_code')[['country_name', 'country_iso3']].to_dict('index')

    print("Processing trade data...")
    csv_files = sorted(glob(str(BASE_DIR / 'BACI_HS12_Y*.csv')))
    
    all_data = []
    
    for csv_file in csv_files:
        year = int(Path(csv_file).stem.split('Y')[1].split('_')[0])
        print(f"Processing {year}...")
        
        try:
            df = pd.read_csv(csv_file, usecols=['i', 'j', 'k', 'v', 'q'])
            df_soy = df[df['k'].isin(PRODUCT_CODES)].copy()
            
            if df_soy.empty:
                continue
                
            df_soy['year'] = year
            
            # Map Exporter
            df_soy['exporter_name'] = df_soy['i'].map(lambda x: code_to_info.get(x, {}).get('country_name', 'Unknown'))
            df_soy['exporter_iso3'] = df_soy['i'].map(lambda x: code_to_info.get(x, {}).get('country_iso3', 'UNK'))
            
            # Map Importer
            df_soy['importer_name'] = df_soy['j'].map(lambda x: code_to_info.get(x, {}).get('country_name', 'Unknown'))
            df_soy['importer_iso3'] = df_soy['j'].map(lambda x: code_to_info.get(x, {}).get('country_iso3', 'UNK'))
            
            # Apply Grouping
            df_soy['exporter_group'] = df_soy.apply(lambda x: get_group(x['exporter_name'], x['exporter_iso3']), axis=1)
            df_soy['importer_group'] = df_soy.apply(lambda x: get_group(x['importer_name'], x['importer_iso3']), axis=1)
            
            # Aggregate by Group
            # We want to keep the original country names for the "Country Profile" section if possible,
            # but for the main map and flows, we use groups.
            # Actually, the user wants "Country Specific Trade Profile" which implies we need individual country data too.
            # So we should save the data with BOTH individual names AND groups.
            # To save space, we can aggregate by (Year, Exporter, Importer) first (which is already the case mostly),
            # then add group columns.
            
            # Let's just keep the necessary columns
            df_final = df_soy[['year', 'exporter_name', 'exporter_group', 'importer_name', 'importer_group', 'v', 'q']]
            all_data.append(df_final)
            
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")

    if not all_data:
        print("No data found.")
        return

    print("Concatenating data...")
    full_df = pd.concat(all_data, ignore_index=True)
    
    # Convert value to USD (v is in 1000 USD)
    full_df['v'] = full_df['v'] * 1000
    
    print(f"Saving to {OUTPUT_FILE}...")
    full_df.to_csv(OUTPUT_FILE, index=False)
    print("Done.")

if __name__ == "__main__":
    main()
