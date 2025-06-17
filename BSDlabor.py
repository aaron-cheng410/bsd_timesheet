import streamlit as st
import json
from openai import OpenAI
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import date

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    .viewerBadge_link__1S137 {display: none !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# --- OpenAI Setup ---
client = OpenAI(api_key=st.secrets["openai_api_key"])

cost_code_mapping_text = """00030 - Financing Fees
00110 - Architectural Fees
00150 - Engineering Fees
00160 - Interior Design
01010 - Supervision
01028 - Safety Audit
01100 - Surveying
01200 - Hydro/Gas/Telus Services
01210 - Temp Hydro
01220 - Temporary Heat
01230 - Temporary Lighting & Security Lighting
01240 - Temporary Water
01250 - Temporary Fencing
01300 - General Labor
01400 - Tree Protection
01510 - Site Office
01520 - Sanitary Facilities
01710 - Progressive Site Clean-up
01720 - Final Clean-up
01721 - Pressure Washing
01750 - Disposal Bins/Fees
01760 - Protect Finishes
01810 - Hoist/ crane/Scaffold rental
02220 - Demolition
02225 - Demolition (secondary)
02270 - Erosion & Sediment Control
02300 - Site Services (Fence)
02310 - Finish Grading
02315 - Excavation & Backfill
02600 - Drainaige & Stormwater
02621 - Foundation Drain Tile
02700 - Exterior Hardscape
02705 - Exterior Decking
02773 - Curbs & Gutters & Sidewalk
02820 - Fencing & Gates (Fnds, Stone & Alumn)
02900 - Landscaping
02910 - Irrigation Systems
03150 - Foundation Labor (Form, Rebar, Hardware)
03350 - Concrete Placing/Finishing
03351 - Concrete Pumping
03360 - Special Concrete Finishes
03800 - Cutting & Coring
04200 - Masonry
04400 - Stone Veneer
05090 - Exterior Railing and Guardrail
05095 - Driveway Gates & Fencing
06110 - Framing Labor/backframing Labor
06175 - Wood Trusses
06220 - Finishing Labor
06410 - Custom Cabinets
06425 - Stone/Countertop - Fabrication
06430 - Interior Railings
06450 - Fireplace Mantels
07200 - Interior Waterproofing/Shower pan
07210 - Building Insulation
07220 - Building Exterior Waterproofing/Vapour Barrier
07311 - Roofing System
07460 - Siding/Trims - Labor
07465 - Stucco
07500 - Torch & Decking
07600 - Metal Roofing - Prepainted Aluminum
07714 - Gutter & Downspouts
07920 - Sealants & Caulking
08220 - Closet Doors - Bifolds
08360 - Garage Door
08560 - Window Material
08570 - Window Installation
08580 - Window Waterproofing
09200 - Drywall Systems
09310 - Exterior Tile Work- Installation
09645 - Wood Flooring - Installation
09655 - Interior Tile Work - Installation
09690 - Carpeting - Labor
09900 - Painting Exterior
09905 - Painting Interior
09920 - Wallpaper Labor
10810 - Residential Washroom Accessories
10820 - Shower Enclosures
11452 - Appliance Installation
12490 - Window Treatment
13150 - Swimming Pools
13160 - Generator
13170 - Dry Sauna
13180 - Hot Tubs
15015 - Plumbing Rough in
15300 - Fire Protection (Sprinklers)
15500 - Radiant Heating
15610 - Wine Cellar Cooling Unit
15700 - Air Conditioning/HRV
15750 - Fire Place Inserts
16050 - General Electrical
16100 - Solar System
16800 - Low Voltage (Security, Internet)
16900 - Sound and Audio"""

# --- Initialize session state ---
if "num_rows" not in st.session_state:
    st.session_state.num_rows = 1

# --- Dropdown options ---
hourly_rates = {
    "Christian": 43.75,
    "Andres De Jesus": 37.50,
    "Enrique": 25.00,
    "Oscar": 31.25,
    "Edgar": 31.25,
    "Eddy": 34.38,
    "Juan Carlos": 34.38,
    "Jose Drywall": 25.00,
    "Tavo": 31.25,
    "Juan Chocoj": 37.50,
    "Victor": 31.25,
    "Tony": 31.25,
    "Enrique": 31.25,
    "Ozzy": 37.50,
    "Jose": 31.25,
    "Luis De Leon": 31.25,
    "Mymor": 25.00,
    "Leon": 25.00,
    "Fernando": 25.00,
    "Junior": 25.00,
    "Leonidas": 25.00,
    "Estvardo": 25.00,
    "Nelson": 25.00,
    "Erick": 25.00,
    "Byron Helper": 25.00,
}

worker_names = list(hourly_rates.keys())
properties = ["Coto", "Milford", "647 Navy", "645 Navy", 'Sagebrush', 'Paramount', '126 Scenic', 'San Marino', 'King Arthur', 'Via Sanoma', 'Highland', 'Channel View', 'Paseo De las Estrellas']
payable_parties = ["Christian Granados (Vendor)", "Jessica Ajtun", "Andres De Jesus"]

# --- Add row button ---

col1, col2 = st.columns(2)
with col1:
    if st.button("➕ Add Entry"):
        st.session_state.num_rows += 1
with col2:
    if st.button("🗑️ Remove Last Entry") and st.session_state.num_rows > 1:
        st.session_state.num_rows -= 1

# --- Timesheet Form ---
with st.form("multi_timesheet_form"):
    st.title("Timesheet Submission")

    entries = []

    for i in range(st.session_state.num_rows):
        st.markdown(f"### Entry {i + 1}")

        col1, col2, col3 = st.columns(3)
        with col1:
            date_invoiced = st.date_input(f"Date Invoiced", value=date.today(), key=f"date_{i}")
            worker = st.selectbox(f"Worker Name", worker_names, key=f"worker_{i}")
        with col2:
            hours = st.number_input(f"Hours", min_value=0.0, step=0.5, key=f"hours_{i}")
        with col3:
            property = st.selectbox(f"Property", properties, key=f"property_{i}")
            payable = st.selectbox(f"Payable Party", payable_parties, key=f"payable_{i}")

        description = st.text_area(f"Project Description", key=f"description_{i}")

        rate = hourly_rates.get(worker, 0.0)
        calculated_amount = hours * rate
        # Collect the entry
        entries.append({
            "Date Invoiced": date_invoiced.strftime("%Y-%m-%d"),
            "Worker Name": worker,
            "Hours": hours,
            "Property": property,
            "Amount": round(calculated_amount, 2),
            "Payable Party": payable,
            "Project Description": description
        })

    submitted = st.form_submit_button("Submit All Entries")

# --- Handle submission ---
if submitted:
    df = pd.DataFrame(entries)

    # Optional: filter out empty/incomplete rows
    df = df[df["Worker Name"] != ""]  # or add more validation here

    if df.empty:
        st.error("Please fill out at least one full entry.")
    else:
        with st.spinner("Uploading and processing..."):

            def assign_cost_codes(descriptions: list[str]) -> list[str]:
                prompt = (
                    "You are given a list of project descriptions. For each one, choose the most appropriate cost code "
                    "from the mapping below. Respond only with a JSON list where each item is the selected cost code string.\n\n"
                    "Cost Code Mapping:\n" + cost_code_mapping_text + "\n\n"
                    "Descriptions:\n" + "\n".join([f"{i+1}. {desc}" for i, desc in enumerate(descriptions)]) +
                    "\n\nRespond with:\n[\"CODE - Description\", ...]"
                )

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}]
                )

                try:
                    parsed = json.loads(response.choices[0].message.content)
                except Exception:
                    st.error("Failed to parse cost codes from OpenAI response.")
                    parsed = [""] * len(descriptions)

                return parsed
            
            descriptions = df["Project Description"].tolist()

            
            cost_codes = assign_cost_codes(descriptions)

   
            df["Cost Code"] = cost_codes
            
           
         
        
            df['Date Paid'] = None
            df['Unique ID'] = None
            df['Item Name'] = None
            df['Claim Number'] = None
            df['QB Property'] = None
            df['Invoice Number'] = None
            df['Payment Method'] = None
            df['Status'] = None
            df['Form'] = "Labor"
            final_df = df[["Date Paid", "Date Invoiced", "Unique ID", "Claim Number", "Worker Name", "Hours", "Item Name", "Property", "QB Property", "Amount", 'Payable Party', 'Project Description', "Invoice Number", "Cost Code", 'Payment Method', "Status", "Form"]]

            def upload_to_google_sheet(df):
                    from gspread.utils import rowcol_to_a1

                    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                    creds_dict = st.secrets["gcp_service_account"]
                    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                    client = gspread.authorize(creds)


                    sheet = client.open("BSD MASTER DATA")
                    worksheet = sheet.worksheet("TEST")

                    existing = worksheet.get_all_values()

                    # If empty, write headers first
                    if not existing:
                        worksheet.append_row(df.columns.tolist(), value_input_option="USER_ENTERED") 
                        start_row = 2
                    else:
                        start_row = len(existing) + 1

                    # Write all rows in one batch
                    data = df.values.tolist()
                    end_row = start_row + len(data) - 1
                    end_col = len(df.columns)
                    cell_range = f"A{start_row}:{rowcol_to_a1(end_row, end_col)}"

                    worksheet.update(cell_range, data, value_input_option="USER_ENTERED")

            upload_to_google_sheet(final_df)

            st.success("✅ Timesheet entries submitted")
        


        # Optional: upload to Google Sheet
        # upload_to_google_sheet(df)
