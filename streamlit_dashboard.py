import streamlit as st
import requests
import pandas as pd
import time

# Page Configuration
st.set_page_config(page_title="ScamShield AI Dashboard", layout="wide")

# Custom CSS for better look
st.markdown("""
    <style>
    .main { background-color: #0f172a; color: white; }
    .stMetric { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# Function to fetch data from FastAPI
def fetch_data():
    try:
        response = requests.get("http://127.0.0.1:8000/history", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return []
    return []

# Normalizer to handle different backend payload shapes
def normalize(entry):
    # backend may return different keys; normalize to a common shape
    session = entry.get('sessionId') or entry.get('session_id') or entry.get('session') or entry.get('id')
    medium = entry.get('medium') or entry.get('channel') or 'UNKNOWN'
    message = entry.get('message') or entry.get('text') or ''
    ai_reply = entry.get('ai_reply') or entry.get('reply') or entry.get('response') or ''

    # intelligence may be nested under different keys
    intel = {'phoneNumbers': [], 'upiIds': [], 'phishingLinks': [], 'bankAccounts': []}
    if 'intel' in entry and isinstance(entry['intel'], dict):
        intel.update(entry['intel'])
    elif 'extracted' in entry and isinstance(entry['extracted'], dict):
        intel.update(entry['extracted'])
    elif 'extracted_intelligence' in entry and isinstance(entry['extracted_intelligence'], dict):
        intel.update(entry['extracted_intelligence'])
    else:
        # legacy possible fields
        if 'upi' in entry and isinstance(entry['upi'], list):
            intel['upiIds'] = entry['upi']
        if 'extracted' in entry and isinstance(entry['extracted'], list):
            intel['upiIds'] = entry['extracted']

    return {
        'sessionId': session or 'N/A',
        'medium': medium,
        'message': message,
        'ai_reply': ai_reply,
        'timestamp': entry.get('timestamp'),
        'conversation': entry.get('conversation', []),
        'intel': intel
    }

# Sidebar Navigation
st.sidebar.title("🛡️ ScamShield Pro")
menu = st.sidebar.radio("Navigation", ["Dashboard", "Live Sessions", "Intelligence Hub"])

# Real-time data loading
raw_data = fetch_data()
scam_data = [normalize(d) for d in raw_data]

# --- DASHBOARD TAB ---
if menu == "Dashboard":
    st.header("🚀 Security Overview")
    
    # Calculate stats from real data
    total_scams = len(scam_data)
    total_intel = sum([len(s['intel'].get('phoneNumbers', [])) + len(s['intel'].get('upiIds', [])) + len(s['intel'].get('phishingLinks', [])) for s in scam_data])
    active_sessions = len(set([s['sessionId'] for s in scam_data]))

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Scams Detected", total_scams)
    col2.metric("Intelligence Collected", total_intel)
    col3.metric("Active Honeypots", active_sessions)
    
    st.subheader("Detection Activity")
    if scam_data:
        df = pd.DataFrame({'Detections': list(range(1, len(scam_data)+1))})
        st.line_chart(df)
    else:
        st.info("Waiting for live data... (Send a request via Swagger)")

# --- LIVE SESSIONS TAB ---
elif menu == "Live Sessions":
    st.header("💬 Live Honeypot Engagement")
    if not scam_data:
        st.warning("No live sessions found. Execute a POST request in Swagger UI to start.")
        st.stop()

    # session selector
    session_ids = [s['sessionId'] for s in scam_data]
    selected = st.selectbox("Select session", session_ids)
    session = next((s for s in scam_data if s['sessionId'] == selected), scam_data[-1])

    col_meta, col_actions = st.columns([3,1])
    with col_meta:
        st.subheader(f"Session: {session['sessionId']}")
        st.caption(f"Channel: {session.get('medium','UNKNOWN')}  •  First seen: {session.get('timestamp','N/A')}" )
        st.markdown("---")

        # conversation view with timestamps
        conv = session.get('conversation') or []
        if conv:
            for msg in conv:
                role = msg.get('role', 'unknown')
                ts = msg.get('timestamp', '')
                text = msg.get('text', '')
                if role == 'scammer':
                    st.markdown(f"**Scammer** <span style='color:#f87171'>@{ts}</span>", unsafe_allow_html=True)
                    st.write(text)
                else:
                    st.markdown(f"**Priya (AI)** <span style='color:#34d399'>@{ts}</span>", unsafe_allow_html=True)
                    st.write(text)
        else:
            # fallback to top-level message/reply
            st.markdown("**Scammer:**")
            st.write(session.get('message',''))
            st.markdown("**Priya (AI):**")
            st.write(session.get('ai_reply',''))

        st.markdown("---")
        st.info(f"Intelligence Extracted: {session.get('intel')}")

    with col_actions:
        if st.button("Refresh session"):
            st.experimental_rerun()

# --- INTELLIGENCE HUB ---
elif menu == "Intelligence Hub":
    st.header("📊 Intelligence Database")
    
    intel_list = []
    for s in scam_data:
        for upi in s['intel'].get('upiIds', []): intel_list.append({"Type": "UPI ID", "Value": upi, "Session": s['sessionId']})
        for link in s['intel'].get('phishingLinks', []): intel_list.append({"Type": "Link", "Value": link, "Session": s['sessionId']})
        for ph in s['intel'].get('phoneNumbers', []): intel_list.append({"Type": "Phone", "Value": ph, "Session": s['sessionId']})
    
    if intel_list:
        st.table(pd.DataFrame(intel_list))
    else:
        st.write("No intelligence data gathered yet.")

# Auto-refresh button
if st.sidebar.button("Refresh Data"):
    st.experimental_rerun()
