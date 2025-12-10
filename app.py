"""
CausaFr - Complete Google Sheets Annotation Tool
Handles multiple JSON datasets with full field preservation
Streamlit Cloud compatible version
"""

import streamlit as st
import pandas as pd
import json
import os
import hashlib
import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from io import StringIO
import itertools

# =============================================================================
# GOOGLE SHEETS CONFIGURATION - Streamlit Secrets Compatible
# =============================================================================

# Try to get from Streamlit secrets, fall back to environment variables
def load_google_config():
    """Load Google Sheets configuration from Streamlit secrets or environment"""
    config = {
        'spreadsheet_id': None,
        'gcp_credentials': None
    }
    
    # Method 1: Streamlit secrets (for cloud deployment)
    try:
        if hasattr(st, 'secrets'):
            if 'GOOGLE_SHEETS' in st.secrets:
                config['spreadsheet_id'] = st.secrets['GOOGLE_SHEETS']['spreadsheet_id']
                
                # Construct credentials from secrets
                config['gcp_credentials'] = {
                    'type': st.secrets['GOOGLE_SHEETS']['type'],
                    'project_id': st.secrets['GOOGLE_SHEETS']['project_id'],
                    'private_key_id': st.secrets['GOOGLE_SHEETS']['private_key_id'],
                    'private_key': st.secrets['GOOGLE_SHEETS']['private_key'],
                    'client_email': st.secrets['GOOGLE_SHEETS']['client_email'],
                    'client_id': st.secrets['GOOGLE_SHEETS']['client_id'],
                    'auth_uri': st.secrets['GOOGLE_SHEETS']['auth_uri'],
                    'token_uri': st.secrets['GOOGLE_SHEETS']['token_uri'],
                    'auth_provider_x509_cert_url': st.secrets['GOOGLE_SHEETS']['auth_provider_x509_cert_url'],
                    'client_x509_cert_url': st.secrets['GOOGLE_SHEETS']['client_x509_cert_url']
                }
                return config
    except Exception as e:
        st.error(f"Error loading Streamlit secrets: {e}")
    
    # Method 2: Environment variables (for local development)
    import os
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    if spreadsheet_id:
        config['spreadsheet_id'] = spreadsheet_id
        
        # Try to get credentials from environment
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if creds_json:
            import json
            config['gcp_credentials'] = json.loads(creds_json)
        else:
            # Try individual environment variables
            config['gcp_credentials'] = {
                'type': os.environ.get('GOOGLE_TYPE', 'service_account'),
                'project_id': os.environ.get('GOOGLE_PROJECT_ID'),
                'private_key_id': os.environ.get('GOOGLE_PRIVATE_KEY_ID'),
                'private_key': os.environ.get('GOOGLE_PRIVATE_KEY', '').replace('\\n', '\n'),
                'client_email': os.environ.get('GOOGLE_CLIENT_EMAIL'),
                'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
                'auth_uri': os.environ.get('GOOGLE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
                'token_uri': os.environ.get('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
                'auth_provider_x509_cert_url': os.environ.get('GOOGLE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
                'client_x509_cert_url': os.environ.get('GOOGLE_CLIENT_X509_CERT_URL')
            }
    
    return config

# Load configuration
GOOGLE_CONFIG = load_google_config()

# =============================================================================
# DATA MODELS (keep as is)
# =============================================================================

@dataclass
class OriginalPair:
    """Original pair data from JSON files"""
    # ... (keep all your dataclass definitions as they are)
    # Copy all your existing dataclass definitions here

# =============================================================================
# GOOGLE SHEETS MANAGER - UPDATED FOR SECURITY
# =============================================================================

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False
    st.error("⚠️ Install dependencies: pip install gspread google-auth")

class GoogleSheetsManager:
    """Complete Google Sheets management for multiple datasets"""
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.connected = False
        self.error_message = ""
        
        # Sheet references
        self.users_sheet = None
        self.datasets_sheet = None
        self.dataset_pairs_sheet = None
        self.annotations_sheet = None
        self.progress_sheet = None
        
    def connect(self) -> bool:
        """Connect to Google Sheets"""
        try:
            if not GOOGLE_CONFIG['spreadsheet_id'] or not GOOGLE_CONFIG['gcp_credentials']:
                self.error_message = "Google Sheets configuration not found. Please check your secrets.toml"
                return False
            
            creds = GOOGLE_CONFIG['gcp_credentials'].copy()
            private_key = creds['private_key']
            
            # Ensure proper newlines
            private_key = private_key.replace('\\n', '\n')
            if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                private_key = '-----BEGIN PRIVATE KEY-----\n' + private_key
            if not private_key.endswith('-----END PRIVATE KEY-----'):
                private_key = private_key + '\n-----END PRIVATE KEY-----'
            
            creds['private_key'] = private_key
            
            # Create credentials
            credentials = Credentials.from_service_account_info(
                creds,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive.file'
                ]
            )
            
            # Authorize
            self.client = gspread.authorize(credentials)
            
            # Open spreadsheet
            spreadsheet_id = GOOGLE_CONFIG['spreadsheet_id']
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            # Setup all sheets
            self._setup_sheets()
            
            self.connected = True
            return True
            
        except Exception as e:
            self.error_message = f"Connection error: {str(e)}"
            return False
    
    def _setup_sheets(self):
        """Create or get all necessary worksheets"""
        # ... (keep your existing _setup_sheets method)
        # Copy all your existing _setup_sheets code here
    
    # ... (keep all your other methods as they are)
    # Copy all your existing methods here (users, datasets, annotations, etc.)

# =============================================================================
# STREAMLIT APPLICATION
# =============================================================================

# Page config
st.set_page_config(
    page_title="CausaFr - Multi-Dataset Annotation",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* ... (keep your existing CSS) */
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.gsheets = None
    st.session_state.current_dataset = None
    st.session_state.pair_index = 0
    st.session_state.current_pairs = []
    st.session_state.is_admin = False

# Initialize Google Sheets
if st.session_state.gsheets is None:
    st.session_state.gsheets = GoogleSheetsManager()
    if not st.session_state.gsheets.connect():
        st.error(f"❌ Connection failed: {st.session_state.gsheets.error_message}")
        
        # Add debug information
        st.info("""
        ### Debug Information:
        
        1. **Check if spreadsheet exists**: Make sure the spreadsheet ID is correct
        2. **Check permissions**: Ensure the service account has edit access to the spreadsheet
        3. **Check credentials**: Verify all credential fields are correct
        
        **Spreadsheet ID used**: `{}`
        """.format(GOOGLE_CONFIG.get('spreadsheet_id', 'Not set')))
        
        # Quick test button
        if st.button("🔍 Test Connection"):
            try:
                import gspread
                from google.oauth2.service_account import Credentials
                
                creds = GOOGLE_CONFIG['gcp_credentials'].copy()
                private_key = creds['private_key'].replace('\\n', '\n')
                creds['private_key'] = private_key
                
                credentials = Credentials.from_service_account_info(
                    creds,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                
                client = gspread.authorize(credentials)
                spreadsheet = client.open_by_key(GOOGLE_CONFIG['spreadsheet_id'])
                sheets = [ws.title for ws in spreadsheet.worksheets()]
                
                st.success(f"✅ Connection successful!")
                st.write(f"**Spreadsheet title**: {spreadsheet.title}")
                st.write(f"**Sheets available**: {', '.join(sheets)}")
                
                # Check if our required sheets exist
                required_sheets = ['users', 'datasets', 'dataset_pairs', 'annotations', 'progress']
                missing = [s for s in required_sheets if s not in sheets]
                if missing:
                    st.warning(f"⚠️ Missing sheets: {', '.join(missing)}")
                    if st.button("🛠️ Create missing sheets"):
                        for sheet in missing:
                            try:
                                spreadsheet.add_worksheet(sheet, 1000, 20)
                                st.success(f"Created {sheet}")
                            except:
                                st.warning(f"Could not create {sheet}")
                else:
                    st.success("✅ All required sheets exist!")
                    
            except Exception as e:
                st.error(f"Test failed: {e}")
        
        st.stop()

# =============================================================================
# PAGES (keep as is)
# =============================================================================

def login_page():
    """Login/Register page"""
    # ... (keep your existing login_page function)
    # Copy all your existing login_page code here

def dataset_management_page():
    """Dataset upload and management page"""
    # ... (keep your existing dataset_management_page function)
    # Copy all your existing dataset_management_page code here

def annotate_page():
    """Main annotation page"""
    # ... (keep your existing annotate_page function)
    # Copy all your existing annotate_page code here

def dashboard_page():
    """Dashboard page"""
    # ... (keep your existing dashboard_page function)
    # Copy all your existing dashboard_page code here

def about_page():
    """About page"""
    # ... (keep your existing about_page function)
    # Copy all your existing about_page code here

def main():
    """Main application"""
    
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2>🔗 CausaFr</h2>
            <p style="color: #666; font-size: 0.9rem;">👤 {st.session_state.username}</p>
            { '<p style="color: #f59e0b; font-size: 0.8rem;">👑 Administrateur</p>' if st.session_state.is_admin else '' }
        </div>
        """, unsafe_allow_html=True)
        
        pages = ["📤 Gérer Datasets", "✏️ Annoter", "📊 Tableau de bord", "ℹ️ À propos"]
        page = st.radio("Navigation", pages, label_visibility="collapsed")
    
    # Show selected page
    if page == "📤 Gérer Datasets":
        dataset_management_page()
    elif page == "✏️ Annoter":
        annotate_page()
    elif page == "📊 Tableau de bord":
        dashboard_page()
    elif page == "ℹ️ À propos":
        about_page()

if __name__ == "__main__":
    main()
