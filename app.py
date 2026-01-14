import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_handler as db
from datetime import timedelta, datetime
import re

# --- Page Config ---
st.set_page_config(page_title="Work & Tax Tracker V3", layout="wide", page_icon="🇦🇺")

# --- Init DB ---
db.init_db()

# --- Feature 1.3: Input Formatting Helper ---
def normalize_time_input(t_str):
    """Converts various time inputs (9am, 1730, 5pm) to HH:MM format."""
    if not isinstance(t_str, str): return ""
    t_str = t_str.lower().strip()
    if not t_str: return ""
    
    # Regex for 9am or 5pm
    am_pm_match = re.match(r"(\d{1,2})([ap]m)", t_str)
    if am_pm_match:
        hr = int(am_pm_match.group(1))
        meridian = am_pm_match.group(2)
        if meridian == 'pm' and hr != 12: hr += 12
        if meridian == 'am' and hr == 12: hr = 0
        return f"{hr:02d}:00"
    
    # Regex for 1730 or 0900
    four_digit = re.match(r"(\d{4})", t_str)
    if four_digit and len(t_str) == 4:
        return f"{t_str[:2]}:{t_str[2:]}"
        
    return t_str # Return original if no match (fallback)

def get_financial_year(date_obj):
    if pd.isnull(date_obj): return "Unknown"
    if date_obj.month >= 7:
        return f"FY{date_obj.year % 100}/{(date_obj.year + 1) % 100}"
    else:
        return f"FY{(date_obj.year - 1) % 100}/{date_obj.year % 100}"

def classify_day_type(row):
    loc = str(row['location']).strip()
    if loc in ['RDO', 'Public Holiday', 'On leave', 'Public holiday', 'Annual Leave', 'Sick Leave']: return 'Leave/RDO'
    if loc == 'Working from home': return 'WFH Day'
    if loc == 'Normal work location': return 'Office Day'
    if loc == 'AFTER HOURS': return 'After Hours'
    return 'Other'

# --- Load Data ---
st.sidebar.title("🇦🇺 Tax Tracker V3.0")
df = db.load_data()

# --- Sidebar Filters ---
selected_filter_type = st.sidebar.radio("Filter By:", ["Financial Year", "Calendar Year"])
df_filtered = pd.DataFrame()
current_selection_label = "All Time"

if not df.empty:
    df['Financial_Year'] = df['date'].apply(get_financial_year)
    df['Calendar_Year'] = df['date'].dt.year
    df['day_type'] = df.apply(classify_day_type, axis=1)

    # 1. Primary Filter: Year
    if selected_filter_type == "Financial Year":
        options = ['All Time'] + sorted(df['Financial_Year'].unique().tolist(), reverse=True)
        selected_fy = st.sidebar.selectbox("Select FY", options)
        current_selection_label = selected_fy
        if selected_fy != 'All Time':
            df_filtered = df[df['Financial_Year'] == selected_fy]
        else:
            df_filtered = df.copy()
            
    else: # Calendar Year
        options = ['All Time'] + sorted(df['Calendar_Year'].unique().tolist(), reverse=True)
        selected_cy = st.sidebar.selectbox("Select Year", options)
        current_selection_label = str(selected_cy)
        if selected_cy != 'All Time':
            df_filtered = df[df['Calendar_Year'] == selected_cy]
        else:
            df_filtered = df.copy()

    # 2. Secondary Filter: Months (Multi-Select)
    if not df_filtered.empty:
        # Get unique months present in the currently filtered data
        # Sort by month number (1-12) to ensure chronological order in the dropdown
        available_month_nums = sorted(df_filtered['date'].dt.month.unique())
        
        # Map numbers to names (e.g., 1 -> 'Jan')
        month_map = {m: datetime(2000, m, 1).strftime('%b') for m in available_month_nums}
        month_options = [month_map[m] for m in available_month_nums]
        
        selected_months = st.sidebar.multiselect(
            "Select Month(s)", 
            options=month_options,
            default=[],
            placeholder="All Months (Select to filter)"
        )
        
        # Apply Filter if months are selected
        if selected_months:
            # Filter rows where the month name matches one of the selections
            df_filtered = df_filtered[df_filtered['date'].dt.strftime('%b').isin(selected_months)]
            
            # Update Label for the charts
            if len(selected_months) <= 3:
                current_selection_label += f" ({', '.join(selected_months)})"
            else:
                current_selection_label += " (Multiple Months)"

else:
    df_filtered = pd.DataFrame()

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Analysis", "💰 Tax Calculator", "🛠 Data Management"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.header(f"Performance Report: {current_selection_label}")
    
    if df_filtered.empty:
        st.info("No data found for this period.")
    else:
        # Metrics
        wfh_days = len(df_filtered[df_filtered['day_type'] == 'WFH Day'])
        office_days = len(df_filtered[df_filtered['day_type'] == 'Office Day'])
        total_working_days = wfh_days + office_days
        wfh_pct = (wfh_days / total_working_days * 100) if total_working_days > 0 else 0

        # Row 1 Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Recorded Days", len(df_filtered))
        m2.metric("In Office", office_days)
        m3.metric("WFH Days", wfh_days)
        m4.metric("WFH %", f"{wfh_pct:.1f}%")
        
        st.divider()

        # --- Feature 2.1: Compare to Last Year ---
        c_chart1, c_chart2 = st.columns([2, 1])
        
        with c_chart1:
            st.subheader("Work Trends")
            show_comparison = st.checkbox("Compare to Previous Year", value=False)
            
            # Prepare current data
            df_trend = df_filtered.copy()
            df_trend['Month'] = df_trend['date'].dt.strftime('%b') # Jan, Feb
            df_trend['MonthNum'] = df_trend['date'].dt.month
            
            # Group current
            current_trend = df_trend[df_trend['day_type'].isin(['WFH Day', 'Office Day'])]\
                .groupby(['MonthNum', 'Month', 'day_type']).size().reset_index(name='Days')
            current_trend['Period'] = 'Current Selection'

            final_trend = current_trend

            if show_comparison and selected_filter_type == "Financial Year" and selected_fy != "All Time":
                # Logic to fetch previous FY
                try:
                    curr_yr_start = int(selected_fy[2:4]) # FY23/24 -> 23
                    prev_fy = f"FY{curr_yr_start-1}/{curr_yr_start}"
                    
                    df_prev = df[df['Financial_Year'] == prev_fy].copy()
                    if not df_prev.empty:
                        df_prev['Month'] = df_prev['date'].dt.strftime('%b')
                        df_prev['MonthNum'] = df_prev['date'].dt.month
                        prev_trend = df_prev[df_prev['day_type'].isin(['WFH Day', 'Office Day'])]\
                            .groupby(['MonthNum', 'Month', 'day_type']).size().reset_index(name='Days')
                        prev_trend['Period'] = f"Prev Year ({prev_fy})"
                        final_trend = pd.concat([current_trend, prev_trend])
                    else:
                        st.caption("No data available for previous financial year.")
                except:
                    pass

            fig_line = px.line(
                final_trend.sort_values('MonthNum'), 
                x="Month", y="Days", 
                color="day_type", 
                line_dash="Period", # Dashed line for previous year
                title=f"Monthly Trends {'(vs Previous Year)' if show_comparison else ''}",
                markers=True,
                color_discrete_map={"Office Day": "#1f77b4", "WFH Day": "#2ca02c"}
            )
            st.plotly_chart(fig_line, use_container_width=True)

        with c_chart2:
            st.subheader("Gap Analysis")
            # --- Feature 1.2: Gap Analysis ---
            if not df_filtered.empty:
                min_date = df_filtered['date'].min()
                max_date = df_filtered['date'].max()
                
                # Create perfect range
                all_dates = pd.date_range(start=min_date, end=max_date)
                existing_dates = pd.to_datetime(df_filtered['date']).dt.normalize()
                
                # Find difference
                missing_dates = all_dates.difference(existing_dates)
                
                st.write(f"**Date Range:** {min_date.strftime('%d/%m')} - {max_date.strftime('%d/%m')}")
                st.metric("Missing Logs", len(missing_dates), delta_color="inverse")
                
                with st.expander("Show Missing Dates"):
                    if len(missing_dates) > 0:
                        st.dataframe(pd.DataFrame({"Missing Dates": missing_dates.strftime('%Y-%m-%d')}), height=200)
                    else:
                        st.success("No gaps found in this period!")

# --- TAB 2: TAX CALCULATOR ---
with tab2:
    st.header(f"Tax Calculator: {current_selection_label}")
    
    if df_filtered.empty:
        st.warning("No data loaded.")
    else:
        # --- Feature 3.1: Deduction Method Switch ---
        st.markdown("### ⚙️ Method Selection")
        method = st.radio("Choose Deduction Method", ["Fixed Rate Method", "Actual Cost Method"], horizontal=True)
        
        wfh_hours = df_filtered[df_filtered['location'] == 'Working from home']['base_hours'].sum()
        ah_hours = df_filtered[df_filtered['location'] == 'AFTER HOURS']['base_hours'].sum()
        ot_hours = df_filtered['ot_hours'].sum()
        total_deductible_hours = wfh_hours + ah_hours + ot_hours

        estimated_deduction = 0.0

        if method == "Fixed Rate Method":
            col1, col2 = st.columns(2)
            rate = col1.number_input("Rate ($/hr)", value=0.67, step=0.01, help="ATO 2024 Fixed Rate is $0.67")
            estimated_deduction = total_deductible_hours * rate
            
            st.info(f"ℹ️Covers: Energy, Phone, Internet, Stationery. Depreciation is claimed separately.")
            
        else: # Actual Cost
            st.markdown("#### Enter Annual Expenses (allocate % for work)")
            c1, c2, c3 = st.columns(3)
            electricity = c1.number_input("Total Electricity Bill ($)", value=0.0)
            percent_work = c2.number_input("Work Use %", value=10.0, max_value=100.0) / 100
            internet = c3.number_input("Total Internet Bill ($)", value=0.0)
            
            c4, c5 = st.columns(2)
            depreciation = c4.number_input("Depreciation (Computer/Chair) ($)", value=0.0)
            other = c5.number_input("Other (Phone/Stationery) ($)", value=0.0)
            
            # Simple calc logic
            est_utilities = (electricity + internet) * percent_work
            estimated_deduction = est_utilities + depreciation + other
            
            st.info("ℹ️ Requires strict record keeping of bills and floor area/time usage logs.")

        st.divider()
        
        # Results
        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("Total Deductible Hours", f"{total_deductible_hours:,.2f}")
        res_col2.metric("Est. Tax Deduction", f"${estimated_deduction:,.2f}", delta="Taxable Income Reduction")
        
        # Visualization of Monthly Contribution
        df_monthly = df_filtered.copy()
        df_monthly['Month'] = df_monthly['date'].dt.strftime('%Y-%m')
        monthly_hrs = df_monthly.groupby('Month')[['base_hours', 'ot_hours']].sum().reset_index()
        monthly_hrs['Total'] = monthly_hrs['base_hours'] + monthly_hrs['ot_hours']
        
        fig_bar = px.bar(monthly_hrs, x='Month', y='Total', title="Monthly Deductible Hours")
        st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 3: DATA MANAGEMENT ---
with tab3:
    st.header("🛠 Data Management")
    
    task = st.selectbox("Choose Action", ["Generate Weekly Schedule", "Bulk Edit Records", "Upload File", "Delete Database"])
    
    # --- Feature 1.1: Conflict Detection in Generator ---
    if task == "Generate Weekly Schedule":
        st.subheader("Weekly Schedule Generator")
        
        c1, c2 = st.columns(2)
        start_date = c1.date_input("From Date")
        end_date = c2.date_input("To Date")
        
        # Conflict Check
        if start_date <= end_date:
            conflicts = db.check_dates_exist(start_date, end_date)
            if conflicts:
                st.warning(f"⚠️ Warning: {len(conflicts)} dates in this range already have data. Generating will skip or duplicate depending on hash.")
                with st.expander("View Conflicting Dates"):
                    st.write(conflicts)
        
        # Config UI (Simplified for brevity, similar to V1)
        st.markdown("**Day Configuration**")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        config = {}
        cols = st.columns(5)
        for i, day in enumerate(days):
            loc = cols[i].selectbox(day, ["Office", "WFH", "Off"], index=1 if i>2 else 0, key=f"d_{i}")
            config[day] = loc

        if st.button("Generate"):
            rows = []
            curr = start_date
            while curr <= end_date:
                day_name = curr.strftime("%A")
                if day_name in config and config[day_name] != "Off":
                    loc_map = {"Office": "Normal work location", "WFH": "Working from home"}
                    # Feature 1.3: Auto-format time here
                    rows.append({
                        "date": curr,
                        "location": loc_map.get(config[day_name], config[day_name]),
                        "base_hours": 7.6,
                        "ot_hours": 0.0,
                        "start_time": normalize_time_input("9am"), 
                        "finish_time": normalize_time_input("5pm")
                    })
                curr += timedelta(days=1)
            
            if rows:
                count = db.insert_data(pd.DataFrame(rows))
                st.success(f"Generated {count} records!")

    # --- Feature 2.2: Bulk Edit ---
    elif task == "Bulk Edit Records":
        st.subheader("Bulk Update")
        st.info("Change location for a specific date range (e.g., if you were sick for a week).")
        
        bc1, bc2 = st.columns(2)
        b_start = bc1.date_input("Start Date", key="b_start")
        b_end = bc2.date_input("End Date", key="b_end")
        
        target_field = st.selectbox("Field to Update", ["location", "base_hours"])
        
        if target_field == "location":
            new_val = st.selectbox("New Value", ["Working from home", "Normal work location", "Sick Leave", "Annual Leave"])
        else:
            new_val = st.number_input("New Hours", value=7.6)
            
        if st.button("Apply Bulk Update"):
            affected = db.bulk_update_range(b_start, b_end, target_field, new_val)
            st.success(f"Updated {affected} records successfully.")
            st.cache_data.clear()

    elif task == "Upload File":
        st.subheader("Import Excel/CSV")
        uploaded_file = st.file_uploader("Upload", type=['xlsx', 'csv'])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'): df_in = pd.read_csv(uploaded_file)
                else: df_in = pd.read_excel(uploaded_file)
                
                # Apply normalization to time columns before inserting
                if 'Start' in df_in.columns:
                    df_in['Start'] = df_in['Start'].astype(str).apply(normalize_time_input)
                
                # ... (rest of standard cleaning logic same as V1) ...
                # Ideally map columns then insert
                # st.write("Import logic placeholder - ensure column mapping matches DB")
                
            except Exception as e:
                st.error(str(e))

    elif task == "Delete Database":
        if st.button("DELETE ALL DATA"):
            db.clear_database()
            st.success("Database wiped.")