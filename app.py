import streamlit as st
st.set_page_config(page_title="📊 Voting App", layout="wide")

# ✅ Then import your panel modules
from frontend import admin_panel, voter_panel, analytics_panel

# Sidebar navigation
st.sidebar.title("📊 Voting App")
page = st.sidebar.radio("Go to", ["🏛️ Admin Panel", "📩 Vote Now", "📈 Analytics"])

# Show the correct panel
if page == "🏛️ Admin Panel":
    admin_panel.show()
elif page == "📩 Vote Now":
    voter_panel.show()
elif page == "📈 Analytics":
    analytics_panel.show()

