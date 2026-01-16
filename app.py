import streamlit as st
import pandas as pd
import plotly.express as px
from models import get_session, Transaction, User
import datetime
from streamlit_cookies_manager import EncryptedCookieManager

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="FinanceFlow",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Initialize Cookie Manager ---
cookies = EncryptedCookieManager(password="financeflow_secure_key_2026")
if not cookies.ready():
    st.stop()

# --- 3. Professional Minimalist CSS ---
st.markdown("""
    <style>
    /* Global Background */
    .stApp { background-color: #f8f9fc; color: #1a1c23; }
    
    /* Force Sidebar Toggle Arrow (>>) to be permanent */
    section[data-testid="stSidebar"] + div { display: flex !important; }
    [data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        z-index: 999999 !important;
    }

    /* Pull the main content up to the very top */
    .main .block-container { padding-top: 1.5rem !important; }

    /* Clean Auth UI - No Boxes, No Stickers */
    .auth-container {
        max-width: 400px;
        margin: auto;
        margin-top: -10px; 
    }

    .brand-title {
        font-weight: 700;
        font-size: 32px;
        color: #1a202c;
        text-align: center;
        margin-bottom: 0px; 
    }

    .brand-subtitle {
        font-size: 15px;
        color: #718096;
        text-align: center;
        margin-bottom: 15px; 
    }

    /* Form UI Refinement - Clean & Flat */
    [data-testid="stForm"] { border: none !important; padding: 0 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; border-bottom: none; }
    
    /* Input & Button Styling */
    .stButton>button { border-radius: 8px; font-weight: 600; height: 3em; border: none; background-color: #2d3748; color: white; }
    .stTextInput input { border-radius: 8px !important; background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; }
    
    /* Hide default Streamlit elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. Persistent Session Logic ---
if 'user_id' not in st.session_state:
    saved_id = cookies.get("user_id")
    if saved_id:
        st.session_state['user_id'] = int(saved_id)
        session = get_session()
        user = session.query(User).filter_by(id=int(saved_id)).first()
        st.session_state['username'] = user.username if user else None
        session.close()
    else:
        st.session_state['user_id'] = None
        st.session_state['username'] = None

session = get_session()

# --- 5. AUTHENTICATION INTERFACE (Pure Text) ---
def auth_ui():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<div class="brand-title">FinanceFlow</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-subtitle">Smart personal finance tracking</div>', unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
        
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("login_form", border=False):
                u_in = st.text_input("Username")
                p_in = st.text_input("Password", type="password")
                if st.form_submit_button("Access Dashboard", use_container_width=True):
                    user = session.query(User).filter_by(username=u_in).first()
                    if user and user.check_password(p_in):
                        st.session_state['user_id'] = user.id
                        st.session_state['username'] = user.username
                        cookies["user_id"] = str(user.id)
                        cookies.save()
                        st.rerun()
                    else: st.error("Invalid credentials.")
        
        with tab_signup:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("signup_form", border=False):
                nu_in = st.text_input("New Username")
                np_in = st.text_input("New Password", type="password")
                cp_in = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Get Started", use_container_width=True):
                    if np_in != cp_in: st.error("Passwords do not match.")
                    elif nu_in and np_in:
                        exists = session.query(User).filter_by(username=nu_in).first()
                        if exists: st.error("Username already taken.")
                        else:
                            new_user = User(username=nu_in); new_user.set_password(np_in)
                            session.add(new_user); session.commit()
                            st.success("Account created! Please Sign In.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. MAIN DASHBOARD INTERFACE ---
def dashboard_ui():
    with st.sidebar:
        st.markdown("<h2 style='text-align: center;'>FinanceFlow</h2>", unsafe_allow_html=True)
        
        # ACCOUNT DROPDOWN (No icon in label)
        with st.expander(f"Account ({st.session_state['username']})", expanded=False):
            if st.button("Log Out", use_container_width=True):
                if "user_id" in cookies:
                    del cookies["user_id"]
                    cookies.save()
                st.session_state['user_id'] = None
                st.rerun()
        
        st.markdown("---")
        
        # NEW RECORD FORM
        with st.form("add_tx", clear_on_submit=True):
            st.subheader("New Record")
            d = st.date_input("Date", datetime.date.today())
            ds = st.text_input("Description")
            a = st.number_input("Amount ($)", min_value=0.01, step=0.01)
            c = st.selectbox("Category", ["Food", "Rent", "Transport", "Salary", "Utilities", "Other"])
            t = st.radio("Type", ["Expense", "Income"], horizontal=True)
            if st.form_submit_button("Save Record", use_container_width=True):
                if ds:
                    new_tx = Transaction(user_id=st.session_state['user_id'], date=d, description=ds, amount=a, category=c, type=t)
                    session.add(new_tx); session.commit()
                    st.toast("Saved!")
                    st.rerun()

    # Data Display Logic
    data = session.query(Transaction).filter_by(user_id=st.session_state['user_id']).all()
    if data:
        df = pd.DataFrame([{"Date": tx.date, "Description": tx.description, "Category": tx.category, "Type": tx.type, "Amount": tx.amount} for tx in data])
        df['Date'] = pd.to_datetime(df['Date'])
        
        inc = df[df['Type'] == 'Income']['Amount'].sum()
        exp = df[df['Type'] == 'Expense']['Amount'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Income", f"${inc:,.2f}")
        m2.metric("Expenses", f"${exp:,.2f}")
        m3.metric("Balance", f"${inc-exp:,.2f}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        # Tabs with text only
        tab_charts, tab_data = st.tabs(["Analytics", "History"])
        with tab_charts:
            col_l, col_r = st.columns(2)
            with col_l:
                exp_df = df[df['Type'] == 'Expense']
                if not exp_df.empty:
                    st.plotly_chart(px.pie(exp_df, values='Amount', names='Category', hole=0.4), use_container_width=True)
            with col_r:
                st.plotly_chart(px.bar(df, x='Date', y='Amount', color='Type', barmode='group'), use_container_width=True)
        
        with tab_data:
            st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            # Button with text only
            st.download_button(label="Download CSV", data=csv, file_name='finance_history.csv', mime='text/csv', use_container_width=True)
    else:
        st.info("Welcome! Use the sidebar to add a record.")

# --- 7. ROUTER ---
if st.session_state['user_id'] is None:
    auth_ui()
else:
    dashboard_ui()

session.close()