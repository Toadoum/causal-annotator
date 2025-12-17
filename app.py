
"""
CausaFr - Complete Google Sheets Annotation Tool
Streamlit Cloud Deployment Version
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
from dataclasses import dataclass, asdict
from io import StringIO

# =============================================================================
# GOOGLE SHEETS CONFIGURATION - Streamlit Secrets
# =============================================================================

# Load config from Streamlit secrets
try:
    if 'GOOGLE_SHEETS' in st.secrets:
        GOOGLE_CONFIG = {
            'spreadsheet_id': st.secrets['GOOGLE_SHEETS']['spreadsheet_id'],
            'gcp_credentials': {
                'type': st.secrets['GOOGLE_SHEETS']['type'],
                'project_id': st.secrets['GOOGLE_SHEETS']['project_id'],
                'private_key_id': st.secrets['GOOGLE_SHEETS']['private_key_id'],
                'private_key': st.secrets['GOOGLE_SHEETS']['private_key'].replace('\\n', '\n'),
                'client_email': st.secrets['GOOGLE_SHEETS']['client_email'],
                'client_id': st.secrets['GOOGLE_SHEETS']['client_id'],
                'auth_uri': st.secrets['GOOGLE_SHEETS']['auth_uri'],
                'token_uri': st.secrets['GOOGLE_SHEETS']['token_uri'],
                'auth_provider_x509_cert_url': st.secrets['GOOGLE_SHEETS']['auth_provider_x509_cert_url'],
                'client_x509_cert_url': st.secrets['GOOGLE_SHEETS']['client_x509_cert_url']
            }
        }
    else:
        st.error("Google Sheets configuration not found in secrets")
        GOOGLE_CONFIG = None
except Exception as e:
    st.error(f"Error loading configuration: {e}")
    GOOGLE_CONFIG = None

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class OriginalPair:
    """Original pair data from JSON files"""
    pair_id: str
    dataset: str
    event1_text: str
    event2_text: str
    event1_id: str
    event2_id: str
    narrative_id: str = ""
    event1_category: str = ""
    event2_category: str = ""
    label: Optional[int] = None
    is_hard_negative: bool = False
    event1_has_causal_cue: bool = False
    event1_causal_cue_type: Optional[str] = None
    event1_causal_cue_text: Optional[str] = None
    event1_has_temporal: bool = False
    event1_temporal_type: Optional[str] = None
    event1_temporal_text: Optional[str] = None
    event2_has_causal_cue: bool = False
    event2_causal_cue_type: Optional[str] = None
    event2_causal_cue_text: Optional[str] = None
    event2_has_temporal: bool = False
    event2_temporal_type: Optional[str] = None
    event2_temporal_text: Optional[str] = None
    pair_has_causal_cue: bool = False
    pair_has_temporal: bool = False
    row_index: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary matching original JSON structure"""
        return {
            "narrative_id": self.narrative_id,
            "event1_id": self.event1_id,
            "event2_id": self.event2_id,
            "event1_text": self.event1_text,
            "event2_text": self.event2_text,
            "event1_category": self.event1_category,
            "event2_category": self.event2_category,
            "label": self.label,
            "is_hard_negative": self.is_hard_negative,
            "event1_has_causal_cue": self.event1_has_causal_cue,
            "event1_causal_cue_type": self.event1_causal_cue_type,
            "event1_causal_cue_text": self.event1_causal_cue_text,
            "event1_has_temporal": self.event1_has_temporal,
            "event1_temporal_type": self.event1_temporal_type,
            "event1_temporal_text": self.event1_temporal_text,
            "event2_has_causal_cue": self.event2_has_causal_cue,
            "event2_causal_cue_type": self.event2_causal_cue_type,
            "event2_causal_cue_text": self.event2_causal_cue_text,
            "event2_has_temporal": self.event2_has_temporal,
            "event2_temporal_type": self.event2_temporal_type,
            "event2_temporal_text": self.event2_temporal_text,
            "pair_has_causal_cue": self.pair_has_causal_cue,
            "pair_has_temporal": self.pair_has_temporal
        }

@dataclass
class UserAnnotation:
    """User annotation data"""
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
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class DatasetMetadata:
    """Dataset metadata"""
    dataset_id: str
    name: str
    description: str
    created_by: str
    created_at: str
    pair_count: int
    original_filename: str = ""

# =============================================================================
# GOOGLE SHEETS MANAGER
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
        if GOOGLE_CONFIG is None:
            self.error_message = "Google Sheets configuration not found"
            return False
            
        try:
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
            self.users_sheet = self.spreadsheet.add_worksheet('users', 100, 6)
            self.users_sheet.update('A1:F1', [
                ['username', 'password_hash', 'email', 'created_at', 'last_login', 'is_admin']
            ])
        else:
            self.users_sheet = self.spreadsheet.worksheet('users')
        
        # 2. DATASETS sheet (dataset metadata)
        if 'datasets' not in sheet_titles:
            self.datasets_sheet = self.spreadsheet.add_worksheet('datasets', 100, 7)
            self.datasets_sheet.update('A1:G1', [
                ['dataset_id', 'name', 'description', 'created_by', 'created_at', 'pair_count', 'original_filename']
            ])
        else:
            self.datasets_sheet = self.spreadsheet.worksheet('datasets')
        
        # 3. DATASET_PAIRS sheet (actual pairs data with ALL fields)
        if 'dataset_pairs' not in sheet_titles:
            self.dataset_pairs_sheet = self.spreadsheet.add_worksheet('dataset_pairs', 10000, 28)
            headers = [
                'pair_id', 'dataset', 'event1_text', 'event2_text', 
                'event1_id', 'event2_id', 'narrative_id', 'event1_category',
                'event2_category', 'original_label', 'is_hard_negative',
                'event1_has_causal_cue', 'event1_causal_cue_type', 'event1_causal_cue_text',
                'event1_has_temporal', 'event1_temporal_type', 'event1_temporal_text',
                'event2_has_causal_cue', 'event2_causal_cue_type', 'event2_causal_cue_text',
                'event2_has_temporal', 'event2_temporal_type', 'event2_temporal_text',
                'pair_has_causal_cue', 'pair_has_temporal', 'row_index',
                'imported_at', 'pair_hash'
            ]
            self.dataset_pairs_sheet.update('A1:AB1', [headers])
        else:
            self.dataset_pairs_sheet = self.spreadsheet.worksheet('dataset_pairs')
        
        # 4. ANNOTATIONS sheet
        if 'annotations' not in sheet_titles:
            self.annotations_sheet = self.spreadsheet.add_worksheet('annotations', 10000, 16)
            headers = [
                'id', 'pair_id', 'dataset', 'username', 'event1_text', 'event2_text',
                'cue1', 'cue2', 'label', 'confidence', 'notes', 'annotated_at',
                'event1_id', 'event2_id', 'exported', 'annotation_hash'
            ]
            self.annotations_sheet.update('A1:P1', [headers])
        else:
            self.annotations_sheet = self.spreadsheet.worksheet('annotations')
        
        # 5. PROGRESS sheet
        if 'progress' not in sheet_titles:
            self.progress_sheet = self.spreadsheet.add_worksheet('progress', 100, 7)
            self.progress_sheet.update('A1:G1', [
                ['username', 'dataset', 'current_index', 'total_annotated', 
                 'last_updated', 'last_pair_id', 'completion_rate']
            ])
        else:
            self.progress_sheet = self.spreadsheet.worksheet('progress')
    
    # ========== USER MANAGEMENT ==========
    
    def create_user(self, username: str, password: str, email: str = "", is_admin: bool = False) -> bool:
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
                datetime.now().isoformat(),
                1 if is_admin else 0
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
    
    def is_admin(self, username: str) -> bool:
        """Check if user is admin"""
        try:
            users = self.users_sheet.get_all_records()
            for user in users:
                if user['username'] == username:
                    return bool(int(user.get('is_admin', 0)))
            return False
        except:
            return False
    
    # ========== DATASET MANAGEMENT ==========
    
    def _generate_pair_hash(self, pair_data: Dict) -> str:
        """Generate hash for pair data to detect duplicates"""
        hash_string = f"{pair_data.get('event1_text', '')}_{pair_data.get('event2_text', '')}"
        return hashlib.md5(hash_string.encode()).hexdigest()[:8]
    
    def import_json_dataset(self, dataset_id: str, json_content: str, 
                           name: str = "", description: str = "", 
                           created_by: str = "", original_filename: str = "") -> Tuple[bool, int, int]:
        """
        Import a JSON dataset into Google Sheets
        Returns: (success, total_pairs, imported_pairs)
        """
        try:
            data = json.loads(json_content)
            
            # Determine pairs based on JSON structure
            if isinstance(data, list):
                pairs = data
            elif isinstance(data, dict) and 'pairs' in data:
                pairs = data['pairs']
            else:
                self.error_message = "Invalid JSON format: Expected list or dict with 'pairs' key"
                return False, 0, 0
            
            # Check if dataset already exists
            datasets = self.datasets_sheet.get_all_records()
            existing_dataset = None
            for dataset in datasets:
                if dataset['dataset_id'] == dataset_id:
                    existing_dataset = dataset
                    break
            
            # If dataset exists, check for duplicates
            existing_pairs = []
            if existing_dataset:
                # Get existing pairs for this dataset
                all_pairs = self.dataset_pairs_sheet.get_all_records()
                existing_pairs = [p for p in all_pairs if p['dataset'] == dataset_id]
                
                # Generate hashes for existing pairs
                existing_hashes = {p.get('pair_hash', '') for p in existing_pairs}
            else:
                existing_hashes = set()
            
            # Use dataset_id as name if not provided
            if not name:
                name = dataset_id
            
            imported_count = 0
            skipped_count = 0
            
            # Import pairs
            for i, pair in enumerate(pairs):
                # Generate pair hash for duplicate detection
                pair_hash = self._generate_pair_hash(pair)
                
                # Skip if already exists
                if pair_hash in existing_hashes:
                    skipped_count += 1
                    continue
                
                # Prepare pair data
                pair_id = pair.get('pair_id', f"{dataset_id}_{len(existing_pairs) + imported_count}")
                
                # Convert boolean values to 1/0 for Google Sheets
                def bool_to_int(value):
                    return 1 if value else 0
                
                self.dataset_pairs_sheet.append_row([
                    pair_id,
                    dataset_id,
                    pair.get('event1_text', ''),
                    pair.get('event2_text', ''),
                    str(pair.get('event1_id', '')),
                    str(pair.get('event2_id', '')),
                    pair.get('narrative_id', ''),
                    pair.get('event1_category', ''),
                    pair.get('event2_category', ''),
                    pair.get('label', ''),
                    bool_to_int(pair.get('is_hard_negative', False)),
                    bool_to_int(pair.get('event1_has_causal_cue', False)),
                    pair.get('event1_causal_cue_type', ''),
                    pair.get('event1_causal_cue_text', ''),
                    bool_to_int(pair.get('event1_has_temporal', False)),
                    pair.get('event1_temporal_type', ''),
                    pair.get('event1_temporal_text', ''),
                    bool_to_int(pair.get('event2_has_causal_cue', False)),
                    pair.get('event2_causal_cue_type', ''),
                    pair.get('event2_causal_cue_text', ''),
                    bool_to_int(pair.get('event2_has_temporal', False)),
                    pair.get('event2_temporal_type', ''),
                    pair.get('event2_temporal_text', ''),
                    bool_to_int(pair.get('pair_has_causal_cue', False)),
                    bool_to_int(pair.get('pair_has_temporal', False)),
                    len(existing_pairs) + imported_count,  # row_index
                    datetime.now().isoformat(),
                    pair_hash
                ])
                
                imported_count += 1
            
            # Update or create dataset metadata
            total_pairs = len(existing_pairs) + imported_count
            
            if existing_dataset:
                # Update existing dataset
                row_num = datasets.index(existing_dataset) + 2
                self.datasets_sheet.update(f'A{row_num}:G{row_num}', [[
                    dataset_id,
                    name,
                    description,
                    created_by,
                    existing_dataset.get('created_at', datetime.now().isoformat()),
                    total_pairs,
                    original_filename
                ]])
            else:
                # Create new dataset
                self.datasets_sheet.append_row([
                    dataset_id,
                    name,
                    description,
                    created_by,
                    datetime.now().isoformat(),
                    total_pairs,
                    original_filename
                ])
            
            return True, len(pairs), imported_count
            
        except json.JSONDecodeError as e:
            self.error_message = f"Invalid JSON: {str(e)}"
            return False, 0, 0
        except Exception as e:
            self.error_message = str(e)
            return False, 0, 0
    
    def get_datasets(self) -> List[DatasetMetadata]:
        """Get all available datasets"""
        try:
            records = self.datasets_sheet.get_all_records()
            datasets = []
            for r in records:
                datasets.append(DatasetMetadata(
                    dataset_id=r['dataset_id'],
                    name=r['name'],
                    description=r['description'],
                    created_by=r['created_by'],
                    created_at=r['created_at'],
                    pair_count=int(r['pair_count']) if r['pair_count'] else 0,
                    original_filename=r.get('original_filename', '')
                ))
            return datasets
        except Exception as e:
            self.error_message = str(e)
            return []
    
    def get_dataset_pairs(self, dataset_id: str) -> List[OriginalPair]:
        """Get all pairs for a dataset"""
        try:
            records = self.dataset_pairs_sheet.get_all_records()
            pairs = []
            
            for record in records:
                if record['dataset'] == dataset_id:
                    # Helper function to convert string to bool
                    def str_to_bool(value):
                        if isinstance(value, str):
                            return value.strip().lower() in ['true', '1', 'yes', 'y']
                        return bool(value)
                    
                    # Helper function to convert to int if possible
                    def to_int(value):
                        try:
                            return int(value)
                        except:
                            return None
                    
                    pairs.append(OriginalPair(
                        pair_id=record['pair_id'],
                        dataset=record['dataset'],
                        event1_text=record['event1_text'],
                        event2_text=record['event2_text'],
                        event1_id=record['event1_id'],
                        event2_id=record['event2_id'],
                        narrative_id=record.get('narrative_id', ''),
                        event1_category=record.get('event1_category', ''),
                        event2_category=record.get('event2_category', ''),
                        label=to_int(record.get('original_label')),
                        is_hard_negative=str_to_bool(record.get('is_hard_negative', False)),
                        event1_has_causal_cue=str_to_bool(record.get('event1_has_causal_cue', False)),
                        event1_causal_cue_type=record.get('event1_causal_cue_type'),
                        event1_causal_cue_text=record.get('event1_causal_cue_text'),
                        event1_has_temporal=str_to_bool(record.get('event1_has_temporal', False)),
                        event1_temporal_type=record.get('event1_temporal_type'),
                        event1_temporal_text=record.get('event1_temporal_text'),
                        event2_has_causal_cue=str_to_bool(record.get('event2_has_causal_cue', False)),
                        event2_causal_cue_type=record.get('event2_causal_cue_type'),
                        event2_causal_cue_text=record.get('event2_causal_cue_text'),
                        event2_has_temporal=str_to_bool(record.get('event2_has_temporal', False)),
                        event2_temporal_type=record.get('event2_temporal_type'),
                        event2_temporal_text=record.get('event2_temporal_text'),
                        pair_has_causal_cue=str_to_bool(record.get('pair_has_causal_cue', False)),
                        pair_has_temporal=str_to_bool(record.get('pair_has_temporal', False)),
                        row_index=int(record.get('row_index', 0)) if record.get('row_index') else 0
                    ))
            
            # Sort by row_index
            pairs.sort(key=lambda x: x.row_index)
            return pairs
        except Exception as e:
            self.error_message = str(e)
            return []
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset and all its data"""
        try:
            # 1. Delete dataset metadata
            datasets = self.datasets_sheet.get_all_records()
            dataset_rows_to_delete = []
            for i, dataset in enumerate(datasets, start=2):
                if dataset['dataset_id'] == dataset_id:
                    dataset_rows_to_delete.append(i)
            
            # Delete from bottom to top to preserve row numbers
            for row in sorted(dataset_rows_to_delete, reverse=True):
                self.datasets_sheet.delete_rows(row)
            
            # 2. Delete dataset pairs
            pairs = self.dataset_pairs_sheet.get_all_records()
            pair_rows_to_delete = []
            for i, pair in enumerate(pairs, start=2):
                if pair['dataset'] == dataset_id:
                    pair_rows_to_delete.append(i)
            
            for row in sorted(pair_rows_to_delete, reverse=True):
                self.dataset_pairs_sheet.delete_rows(row)
            
            # 3. Delete annotations for this dataset
            annotations = self.annotations_sheet.get_all_records()
            annotation_rows_to_delete = []
            for i, ann in enumerate(annotations, start=2):
                if ann['dataset'] == dataset_id:
                    annotation_rows_to_delete.append(i)
            
            for row in sorted(annotation_rows_to_delete, reverse=True):
                self.annotations_sheet.delete_rows(row)
            
            # 4. Delete progress records for this dataset
            progress = self.progress_sheet.get_all_records()
            progress_rows_to_delete = []
            for i, prog in enumerate(progress, start=2):
                if prog['dataset'] == dataset_id:
                    progress_rows_to_delete.append(i)
            
            for row in sorted(progress_rows_to_delete, reverse=True):
                self.progress_sheet.delete_rows(row)
            
            return True
        except Exception as e:
            self.error_message = str(e)
            return False
    
    # ========== ANNOTATION MANAGEMENT ==========
    
    def save_annotation(self, annotation: UserAnnotation) -> str:
        """Save an annotation"""
        try:
            ann_id = str(uuid.uuid4())[:8]
            
            # Generate hash for duplicate detection
            hash_string = f"{annotation.pair_id}_{annotation.username}_{annotation.annotated_at}"
            annotation_hash = hashlib.md5(hash_string.encode()).hexdigest()[:8]
            
            # Check if annotation already exists for this user and pair
            existing_annotations = self.annotations_sheet.get_all_records()
            for existing in existing_annotations:
                if (existing['pair_id'] == annotation.pair_id and 
                    existing['username'] == annotation.username):
                    # Update existing annotation
                    row_num = existing_annotations.index(existing) + 2
                    self.annotations_sheet.update(f'A{row_num}:P{row_num}', [[
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
                        "0",  # not exported
                        annotation_hash
                    ]])
                    return ann_id
            
            # Create new annotation
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
                "0",  # not exported
                annotation_hash
            ])
            
            return ann_id
        except Exception as e:
            self.error_message = str(e)
            return ""
    
    def get_user_annotations(self, username: str, dataset_id: str = None) -> List[UserAnnotation]:
        """Get annotations for a user"""
        try:
            records = self.annotations_sheet.get_all_records()
            annotations = []
            
            for record in records:
                if record['username'] == username:
                    if dataset_id and record['dataset'] != dataset_id:
                        continue
                    
                    annotations.append(UserAnnotation(
                        id=record['id'],
                        pair_id=record['pair_id'],
                        dataset=record['dataset'],
                        username=record['username'],
                        event1_text=record['event1_text'],
                        event2_text=record['event2_text'],
                        cue1=int(record['cue1']) if record['cue1'] else 0,
                        cue2=int(record['cue2']) if record['cue2'] else 0,
                        label=int(record['label']) if record['label'] else None,
                        confidence=int(record['confidence']) if record['confidence'] else 3,
                        notes=record['notes'],
                        annotated_at=record['annotated_at'],
                        event1_id=record['event1_id'],
                        event2_id=record['event2_id']
                    ))
            
            return annotations
        except Exception as e:
            self.error_message = str(e)
            return []
    
    def get_all_annotations(self, dataset_id: str = None) -> List[Dict]:
        """Get all annotations"""
        try:
            records = self.annotations_sheet.get_all_records()
            if dataset_id:
                return [r for r in records if r['dataset'] == dataset_id]
            return records
        except Exception as e:
            self.error_message = str(e)
            return []
    
    def get_annotations_by_pair(self, pair_id: str) -> List[UserAnnotation]:
        """Get all annotations for a specific pair"""
        try:
            records = self.annotations_sheet.get_all_records()
            annotations = []
            
            for record in records:
                if record['pair_id'] == pair_id:
                    annotations.append(UserAnnotation(
                        id=record['id'],
                        pair_id=record['pair_id'],
                        dataset=record['dataset'],
                        username=record['username'],
                        event1_text=record['event1_text'],
                        event2_text=record['event2_text'],
                        cue1=int(record['cue1']) if record['cue1'] else 0,
                        cue2=int(record['cue2']) if record['cue2'] else 0,
                        label=int(record['label']) if record['label'] else None,
                        confidence=int(record['confidence']) if record['confidence'] else 3,
                        notes=record['notes'],
                        annotated_at=record['annotated_at'],
                        event1_id=record['event1_id'],
                        event2_id=record['event2_id']
                    ))
            
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
            
            # Get total pairs in dataset
            dataset_pairs = self.get_dataset_pairs(dataset_id)
            total_pairs = len(dataset_pairs)
            completion_rate = (total_annotated / total_pairs * 100) if total_pairs > 0 else 0
            
            if row_num:
                self.progress_sheet.update(f'A{row_num}:G{row_num}', [[
                    username, dataset_id, current_index, total_annotated,
                    datetime.now().isoformat(), last_pair_id,
                    f"{completion_rate:.1f}%"
                ]])
            else:
                self.progress_sheet.append_row([
                    username, dataset_id, current_index, total_annotated,
                    datetime.now().isoformat(), last_pair_id,
                    f"{completion_rate:.1f}%"
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
                        'last_pair_id': record.get('last_pair_id', ''),
                        'completion_rate': record.get('completion_rate', '0%')
                    }
            
            return {
                'current_index': 0,
                'total_annotated': 0,
                'last_updated': '',
                'last_pair_id': '',
                'completion_rate': '0%'
            }
        except Exception as e:
            self.error_message = str(e)
            return {'current_index': 0, 'total_annotated': 0, 'last_updated': ''}
    
    # ========== EXPORT FUNCTIONALITY ==========
    
    def export_annotated_dataset(self, dataset_id: str, include_original: bool = True) -> Optional[Dict]:
        """
        Export annotated dataset with all original fields plus annotations
        Returns JSON structure matching original format
        """
        try:
            # Get dataset metadata
            datasets = self.get_datasets()
            dataset_meta = None
            for ds in datasets:
                if ds.dataset_id == dataset_id:
                    dataset_meta = ds
                    break
            
            if not dataset_meta:
                self.error_message = f"Dataset {dataset_id} not found"
                return None
            
            # Get original pairs
            original_pairs = self.get_dataset_pairs(dataset_id)
            if not original_pairs:
                self.error_message = f"No pairs found for dataset {dataset_id}"
                return None
            
            # Get all annotations for this dataset
            all_annotations = self.get_all_annotations(dataset_id)
            
            # Create annotation lookup by pair_id
            annotations_by_pair = {}
            for ann in all_annotations:
                pair_id = ann['pair_id']
                if pair_id not in annotations_by_pair:
                    annotations_by_pair[pair_id] = []
                annotations_by_pair[pair_id].append(ann)
            
            # Build exported pairs
            exported_pairs = []
            for pair in original_pairs:
                pair_dict = pair.to_dict()
                
                # Add annotations if available
                if pair.pair_id in annotations_by_pair:
                    pair_annotations = annotations_by_pair[pair.pair_id]
                    
                    # Add annotation data
                    pair_dict['annotations'] = []
                    for ann in pair_annotations:
                        pair_dict['annotations'].append({
                            'username': ann['username'],
                            'cue1': bool(int(ann.get('cue1', 0))),
                            'cue2': bool(int(ann.get('cue2', 0))),
                            'label': int(ann.get('label', 0)) if ann.get('label') else None,
                            'confidence': int(ann.get('confidence', 3)),
                            'notes': ann.get('notes', ''),
                            'annotated_at': ann.get('annotated_at', '')
                        })
                    
                    # Calculate consensus if multiple annotations
                    if len(pair_annotations) > 1:
                        labels = [int(a['label']) for a in pair_annotations if a.get('label')]
                        if labels:
                            pair_dict['consensus_label'] = 1 if sum(labels) / len(labels) >= 0.5 else 0
                            pair_dict['agreement_rate'] = f"{(sum(1 for l in labels if l == pair_dict['consensus_label']) / len(labels) * 100):.1f}%"
                
                exported_pairs.append(pair_dict)
            
            # Build export structure
            export_data = {
                'metadata': {
                    'dataset_id': dataset_meta.dataset_id,
                    'name': dataset_meta.name,
                    'description': dataset_meta.description,
                    'created_by': dataset_meta.created_by,
                    'created_at': dataset_meta.created_at,
                    'exported_at': datetime.now().isoformat(),
                    'total_pairs': dataset_meta.pair_count,
                    'original_filename': dataset_meta.original_filename,
                    'export_format': 'annotated_full'
                },
                'statistics': {
                    'total_annotations': len(all_annotations),
                    'unique_annotators': len(set(a['username'] for a in all_annotations)),
                    'annotated_pairs': len(annotations_by_pair),
                    'completion_rate': f"{(len(annotations_by_pair) / len(original_pairs) * 100):.1f}%" if original_pairs else "0%"
                },
                'pairs': exported_pairs
            }
            
            return export_data
            
        except Exception as e:
            self.error_message = str(e)
            return None
    
    def export_user_annotations(self, username: str, dataset_id: str = None) -> Optional[Dict]:
        """
        Export user's annotations only
        """
        try:
            user_annotations = self.get_user_annotations(username, dataset_id)
            
            if not user_annotations:
                self.error_message = "No annotations found"
                return None
            
            # Group by dataset if no specific dataset
            if dataset_id:
                datasets = [self.get_datasets()[0]]  # Get specific dataset
            else:
                datasets = self.get_datasets()
            
            export_data = {
                'metadata': {
                    'username': username,
                    'exported_at': datetime.now().isoformat(),
                    'total_annotations': len(user_annotations)
                },
                'annotations_by_dataset': {}
            }
            
            for ds in datasets:
                ds_annotations = [a for a in user_annotations if a.dataset == ds.dataset_id]
                if ds_annotations:
                    export_data['annotations_by_dataset'][ds.dataset_id] = {
                        'dataset_name': ds.name,
                        'annotations': [a.to_dict() for a in ds_annotations]
                    }
            
            return export_data
            
        except Exception as e:
            self.error_message = str(e)
            return None
    
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
    page_title="CausaFr - Multi-Dataset Annotation",
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
    .alert-info {
        background: #cff4fc;
        border: 1px solid #b6effb;
        color: #055160;
    }
    .dataset-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #e3e6f0;
        transition: all 0.3s;
    }
    .dataset-card:hover {
        border-color: #667eea;
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.1);
    }
    .tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .tag-primary {
        background: #667eea;
        color: white;
    }
    .tag-success {
        background: #10b981;
        color: white;
    }
    .tag-warning {
        background: #f59e0b;
        color: white;
    }
    .tag-info {
        background: #3b82f6;
        color: white;
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
    st.session_state.is_admin = False

# Check configuration
if GOOGLE_CONFIG is None:
    st.error("Google Sheets configuration not found. Please check your secrets.")
    st.stop()

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
        <h1>🔗 CausaFr - Multi-Dataset Annotation Tool</h1>
        <p>All data stored in Google Sheets - Supports multiple JSON datasets</p>
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
                        st.session_state.is_admin = st.session_state.gsheets.is_admin(username)
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
            
            # Only admins can create admin accounts - removed from public registration
            # is_admin = st.checkbox("Créer comme administrateur", value=False)
            
            if st.button("Créer le compte", type="primary", use_container_width=True):
                if new_user and new_pass:
                    if new_pass != confirm_pass:
                        st.error("❌ Les mots de passe ne correspondent pas")
                    else:
                        # Always create as non-admin for public registration
                        if st.session_state.gsheets.create_user(new_user, new_pass, email, is_admin=False):
                            st.success("✅ Compte créé !")
                            st.info("Connectez-vous maintenant")
                        else:
                            st.error("❌ Ce nom d'utilisateur existe déjà")
                else:
                    st.warning("⚠️ Remplissez tous les champs obligatoires")

def dataset_management_page():
    """Dataset upload and management page - ADMIN ONLY"""
    # Double-check admin status
    if not st.session_state.is_admin:
        st.error("⛔ Accès refusé - Cette section est réservée aux administrateurs")
        st.info("Veuillez contacter un administrateur si vous avez besoin d'accéder à cette fonctionnalité.")
        return
    
    st.markdown("""
    <div class="main-header">
        <h1>📁 Gestion des Datasets</h1>
        <p>Importez et gérez vos datasets JSON dans Google Sheets</p>
        <p style="color: #f59e0b; font-size: 0.9rem;">👑 Section Administrateur</p>
    </div>
    """, unsafe_allow_html=True)
    
    gsheets = st.session_state.gsheets
    
    tab1, tab2, tab3 = st.tabs(["📤 Importer Dataset", "📋 Datasets Disponibles", "🗑️ Gestion"])
    
    with tab1:
        st.markdown("### Importer un Dataset JSON")
        
        # Dataset info
        col1, col2 = st.columns(2)
        with col1:
            dataset_id = st.text_input("ID du Dataset*", 
                                      placeholder="ex: dataset_1, causal_fr, etc.")
            dataset_name = st.text_input("Nom du Dataset*", 
                                        placeholder="Nom affiché")
        with col2:
            created_by = st.text_input("Créé par*", value=st.session_state.username)
            original_filename = st.text_input("Nom du fichier original", 
                                            placeholder="ex: Ya_Tening_Gining.json")
        
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
                    
                    # Auto-fill fields
                    if not original_filename:
                        original_filename = uploaded_file.name
                    
                    if not dataset_id:
                        dataset_id = uploaded_file.name.replace('.json', '').replace(' ', '_')
                    
                    if not dataset_name:
                        dataset_name = uploaded_file.name.replace('.json', '')
                    
                    # Preview
                    with st.expander("📄 Aperçu du JSON"):
                        try:
                            data = json.loads(json_content)
                            if isinstance(data, list):
                                st.write(f"Format: Liste de {len(data)} paires")
                                if data and len(data) > 0:
                                    st.json(data[0])
                            elif isinstance(data, dict):
                                if 'pairs' in data:
                                    st.write(f"Format: Dictionnaire avec {len(data['pairs'])} paires")
                                    if data['pairs'] and len(data['pairs'] > 0):
                                        st.json(data['pairs'][0])
                                else:
                                    st.write("Format: Dictionnaire")
                                    st.json(data)
                        except:
                            st.code(json_content[:1000] + "..." if len(json_content) > 1000 else json_content)
                except Exception as e:
                    st.error(f"❌ Erreur de lecture: {e}")
        
        else:  # Paste JSON
            json_content = st.text_area("Collez votre JSON ici", height=300,
                                       placeholder='{"pairs": [...]} ou [...]')
            if json_content:
                try:
                    data = json.loads(json_content)
                    if isinstance(data, list):
                        st.success(f"✅ JSON valide: Liste de {len(data)} paires")
                    elif isinstance(data, dict) and 'pairs' in data:
                        st.success(f"✅ JSON valide: Dictionnaire avec {len(data['pairs'])} paires")
                    else:
                        st.warning("⚠️ Format JSON valide mais structure inattendue")
                except json.JSONDecodeError as e:
                    st.error(f"❌ JSON invalide: {e}")
        
        # Import button
        if st.button("🚀 Importer dans Google Sheets", type="primary", 
                    disabled=not (dataset_id and json_content)):
            with st.spinner("Importation en cours..."):
                success, total_pairs, imported_pairs = gsheets.import_json_dataset(
                    dataset_id, json_content, 
                    dataset_name or dataset_id, 
                    description, created_by, original_filename
                )
                
                if success:
                    st.success(f"✅ Dataset importé avec succès !")
                    st.info(f"📊 {imported_pairs} nouvelles paires importées (sur {total_pairs} total)")
                    if imported_pairs < total_pairs:
                        st.warning(f"⚠️ {total_pairs - imported_pairs} paires déjà existantes ignorées")
                    st.balloons()
                else:
                    st.error(f"❌ Erreur: {gsheets.error_message}")
    
    with tab2:
        st.markdown("### Datasets disponibles")
        
        datasets = gsheets.get_datasets()
        
        if not datasets:
            st.info("📭 Aucun dataset disponible")
            return
        
        # Statistics
        total_pairs = sum(d.pair_count for d in datasets)
        total_datasets = len(datasets)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Datasets", total_datasets)
        with col2:
            st.metric("Paires totales", total_pairs)
        with col3:
            st.metric("Dernier import", datasets[-1].created_at[:10] if datasets else "N/A")
        
        # Dataset cards
        for dataset in datasets:
            with st.container():
                st.markdown(f"""
                <div class="dataset-card">
                    <h4>📁 {dataset.name}</h4>
                    <p>{dataset.description}</p>
                    <div style="margin-top: 1rem;">
                        <span class="tag tag-primary">ID: {dataset.dataset_id}</span>
                        <span class="tag tag-success">{dataset.pair_count} paires</span>
                        <span class="tag tag-info">Créé par: {dataset.created_by}</span>
                        <span class="tag tag-warning">{dataset.created_at[:10]}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Buttons in expander
                with st.expander("Actions", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(f"📊 Charger pour annotation", key=f"load_{dataset.dataset_id}"):
                            st.session_state.current_dataset = dataset.dataset_id
                            st.session_state.pair_index = 0
                            st.rerun()
                    
                    with col2:
                        # Preview pairs
                        if st.button(f"👁️ Aperçu", key=f"preview_{dataset.dataset_id}"):
                            pairs = gsheets.get_dataset_pairs(dataset.dataset_id)
                            if pairs:
                                st.info(f"📋 {len(pairs)} paires chargées")
                                # Show first 3 pairs
                                for i, pair in enumerate(pairs[:3]):
                                    with st.expander(f"Paire {i+1}: {pair.event1_text[:50]}..."):
                                        col_a, col_b = st.columns(2)
                                        with col_a:
                                            st.write("**Événement 1:**")
                                            st.write(pair.event1_text)
                                            if pair.event1_has_causal_cue:
                                                st.info(f"Marqueur causal: {pair.event1_causal_cue_text or pair.event1_causal_cue_type}")
                                        with col_b:
                                            st.write("**Événement 2:**")
                                            st.write(pair.event2_text)
                                            if pair.event2_has_causal_cue:
                                                st.info(f"Marqueur causal: {pair.event2_causal_cue_text or pair.event2_causal_cue_type}")
                                        
                                        # Metadata
                                        st.caption(f"Narrative: {pair.narrative_id} | Catégories: {pair.event1_category}/{pair.event2_category}")
                                        
                                if len(pairs) > 3:
                                    st.caption(f"... et {len(pairs)-3} autres paires")
                    
                    with col3:
                        # Export button
                        if st.button(f"📥 Exporter", key=f"export_{dataset.dataset_id}"):
                            export_data = gsheets.export_annotated_dataset(dataset.dataset_id)
                            if export_data:
                                json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
                                st.download_button(
                                    "⬇️ Télécharger JSON complet",
                                    json_str,
                                    file_name=f"causafr_{dataset.dataset_id}_{datetime.now().strftime('%Y%m%d')}.json",
                                    mime="application/json",
                                    key=f"download_{dataset.dataset_id}"
                                )
                            else:
                                st.error(f"Erreur: {gsheets.error_message}")
    
    with tab3:
        st.markdown("### 🗑️ Gestion des Datasets (Admin)")
        
        datasets = gsheets.get_datasets()
        if not datasets:
            st.info("Aucun dataset à gérer")
            return
        
        dataset_options = {f"{d.name} ({d.dataset_id})": d.dataset_id for d in datasets}
        selected_display = st.selectbox("Sélectionner un dataset à gérer", list(dataset_options.keys()))
        selected_id = dataset_options[selected_display]
        
        selected_dataset = None
        for ds in datasets:
            if ds.dataset_id == selected_id:
                selected_dataset = ds
                break
        
        if selected_dataset:
            st.markdown(f"### Dataset: {selected_dataset.name}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Paires", selected_dataset.pair_count)
            with col2:
                st.metric("Créé le", selected_dataset.created_at[:10])
            with col3:
                st.metric("Fichier", selected_dataset.original_filename)
            
            # Get dataset statistics
            pairs = gsheets.get_dataset_pairs(selected_id)
            annotations = gsheets.get_all_annotations(selected_id)
            unique_annotators = len(set(a['username'] for a in annotations))
            
            st.markdown("#### 📊 Statistiques")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Annotations totales", len(annotations))
            with col2:
                st.metric("Annotateurs", unique_annotators)
            with col3:
                completion = (len(set(a['pair_id'] for a in annotations)) / selected_dataset.pair_count * 100) if selected_dataset.pair_count > 0 else 0
                st.metric("Taux d'annotation", f"{completion:.1f}%")
            
            # Danger zone
            st.markdown("#### ⚠️ Zone de danger")
            st.warning("Les actions suivantes sont irréversibles")
            
            if st.button("🗑️ Supprimer ce dataset", type="secondary"):
                if st.checkbox("Je confirme la suppression de ce dataset et toutes ses données"):
                    if gsheets.delete_dataset(selected_id):
                        st.success("✅ Dataset supprimé avec succès")
                        st.rerun()
                    else:
                        st.error(f"❌ Erreur: {gsheets.error_message}")

def annotate_page():
    """Main annotation page"""
    username = st.session_state.username
    gsheets = st.session_state.gsheets
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {username}")
        if st.session_state.is_admin:
            st.markdown("👑 **Administrateur**")
        
        # Dataset selection
        st.markdown("### 📁 Dataset")
        
        datasets = gsheets.get_datasets()
        if not datasets:
            st.error("Aucun dataset disponible")
            st.info("Contactez un administrateur pour importer des datasets")
            return
        
        dataset_options = {f"{d.name} ({d.pair_count} paires)": d.dataset_id for d in datasets}
        selected_display = st.selectbox("Choisir un dataset", list(dataset_options.keys()))
        selected_id = dataset_options[selected_display]
        
        # Get dataset name for display
        dataset_name = ""
        for ds in datasets:
            if ds.dataset_id == selected_id:
                dataset_name = ds.name
                break
        
        if st.session_state.current_dataset != selected_id:
            st.session_state.current_dataset = selected_id
            st.session_state.pair_index = 0
            st.session_state.current_pairs = []
        
        # Load dataset pairs
        if not st.session_state.current_pairs:
            with st.spinner("Chargement des paires..."):
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
        causal_count = sum(1 for ann in user_annotations if ann.label == 1)
        non_causal_count = sum(1 for ann in user_annotations if ann.label == 0)
        
        st.markdown("### 📊 Vos statistiques")
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
        if st.button("📍 Aller", use_container_width=True):
            st.session_state.pair_index = jump_to - 1
            st.rerun()
        
        # Quick navigation
        if st.button("⏭️ Prochaine non annotée", use_container_width=True):
            for i in range(st.session_state.pair_index + 1, total_pairs):
                pair_id = pairs[i].pair_id
                existing = [ann for ann in user_annotations if ann.pair_id == pair_id]
                if not existing:
                    st.session_state.pair_index = i
                    st.rerun()
                    break
        
        # Export button in sidebar
        st.markdown("---")
        if st.button("📥 Exporter ce dataset", use_container_width=True):
            export_data = gsheets.export_annotated_dataset(selected_id)
            if export_data:
                json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
                st.download_button(
                    "⬇️ Télécharger JSON annoté",
                    json_str,
                    file_name=f"causafr_{selected_id}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
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
        <div style="display: flex; gap: 1rem; align-items: center;">
            <span style="background: #e9ecef; padding: 0.5rem 1rem; border-radius: 20px;">
                📄 {dataset_name}
            </span>
            <span style="background: #d1fae5; padding: 0.5rem 1rem; border-radius: 20px;">
                ID: {current_pair.pair_id}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if already annotated
    existing_annotations = [ann for ann in user_annotations 
                          if ann.pair_id == current_pair.pair_id]
    
    if existing_annotations:
        existing = existing_annotations[0]
        st.markdown(f"""
        <div class="alert alert-warning">
            ✏️ <strong>Déjà annotée</strong> le {existing.annotated_at[:16]}
            (Confidence: {existing.confidence}/5 - { '✅ Causal' if existing.label == 1 else '❌ Non causal'})
        </div>
        """, unsafe_allow_html=True)
    
    # Additional information
    with st.expander("📊 Informations supplémentaires", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Identifiants:**")
            st.write(f"- Narrative: `{current_pair.narrative_id}`")
            st.write(f"- Event1: `{current_pair.event1_id}`")
            st.write(f"- Event2: `{current_pair.event2_id}`")
            
            st.write("**Catégories:**")
            st.write(f"- E1: `{current_pair.event1_category}`")
            st.write(f"- E2: `{current_pair.event2_category}`")
        
        with col2:
            st.write("**Marqueurs causaux:**")
            if current_pair.event1_has_causal_cue:
                st.info(f"✅ E1: {current_pair.event1_causal_cue_text or current_pair.event1_causal_cue_type}")
            if current_pair.event2_has_causal_cue:
                st.info(f"✅ E2: {current_pair.event2_causal_cue_text or current_pair.event2_causal_cue_type}")
            
            st.write("**Marqueurs temporels:**")
            if current_pair.event1_has_temporal:
                st.info(f"⏱️ E1: {current_pair.event1_temporal_text or current_pair.event1_temporal_type}")
            if current_pair.event2_has_temporal:
                st.info(f"⏱️ E2: {current_pair.event2_temporal_text or current_pair.event2_temporal_type}")
        
        with col3:
            st.write("**Métadonnées:**")
            if current_pair.is_hard_negative:
                st.warning("⚠️ Hard Negative")
            if current_pair.pair_has_causal_cue:
                st.info("🔗 Paire a un marqueur causal")
            if current_pair.pair_has_temporal:
                st.info("⏱️ Paire a un marqueur temporel")
            
            if current_pair.label is not None:
                st.write(f"**Label original:** {'✅ Causal' if current_pair.label == 1 else '❌ Non causal'}")
    
    # Events display
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔵 Événement 1 (Cause)")
        st.markdown(f'<div class="sentence-box">{current_pair.event1_text}</div>', unsafe_allow_html=True)
        cue1 = st.checkbox("Marqueur causal explicite", 
                          value=existing_annotations[0].cue1 if existing_annotations else False,
                          key="cue1")
    
    with col2:
        st.markdown("#### 🟢 Événement 2 (Effet)")
        st.markdown(f'<div class="sentence-box">{current_pair.event2_text}</div>', unsafe_allow_html=True)
        cue2 = st.checkbox("Marqueur causal explicite",
                          value=existing_annotations[0].cue2 if existing_annotations else False,
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
        current_label = existing_annotations[0].label if existing_annotations else None
        label = st.radio(
            "Décision",
            [1, 0],
            index=0 if current_label == 1 else 1,
            format_func=lambda x: "✅ OUI - Relation causale" if x == 1 else "❌ NON - Pas de relation",
            key="label"
        )
    
    with col2:
        current_conf = existing_annotations[0].confidence if existing_annotations else 3
        confidence = st.slider("Confiance", 1, 5, current_conf, key="confidence")
        notes = st.text_input("Notes", 
                             value=existing_annotations[0].notes if existing_annotations else '',
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
            annotation = UserAnnotation(
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
            annotation = UserAnnotation(
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

def dashboard_page():
    """Dashboard page"""
    username = st.session_state.username
    gsheets = st.session_state.gsheets
    
    st.markdown(f"""
    <div class="main-header">
        <h1>📊 Tableau de bord</h1>
        <p>Statistiques et visualisation globale</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get all data
    datasets = gsheets.get_datasets()
    all_annotations = gsheets.get_all_annotations()
    
    # Global statistics
    st.markdown("### 📈 Statistiques globales")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_pairs = sum(d.pair_count for d in datasets)
        st.metric("Paires totales", total_pairs)
    with col2:
        st.metric("Datasets", len(datasets))
    with col3:
        st.metric("Annotations totales", len(all_annotations))
    with col4:
        unique_users = len(set(a['username'] for a in all_annotations))
        st.metric("Annotateurs uniques", unique_users)
    
    # User statistics
    st.markdown(f"### 👤 Vos statistiques")
    user_annotations = gsheets.get_user_annotations(username)
    
    if user_annotations:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Vos annotations", len(user_annotations))
        with col2:
            user_datasets = len(set(a.dataset for a in user_annotations))
            st.metric("Datasets annotés", user_datasets)
        with col3:
            causal = sum(1 for a in user_annotations if a.label == 1)
            st.metric("Vos relations causales", causal)
        with col4:
            avg_conf = sum(a.confidence for a in user_annotations) / len(user_annotations) if user_annotations else 0
            st.metric("Confiance moyenne", f"{avg_conf:.1f}/5")
    
    # Dataset statistics
    st.markdown("### 📋 Statistiques par dataset")
    
    for dataset in datasets:
        dataset_anns = [a for a in all_annotations if a['dataset'] == dataset.dataset_id]
        user_ds_anns = [a for a in user_annotations if a.dataset == dataset.dataset_id]
        
        with st.expander(f"📁 {dataset.name} ({dataset.dataset_id})"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                completion = (len(set(a['pair_id'] for a in dataset_anns)) / dataset.pair_count * 100) if dataset.pair_count > 0 else 0
                st.metric("Taux d'annotation", f"{completion:.1f}%")
            
            with col2:
                st.metric("Annotations totales", len(dataset_anns))
            
            with col3:
                unique_annotators = len(set(a['username'] for a in dataset_anns))
                st.metric("Annotateurs", unique_annotators)
            
            with col4:
                if user_ds_anns:
                    user_completion = (len(user_ds_anns) / dataset.pair_count * 100) if dataset.pair_count > 0 else 0
                    st.metric("Votre progression", f"{user_completion:.1f}%")
                else:
                    st.metric("Votre progression", "0%")
            
            # Export button
            if st.button(f"📥 Exporter {dataset.name}", key=f"export_dash_{dataset.dataset_id}"):
                export_data = gsheets.export_annotated_dataset(dataset.dataset_id)
                if export_data:
                    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
                    st.download_button(
                        "⬇️ Télécharger",
                        json_str,
                        file_name=f"causafr_{dataset.dataset_id}_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json",
                        key=f"download_dash_{dataset.dataset_id}"
                    )

def about_page():
    """About page"""
    gsheets = st.session_state.gsheets
    
    st.markdown(f"""
    <div class="main-header">
        <h1>ℹ️ À propos de CausaFr</h1>
        <p>Outil d'annotation multi-datasets avec Google Sheets</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <h3>🎯 Objectif</h3>
        <p>CausaFr est un outil collaboratif pour l'annotation de relations causales entre événements dans des textes en français. 
        Supporte <strong>plusieurs datasets JSON simultanément</strong> avec préservation de tous les champs originaux.</p>
        
        <h3>🔗 État de la connexion</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if gsheets.connected:
        st.success("✅ Connecté à Google Sheets")
        
        # Statistics
        datasets = gsheets.get_datasets()
        all_annotations = gsheets.get_all_annotations()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Datasets", len(datasets))
        with col2:
            total_pairs = sum(d.pair_count for d in datasets)
            st.metric("Paires totales", total_pairs)
        with col3:
            st.metric("Annotations", len(all_annotations))
        with col4:
            users = gsheets.get_all_users()
            st.metric("Utilisateurs", len(users))
    else:
        st.error(f"❌ Non connecté: {gsheets.error_message}")

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
        
        # Create navigation options based on user role
        if st.session_state.is_admin:
            pages = ["📤 Gérer Datasets", "✏️ Annoter", "📊 Tableau de bord", "ℹ️ À propos"]
        else:
            pages = ["✏️ Annoter", "📊 Tableau de bord", "ℹ️ À propos"]
        
        page = st.radio("Navigation", pages, label_visibility="collapsed")
    
    # Show selected page with admin check
    if page == "📤 Gérer Datasets":
        if not st.session_state.is_admin:
            st.error("⛔ Accès refusé - Cette section est réservée aux administrateurs")
            st.info("Veuillez contacter un administrateur si vous avez besoin d'accéder à cette fonctionnalité.")
        else:
            dataset_management_page()
    elif page == "✏️ Annoter":
        annotate_page()
    elif page == "📊 Tableau de bord":
        dashboard_page()
    elif page == "ℹ️ À propos":
        about_page()

if __name__ == "__main__":
    main()





