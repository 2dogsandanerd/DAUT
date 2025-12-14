
import streamlit as st
import requests
import os

def display_mcp_status_in_sidebar(mcp_port: int = 8001):
    """
    Shows a small status widget for the MCP Server in the sidebar.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔌 MCP Server Status")
    
    status_url = f"http://localhost:{mcp_port}/status"
    
    try:
        # Short timeout to not block UI
        response = requests.get(status_url, timeout=0.5)
        
        if response.status_code == 200:
            data = response.json()
            st.sidebar.success(f"🟢 Online (Port {mcp_port})")
            
            # Show connections if available (our middleware tracking)
            # Since my logic for tracking was 'imperfect' in mcp_entry.py for now, 
            # I will assume I might iterate on it. 
            # But let's show whatever /status gives.
            if "active_connections" in data:
                 count = data["active_connections"]
                 st.sidebar.metric("Active Clients", count)
            
            # Show "Who is connected" as requested?
            # If I add the tracked IPs to the status response in mcp_entry.py I could show them.
            # Currently my previous edit commented it out? 
            # Let's check mcp_entry.py again via file read to be sure what I wrote.
        else:
            st.sidebar.warning(f"⚠️ Status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        st.sidebar.error("🔴 Offline")
        st.sidebar.caption(f"Server not reachable on port {mcp_port}")
        if st.sidebar.button("Start Help"):
             st.sidebar.info("Run `./start_mcp.sh` in terminal.")
    except Exception as e:
        st.sidebar.error("🔴 Error")
