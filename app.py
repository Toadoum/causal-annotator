"""
CausaFr - Complete Google Sheets Annotation Tool
Datasets and annotations all stored in Google Sheets
"""

import streamlit as st
import pandas as pd
import json
import os
import hashlib
import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from io import StringIO

# =============================================================================
# GOOGLE SHEETS CONFIGURATION
# =============================================================================

GOOGLE_CONFIG = {
    'spreadsheet_id': "1K4zUiRVOnyDuEAjzoZ5qb7B5fg9dKOdaJJjbQfDsBKw",
    'gcp_credentials': {
        'type': "service_account",
        'project_id': "machine-translation-375907",
        'private_key_id': "887c96056fc68e0e2eb9b740176735bfe7db003f",
        'private_key': """-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQCSWZ9wD1lxSVls
Iy/olVuIDnDGbttm16jBqFlRXHDmBn5yn7YuCRoKlqoCadJL/7MuE+xPiS17WYI3
IhcWssMJfdD2DMYk+F0wGdS2FZUzNrIqWg+NiX/mUs8U3/kytxBqK8kpi1yrr/b0
sTi1ZmvJd60f8o5UcCQ2CLbI6VZhH0shmE07q1wO8yMz4HnbSHyTyFizWxFCXqMN
0Y6+WPBUsfj7G5pcNFtyHAsqIzoEFRuScebrPHrB2f2uvznnuODxUSJKKr+I/9NE
dcExK3vdKvKWz84lGxxeVL5Jdw0SCH9zJFbrG/YxJixBYPtc/QsbjHs/pnoiS/tl
aRvJQU/tAgMBAAECggEACdE1wwpgjVsmgrzEhrVYL8MKOSFwGdC/Kwh8P1s0XpXS
byV8DtAA/XNYYbOQDhWPwzhGappw4NyjAchJZLYmo7EbLpoyQ4IenC6raHB/svEJ
GBK1BuFRoVVuO0AAAzEpCno38w+8bm7uIcFupKqDcf8Tb7hxaEQihbZlbopKh1a8
VVDR5AS1Cy1rPRDphckYPH+MNN/VO5AWUsV1hoEMY7b2G+mADUduzdAAyeHGH2Te
GlRs4+I02PdDHokMZRej4lbo5CkUQ5YlwoV9zJ3PJBHRatpGWfQ0XGxynTINRGbJ
IU/bmjA8xXbYC7FESkPBaFVdQMY/kthcFRAbg/qKsQKBgQDGTcxZp+iVv/l1hvPa
4LdPdvEO8nSdeYuJ/4q0dg0zny+xoaBAKhyqYUWAsYIhU2pTHmQteffEYmxEG2GO
KttH//1klVsltk+sjKYiAGdHFj4ErEqeQKpV+d8ybiFL6mtbux+AHhmFhhA5U1s9
t5SyQp46FZG5y1r5BdwN1T9F0QKBgQC87iqnJK28I6c9/QrAKMCavhT1NLwcnjln
EKXXCcP6CmAXsciRvyx1/YB7xkNBloHYs/YC6ZzVDPsmSn55SVyLGW50scyXf6e7
Lw3s5OJxQemnk76ExBM8pyynJPk6FvEmrtVmZZmNlUG9CNHfReBSq2+jyStW5D5y
XxL3u5uDXQKBgQC2KgN9nLQY1EhpgTYDrAhYtC+PBoS/oEbh1uBpFETeVe4vJAUc
zFKW5VI+fVHIIWN7xWBLMk67lZpVGj4MpivXwT3ZpyYax5X7MRzwASTedX01N7w4
Ebknz6kMH4TwwwAqPQQb4gqZ0OSYdI1NbZXoBzBotSWv4jHIrmxOPMWp8QKBgQCr
SOGylzZLk6dUM81DWa8Em8A0bpL8/xXbsuQniNr8Hdvwn2XPfRq5/hI2JRFkrScb
aExpZ5KgNRydInx3SWN1WKEjeu6Zi0puEcL2OqxxMei73N6lT36BRq7c+lBZseL/
xxIBu6rzCZaH4y8i1R8C1Bpqyz9Xj6Zt2nQ/1P6woQKBgQCePFKM+mTxpeADpVEF
pnGN3cQJGvC22FyjIhOOXI5JfkgzL/Ae2Q40/t15WrW/Q3737YxEm7vPbfZDfajQ
nDpTfKxIe9mDB/MBi7IQjzwdhCdMj7gzk2TPM2XflK3CsWOtQiKYAak6QJJXjKzz
I7HHSEOBRuAsvaYHD7nOg6KdMg==
-----END PRIVATE KEY-----""",
        'client_email': "annotation-bot@machine-translation-375907.iam.gserviceaccount.com",
        'client_id': "107890068241269374646",
        'auth_uri': "https://accounts.google.com/o/oauth2/auth",
        'token_uri': "https://oauth2.googleapis.com/token",
        'auth_provider_x509_cert_url': "https://www.googleapis.com/oauth2/v1/certs",
        'client_x509_cert_url': "https://www.googleapis.com/robot/v1/metadata/x509/annotation-bot%40machine-translation-375907.iam.gserviceaccount.com"
    }
}

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Annotation:
    """Data model for an annotation"""
    id: str
    pair_id: str
    dataset: str
    username: str
    event1_text: str
    event2_text: str
    cue1: int = 0
    cue2: int = 0
    label: Optional[int] = None
    confidence: int = 3
    notes: str = ""
    annotated_at: str = ""
    event1_id: str = ""
    event2_id: str = ""

@dataclass
class DatasetPair:
    """Data model for a dataset pair"""
    pair_id: str
    dataset: str
    event1_text: str
    event2_text: str
    event1_id: str = ""
    event2_id: str = ""
    metadata: str = "{}"

# =============================================================================
# GOOGLE SHEETS MANAGER
# =============================================================================

try:
    import gspread
    from google.oauth2.service_account import Credentials
    from google.auth.exceptions import GoogleAuthError
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False
    st.error("⚠️ Install dependencies: pip install gspread google-auth")

class GoogleSheetsManager:
    """Complete Google Sheets management"""
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.connected = False
        self.error_message = ""
        
        # Sheet references
        self.users_sheet = None
        self.annotations_sheet = None
        self.progress_sheet = None
        self.datasets_sheet = None
        self.dataset_pairs_sheet = None
        
    def connect(self) -> bool:
        """Connect to Google Sheets"""
        try:
            # Fix private key formatting
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
        sheet_titles = [ws.title for ws in self.spreadsheet.worksheets()]
        
        # 1. USERS sheet
        if 'users' not in sheet_titles:
            self.users_sheet = self.spreadsheet.add_worksheet('users', 100, 5)
            self.users_sheet.update('A1:E1', [
                ['username', 'password_hash', 'email', 'created_at', 'last_login']
            ])
        else:
            self.users_sheet = self.spreadsheet.worksheet('users')
        
        # 2. DATASETS sheet (dataset metadata)
        if 'datasets' not in sheet_titles:
            self.datasets_sheet = self.spreadsheet.add_worksheet('datasets', 100, 6)
            self.datasets_sheet.update('A1:F1', [
                ['dataset_id', 'name', 'description', 'created_by', 'created_at', 'pair_count']
            ])
        else:
            self.datasets_sheet = self.spreadsheet.worksheet('datasets')
        
        # 3. DATASET_PAIRS sheet (actual pairs data)
        if 'dataset_pairs' not in sheet_titles:
            self.dataset_pairs_sheet = self.spreadsheet.add_worksheet('dataset_pairs', 10000, 8)
            self.dataset_pairs_sheet.update('A1:H1', [
                ['pair_id', 'dataset', 'event1_text', 'event2_text', 
                 'event1_id', 'event2_id', 'metadata', 'row_index']
            ])
        else:
            self.dataset_pairs_sheet = self.spreadsheet.worksheet('dataset_pairs')
        
        # 4. ANNOTATIONS sheet
        if 'annotations' not in sheet_titles:
            self.annotations_sheet = self.spreadsheet.add_worksheet('annotations', 10000, 15)
            headers = [
                'id', 'pair_id', 'dataset', 'username', 'event1_text', 'event2_text',
                'cue1', 'cue2', 'label', 'confidence', 'notes', 'annotated_at',
                'event1_id', 'event2_id', 'exported'
            ]
            self.annotations_sheet.update('A1:O1', [headers])
        else:
            self.annotations_sheet = self.spreadsheet.worksheet('annotations')
        
        # 5. PROGRESS sheet
        if 'progress' not in sheet_titles:
            self.progress_sheet = self.spreadsheet.add_worksheet('progress', 100, 6)
            self.progress_sheet.update('A1:F1', [
                ['username', 'dataset', 'current_index', 'total_annotated', 
                 'last_updated', 'last_pair_id']
            ])
        else:
            self.progress_sheet = self.spreadsheet.worksheet('progress')
    
    # ========== USER MANAGEMENT ==========
    
    def create_user(self, username: str, password: str, email: str = "") -> bool:
        """Create a new user"""
        try:
            users = self.users_sheet.get_all_records()
            for user in users:
                if user['username'] == username:
                    return False
            
            self.users_sheet.append_row([
                username,
                hashlib.sha256(password.encode()).hexdigest(),
                email,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ])
            return True
        except Exception as e:
            self.error_message = str(e)
            return False
    
    def verify_user(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        try:
            users = self.users_sheet.get_all_records()
            for user in users:
                if user['username'] == username:
                    return user['password_hash'] == hashlib.sha256(password.encode()).hexdigest()
            return False
        except Exception as e:
            self.error_message = str(e)
            return False
    
    # ========== DATASET MANAGEMENT ==========
    
    def create_dataset(self, dataset_id: str, name: str, description: str, 
                      created_by: str, pairs: List[Dict]) -> bool:
        """Create a new dataset in Google Sheets"""
        try:
            # Check if dataset exists
            datasets = self.datasets_sheet.get_all_records()
            for dataset in datasets:
                if dataset['dataset_id'] == dataset_id:
                    return False
            
            # Add dataset metadata
            self.datasets_sheet.append_row([
                dataset_id,
                name,
                description,
                created_by,
                datetime.now().isoformat(),
                len(pairs)
            ])
            
            # Add all pairs
            for i, pair in enumerate(pairs):
                self.dataset_pairs_sheet.append_row([
                    pair.get('pair_id', f"{dataset_id}_{i}"),
                    dataset_id,
                    pair.get('event1_text', ''),
                    pair.get('event2_text', ''),
                    pair.get('event1_id', f"e1_{i}"),
                    pair.get('event2_id', f"e2_{i}"),
                    json.dumps(pair.get('metadata', {})),
                    i  # row index for ordering
                ])
            
            return True
        except Exception as e:
            self.error_message = str(e)
            return False
    
    def get_datasets(self) -> List[Dict]:
        """Get all available datasets"""
        try:
            records = self.datasets_sheet.get_all_records()
            return [
                {
                    'id': r['dataset_id'],
                    'name': r['name'],
                    'description': r['description'],
                    'created_by': r['created_by'],
                    'created_at': r['created_at'],
                    'pair_count': int(r['pair_count']) if r['pair_count'] else 0
                }
                for r in records
            ]
        except Exception as e:
            self.error_message = str(e)
            return []
    
    def get_dataset_pairs(self, dataset_id: str) -> List[DatasetPair]:
        """Get all pairs for a dataset"""
        try:
            records = self.dataset_pairs_sheet.get_all_records()
            pairs = []
            
            for record in records:
                if record['dataset'] == dataset_id:
                    pairs.append(DatasetPair(
                        pair_id=record['pair_id'],
                        dataset=record['dataset'],
                        event1_text=record['event1_text'],
                        event2_text=record['event2_text'],
                        event1_id=record['event1_id'],
                        event2_id=record['event2_id'],
                        metadata=record['metadata']
                    ))
            
            # Sort by row_index if available
            pairs.sort(key=lambda x: int(record.get('row_index', 0)) 
                      if isinstance(record.get('row_index'), (int, str)) and str(record.get('row_index', '0')).isdigit() 
                      else 0)
            
            return pairs
        except Exception as e:
            self.error_message = str(e)
            return []
    
    def import_json_dataset(self, dataset_id: str, json_content: str, 
                           name: str = "", description: str = "", 
                           created_by: str = "") -> bool:
        """Import a JSON dataset into Google Sheets"""
        try:
            data = json.loads(json_content)
            
            # Determine pairs based on JSON structure
            if isinstance(data, list):
                pairs = data
            elif isinstance(data, dict) and 'pairs' in data:
                pairs = data['pairs']
            else:
                self.error_message = "Invalid JSON format"
                return False
            
            # Use dataset_id as name if not provided
            if not name:
                name = dataset_id
            
            # Create dataset
            return self.create_dataset(dataset_id, name, description, created_by, pairs)
            
        except json.JSONDecodeError as e:
            self.error_message = f"Invalid JSON: {str(e)}"
            return False
        except Exception as e:
            self.error_message = str(e)
            return False
    
    # ========== ANNOTATION MANAGEMENT ==========
    
    def save_annotation(self, annotation: Annotation) -> str:
        """Save an annotation"""
        try:
            ann_id = str(uuid.uuid4())[:8]
            
            self.annotations_sheet.append_row([
                ann_id,
                annotation.pair_id,
                annotation.dataset,
                annotation.username,
                annotation.event1_text[:500],
                annotation.event2_text[:500],
                annotation.cue1,
                annotation.cue2,
                annotation.label if annotation.label is not None else "",
                annotation.confidence,
                annotation.notes[:200],
                annotation.annotated_at or datetime.now().isoformat(),
                annotation.event1_id,
                annotation.event2_id,
                "0"
            ])
            
            return ann_id
        except Exception as e:
            self.error_message = str(e)
            return ""
    
    def get_user_annotations(self, username: str, dataset_id: str = None) -> List[Dict]:
        """Get annotations for a user"""
        try:
            records = self.annotations_sheet.get_all_records()
            annotations = []
            
            for record in records:
                if record['username'] == username:
                    if dataset_id and record['dataset'] != dataset_id:
                        continue
                    
                    annotations.append({
                        'id': record['id'],
                        'pair_id': record['pair_id'],
                        'dataset': record['dataset'],
                        'username': record['username'],
                        'event1_text': record['event1_text'],
                        'event2_text': record['event2_text'],
                        'cue1': int(record['cue1']) if record['cue1'] else 0,
                        'cue2': int(record['cue2']) if record['cue2'] else 0,
                        'label': int(record['label']) if record['label'] else None,
                        'confidence': int(record['confidence']) if record['confidence'] else 3,
                        'notes': record['notes'],
                        'annotated_at': record['annotated_at'],
                        'event1_id': record['event1_id'],
                        'event2_id': record['event2_id']
                    })
            
            return annotations
        except Exception as e:
            self.error_message = str(e)
            return []
    
    # ========== PROGRESS MANAGEMENT ==========
    
    def update_progress(self, username: str, dataset_id: str, current_index: int, 
                       total_annotated: int, last_pair_id: str = "") -> bool:
        """Update user progress"""
        try:
            records = self.progress_sheet.get_all_records()
            row_num = None
            
            for i, record in enumerate(records, start=2):
                if record['username'] == username and record['dataset'] == dataset_id:
                    row_num = i
                    break
            
            if row_num:
                self.progress_sheet.update(f'A{row_num}:F{row_num}', [[
                    username, dataset_id, current_index, total_annotated,
                    datetime.now().isoformat(), last_pair_id
                ]])
            else:
                self.progress_sheet.append_row([
                    username, dataset_id, current_index, total_annotated,
                    datetime.now().isoformat(), last_pair_id
                ])
            
            return True
        except Exception as e:
            self.error_message = str(e)
            return False
    
    def get_user_progress(self, username: str, dataset_id: str) -> Dict:
        """Get user progress"""
        try:
            records = self.progress_sheet.get_all_records()
            
            for record in records:
                if record['username'] == username and record['dataset'] == dataset_id:
                    return {
                        'current_index': int(record['current_index']) if record['current_index'] else 0,
                        'total_annotated': int(record['total_annotated']) if record['total_annotated'] else 0,
                        'last_updated': record['last_updated'],
                        'last_pair_id': record.get('last_pair_id', '')
                    }
            
            return {
                'current_index': 0,
                'total_annotated': 0,
                'last_updated': '',
                'last_pair_id': ''
            }
        except Exception as e:
            self.error_message = str(e)
            return {'current_index': 0, 'total_annotated': 0, 'last_updated': ''}
    
    def get_all_users(self) -> List[str]:
        """Get all registered usernames"""
        try:
            users = self.users_sheet.get_all_records()
            return [user['username'] for user in users]
        except:
            return []

# =============================================================================
# STREAMLIT APPLICATION
# =============================================================================

# Page config
st.set_page_config(
    page_title="CausaFr - Google Sheets Annotation",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .sentence-box {
        background: #f8f9fa;
        border-left: 4px solid #4e73df;
        padding: 1.5rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border: 1px solid #e3e6f0;
    }
    .progress-bar {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 10px;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .stat-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e3e6f0;
    }
    .alert {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .alert-success {
        background: #d1e7dd;
        border: 1px solid #badbcc;
        color: #0f5132;
    }
    .alert-warning {
        background: #fff3cd;
        border: 1px solid #ffecb5;
        color: #664d03;
    }
    .alert-error {
        background: #f8d7da;
        border: 1px solid #f5c2c7;
        color: #842029;
    }
    .tab-content {
        padding: 1rem 0;
    }
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

# Initialize Google Sheets
if st.session_state.gsheets is None:
    st.session_state.gsheets = GoogleSheetsManager()
    if not st.session_state.gsheets.connect():
        st.error(f"❌ Connection failed: {st.session_state.gsheets.error_message}")
        st.stop()

# =============================================================================
# PAGES
# =============================================================================

def login_page():
    """Login/Register page"""
    st.markdown("""
    <div class="main-header">
        <h1>🔗 CausaFr Annotation Tool</h1>
        <p>All data stored in Google Sheets - No local files needed</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Créer un compte"])
        
        with tab1:
            st.markdown("### Connexion")
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            
            if st.button("Se connecter", type="primary", use_container_width=True):
                if username and password:
                    if st.session_state.gsheets.verify_user(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("❌ Identifiants incorrects")
                else:
                    st.warning("⚠️ Remplissez tous les champs")
        
        with tab2:
            st.markdown("### Créer un compte")
            new_user = st.text_input("Nouvel utilisateur")
            new_pass = st.text_input("Nouveau mot de passe", type="password")
            confirm_pass = st.text_input("Confirmer le mot de passe", type="password")
            email = st.text_input("Email (optionnel)")
            
            if st.button("Créer le compte", type="primary", use_container_width=True):
                if new_user and new_pass:
                    if new_pass != confirm_pass:
                        st.error("❌ Les mots de passe ne correspondent pas")
                    else:
                        if st.session_state.gsheets.create_user(new_user, new_pass, email):
                            st.success("✅ Compte créé !")
                            st.info("Connectez-vous maintenant")
                        else:
                            st.error("❌ Ce nom d'utilisateur existe déjà")
                else:
                    st.warning("⚠️ Remplissez tous les champs obligatoires")

def dataset_management_page():
    """Dataset upload and management page"""
    st.markdown("""
    <div class="main-header">
        <h1>📁 Gestion des Datasets</h1>
        <p>Importez vos datasets JSON dans Google Sheets</p>
    </div>
    """, unsafe_allow_html=True)
    
    gsheets = st.session_state.gsheets
    
    tab1, tab2 = st.tabs(["📤 Importer un Dataset", "📋 Datasets Disponibles"])
    
    with tab1:
        st.markdown("### Importer un Dataset JSON")
        
        # Dataset info
        col1, col2 = st.columns(2)
        with col1:
            dataset_id = st.text_input("ID du Dataset", 
                                      placeholder="ex: dataset_1, causal_fr, etc.")
            dataset_name = st.text_input("Nom du Dataset", 
                                        placeholder="Nom affiché")
        with col2:
            created_by = st.text_input("Créé par", value=st.session_state.username)
            description = st.text_area("Description", placeholder="Description du dataset")
        
        # JSON upload
        st.markdown("### Contenu JSON")
        json_method = st.radio("Méthode d'import", 
                              ["📤 Upload fichier", "📝 Coller le JSON"])
        
        json_content = ""
        
        if json_method == "📤 Upload fichier":
            uploaded_file = st.file_uploader("Choisir un fichier JSON", type=['json'])
            if uploaded_file is not None:
                try:
                    json_content = uploaded_file.getvalue().decode('utf-8')
                    st.success(f"✅ Fichier chargé: {uploaded_file.name}")
                    
                    # Preview
                    with st.expander("📄 Aperçu du JSON"):
                        st.code(json_content[:1000] + "..." if len(json_content) > 1000 else json_content, 
                               language="json")
                except Exception as e:
                    st.error(f"❌ Erreur de lecture: {e}")
        
        else:  # Paste JSON
            json_content = st.text_area("Collez votre JSON ici", height=300,
                                       placeholder='{"pairs": [...]} ou [...]')
            if json_content:
                try:
                    json.loads(json_content)
                    st.success("✅ JSON valide")
                except json.JSONDecodeError as e:
                    st.error(f"❌ JSON invalide: {e}")
        
        # Import button
        if st.button("🚀 Importer dans Google Sheets", type="primary", 
                    disabled=not (dataset_id and json_content)):
            with st.spinner("Importation en cours..."):
                if gsheets.import_json_dataset(dataset_id, json_content, 
                                              dataset_name or dataset_id, 
                                              description, created_by):
                    st.success("✅ Dataset importé avec succès !")
                    st.balloons()
                else:
                    st.error(f"❌ Erreur: {gsheets.error_message}")
    
    with tab2:
        st.markdown("### Datasets disponibles")
        
        datasets = gsheets.get_datasets()
        
        if not datasets:
            st.info("📭 Aucun dataset disponible")
            return
        
        for dataset in datasets:
            with st.expander(f"📁 {dataset['name']} ({dataset['id']})"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Description:** {dataset['description']}")
                    st.write(f"**Créé par:** {dataset['created_by']}")
                    st.write(f"**Date:** {dataset['created_at'][:10]}")
                with col2:
                    st.metric("Paires", dataset['pair_count'])
                
                # Load pairs button
                if st.button(f"📊 Voir les paires", key=f"view_{dataset['id']}"):
                    pairs = gsheets.get_dataset_pairs(dataset['id'])
                    if pairs:
                        st.info(f"📋 {len(pairs)} paires chargées")
                        # Preview first 3 pairs
                        for i, pair in enumerate(pairs[:3]):
                            st.write(f"**Paire {i+1}:** {pair.event1_text[:50]}... → {pair.event2_text[:50]}...")
                        if len(pairs) > 3:
                            st.caption(f"... et {len(pairs)-3} autres paires")
                    else:
                        st.warning("❌ Erreur de chargement")

def annotate_page():
    """Main annotation page"""
    username = st.session_state.username
    gsheets = st.session_state.gsheets
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {username}")
        
        # Dataset selection
        st.markdown("### 📁 Dataset")
        
        datasets = gsheets.get_datasets()
        if not datasets:
            st.error("Aucun dataset disponible")
            st.info("Importez d'abord un dataset")
            return
        
        dataset_options = {f"{d['name']} ({d['id']})": d['id'] for d in datasets}
        selected_display = st.selectbox("Choisir un dataset", list(dataset_options.keys()))
        selected_id = dataset_options[selected_display]
        
        if st.session_state.current_dataset != selected_id:
            st.session_state.current_dataset = selected_id
            st.session_state.pair_index = 0
            st.session_state.current_pairs = []
        
        # Load dataset pairs
        if not st.session_state.current_pairs:
            pairs = gsheets.get_dataset_pairs(selected_id)
            if not pairs:
                st.error("❌ Erreur de chargement des paires")
                return
            st.session_state.current_pairs = pairs
        
        pairs = st.session_state.current_pairs
        total_pairs = len(pairs)
        
        # Load progress
        progress = gsheets.get_user_progress(username, selected_id)
        current_index = progress.get('current_index', 0)
        
        if st.session_state.pair_index == 0 and current_index > 0:
            st.session_state.pair_index = min(current_index, total_pairs - 1)
        
        # Statistics
        user_annotations = gsheets.get_user_annotations(username, selected_id)
        annotated_count = len(user_annotations)
        causal_count = sum(1 for ann in user_annotations if ann.get('label') == 1)
        non_causal_count = sum(1 for ann in user_annotations if ann.get('label') == 0)
        
        st.markdown("### 📊 Statistiques")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", total_pairs)
            st.metric("Causales", causal_count)
        with col2:
            st.metric("Annotées", annotated_count)
            st.metric("Non causales", non_causal_count)
        
        # Progress
        st.markdown("### 📍 Progression")
        progress_pct = (annotated_count / total_pairs * 100) if total_pairs > 0 else 0
        st.markdown(f'<div class="progress-bar" style="width: {progress_pct}%"></div>', unsafe_allow_html=True)
        st.caption(f"{annotated_count}/{total_pairs} ({progress_pct:.1f}%)")
        
        # Navigation
        st.markdown("### 🧭 Navigation")
        jump_to = st.number_input("Aller à", 1, total_pairs, st.session_state.pair_index + 1)
        if st.button("Aller", use_container_width=True):
            st.session_state.pair_index = jump_to - 1
            st.rerun()
        
        # Quick navigation
        if st.button("⏭️ Prochaine non annotée", use_container_width=True):
            for i in range(st.session_state.pair_index + 1, total_pairs):
                pair_id = pairs[i].pair_id
                existing = [ann for ann in user_annotations if ann.get('pair_id') == pair_id]
                if not existing:
                    st.session_state.pair_index = i
                    st.rerun()
                    break
        
        st.markdown("---")
        if st.button("🚪 Déconnexion", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content
    if not pairs:
        st.warning("Aucune paire à annoter")
        return
    
    idx = st.session_state.pair_index
    current_pair = pairs[idx]
    
    # Header
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <h2>Paire {idx + 1} / {total_pairs}</h2>
        <span style="background: #e9ecef; padding: 0.5rem 1rem; border-radius: 20px;">
            📄 {selected_display}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if already annotated
    existing_annotations = [ann for ann in user_annotations 
                          if ann.get('pair_id') == current_pair.pair_id]
    
    if existing_annotations:
        existing = existing_annotations[0]
        st.markdown(f"""
        <div class="alert alert-warning">
            ✏️ <strong>Déjà annotée</strong> le {existing.get('annotated_at', '')[:16]}
            (Confidence: {existing.get('confidence', 3)}/5)
        </div>
        """, unsafe_allow_html=True)
    
    # Events display
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔵 Événement 1 (Cause)")
        st.markdown(f'<div class="sentence-box">{current_pair.event1_text}</div>', unsafe_allow_html=True)
        cue1 = st.checkbox("Marqueur causal explicite", 
                          value=bool(existing_annotations[0].get('cue1', 0)) if existing_annotations else False,
                          key="cue1")
    
    with col2:
        st.markdown("#### 🟢 Événement 2 (Effet)")
        st.markdown(f'<div class="sentence-box">{current_pair.event2_text}</div>', unsafe_allow_html=True)
        cue2 = st.checkbox("Marqueur causal explicite",
                          value=bool(existing_annotations[0].get('cue2', 0)) if existing_annotations else False,
                          key="cue2")
    
    # Annotation question
    st.markdown("""
    <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                padding: 1.5rem; border-radius: 10px; margin: 2rem 0; text-align: center;">
        <h3 style="color: #1565c0; margin: 0 0 0.5rem 0;">❓ Relation causale ?</h3>
        <p style="color: #1976d2; margin: 0;">L'événement 1 cause-t-il l'événement 2 ?</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Annotation controls
    col1, col2 = st.columns(2)
    
    with col1:
        current_label = existing_annotations[0].get('label') if existing_annotations else None
        label = st.radio(
            "Décision",
            [1, 0],
            index=0 if current_label == 1 else 1,
            format_func=lambda x: "✅ OUI - Relation causale" if x == 1 else "❌ NON - Pas de relation",
            key="label"
        )
    
    with col2:
        current_conf = existing_annotations[0].get('confidence', 3) if existing_annotations else 3
        confidence = st.slider("Confiance", 1, 5, current_conf, key="confidence")
        notes = st.text_input("Notes", 
                             value=existing_annotations[0].get('notes', '') if existing_annotations else '',
                             placeholder="Notes optionnelles...",
                             key="notes")
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
    with col1:
        if st.button("⬅️", disabled=idx == 0, use_container_width=True):
            st.session_state.pair_index -= 1
            st.rerun()
    
    with col2:
        if st.button("💾 Enregistrer", type="primary", use_container_width=True):
            annotation = Annotation(
                id="",
                pair_id=current_pair.pair_id,
                dataset=selected_id,
                username=username,
                event1_text=current_pair.event1_text,
                event2_text=current_pair.event2_text,
                cue1=int(cue1),
                cue2=int(cue2),
                label=int(label),
                confidence=confidence,
                notes=notes,
                annotated_at=datetime.now().isoformat(),
                event1_id=current_pair.event1_id,
                event2_id=current_pair.event2_id
            )
            
            ann_id = gsheets.save_annotation(annotation)
            if ann_id:
                user_anns = gsheets.get_user_annotations(username, selected_id)
                gsheets.update_progress(username, selected_id, idx, len(user_anns), current_pair.pair_id)
                st.success("✅ Annotation sauvegardée")
                st.rerun()
            else:
                st.error(f"❌ Erreur: {gsheets.error_message}")
    
    with col3:
        if st.button("💾 & ⏭️ Suivant", use_container_width=True):
            annotation = Annotation(
                id="",
                pair_id=current_pair.pair_id,
                dataset=selected_id,
                username=username,
                event1_text=current_pair.event1_text,
                event2_text=current_pair.event2_text,
                cue1=int(cue1),
                cue2=int(cue2),
                label=int(label),
                confidence=confidence,
                notes=notes,
                annotated_at=datetime.now().isoformat(),
                event1_id=current_pair.event1_id,
                event2_id=current_pair.event2_id
            )
            
            ann_id = gsheets.save_annotation(annotation)
            if ann_id:
                user_anns = gsheets.get_user_annotations(username, selected_id)
                gsheets.update_progress(username, selected_id, idx, len(user_anns), current_pair.pair_id)
                if idx < total_pairs - 1:
                    st.session_state.pair_index += 1
                st.rerun()
            else:
                st.error(f"❌ Erreur: {gsheets.error_message}")
    
    with col4:
        if st.button("➡️", disabled=idx >= total_pairs - 1, use_container_width=True):
            st.session_state.pair_index += 1
            st.rerun()
    
    # Export button
    st.markdown("---")
    if st.button("📥 Exporter mes annotations", use_container_width=True):
        user_annotations = gsheets.get_user_annotations(username, selected_id)
        if user_annotations:
            export_data = {
                'metadata': {
                    'username': username,
                    'dataset': selected_id,
                    'exported_at': datetime.now().isoformat(),
                    'total_annotations': len(user_annotations)
                },
                'annotations': user_annotations
            }
            
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            st.download_button(
                "⬇️ Télécharger JSON",
                json_str,
                file_name=f"causafr_{username}_{selected_id}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.warning("Aucune annotation à exporter")

def dashboard_page():
    """Dashboard page"""
    username = st.session_state.username
    gsheets = st.session_state.gsheets
    
    st.markdown(f"""
    <div class="main-header">
        <h1>📊 Tableau de bord</h1>
        <p>Statistiques et visualisation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get all data
    datasets = gsheets.get_datasets()
    all_annotations = []
    for dataset in datasets:
        annotations = gsheets.get_user_annotations(username, dataset['id'])
        all_annotations.extend(annotations)
    
    if not all_annotations:
        st.info("📭 Aucune annotation trouvée")
        return
    
    # Statistics
    st.markdown("### 📈 Vos statistiques")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Annotations totales", len(all_annotations))
    with col2:
        datasets_annotated = len(set(ann['dataset'] for ann in all_annotations))
        st.metric("Datasets annotés", datasets_annotated)
    with col3:
        causal = sum(1 for ann in all_annotations if ann.get('label') == 1)
        st.metric("Relations causales", causal)
    with col4:
        avg_conf = sum(ann.get('confidence', 3) for ann in all_annotations) / len(all_annotations) if all_annotations else 0
        st.metric("Confiance moyenne", f"{avg_conf:.1f}/5")
    
    # Per dataset statistics
    st.markdown("### 📋 Par dataset")
    
    for dataset in datasets:
        dataset_anns = [ann for ann in all_annotations if ann['dataset'] == dataset['id']]
        if dataset_anns:
            with st.expander(f"📁 {dataset['name']} ({len(dataset_anns)} annotations)"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    causal_rate = sum(1 for ann in dataset_anns if ann.get('label') == 1) / len(dataset_anns) * 100
                    st.metric("Taux causal", f"{causal_rate:.1f}%")
                with col2:
                    avg_conf = sum(ann.get('confidence', 3) for ann in dataset_anns) / len(dataset_anns)
                    st.metric("Confiance", f"{avg_conf:.1f}/5")
                with col3:
                    progress = gsheets.get_user_progress(username, dataset['id'])
                    st.metric("Progression", f"{progress.get('total_annotated', 0)}/{dataset['pair_count']}")
                
                # Recent annotations
                st.markdown("**Dernières annotations:**")
                for ann in dataset_anns[-5:]:
                    label_icon = "✅" if ann.get('label') == 1 else "❌"
                    st.write(f"{label_icon} {ann.get('event1_text', '')[:50]}... → {ann.get('event2_text', '')[:50]}...")

def about_page():
    """About page"""
    st.markdown(f"""
    <div class="main-header">
        <h1>ℹ️ À propos</h1>
        <p>CausaFr - Annotation Tool</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <h3>🎯 Objectif</h3>
        <p>Outil collaboratif d'annotation de relations causales. Toutes les données sont stockées dans Google Sheets.</p>
        
        <h3>🔧 Architecture</h3>
        <p><strong>5 feuilles Google Sheets :</strong></p>
        <ol>
            <li><strong>users</strong> - Comptes utilisateurs</li>
            <li><strong>datasets</strong> - Métadonnées des datasets</li>
            <li><strong>dataset_pairs</strong> - Paires d'événements à annoter</li>
            <li><strong>annotations</strong> - Annotations sauvegardées</li>
            <li><strong>progress</strong> - Progression des utilisateurs</li>
        </ol>
        
        <h3>🚀 Avantages</h3>
        <ul>
            <li>✅ Aucun fichier local nécessaire</li>
            <li>✅ Collaboration en temps réel</li>
            <li>✅ Données persistantes dans Google Sheets</li>
            <li>✅ Export facile vers JSON</li>
            <li>✅ Déploiement simple sur Streamlit Cloud</li>
        </ul>
        
        <h3>📊 État de la connexion</h3>
    </div>
    """, unsafe_allow_html=True)
    
    gsheets = st.session_state.gsheets
    if gsheets.connected:
        st.success("✅ Connecté à Google Sheets")
        
        # Quick stats
        col1, col2, col3 = st.columns(3)
        with col1:
            users = gsheets.get_all_users()
            st.metric("Utilisateurs", len(users))
        with col2:
            datasets = gsheets.get_datasets()
            st.metric("Datasets", len(datasets))
        with col3:
            # Count total pairs across all datasets
            total_pairs = sum(d['pair_count'] for d in datasets)
            st.metric("Paires totales", total_pairs)
    else:
        st.error(f"❌ Non connecté")

# =============================================================================
# MAIN APP
# =============================================================================

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
        </div>
        """, unsafe_allow_html=True)
        
        page = st.radio(
            "Navigation",
            ["📤 Gérer Datasets", "✏️ Annoter", "📊 Tableau de bord", "ℹ️ À propos"],
            label_visibility="collapsed"
        )
    
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
