import streamlit as st
import pandas as pd
import numpy as np
import datetime
import json
import os
from supabase import create_client, Client
from groq import Groq

# Page Config
st.set_page_config(
    page_title="Smart Financial Ledger v1",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling for Mobile Responsiveness & Polish
st.markdown("""
<style>
    /* Global & Responsive Adjustments */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 1200px;
    }
    
    /* Card Container */
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #6c757d;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #212529;
        margin-top: 0.25rem;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25em 0.6em;
        font-size: 0.85rem;
        font-weight: 700;
        border-radius: 4px;
        color: #fff;
    }
    .status-balance { background-color: #28a745; }
    .status-inbalance { background-color: #dc3545; }
    
    /* Form & Button Adjustments for Touch Targets */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 2.75rem;
        font-weight: 600;
    }
    
    /* Table Responsive Wrapper */
    .table-container {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
</style>
""", unsafe_allow_html=True)

# Helper for Currency Formatting
def fmt_idr(val):
    if pd.isna(val):
        return "Rp 0"
    return f"Rp {int(val):,}".replace(",", ".")

# ------------------------------------------------------------------------------
# 1. DATABASE & AUTHENTICATION WRAPPER
# ------------------------------------------------------------------------------
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY", ""))
    if url and key:
        try:
            return create_client(url, key)
        except Exception as e:
            st.error(f"Supabase connection error: {e}")
            return None
    return None

supabase = init_supabase()

def init_groq():
    groq_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    if groq_key:
        try:
            return Groq(api_key=groq_key)
        except Exception:
            return None
    return None

groq_client = init_groq()

# Fallback In-Memory Initial Seed Data (From enhanced model_3.xlsx)
def init_session_demo_data():
    if "demo_income" not in st.session_state:
        st.session_state.demo_income = pd.DataFrame([
            {"id": "1", "date": "2026-09-01", "description": "Last month leftover gapok", "amount": 1889883},
            {"id": "2", "date": "2026-09-01", "description": "Last month leftover tukin", "amount": 1552497},
            {"id": "3", "date": "2026-09-01", "description": "gapok", "amount": 2798600},
            {"id": "4", "date": "2026-09-01", "description": "tukin", "amount": 11450000},
        ])
    if "demo_fix_spendings" not in st.session_state:
        st.session_state.demo_fix_spendings = pd.DataFrame([
            {"id": "1", "date": "2026-09-01", "description": "Cicilan kartu kredit", "amount": 1936863},
            {"id": "2", "date": "2026-09-01", "description": "Iuran kantor", "amount": 200000},
            {"id": "3", "date": "2026-09-01", "description": "Bulanan ke rumah", "amount": 2002500},
            {"id": "4", "date": "2026-09-02", "description": "Rumah dinas", "amount": 25000},
        ])
    if "demo_savings" not in st.session_state:
        st.session_state.demo_savings = pd.DataFrame([
            {"id": "1", "date": "2026-09-01", "description": "Tabungan rutin", "amount": 3830000},
        ])
    if "demo_encumbrance" not in st.session_state:
        st.session_state.demo_encumbrance = pd.DataFrame([
            {"id": "1", "description": "Beli tiket bus tua", "amount": 1500000},
            {"id": "2", "description": "Jatah konsumsi harian", "amount": 4650000},
            {"id": "3", "description": "Listrik", "amount": 305000},
            {"id": "4", "description": "Bensin", "amount": 200000},
            {"id": "5", "description": "Keperluan rumah", "amount": 300000},
            {"id": "6", "description": "Subscription", "amount": 150000},
            {"id": "7", "description": "Paket Internet", "amount": 600000},
            {"id": "8", "description": "Entertainment", "amount": 300000},
        ])
    if "demo_wallets" not in st.session_state:
        st.session_state.demo_wallets = pd.DataFrame([
            {"id": "1", "description": "Starbucks Card", "amount": 8500},
            {"id": "2", "description": "Ovo", "amount": 5680},
            {"id": "3", "description": "Gopay", "amount": 1250},
            {"id": "4", "description": "E-Money", "amount": 14000},
            {"id": "5", "description": "Dana", "amount": 4500},
            {"id": "6", "description": "Cash on hand", "amount": 10000},
            {"id": "7", "description": "Shopee Pay", "amount": 12019},
        ])
    if "demo_records" not in st.session_state:
        st.session_state.demo_records = pd.DataFrame([
            {"id": "1", "date": "2026-09-01", "description": "Sarapan ketoprak mas aris", "allocation": "Jatah konsumsi harian", "cash_basis": -44000, "receivables": 22000, "acrual_basis": -22000},
            {"id": "2", "date": "2026-09-01", "description": "Sarapan ketoprak mas aris", "allocation": "Jatah konsumsi harian", "cash_basis": 22000, "receivables": -22000, "acrual_basis": 0},
            {"id": "3", "date": "2026-09-01", "description": "Top up starbucks", "allocation": "Buffer", "cash_basis": -100000, "receivables": 0, "acrual_basis": -100000},
            {"id": "4", "date": "2026-09-01", "description": "Top up starbucks", "allocation": "Starbucks Card", "cash_basis": 100000, "receivables": 0, "acrual_basis": 100000},
            {"id": "5", "date": "2026-09-01", "description": "Beli starbucks", "allocation": "Starbucks Card", "cash_basis": -49000, "receivables": 0, "acrual_basis": -49000},
            {"id": "6", "date": "2026-09-01", "description": "Beli starbucks", "allocation": "Jatah konsumsi harian", "cash_basis": -49000, "receivables": 24500, "acrual_basis": -24500},
            {"id": "7", "date": "2026-09-01", "description": "Beli starbucks", "allocation": "Jatah konsumsi harian", "cash_basis": 24500, "receivables": -24500, "acrual_basis": 0},
            {"id": "8", "date": "2026-09-01", "description": "Beli starbucks", "allocation": "Buffer", "cash_basis": 49000, "receivables": 0, "acrual_basis": 49000},
            {"id": "9", "date": "2026-09-01", "description": "Parkir", "allocation": "E-Money", "cash_basis": -6000, "receivables": 0, "acrual_basis": -6000},
            {"id": "10", "date": "2026-09-01", "description": "Makan malam", "allocation": "Jatah konsumsi harian", "cash_basis": -56100, "receivables": 0, "acrual_basis": -56100},
            {"id": "11", "date": "2026-09-01", "description": "Tiket bioskop", "allocation": "Entertainment", "cash_basis": -40000, "receivables": 0, "acrual_basis": -40000},
            {"id": "12", "date": "2026-09-01", "description": "Tarik uang", "allocation": "Buffer", "cash_basis": -100000, "receivables": 0, "acrual_basis": -100000},
            {"id": "13", "date": "2026-09-01", "description": "Tarik uang", "allocation": "Cash on hand", "cash_basis": 100000, "receivables": 0, "acrual_basis": 100000},
            {"id": "14", "date": "2026-09-01", "description": "Isi bensin", "allocation": "Bensin", "cash_basis": -67000, "receivables": 0, "acrual_basis": -67000},
            {"id": "15", "date": "2026-09-01", "description": "Isi bensin", "allocation": "Cash on hand", "cash_basis": -67000, "receivables": 0, "acrual_basis": -67000},
            {"id": "16", "date": "2026-09-01", "description": "Isi bensin", "allocation": "Buffer", "cash_basis": 67000, "receivables": 0, "acrual_basis": 67000},
            {"id": "17", "date": "2026-09-02", "description": "Iuran tambahan kantor", "allocation": "Buffer", "cash_basis": -50000, "receivables": 0, "acrual_basis": -50000},
            {"id": "18", "date": "2026-09-02", "description": "Sarapan kopi kaya", "allocation": "Jatah konsumsi harian", "cash_basis": -42000, "receivables": 0, "acrual_basis": -42000},
            {"id": "19", "date": "2026-09-02", "description": "Tiket bus tua", "allocation": "Beli tiket bus tua", "cash_basis": -1500000, "receivables": 0, "acrual_basis": -1500000},
            {"id": "20", "date": "2026-09-02", "description": "Beli point", "allocation": "Jatah konsumsi harian", "cash_basis": -21000, "receivables": 0, "acrual_basis": -21000},
            {"id": "21", "date": "2026-09-02", "description": "Beli kopi orang", "allocation": "Buffer", "cash_basis": -123000, "receivables": 123000, "acrual_basis": 0},
            {"id": "22", "date": "2026-09-02", "description": "Beli kopi orang", "allocation": "Buffer", "cash_basis": 25000, "receivables": -25000, "acrual_basis": 0},
        ])

init_session_demo_data()

# Auth System
if "user" not in st.session_state:
    st.session_state.user = None

def render_auth_sidebar():
    with st.sidebar:
        st.title("👤 User Account")
        if supabase:
            if st.session_state.user is None:
                auth_mode = st.radio("Authentication", ["Log In", "Sign Up"])
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                
                if auth_mode == "Log In" and st.button("Log In"):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = res.user
                        st.success("Logged in successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {e}")
                elif auth_mode == "Sign Up" and st.button("Sign Up"):
                    try:
                        res = supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Sign up successful! Please check your email or log in.")
                    except Exception as e:
                        st.error(f"Sign up failed: {e}")
            else:
                st.write(f"Logged in as: **{st.session_state.user.email}**")
                if st.button("Log Out"):
                    try:
                        supabase.auth.sign_out()
                    except Exception:
                        pass
                    st.session_state.user = None
                    st.rerun()
        else:
            st.info("💡 Running in **Standalone Demo Mode** (Data stored in local session). Configure Supabase credentials in Streamlit secrets for persistent cloud storage.")

render_auth_sidebar()

# ------------------------------------------------------------------------------
# 2. DATA LOADERS & DETERMINISTIC MODEL COMPUTATIONS
# ------------------------------------------------------------------------------
def get_data(table_name):
    if supabase and st.session_state.user:
        try:
            res = supabase.table(table_name).select("*").execute()
            df = pd.DataFrame(res.data)
            return df
        except Exception:
            pass
    return st.session_state[f"demo_{table_name}"].copy()

def calculate_financial_model():
    income_df = get_data("income")
    fix_df = get_data("fix_spendings")
    savings_df = get_data("savings")
    enc_df = get_data("encumbrance")
    wallets_df = get_data("wallets")
    records_df = get_data("records")
    
    total_income = income_df["amount"].sum() if not income_df.empty else 0
    total_fix = fix_df["amount"].sum() if not fix_df.empty else 0
    total_savings = savings_df["amount"].sum() if not savings_df.empty else 0
    total_enc = enc_df["amount"].sum() if not enc_df.empty else 0
    
    buffer_fund = total_income - total_fix - total_savings - total_enc
    total_fund_in_balance = total_income - total_fix - total_savings
    
    # Calculate Realisations per allocation from records
    if not records_df.empty:
        # Normalize column names if needed
        records_df["allocation_clean"] = records_df["allocation"].str.strip().str.lower()
        realisations = records_df.groupby("allocation_clean")["cash_basis"].sum().to_dict()
    else:
        realisations = {}
        
    def get_realisation(name):
        return realisations.get(str(name).strip().lower(), 0)
    
    # Build Model Table Rows
    model_rows = []
    
    # 1. Buffer
    buf_real = get_realisation("Buffer")
    model_rows.append({
        "Allocation": "Buffer",
        "Category": "Buffer Account",
        "Fund": buffer_fund,
        "Realisation": buf_real,
        "Remaining": buffer_fund + buf_real
    })
    
    # 2. Encumbrances
    for _, r in enc_df.iterrows():
        desc = r["description"]
        fund = r["amount"]
        real = get_realisation(desc)
        model_rows.append({
            "Allocation": desc,
            "Category": "Encumbrance Budget",
            "Fund": fund,
            "Realisation": real,
            "Remaining": fund + real
        })
        
    # 3. Wallets
    for _, r in wallets_df.iterrows():
        desc = r["description"]
        fund = r["amount"]
        real = get_realisation(desc)
        model_rows.append({
            "Allocation": desc,
            "Category": "Physical Wallet",
            "Fund": fund,
            "Realisation": real,
            "Remaining": fund + real
        })
        
    model_table = pd.DataFrame(model_rows)
    
    # Total fund in balance summary
    total_realisation = model_table["Realisation"].sum()
    total_remaining = total_fund_in_balance + total_realisation
    
    # Receivables Total
    total_receivables = records_df["receivables"].sum() if not records_df.empty else 0
    
    # Total Outflow calculation (excluding fixed spendings and savings)
    total_outflow = total_realisation - total_fix - total_savings
    
    # Check Balance Status
    balance_check = total_remaining - total_outflow
    status = "Balance" if abs(balance_check - total_income) < 1 else "Inbalance"
    
    return {
        "total_income": total_income,
        "total_fix": total_fix,
        "total_savings": total_savings,
        "total_encumbrance": total_enc,
        "buffer_fund": buffer_fund,
        "total_fund_in_balance": total_fund_in_balance,
        "model_table": model_table,
        "total_realisation": total_realisation,
        "total_remaining": total_remaining,
        "total_receivables": total_receivables,
        "total_outflow": total_outflow,
        "status": status,
        "records_df": records_df
    }

# ------------------------------------------------------------------------------
# 3. MAIN APP INTERFACE & NAVIGATION
# ------------------------------------------------------------------------------
st.title("💳 Smart Financial Ledger")

# Navigation Tabs
tabs = st.tabs([
    "📊 Quick View", 
    "🤖 Journal & AI Assistant", 
    "📈 Model & Allocations", 
    "⚙️ Master Setup"
])

fin_data = calculate_financial_model()

# ==============================================================================
# TAB 1: QUICK VIEW & CONSUMPTION PERFORMANCE
# ==============================================================================
with tabs[0]:
    st.subheader("Overview & Financial Health")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Remaining Fund</div>
            <div class="metric-value">{fmt_idr(fin_data['total_remaining'])}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Receivables</div>
            <div class="metric-value">{fmt_idr(fin_data['total_receivables'])}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Outflow</div>
            <div class="metric-value">{fmt_idr(fin_data['total_outflow'])}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        badge_cls = "status-balance" if fin_data["status"] == "Balance" else "status-inbalance"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Ledger Status</div>
            <div class="metric-value"><span class="status-badge {badge_cls}">{fin_data['status']}</span></div>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("---")
    st.subheader("📅 Daily Consumption Pacing (Jatah Konsumsi Harian)")
    
    rec_df = fin_data["records_df"]
    if not rec_df.empty:
        # Filter records for Jatah konsumsi harian
        rec_df["alloc_lower"] = rec_df["allocation"].str.strip().str.lower()
        daily_df = rec_df[rec_df["alloc_lower"] == "jatah konsumsi harian"].copy()
        
        if not daily_df.empty:
            daily_df["date_str"] = pd.to_datetime(daily_df["date"]).dt.strftime("%Y-%m-%d")
            # Group by date summing accrual basis
            daily_summary = daily_df.groupby("date_str")["acrual_basis"].sum().reset_index()
            daily_summary.rename(columns={"acrual_basis": "Realisation"}, inplace=True)
            daily_summary["Daily Target"] = -150000  # Expense target limit per day
            daily_summary["Surplus/Deficit"] = 150000 + daily_summary["Realisation"]
            
            st.dataframe(
                daily_summary.style.format({
                    "Realisation": lambda x: fmt_idr(x),
                    "Daily Target": lambda x: fmt_idr(-150000),
                    "Surplus/Deficit": lambda x: fmt_idr(x)
                }),
                use_container_width=True
            )
        else:
            st.info("No records recorded under 'Jatah konsumsi harian' yet.")
    else:
        st.info("No ledger records available.")

# ==============================================================================
# TAB 2: JOURNAL & AI ASSISTANT (GROQ + MANUAL PHONE CONTROL)
# ==============================================================================
with tabs[1]:
    st.subheader("📝 Journal & Transaction Entry")
    
    # Dynamic Allocations List for Dropdowns & Prompt (Safely handles empty tables)
    enc_df = get_data("encumbrance")
    wallets_df = get_data("wallets")
    
    enc_list = list(enc_df["description"].unique()) if "description" in enc_df.columns else []
    wallets_list = list(wallets_df["description"].unique()) if "description" in wallets_df.columns else []
    all_allocations = ["Buffer"] + enc_list + wallets_list
    
    entry_mode = st.radio("Entry Mode", ["🤖 Groq AI Natural Language Assistant", "📱 Phone-Friendly Manual Entry"], horizontal=True)
    
    if entry_mode == "🤖 Groq AI Natural Language Assistant":
        st.info("Describe your transaction in plain Indonesian or English. Groq will generate the required balanced journal rows.")
        
        tx_input = st.text_input("Transaction Prompt:", placeholder="e.g., Beli starbucks 49000 pake starbucks card, 24.5k dibayar temen")
        
        if st.button("Interpret & Generate Journal"):
            if tx_input:
                if groq_client:
                    with st.spinner("Analyzing accounting logic with Groq..."):
                        system_prompt = f"""
                        You are a specialized financial parsing AI. The user follows a ledger system with a Buffer contra-account.
                        Available Allocations: {json.dumps(all_allocations)}
                        
                        RULES:
                        1. Expense against Budget: Deduct amount from relevant budget allocation.
                        2. Expense against Wallet: Deduct amount from physical wallet used.
                        3. Buffer Offset: When spending from a wallet for a budget category, add positive offset to Buffer to prevent double-counting.
                        4. Split/Receivables: Calculate user's true expense, track receivables, and handle wallet/buffer offsets.
                        
                        OUTPUT REQUIREMENT:
                        Return ONLY a valid JSON array of objects with keys:
                        "Date" (YYYY-MM-DD), "Description" (string), "Allocation" (must match one in Available Allocations), "Cash_basis" (integer), "Receivables" (integer).
                        Do not include backticks or conversational text.
                        """
                        try:
                            response = groq_client.chat.completions.create(
                                model="llama3-70b-8192",
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": f"Today: {datetime.date.today()}. Input: {tx_input}"}
                                ],
                                temperature=0.1
                            )
                            raw_json = response.choices[0].message.content.strip()
                            parsed_rows = json.loads(raw_json)
                            st.session_state.proposed_rows = parsed_rows
                        except Exception as e:
                            st.error(f"Error parsing with Groq: {e}")
                else:
                    st.warning("GROQ_API_KEY not configured. Simulating Groq parser for demo...")
                    st.session_state.proposed_rows = [
                        {"Date": str(datetime.date.today()), "Description": tx_input, "Allocation": "Jatah konsumsi harian", "Cash_basis": -49000, "Receivables": 24500},
                        {"Date": str(datetime.date.today()), "Description": tx_input, "Allocation": "Buffer", "Cash_basis": 49000, "Receivables": 0}
                    ]
        
        if "proposed_rows" in st.session_state and st.session_state.proposed_rows:
            st.write("### 📋 Review Proposed Rows")
            df_prop = pd.DataFrame(st.session_state.proposed_rows)
            df_prop["Acrual_basis"] = df_prop["Cash_basis"] + df_prop["Receivables"]
            edited_prop = st.data_editor(df_prop, use_container_width=True, num_rows="dynamic")
            
            if st.button("Confirm & Post to Ledger"):
                records_to_insert = edited_prop.to_dict(orient="records")
                if supabase and st.session_state.user:
                    for r in records_to_insert:
                        supabase.table("records").insert({
                            "user_id": st.session_state.user.id,
                            "date": r["Date"],
                            "description": r["Description"],
                            "allocation": r["Allocation"],
                            "cash_basis": r["Cash_basis"],
                            "receivables": r["Receivables"]
                        }).execute()
                else:
                    demo_recs = st.session_state.demo_records
                    for r in records_to_insert:
                        new_row = {
                            "id": str(len(demo_recs) + 1),
                            "date": r["Date"],
                            "description": r["Description"],
                            "allocation": r["Allocation"],
                            "cash_basis": r["Cash_basis"],
                            "receivables": r["Receivables"],
                            "acrual_basis": r["Cash_basis"] + r["Receivables"]
                        }
                        st.session_state.demo_records = pd.concat([st.session_state.demo_records, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Successfully posted journal entry!")
                st.session_state.proposed_rows = None
                st.rerun()

    else:
        st.write("### 📱 Phone-Friendly Manual Form")
        with st.form("manual_entry_form"):
            date_val = st.date_input("Date", datetime.date.today())
            desc_val = st.text_input("Description", placeholder="e.g. Sarapan ketoprak")
            alloc_val = st.selectbox("Allocation", all_allocations)
            cash_val = st.number_input("Cash Basis (Outflow negative, Inflow positive)", value=0, step=1000)
            rec_val = st.number_input("Receivables (Positive if owed to you)", value=0, step=1000)
            accrual_preview = cash_val + rec_val
            st.write(f"**Calculated Accrual Basis:** {fmt_idr(accrual_preview)}")
            
            submitted = st.form_submit_button("Add Journal Record")
            if submitted:
                if supabase and st.session_state.user:
                    supabase.table("records").insert({
                        "user_id": st.session_state.user.id,
                        "date": str(date_val),
                        "description": desc_val,
                        "allocation": alloc_val,
                        "cash_basis": cash_val,
                        "receivables": rec_val
                    }).execute()
                else:
                    demo_recs = st.session_state.demo_records
                    new_row = {
                        "id": str(len(demo_recs) + 1),
                        "date": str(date_val),
                        "description": desc_val,
                        "allocation": alloc_val,
                        "cash_basis": cash_val,
                        "receivables": rec_val,
                        "acrual_basis": accrual_preview
                    }
                    st.session_state.demo_records = pd.concat([st.session_state.demo_records, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Record added successfully!")
                st.rerun()

    st.write("---")
    st.subheader("📖 Full Ledger Records")
    current_records = get_data("records")
    if not current_records.empty:
        search_term = st.text_input("🔍 Search Records:", "")
        if search_term:
            current_records = current_records[
                current_records["description"].str.contains(search_term, case=False, na=False) |
                current_records["allocation"].str.contains(search_term, case=False, na=False)
            ]
        st.dataframe(current_records, use_container_width=True)
    else:
        st.info("No records available.")

# ==============================================================================
# TAB 3: MODEL & ALLOCATIONS
# ==============================================================================
with tabs[2]:
    st.subheader("📈 Live Model & Fund Allocations")
    
    m_df = fin_data["model_table"]
    
    st.dataframe(
        m_df.style.format({
            "Fund": lambda x: fmt_idr(x),
            "Realisation": lambda x: fmt_idr(x),
            "Remaining": lambda x: fmt_idr(x)
        }),
        use_container_width=True
    )
    
    st.write("---")
    st.markdown(f"**Total Fund in Balance Fund Target:** {fmt_idr(fin_data['total_fund_in_balance'])}")
    st.markdown(f"**Total Realisation across all allocations:** {fmt_idr(fin_data['total_realisation'])}")
    st.markdown(f"**Total Net Remaining Fund:** {fmt_idr(fin_data['total_remaining'])}")

# ==============================================================================
# TAB 4: MASTER SETUP & DYNAMIC TABLES
# ==============================================================================
with tabs[3]:
    st.subheader("⚙️ Manage Master Data & Dynamic Tables")
    st.write("Add or edit your income, fixed spendings, savings, dynamic encumbrances, and physical wallets.")
    
    master_tab = st.selectbox("Select Table to Manage", ["Wallets", "Encumbrance (Budgets)", "Income", "Fix Spendings", "Savings"])
    
    tbl_key_map = {
        "Wallets": "wallets",
        "Encumbrance (Budgets)": "encumbrance",
        "Income": "income",
        "Fix Spendings": "fix_spendings",
        "Savings": "savings"
    }
    
    target_tbl = tbl_key_map[master_tab]
    current_df = get_data(target_tbl)
    
    st.write(f"### Current {master_tab}")
    st.dataframe(current_df, use_container_width=True)
    
    st.write(f"### Add New Entry to {master_tab}")
    with st.form("add_master_form"):
        new_desc = st.text_input("Description / Name")
        new_amt = st.number_input("Amount (IDR)", min_value=0, step=10000)
        has_date = target_tbl in ["income", "fix_spendings", "savings"]
        new_date = st.date_input("Date", datetime.date.today()) if has_date else None
        
        save_btn = st.form_submit_button("Save Entry")
        if save_btn:
            if new_desc:
                row_dict = {"description": new_desc, "amount": new_amt}
                if has_date:
                    row_dict["date"] = str(new_date)
                
                if supabase and st.session_state.user:
                    row_dict["user_id"] = st.session_state.user.id
                    supabase.table(target_tbl).insert(row_dict).execute()
                else:
                    demo_df = st.session_state[f"demo_{target_tbl}"]
                    row_dict["id"] = str(len(demo_df) + 1)
                    st.session_state[f"demo_{target_tbl}"] = pd.concat([demo_df, pd.DataFrame([row_dict])], ignore_index=True)
                st.success("Entry added!")
                st.rerun()
