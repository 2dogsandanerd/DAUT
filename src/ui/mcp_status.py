
import streamlit as st
import requests
import os

def display_mcp_status_in_sidebar(mcp_port: int = 8001):
    """
    Shows a small status widget for the MCP Server in the sidebar.
    """
    # Removed redundant headers/separators as main.py handles the section
    
    status_url = f"http://localhost:{mcp_port}/status"
    
    try:
        # Short timeout to not block UI
        response = requests.get(status_url, timeout=0.5)
        
        if response.status_code == 200:
            data = response.json()
            st.success(f"🟢 Online (Port {mcp_port})")
            
            if "active_count" in data:
                 st.metric("Active Clients", data["active_count"])
            elif "active_connections" in data:
                 # Falls nur die Liste zurückkommt, Länge berechnen
                 conns = data["active_connections"]
                 count = len(conns) if isinstance(conns, list) else conns
                 st.metric("Active Clients", count)
            
        else:
            st.warning(f"⚠️ Status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        st.error("🔴 Offline")
        st.caption(f"Server not reachable on port {mcp_port}")
        if st.button("Start Code Helper"): # Renamed for clarity vs 'Start Help'
             st.info("Run `./start_mcp.sh` in terminal.")
    except Exception as e:
        st.error(f"🔴 Error: {e}")
