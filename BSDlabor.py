import streamlit as st
import json
from openai import OpenAI
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import date, datetime

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

def translate_to_english_if_needed(descriptions):
    system_msg = {
        "role": "system",
        "content": "You are a translator. Detect if a sentence is in Spanish and translate it to English. If it's already in English, return it unchanged."
    }
    user_msg = {
        "role": "user",
        "content": json.dumps(descriptions, ensure_ascii=False)
    }

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[system_msg, user_msg]
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except:
        return descriptions

creds_dict = st.secrets["gcp_service_account"]

worker_to_payable = {
    "Christian Granados (Christian)": "Christian Granados (Vendor)",
    "Eddy (Christian)": "Christian Granados (Vendor)",
    "Juan Carlos Aguilar (Christian)": "Christian Granados (Vendor)",
    "Jose (Christian)": "Christian Granados (Vendor)",
    "Osvaldo Ramirez (Ozzy)": "Jessica Ajtun",
    "Jose Zalasar (Ozzy)": "Jessica Ajtun",
    "Luis De Leon (Ozzy)": "Jessica Ajtun",
    "Rufino Gonzales (Ozzy)": "Jessica Ajtun",
    "Mymor Areola (Ozzy)": "Jessica Ajtun",
    "Fernando Vasqes (Ozzy)": "Jessica Ajtun",
    "Junior Ramierez (Ozzy)": "Jessica Ajtun",
    "Leonidas Yoc (Ozzy)": "Jessica Ajtun",
    "Estvardo Serrano (Ozzy)": "Jessica Ajtun",
    "Nelson Vasqes (Ozzy)": "Jessica Ajtun",
    "Erick Mendez (Ozzy)": "Jessica Ajtun",
    "Andres De Jesus (Andres)": "Andres De Jesus",
    "Victor (Andres)": "Andres De Jesus",
    "Enrique (Andres)": "Andres De Jesus",
    "Kike (Andres)": "Andres De Jesus"
}

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

if "num_rows" not in st.session_state:
    st.session_state.num_rows = 1
if "dates" not in st.session_state:
    st.session_state.dates = [date.today()]

for i in range(len(st.session_state.dates)):
    if isinstance(st.session_state.dates[i], str):
        try:
            st.session_state.dates[i] = datetime.strptime(st.session_state.dates[i], "%m/%d/%Y").date()
        except:
            st.session_state.dates[i] = date.today()

if len(st.session_state.dates) < st.session_state.num_rows:
    for _ in range(st.session_state.num_rows - len(st.session_state.dates)):
        st.session_state.dates.append(date.today())
elif len(st.session_state.dates) > st.session_state.num_rows:
    st.session_state.dates = st.session_state.dates[:st.session_state.num_rows]

hourly_rates = {
    "Christian Granados (Christian)": 43.75,
    "Andres De Jesus (Andres)": 37.50,
    "Eddy (Christian)": 34.38,
    "Juan Carlos Aguilar (Christian)": 34.38,
    "Jose (Christian)": 25.00,
    "Victor (Andres)": 25.00,
    "Enrique (Andres)": 25.00,
    "Osvaldo Ramirez (Ozzy)": 37.50,
    "Jose Zalasar (Ozzy)": 31.25,
    "Luis De Leon (Ozzy)": 31.25,
    "Rufino Gonzales (Ozzy)": 31.25,
    "Mymor Areola (Ozzy)": 25.00,
    "Fernando Vasqes (Ozzy)": 25.00,
    "Junior Ramierez (Ozzy)": 25.00,
    "Leonidas Yoc (Ozzy)": 25.00,
    "Estvardo Serrano (Ozzy)": 25.00,
    "Nelson Vasqes (Ozzy)": 25.00,
    "Erick Mendez (Ozzy)": 25.00,
    "Kike (Andres)": 25.00,
}

worker_names = list(hourly_rates.keys())
properties = ["Coto", "Milford", "647 Navy", "645 Navy", 'Sagebrush', 'Paramount', '126 Scenic', 'San Marino', 'King Arthur', 'Via Sonoma', 'Highland', 'Channel View', 'Paseo De las Estrellas', 'Marguerite', 'BSD SHOP']

st.title("Timesheet Submission")

if st.button("Reset Timesheet"):
    st.session_state.clear()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

selected_worker = st.selectbox("Select Worker", [""] + worker_names, key="worker_select")
if not selected_worker:
    st.stop()

rate = hourly_rates.get(selected_worker, 0.0)

col1, col2 = st.columns(2)
with col1:
    if st.button("➕ Add Date"):
        st.session_state.num_rows += 1
        st.session_state.dates.append(date.today())
with col2:
    if st.button("🗑️ Remove Last Date") and st.session_state.num_rows > 1:
        st.session_state.num_rows -= 1
        st.session_state.dates.pop()

# --- Form Input ---
with st.form("multi_timesheet_form"):
    entries = []
    for i in range(st.session_state.num_rows):
        st.markdown(f"### Entry {i + 1}")
        st.session_state.dates[i] = st.date_input("Labor Date", value=st.session_state.dates[i], key=f"date_{i}")
        col1, col2 = st.columns(2)
        with col1:
            hours = st.number_input("Hours Worked", min_value=0.0, step=0.5, key=f"hours_{i}")
        with col2:
            property_choice = st.selectbox("Select Property", [""] + properties, index=0, key=f"property_{i}")
            
        manual_property = st.text_input("Or Enter Property", key=f"manual_property_{i}").strip()
        effective_property = manual_property if manual_property else property_choice
        
        payable = worker_to_payable.get(selected_worker, "")
        st.markdown(f"**Payable Party:** {payable}")
        description = st.text_area("Description of Work", key=f"description_{i}")
        amount = round(hours * rate, 2)
        entries.append({
            "Date Invoiced": st.session_state.dates[i].strftime("%m/%d/%Y"),
            "Worker Name": selected_worker,
            "Hours": hours,
            "Property": effective_property,
            "Amount": amount,
            "Payable Party": payable,
            "Project Description": description
        })
    review_clicked = st.form_submit_button("Make Changes & Review Summary")

if review_clicked:
    st.session_state.entries_preview = entries

if "entries_preview" in st.session_state:
    df_preview = pd.DataFrame(st.session_state.entries_preview)
    df_preview = df_preview[
        (df_preview["Worker Name"].str.strip() != "") &
        (df_preview["Payable Party"].str.strip() != "") &
        (df_preview["Hours"] > 0)
    ]

    if not df_preview.empty:
        
        st.markdown("**📅 All Entries**")
        st.table(df_preview[["Date Invoiced", "Hours", "Property"]])

        st.subheader("📊 Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Total Hours by Worker**")
            st.table(df_preview.groupby("Worker Name")["Hours"].sum().reset_index())
        with col2:
            st.markdown("**Total Hours by Payable Party**")
            st.table(df_preview.groupby("Payable Party")["Hours"].sum().reset_index())

        if st.button("✅ Confirm & Submit Timesheet"):
            df = df_preview.copy()
            invalid = [
                idx + 1 for idx, row in df.iterrows()
                if not all([row["Date Invoiced"], row["Property"], row["Payable Party"], row["Project Description"]])
            ]
            if invalid:
                st.error(f"Fill out all fields for entry(s): {', '.join(map(str, invalid))}")
                st.stop()

            with st.spinner("Processing and uploading..."):
                def assign_cost_codes(descriptions):
                    prompt = (
                        "You are given a list of project descriptions. Some may be in Spanish. Translate each to English if necessary. For each description, choose exactly **one** most appropriate cost code "
                        "from the mapping below. Do not explain your choices. Only respond with a JSON list of strings — one cost code per description, "
                        "in the same order. Do not include multiple codes per item. Do not include extra text.\n\n"
                        "Cost Code Mapping:\n" + cost_code_mapping_text + "\n\n" +
                        "Descriptions:\n" + "\n".join([f"{i+1}. {desc}" for i, desc in enumerate(descriptions)]) +
                        "\n\nRespond in this format:\n[\"CODE - Description\", ...]"
                    ) 
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    try:
                        return json.loads(response.choices[0].message.content)
                    except:
                        st.error("Error parsing cost codes.")
                        return [""] * len(descriptions)
                df["Project Description"] = translate_to_english_if_needed(df["Project Description"].tolist())
                codes = assign_cost_codes(df["Project Description"].tolist())

                if len(codes) > len(df):
                    codes = codes[:len(df)]
                elif len(codes) < len(df):
                    codes += [""] * (len(df) - len(codes))
                
                df["Cost Code"] = [
                    c.split(",")[0].strip() if isinstance(c, str)
                    else c[0].strip() if isinstance(c, list) and c
                    else ""
                    for c in codes
                ]
                df['Date Paid'] = None
                df['Unique ID'] = None
                df['Item Name'] = None
                df['Claim Number'] = None
                df['QB Property'] = None
                df['Invoice Number'] = None
                df['Payment Method'] = None
                df['Status'] = None
                df['Form'] = "LABOR"
                df['Drive Link'] = None
                df['Equation Description'] = (
                    pd.to_datetime(df['Date Invoiced']).dt.strftime("%m/%d/%Y") + " " +
                    df['Worker Name'] + " " +
                    df['Project Description']
                )

                final_df = df[["Date Paid", "Date Invoiced", "Unique ID", "Claim Number", "Worker Name", "Hours", "Item Name",
                               "Property", "QB Property", "Amount", 'Payable Party', 'Project Description',
                               "Invoice Number", "Cost Code", 'Payment Method', "Status", "Form", 'Drive Link', 'Equation Description']]

                def upload_to_google_sheet(df):
                    from gspread.utils import rowcol_to_a1
                    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                    client = gspread.authorize(creds)
                    sheet = client.open("BSD Master Data Submittals")
                    worksheet = sheet.worksheet("Master Data")
                    existing = worksheet.get_all_values()
                    start_row = len(existing) + 1 if existing else 2
                    if not existing:
                        worksheet.append_row(df.columns.tolist(), value_input_option="USER_ENTERED")
                    data = df.values.tolist()
                    end_row = start_row + len(data) - 1
                    cell_range = f"A{start_row}:{rowcol_to_a1(end_row, len(df.columns))}"
                    worksheet.update(cell_range, data, value_input_option="USER_ENTERED")

                upload_to_google_sheet(final_df)
                st.success("✅ Timesheet entries submitted.")
    else:
        st.info("No complete entries to summarize.")

