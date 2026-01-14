import streamlit as st
import pandas as pd
import plotly.express as px
import db_handler as db
from datetime import timedelta, datetime
import re

# --- Page Config ---
st.set_page_config(page_title="Work & Tax Tracker V2.0", layout="wide", page_icon="🇦🇺")
db.init_db()

def normalize_time_input(t_str):
    if not isinstance(t_str, str): return ""
    t_str = t_str.lower().strip()
    if not t_str: return ""
    am_pm_match = re.match(r"(\d{1,2})([ap]m)", t_str)
    if am_pm_match:
        hr = int(am_pm_match.group(1))
        meridian = am_pm_match.group(2)
        if meridian == 'pm' and hr != 12: hr += 12
        if meridian == 'am' and hr == 12: hr = 0
        return f"{hr:02d}:00"
    four_digit = re.match(r"(\d{4})", t_str)
    if four_digit and len(t_str) == 4:
        return f"{t_str[:2]}:{t_str[2:]}"
    return t_str

def get_financial_year(date_obj):
    if pd.isnull(date_obj): return "Unknown"
    return f"FY{date_obj.year % 100}/{(date_obj.year + 1) % 100}" if date_obj.month >= 7 else f"FY{(date_obj.year - 1) % 100}/{date_obj.year % 100}"

def classify_day_type(row):
    loc = str(row.get('location', '')).strip()
    if loc in ['RDO', 'Public Holiday', 'On leave', 'Public holiday', 'Annual Leave', 'Sick Leave']: return 'Leave/RDO'
    if loc == 'Working from home': return 'WFH Day'
    if loc == 'Normal work location': return 'Office Day'
    if loc == 'AFTER HOURS': return 'After Hours'
    return 'Other'

# --- Sidebar ---
st.sidebar.title("🇦🇺 Tax Tracker V2.0.0")

# NEW: Date and Time Header
now = datetime.now()
st.sidebar.caption(f"📅 {now.strftime('%A, %d %b %Y')}")
st.sidebar.caption(f"⏰ Last Sync: {now.strftime('%H:%M:%S')}")
st.sidebar.divider()

# --- Load Data & Sidebar Filters ---
df = db.load_data()
selected_filter_type = st.sidebar.radio("Filter By:", ["Financial Year", "Calendar Year"])
df_filtered = pd.DataFrame()
current_selection_label = "All Time"

if not df.empty:
    df['Financial_Year'] = df['date'].apply(get_financial_year)
    df['Calendar_Year'] = df['date'].dt.year.astype(str)
    df['day_type'] = df.apply(classify_day_type, axis=1)

    year_col = 'Financial_Year' if selected_filter_type == "Financial Year" else 'Calendar_Year'
    year_options = sorted(df[year_col].unique().tolist(), reverse=True)
    selected_years = st.sidebar.multiselect(f"Select {selected_filter_type}(s)", options=year_options, default=[year_options[0]] if year_options else [])

    if selected_years:
        df_filtered = df[df[year_col].isin(selected_years)]
        current_selection_label = ", ".join(selected_years)
    else:
        df_filtered = df.copy()

    # Month Filter
    available_months = sorted(df_filtered['date'].dt.month.unique())
    month_map = {m: datetime(2000, m, 1).strftime('%b') for m in available_months}
    selected_months = st.sidebar.multiselect("Select Month(s)", options=[month_map[m] for m in available_months])
    if selected_months:
        df_filtered = df_filtered[df_filtered['date'].dt.strftime('%b').isin(selected_months)]
        current_selection_label += f" ({', '.join(selected_months)})"

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Analysis", "💰 Tax Calculator", "🛠 Data Management"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.header(f"Performance Report: {current_selection_label}")
    if df_filtered.empty:
        st.info("No data found for this period. Go to Data Management to upload or generate logs.")
    else:
        wfh_days = len(df_filtered[df_filtered['day_type'] == 'WFH Day'])
        office_days = len(df_filtered[df_filtered['day_type'] == 'Office Day'])
        total_working_days = wfh_days + office_days
        wfh_pct = (wfh_days / total_working_days * 100) if total_working_days > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Recorded Days", len(df_filtered))
        m2.metric("In Office", office_days)
        m3.metric("WFH Days", wfh_days)
        m4.metric("WFH %", f"{wfh_pct:.1f}%")
        st.divider()

        c_chart1, c_chart2 = st.columns([2, 1])
        with c_chart1:
            st.subheader("Work Trends")
            df_trend = df_filtered.copy()
            df_trend['Month'] = df_trend['date'].dt.strftime('%b')
            df_trend['MonthNum'] = df_trend['date'].dt.month
            year_group_col = 'Financial_Year' if selected_filter_type == "Financial Year" else 'Calendar_Year'
            final_trend = df_trend[df_trend['day_type'].isin(['WFH Day', 'Office Day'])].groupby(['MonthNum', 'Month', year_group_col, 'day_type']).size().reset_index(name='Days')
            fig_line = px.line(final_trend.sort_values('MonthNum'), x="Month", y="Days", color=year_group_col, line_dash="day_type", title=f"Monthly Trends: {current_selection_label}", markers=True, category_orders={"Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]})
            fig_line.update_layout(hovermode="x unified")
            st.plotly_chart(fig_line, use_container_width=True)
        with c_chart2:
            st.subheader("Gap Analysis")
            min_date, max_date = df_filtered['date'].min(), df_filtered['date'].max()
            all_dates = pd.date_range(start=min_date, end=max_date)
            missing_dates = all_dates.difference(pd.to_datetime(df_filtered['date']).dt.normalize())
            st.write(f"**Range:** {min_date.strftime('%d/%m')} - {max_date.strftime('%d/%m')}")
            st.metric("Missing Logs", len(missing_dates), delta_color="inverse")
            with st.expander("Show Missing Dates"):
                if len(missing_dates) > 0: st.dataframe(pd.DataFrame({"Missing Dates": missing_dates.strftime('%Y-%m-%d')}), height=200)
                else: st.success("No gaps found!")

# --- TAB 2: TAX CALCULATOR ---
with tab2:
    st.header(f"Tax Calculator: {current_selection_label}")
    if df_filtered.empty:
        st.warning("Please upload data to calculate deductions.")
    else:
        method = st.radio("Choose Deduction Method", ["Fixed Rate Method", "Actual Cost Method"], horizontal=True)
        wfh_hours = df_filtered[df_filtered['location'] == 'Working from home']['base_hours'].sum()
        ah_hours = df_filtered[df_filtered['location'] == 'AFTER HOURS']['base_hours'].sum()
        ot_hours = df_filtered['ot_hours'].sum()
        total_deductible_hours = wfh_hours + ah_hours + ot_hours
        estimated_deduction = 0.0

        if method == "Fixed Rate Method":
            col1, col2 = st.columns(2)
            rate = col1.number_input("Rate ($/hr)", value=0.67, step=0.01)
            estimated_deduction = total_deductible_hours * rate
            st.info("ℹ️ Fixed Rate covers Energy, Phone, Internet, and Stationery.")
        else:
            c1, c2, c3 = st.columns(3)
            electricity = c1.number_input("Electricity ($)", value=0.0)
            percent_work = c2.number_input("Work Use %", value=10.0) / 100
            internet = c3.number_input("Internet ($)", value=0.0)
            c4, c5 = st.columns(2)
            depreciation = c4.number_input("Depreciation ($)", value=0.0)
            other = c5.number_input("Other ($)", value=0.0)
            estimated_deduction = ((electricity + internet) * percent_work) + depreciation + other

        st.divider()
        res_col1, res_col2 = st.columns(2)
        res_col1.metric("Total Deductible Hours", f"{total_deductible_hours:,.2f}")
        res_col2.metric("Est. Tax Deduction", f"${estimated_deduction:,.2f}")
        
        df_monthly = df_filtered.copy()
        df_monthly['Month'] = df_monthly['date'].dt.strftime('%Y-%m')
        monthly_hrs = df_monthly.groupby('Month')[['base_hours', 'ot_hours']].sum().reset_index()
        monthly_hrs['Total'] = monthly_hrs['base_hours'] + monthly_hrs['ot_hours']
        fig_bar = px.bar(monthly_hrs, x='Month', y='Total', title="Total Deductible Hours by Month")
        st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 3: DATA MANAGEMENT ---
with tab3:
    task = st.selectbox("Choose Action", ["Generate Weekly Schedule", "Bulk Edit Records", "Upload File", "Delete Database"])
    
    if task == "Generate Weekly Schedule":
        st.subheader("7-Day Schedule Generator")
        c1, c2 = st.columns(2)
        s_date, e_date = c1.date_input("From Date"), c2.date_input("To Date")
        conflicts = db.check_dates_exist(s_date, e_date)
        if conflicts: st.warning(f"⚠️ {len(conflicts)} dates already have data.")

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekly_config = {}
        for d in days:
            cols = st.columns([1.5, 2, 1, 1])
            loc = cols[0].selectbox(d, ["Office", "WFH", "Off", "Leave"], index=0 if d not in ["Saturday", "Sunday"] else 2, key=f"l_{d}")
            times = cols[1].text_input("Times", "09:00-17:00" if loc != "Off" else "", key=f"t_{d}")
            base_h = cols[2].number_input("Base", value=7.6 if loc not in ["Off", "Leave"] else 0.0, key=f"b_{d}")
            ot_h = cols[3].number_input("OT", value=0.0, key=f"o_{d}")
            weekly_config[d] = {"loc": loc, "times": times, "base": base_h, "ot": ot_h}

        if st.button("Generate & Save", type="primary"):
            rows = []
            curr = s_date
            l_map = {"Office": "Normal work location", "WFH": "Working from home", "Leave": "On leave"}
            while curr <= e_date:
                cfg = weekly_config[curr.strftime("%A")]
                if cfg["loc"] != "Off":
                    t_parts = cfg["times"].split('-')
                    rows.append({"date": curr, "location": l_map.get(cfg["loc"], cfg["loc"]), "base_hours": cfg["base"], "ot_hours": cfg["ot"], "start_time": normalize_time_input(t_parts[0]) if len(t_parts)>0 else "", "finish_time": normalize_time_input(t_parts[1]) if len(t_parts)>1 else ""})
                curr += timedelta(days=1)
            db.insert_data(pd.DataFrame(rows))
            st.success("Generated!")
            st.rerun()

    elif task == "Bulk Edit Records":
        st.subheader("Multi-Lens Bulk Update")
        with st.form("bulk_form"):
            bc1, bc2 = st.columns(2)
            bs, be = bc1.date_input("Start"), bc2.date_input("End")
            payload = {}
            e1, e2 = st.columns(2)
            if e1.checkbox("Update Location"): payload['location'] = e1.selectbox("New Loc", ["Working from home", "Normal work location", "On leave"])
            if e2.checkbox("Update Base Hours"): payload['base_hours'] = e2.number_input("New Base", value=7.6)
            if e1.checkbox("Update OT"): payload['ot_hours'] = e1.number_input("New OT", value=0.0)
            if st.form_submit_button("Apply Updates"):
                if payload:
                    db.bulk_update_multi_field(bs, be, payload)
                    st.success("Updated!")
                    st.rerun()

    elif task == "Upload File":
        up_file = st.file_uploader("Choose file", type=['xlsx', 'csv'])
        if up_file:
            if 'temp_df' not in st.session_state:
                df_up = pd.read_csv(up_file) if up_file.name.endswith('.csv') else pd.read_excel(up_file)
                df_up.columns = df_up.columns.str.strip()
                col_map = {'Date': 'date', 'Location': 'location', 'Start': 'start_time', 'Finish': 'finish_time', 'Break': 'break_duration', 'Hours Worked': 'base_hours', 'OT HOURS': 'ot_hours'}
                df_up = df_up.rename(columns=col_map)
                db_cols = ['date', 'location', 'start_time', 'finish_time', 'break_duration', 'base_hours', 'ot_hours']
                available = [c for c in db_cols if c in df_up.columns]
                df_up = df_up[available]
                df_up['date'] = pd.to_datetime(df_up['date'], format='mixed', dayfirst=True, errors='coerce')
                df_up = df_up.dropna(subset=['date'])
                st.session_state.temp_df = df_up
                
            edited = st.data_editor(st.session_state.temp_df, use_container_width=True, num_rows="dynamic")
            if st.button("Confirm and Upload"):
                db.insert_data(edited)
                st.success("Imported!")
                del st.session_state.temp_df
                st.rerun()

    elif task == "Delete Database":
        st.error("☢️ CRITICAL: Permanent Data Loss")
        security = st.text_input("Type 'DELETE' in all caps to confirm:")
        if st.button("Wipe Records") and security == "DELETE":
            db.clear_database()
            st.success("Database cleared.")
            st.rerun()