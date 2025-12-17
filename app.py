
# """
# CausaFr - Complete Google Sheets Annotation Tool
# Streamlit Cloud Deployment Version
# """

# import streamlit as st
# import pandas as pd
# import json
# import os
# import hashlib
# import uuid
# import re
# from datetime import datetime
# from typing import Dict, List, Optional, Any, Tuple
# from dataclasses import dataclass, asdict
# from io import StringIO

# # =============================================================================
# # GOOGLE SHEETS CONFIGURATION - Streamlit Secrets
# # =============================================================================

# # Load config from Streamlit secrets
# try:
#     if 'GOOGLE_SHEETS' in st.secrets:
#         GOOGLE_CONFIG = {
#             'spreadsheet_id': st.secrets['GOOGLE_SHEETS']['spreadsheet_id'],
#             'gcp_credentials': {
#                 'type': st.secrets['GOOGLE_SHEETS']['type'],
#                 'project_id': st.secrets['GOOGLE_SHEETS']['project_id'],
#                 'private_key_id': st.secrets['GOOGLE_SHEETS']['private_key_id'],
#                 'private_key': st.secrets['GOOGLE_SHEETS']['private_key'].replace('\\n', '\n'),
#                 'client_email': st.secrets['GOOGLE_SHEETS']['client_email'],
#                 'client_id': st.secrets['GOOGLE_SHEETS']['client_id'],
#                 'auth_uri': st.secrets['GOOGLE_SHEETS']['auth_uri'],
#                 'token_uri': st.secrets['GOOGLE_SHEETS']['token_uri'],
#                 'auth_provider_x509_cert_url': st.secrets['GOOGLE_SHEETS']['auth_provider_x509_cert_url'],
#                 'client_x509_cert_url': st.secrets['GOOGLE_SHEETS']['client_x509_cert_url']
#             }
#         }
#     else:
#         st.error("Google Sheets configuration not found in secrets")
#         GOOGLE_CONFIG = None
# except Exception as e:
#     st.error(f"Error loading configuration: {e}")
#     GOOGLE_CONFIG = None

# # =============================================================================
# # DATA MODELS
# # =============================================================================

# @dataclass
# class OriginalPair:
#     """Original pair data from JSON files"""
#     pair_id: str
#     dataset: str
#     event1_text: str
#     event2_text: str
#     event1_id: str
#     event2_id: str
#     narrative_id: str = ""
#     event1_category: str = ""
#     event2_category: str = ""
#     label: Optional[int] = None
#     is_hard_negative: bool = False
#     event1_has_causal_cue: bool = False
#     event1_causal_cue_type: Optional[str] = None
#     event1_causal_cue_text: Optional[str] = None
#     event1_has_temporal: bool = False
#     event1_temporal_type: Optional[str] = None
#     event1_temporal_text: Optional[str] = None
#     event2_has_causal_cue: bool = False
#     event2_causal_cue_type: Optional[str] = None
#     event2_causal_cue_text: Optional[str] = None
#     event2_has_temporal: bool = False
#     event2_temporal_type: Optional[str] = None
#     event2_temporal_text: Optional[str] = None
#     pair_has_causal_cue: bool = False
#     pair_has_temporal: bool = False
#     row_index: int = 0
    
#     def to_dict(self) -> Dict:
#         """Convert to dictionary matching original JSON structure"""
#         return {
#             "narrative_id": self.narrative_id,
#             "event1_id": self.event1_id,
#             "event2_id": self.event2_id,
#             "event1_text": self.event1_text,
#             "event2_text": self.event2_text,
#             "event1_category": self.event1_category,
#             "event2_category": self.event2_category,
#             "label": self.label,
#             "is_hard_negative": self.is_hard_negative,
#             "event1_has_causal_cue": self.event1_has_causal_cue,
#             "event1_causal_cue_type": self.event1_causal_cue_type,
#             "event1_causal_cue_text": self.event1_causal_cue_text,
#             "event1_has_temporal": self.event1_has_temporal,
#             "event1_temporal_type": self.event1_temporal_type,
#             "event1_temporal_text": self.event1_temporal_text,
#             "event2_has_causal_cue": self.event2_has_causal_cue,
#             "event2_causal_cue_type": self.event2_causal_cue_type,
#             "event2_causal_cue_text": self.event2_causal_cue_text,
#             "event2_has_temporal": self.event2_has_temporal,
#             "event2_temporal_type": self.event2_temporal_type,
#             "event2_temporal_text": self.event2_temporal_text,
#             "pair_has_causal_cue": self.pair_has_causal_cue,
#             "pair_has_temporal": self.pair_has_temporal
#         }

# @dataclass
# class UserAnnotation:
#     """User annotation data"""
#     id: str
#     pair_id: str
#     dataset: str
#     username: str
#     event1_text: str
#     event2_text: str
#     cue1: int = 0
#     cue2: int = 0
#     label: Optional[int] = None
#     confidence: int = 3
#     notes: str = ""
#     annotated_at: str = ""
#     event1_id: str = ""
#     event2_id: str = ""
    
#     def to_dict(self) -> Dict:
#         """Convert to dictionary"""
#         return asdict(self)

# @dataclass
# class DatasetMetadata:
#     """Dataset metadata"""
#     dataset_id: str
#     name: str
#     description: str
#     created_by: str
#     created_at: str
#     pair_count: int
#     original_filename: str = ""

# # =============================================================================
# # GOOGLE SHEETS MANAGER
# # =============================================================================

# try:
#     import gspread
#     from google.oauth2.service_account import Credentials
#     GSHEETS_AVAILABLE = True
# except ImportError:
#     GSHEETS_AVAILABLE = False
#     st.error("⚠️ Install dependencies: pip install gspread google-auth")

# class GoogleSheetsManager:
#     """Complete Google Sheets management for multiple datasets"""
    
#     def __init__(self):
#         self.client = None
#         self.spreadsheet = None
#         self.connected = False
#         self.error_message = ""
        
#         # Sheet references
#         self.users_sheet = None
#         self.datasets_sheet = None
#         self.dataset_pairs_sheet = None
#         self.annotations_sheet = None
#         self.progress_sheet = None
        
#     def connect(self) -> bool:
#         """Connect to Google Sheets"""
#         if GOOGLE_CONFIG is None:
#             self.error_message = "Google Sheets configuration not found"
#             return False
            
#         try:
#             creds = GOOGLE_CONFIG['gcp_credentials'].copy()
#             private_key = creds['private_key']
            
#             # Ensure proper newlines
#             private_key = private_key.replace('\\n', '\n')
#             if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
#                 private_key = '-----BEGIN PRIVATE KEY-----\n' + private_key
#             if not private_key.endswith('-----END PRIVATE KEY-----'):
#                 private_key = private_key + '\n-----END PRIVATE KEY-----'
            
#             creds['private_key'] = private_key
            
#             # Create credentials
#             credentials = Credentials.from_service_account_info(
#                 creds,
#                 scopes=[
#                     'https://www.googleapis.com/auth/spreadsheets',
#                     'https://www.googleapis.com/auth/drive.file'
#                 ]
#             )
            
#             # Authorize
#             self.client = gspread.authorize(credentials)
            
#             # Open spreadsheet
#             spreadsheet_id = GOOGLE_CONFIG['spreadsheet_id']
#             self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            
#             # Setup all sheets
#             self._setup_sheets()
            
#             self.connected = True
#             return True
            
#         except Exception as e:
#             self.error_message = f"Connection error: {str(e)}"
#             return False
    
#     def _setup_sheets(self):
#         """Create or get all necessary worksheets"""
#         sheet_titles = [ws.title for ws in self.spreadsheet.worksheets()]
        
#         # 1. USERS sheet
#         if 'users' not in sheet_titles:
#             self.users_sheet = self.spreadsheet.add_worksheet('users', 100, 6)
#             self.users_sheet.update('A1:F1', [
#                 ['username', 'password_hash', 'email', 'created_at', 'last_login', 'is_admin']
#             ])
#         else:
#             self.users_sheet = self.spreadsheet.worksheet('users')
        
#         # 2. DATASETS sheet (dataset metadata)
#         if 'datasets' not in sheet_titles:
#             self.datasets_sheet = self.spreadsheet.add_worksheet('datasets', 100, 7)
#             self.datasets_sheet.update('A1:G1', [
#                 ['dataset_id', 'name', 'description', 'created_by', 'created_at', 'pair_count', 'original_filename']
#             ])
#         else:
#             self.datasets_sheet = self.spreadsheet.worksheet('datasets')
        
#         # 3. DATASET_PAIRS sheet (actual pairs data with ALL fields)
#         if 'dataset_pairs' not in sheet_titles:
#             self.dataset_pairs_sheet = self.spreadsheet.add_worksheet('dataset_pairs', 10000, 28)
#             headers = [
#                 'pair_id', 'dataset', 'event1_text', 'event2_text', 
#                 'event1_id', 'event2_id', 'narrative_id', 'event1_category',
#                 'event2_category', 'original_label', 'is_hard_negative',
#                 'event1_has_causal_cue', 'event1_causal_cue_type', 'event1_causal_cue_text',
#                 'event1_has_temporal', 'event1_temporal_type', 'event1_temporal_text',
#                 'event2_has_causal_cue', 'event2_causal_cue_type', 'event2_causal_cue_text',
#                 'event2_has_temporal', 'event2_temporal_type', 'event2_temporal_text',
#                 'pair_has_causal_cue', 'pair_has_temporal', 'row_index',
#                 'imported_at', 'pair_hash'
#             ]
#             self.dataset_pairs_sheet.update('A1:AB1', [headers])
#         else:
#             self.dataset_pairs_sheet = self.spreadsheet.worksheet('dataset_pairs')
        
#         # 4. ANNOTATIONS sheet
#         if 'annotations' not in sheet_titles:
#             self.annotations_sheet = self.spreadsheet.add_worksheet('annotations', 10000, 16)
#             headers = [
#                 'id', 'pair_id', 'dataset', 'username', 'event1_text', 'event2_text',
#                 'cue1', 'cue2', 'label', 'confidence', 'notes', 'annotated_at',
#                 'event1_id', 'event2_id', 'exported', 'annotation_hash'
#             ]
#             self.annotations_sheet.update('A1:P1', [headers])
#         else:
#             self.annotations_sheet = self.spreadsheet.worksheet('annotations')
        
#         # 5. PROGRESS sheet
#         if 'progress' not in sheet_titles:
#             self.progress_sheet = self.spreadsheet.add_worksheet('progress', 100, 7)
#             self.progress_sheet.update('A1:G1', [
#                 ['username', 'dataset', 'current_index', 'total_annotated', 
#                  'last_updated', 'last_pair_id', 'completion_rate']
#             ])
#         else:
#             self.progress_sheet = self.spreadsheet.worksheet('progress')
    
#     # ========== USER MANAGEMENT ==========
    
#     def create_user(self, username: str, password: str, email: str = "", is_admin: bool = False) -> bool:
#         """Create a new user"""
#         try:
#             users = self.users_sheet.get_all_records()
#             for user in users:
#                 if user['username'] == username:
#                     return False
            
#             self.users_sheet.append_row([
#                 username,
#                 hashlib.sha256(password.encode()).hexdigest(),
#                 email,
#                 datetime.now().isoformat(),
#                 datetime.now().isoformat(),
#                 1 if is_admin else 0
#             ])
#             return True
#         except Exception as e:
#             self.error_message = str(e)
#             return False
    
#     def verify_user(self, username: str, password: str) -> bool:
#         """Verify user credentials"""
#         try:
#             users = self.users_sheet.get_all_records()
#             for user in users:
#                 if user['username'] == username:
#                     return user['password_hash'] == hashlib.sha256(password.encode()).hexdigest()
#             return False
#         except Exception as e:
#             self.error_message = str(e)
#             return False
    
#     def is_admin(self, username: str) -> bool:
#         """Check if user is admin"""
#         try:
#             users = self.users_sheet.get_all_records()
#             for user in users:
#                 if user['username'] == username:
#                     return bool(int(user.get('is_admin', 0)))
#             return False
#         except:
#             return False
    
#     # ========== DATASET MANAGEMENT ==========
    
#     def _generate_pair_hash(self, pair_data: Dict) -> str:
#         """Generate hash for pair data to detect duplicates"""
#         hash_string = f"{pair_data.get('event1_text', '')}_{pair_data.get('event2_text', '')}"
#         return hashlib.md5(hash_string.encode()).hexdigest()[:8]
    
#     def import_json_dataset(self, dataset_id: str, json_content: str, 
#                            name: str = "", description: str = "", 
#                            created_by: str = "", original_filename: str = "") -> Tuple[bool, int, int]:
#         """
#         Import a JSON dataset into Google Sheets
#         Returns: (success, total_pairs, imported_pairs)
#         """
#         try:
#             data = json.loads(json_content)
            
#             # Determine pairs based on JSON structure
#             if isinstance(data, list):
#                 pairs = data
#             elif isinstance(data, dict) and 'pairs' in data:
#                 pairs = data['pairs']
#             else:
#                 self.error_message = "Invalid JSON format: Expected list or dict with 'pairs' key"
#                 return False, 0, 0
            
#             # Check if dataset already exists
#             datasets = self.datasets_sheet.get_all_records()
#             existing_dataset = None
#             for dataset in datasets:
#                 if dataset['dataset_id'] == dataset_id:
#                     existing_dataset = dataset
#                     break
            
#             # If dataset exists, check for duplicates
#             existing_pairs = []
#             if existing_dataset:
#                 # Get existing pairs for this dataset
#                 all_pairs = self.dataset_pairs_sheet.get_all_records()
#                 existing_pairs = [p for p in all_pairs if p['dataset'] == dataset_id]
                
#                 # Generate hashes for existing pairs
#                 existing_hashes = {p.get('pair_hash', '') for p in existing_pairs}
#             else:
#                 existing_hashes = set()
            
#             # Use dataset_id as name if not provided
#             if not name:
#                 name = dataset_id
            
#             imported_count = 0
#             skipped_count = 0
            
#             # Import pairs
#             for i, pair in enumerate(pairs):
#                 # Generate pair hash for duplicate detection
#                 pair_hash = self._generate_pair_hash(pair)
                
#                 # Skip if already exists
#                 if pair_hash in existing_hashes:
#                     skipped_count += 1
#                     continue
                
#                 # Prepare pair data
#                 pair_id = pair.get('pair_id', f"{dataset_id}_{len(existing_pairs) + imported_count}")
                
#                 # Convert boolean values to 1/0 for Google Sheets
#                 def bool_to_int(value):
#                     return 1 if value else 0
                
#                 self.dataset_pairs_sheet.append_row([
#                     pair_id,
#                     dataset_id,
#                     pair.get('event1_text', ''),
#                     pair.get('event2_text', ''),
#                     str(pair.get('event1_id', '')),
#                     str(pair.get('event2_id', '')),
#                     pair.get('narrative_id', ''),
#                     pair.get('event1_category', ''),
#                     pair.get('event2_category', ''),
#                     pair.get('label', ''),
#                     bool_to_int(pair.get('is_hard_negative', False)),
#                     bool_to_int(pair.get('event1_has_causal_cue', False)),
#                     pair.get('event1_causal_cue_type', ''),
#                     pair.get('event1_causal_cue_text', ''),
#                     bool_to_int(pair.get('event1_has_temporal', False)),
#                     pair.get('event1_temporal_type', ''),
#                     pair.get('event1_temporal_text', ''),
#                     bool_to_int(pair.get('event2_has_causal_cue', False)),
#                     pair.get('event2_causal_cue_type', ''),
#                     pair.get('event2_causal_cue_text', ''),
#                     bool_to_int(pair.get('event2_has_temporal', False)),
#                     pair.get('event2_temporal_type', ''),
#                     pair.get('event2_temporal_text', ''),
#                     bool_to_int(pair.get('pair_has_causal_cue', False)),
#                     bool_to_int(pair.get('pair_has_temporal', False)),
#                     len(existing_pairs) + imported_count,  # row_index
#                     datetime.now().isoformat(),
#                     pair_hash
#                 ])
                
#                 imported_count += 1
            
#             # Update or create dataset metadata
#             total_pairs = len(existing_pairs) + imported_count
            
#             if existing_dataset:
#                 # Update existing dataset
#                 row_num = datasets.index(existing_dataset) + 2
#                 self.datasets_sheet.update(f'A{row_num}:G{row_num}', [[
#                     dataset_id,
#                     name,
#                     description,
#                     created_by,
#                     existing_dataset.get('created_at', datetime.now().isoformat()),
#                     total_pairs,
#                     original_filename
#                 ]])
#             else:
#                 # Create new dataset
#                 self.datasets_sheet.append_row([
#                     dataset_id,
#                     name,
#                     description,
#                     created_by,
#                     datetime.now().isoformat(),
#                     total_pairs,
#                     original_filename
#                 ])
            
#             return True, len(pairs), imported_count
            
#         except json.JSONDecodeError as e:
#             self.error_message = f"Invalid JSON: {str(e)}"
#             return False, 0, 0
#         except Exception as e:
#             self.error_message = str(e)
#             return False, 0, 0
    
#     def get_datasets(self) -> List[DatasetMetadata]:
#         """Get all available datasets"""
#         try:
#             records = self.datasets_sheet.get_all_records()
#             datasets = []
#             for r in records:
#                 datasets.append(DatasetMetadata(
#                     dataset_id=r['dataset_id'],
#                     name=r['name'],
#                     description=r['description'],
#                     created_by=r['created_by'],
#                     created_at=r['created_at'],
#                     pair_count=int(r['pair_count']) if r['pair_count'] else 0,
#                     original_filename=r.get('original_filename', '')
#                 ))
#             return datasets
#         except Exception as e:
#             self.error_message = str(e)
#             return []
    
#     def get_dataset_pairs(self, dataset_id: str) -> List[OriginalPair]:
#         """Get all pairs for a dataset"""
#         try:
#             records = self.dataset_pairs_sheet.get_all_records()
#             pairs = []
            
#             for record in records:
#                 if record['dataset'] == dataset_id:
#                     # Helper function to convert string to bool
#                     def str_to_bool(value):
#                         if isinstance(value, str):
#                             return value.strip().lower() in ['true', '1', 'yes', 'y']
#                         return bool(value)
                    
#                     # Helper function to convert to int if possible
#                     def to_int(value):
#                         try:
#                             return int(value)
#                         except:
#                             return None
                    
#                     pairs.append(OriginalPair(
#                         pair_id=record['pair_id'],
#                         dataset=record['dataset'],
#                         event1_text=record['event1_text'],
#                         event2_text=record['event2_text'],
#                         event1_id=record['event1_id'],
#                         event2_id=record['event2_id'],
#                         narrative_id=record.get('narrative_id', ''),
#                         event1_category=record.get('event1_category', ''),
#                         event2_category=record.get('event2_category', ''),
#                         label=to_int(record.get('original_label')),
#                         is_hard_negative=str_to_bool(record.get('is_hard_negative', False)),
#                         event1_has_causal_cue=str_to_bool(record.get('event1_has_causal_cue', False)),
#                         event1_causal_cue_type=record.get('event1_causal_cue_type'),
#                         event1_causal_cue_text=record.get('event1_causal_cue_text'),
#                         event1_has_temporal=str_to_bool(record.get('event1_has_temporal', False)),
#                         event1_temporal_type=record.get('event1_temporal_type'),
#                         event1_temporal_text=record.get('event1_temporal_text'),
#                         event2_has_causal_cue=str_to_bool(record.get('event2_has_causal_cue', False)),
#                         event2_causal_cue_type=record.get('event2_causal_cue_type'),
#                         event2_causal_cue_text=record.get('event2_causal_cue_text'),
#                         event2_has_temporal=str_to_bool(record.get('event2_has_temporal', False)),
#                         event2_temporal_type=record.get('event2_temporal_type'),
#                         event2_temporal_text=record.get('event2_temporal_text'),
#                         pair_has_causal_cue=str_to_bool(record.get('pair_has_causal_cue', False)),
#                         pair_has_temporal=str_to_bool(record.get('pair_has_temporal', False)),
#                         row_index=int(record.get('row_index', 0)) if record.get('row_index') else 0
#                     ))
            
#             # Sort by row_index
#             pairs.sort(key=lambda x: x.row_index)
#             return pairs
#         except Exception as e:
#             self.error_message = str(e)
#             return []
    
#     def delete_dataset(self, dataset_id: str) -> bool:
#         """Delete a dataset and all its data"""
#         try:
#             # 1. Delete dataset metadata
#             datasets = self.datasets_sheet.get_all_records()
#             dataset_rows_to_delete = []
#             for i, dataset in enumerate(datasets, start=2):
#                 if dataset['dataset_id'] == dataset_id:
#                     dataset_rows_to_delete.append(i)
            
#             # Delete from bottom to top to preserve row numbers
#             for row in sorted(dataset_rows_to_delete, reverse=True):
#                 self.datasets_sheet.delete_rows(row)
            
#             # 2. Delete dataset pairs
#             pairs = self.dataset_pairs_sheet.get_all_records()
#             pair_rows_to_delete = []
#             for i, pair in enumerate(pairs, start=2):
#                 if pair['dataset'] == dataset_id:
#                     pair_rows_to_delete.append(i)
            
#             for row in sorted(pair_rows_to_delete, reverse=True):
#                 self.dataset_pairs_sheet.delete_rows(row)
            
#             # 3. Delete annotations for this dataset
#             annotations = self.annotations_sheet.get_all_records()
#             annotation_rows_to_delete = []
#             for i, ann in enumerate(annotations, start=2):
#                 if ann['dataset'] == dataset_id:
#                     annotation_rows_to_delete.append(i)
            
#             for row in sorted(annotation_rows_to_delete, reverse=True):
#                 self.annotations_sheet.delete_rows(row)
            
#             # 4. Delete progress records for this dataset
#             progress = self.progress_sheet.get_all_records()
#             progress_rows_to_delete = []
#             for i, prog in enumerate(progress, start=2):
#                 if prog['dataset'] == dataset_id:
#                     progress_rows_to_delete.append(i)
            
#             for row in sorted(progress_rows_to_delete, reverse=True):
#                 self.progress_sheet.delete_rows(row)
            
#             return True
#         except Exception as e:
#             self.error_message = str(e)
#             return False
    
#     # ========== ANNOTATION MANAGEMENT ==========
    
#     def save_annotation(self, annotation: UserAnnotation) -> str:
#         """Save an annotation"""
#         try:
#             ann_id = str(uuid.uuid4())[:8]
            
#             # Generate hash for duplicate detection
#             hash_string = f"{annotation.pair_id}_{annotation.username}_{annotation.annotated_at}"
#             annotation_hash = hashlib.md5(hash_string.encode()).hexdigest()[:8]
            
#             # Check if annotation already exists for this user and pair
#             existing_annotations = self.annotations_sheet.get_all_records()
#             for existing in existing_annotations:
#                 if (existing['pair_id'] == annotation.pair_id and 
#                     existing['username'] == annotation.username):
#                     # Update existing annotation
#                     row_num = existing_annotations.index(existing) + 2
#                     self.annotations_sheet.update(f'A{row_num}:P{row_num}', [[
#                         ann_id,
#                         annotation.pair_id,
#                         annotation.dataset,
#                         annotation.username,
#                         annotation.event1_text[:500],
#                         annotation.event2_text[:500],
#                         annotation.cue1,
#                         annotation.cue2,
#                         annotation.label if annotation.label is not None else "",
#                         annotation.confidence,
#                         annotation.notes[:200],
#                         annotation.annotated_at or datetime.now().isoformat(),
#                         annotation.event1_id,
#                         annotation.event2_id,
#                         "0",  # not exported
#                         annotation_hash
#                     ]])
#                     return ann_id
            
#             # Create new annotation
#             self.annotations_sheet.append_row([
#                 ann_id,
#                 annotation.pair_id,
#                 annotation.dataset,
#                 annotation.username,
#                 annotation.event1_text[:500],
#                 annotation.event2_text[:500],
#                 annotation.cue1,
#                 annotation.cue2,
#                 annotation.label if annotation.label is not None else "",
#                 annotation.confidence,
#                 annotation.notes[:200],
#                 annotation.annotated_at or datetime.now().isoformat(),
#                 annotation.event1_id,
#                 annotation.event2_id,
#                 "0",  # not exported
#                 annotation_hash
#             ])
            
#             return ann_id
#         except Exception as e:
#             self.error_message = str(e)
#             return ""
    
#     def get_user_annotations(self, username: str, dataset_id: str = None) -> List[UserAnnotation]:
#         """Get annotations for a user"""
#         try:
#             records = self.annotations_sheet.get_all_records()
#             annotations = []
            
#             for record in records:
#                 if record['username'] == username:
#                     if dataset_id and record['dataset'] != dataset_id:
#                         continue
                    
#                     annotations.append(UserAnnotation(
#                         id=record['id'],
#                         pair_id=record['pair_id'],
#                         dataset=record['dataset'],
#                         username=record['username'],
#                         event1_text=record['event1_text'],
#                         event2_text=record['event2_text'],
#                         cue1=int(record['cue1']) if record['cue1'] else 0,
#                         cue2=int(record['cue2']) if record['cue2'] else 0,
#                         label=int(record['label']) if record['label'] else None,
#                         confidence=int(record['confidence']) if record['confidence'] else 3,
#                         notes=record['notes'],
#                         annotated_at=record['annotated_at'],
#                         event1_id=record['event1_id'],
#                         event2_id=record['event2_id']
#                     ))
            
#             return annotations
#         except Exception as e:
#             self.error_message = str(e)
#             return []
    
#     def get_all_annotations(self, dataset_id: str = None) -> List[Dict]:
#         """Get all annotations"""
#         try:
#             records = self.annotations_sheet.get_all_records()
#             if dataset_id:
#                 return [r for r in records if r['dataset'] == dataset_id]
#             return records
#         except Exception as e:
#             self.error_message = str(e)
#             return []
    
#     def get_annotations_by_pair(self, pair_id: str) -> List[UserAnnotation]:
#         """Get all annotations for a specific pair"""
#         try:
#             records = self.annotations_sheet.get_all_records()
#             annotations = []
            
#             for record in records:
#                 if record['pair_id'] == pair_id:
#                     annotations.append(UserAnnotation(
#                         id=record['id'],
#                         pair_id=record['pair_id'],
#                         dataset=record['dataset'],
#                         username=record['username'],
#                         event1_text=record['event1_text'],
#                         event2_text=record['event2_text'],
#                         cue1=int(record['cue1']) if record['cue1'] else 0,
#                         cue2=int(record['cue2']) if record['cue2'] else 0,
#                         label=int(record['label']) if record['label'] else None,
#                         confidence=int(record['confidence']) if record['confidence'] else 3,
#                         notes=record['notes'],
#                         annotated_at=record['annotated_at'],
#                         event1_id=record['event1_id'],
#                         event2_id=record['event2_id']
#                     ))
            
#             return annotations
#         except Exception as e:
#             self.error_message = str(e)
#             return []
    
#     # ========== PROGRESS MANAGEMENT ==========
    
#     def update_progress(self, username: str, dataset_id: str, current_index: int, 
#                        total_annotated: int, last_pair_id: str = "") -> bool:
#         """Update user progress"""
#         try:
#             records = self.progress_sheet.get_all_records()
#             row_num = None
            
#             for i, record in enumerate(records, start=2):
#                 if record['username'] == username and record['dataset'] == dataset_id:
#                     row_num = i
#                     break
            
#             # Get total pairs in dataset
#             dataset_pairs = self.get_dataset_pairs(dataset_id)
#             total_pairs = len(dataset_pairs)
#             completion_rate = (total_annotated / total_pairs * 100) if total_pairs > 0 else 0
            
#             if row_num:
#                 self.progress_sheet.update(f'A{row_num}:G{row_num}', [[
#                     username, dataset_id, current_index, total_annotated,
#                     datetime.now().isoformat(), last_pair_id,
#                     f"{completion_rate:.1f}%"
#                 ]])
#             else:
#                 self.progress_sheet.append_row([
#                     username, dataset_id, current_index, total_annotated,
#                     datetime.now().isoformat(), last_pair_id,
#                     f"{completion_rate:.1f}%"
#                 ])
            
#             return True
#         except Exception as e:
#             self.error_message = str(e)
#             return False
    
#     def get_user_progress(self, username: str, dataset_id: str) -> Dict:
#         """Get user progress"""
#         try:
#             records = self.progress_sheet.get_all_records()
            
#             for record in records:
#                 if record['username'] == username and record['dataset'] == dataset_id:
#                     return {
#                         'current_index': int(record['current_index']) if record['current_index'] else 0,
#                         'total_annotated': int(record['total_annotated']) if record['total_annotated'] else 0,
#                         'last_updated': record['last_updated'],
#                         'last_pair_id': record.get('last_pair_id', ''),
#                         'completion_rate': record.get('completion_rate', '0%')
#                     }
            
#             return {
#                 'current_index': 0,
#                 'total_annotated': 0,
#                 'last_updated': '',
#                 'last_pair_id': '',
#                 'completion_rate': '0%'
#             }
#         except Exception as e:
#             self.error_message = str(e)
#             return {'current_index': 0, 'total_annotated': 0, 'last_updated': ''}
    
#     # ========== EXPORT FUNCTIONALITY ==========
    
#     def export_annotated_dataset(self, dataset_id: str, include_original: bool = True) -> Optional[Dict]:
#         """
#         Export annotated dataset with all original fields plus annotations
#         Returns JSON structure matching original format
#         """
#         try:
#             # Get dataset metadata
#             datasets = self.get_datasets()
#             dataset_meta = None
#             for ds in datasets:
#                 if ds.dataset_id == dataset_id:
#                     dataset_meta = ds
#                     break
            
#             if not dataset_meta:
#                 self.error_message = f"Dataset {dataset_id} not found"
#                 return None
            
#             # Get original pairs
#             original_pairs = self.get_dataset_pairs(dataset_id)
#             if not original_pairs:
#                 self.error_message = f"No pairs found for dataset {dataset_id}"
#                 return None
            
#             # Get all annotations for this dataset
#             all_annotations = self.get_all_annotations(dataset_id)
            
#             # Create annotation lookup by pair_id
#             annotations_by_pair = {}
#             for ann in all_annotations:
#                 pair_id = ann['pair_id']
#                 if pair_id not in annotations_by_pair:
#                     annotations_by_pair[pair_id] = []
#                 annotations_by_pair[pair_id].append(ann)
            
#             # Build exported pairs
#             exported_pairs = []
#             for pair in original_pairs:
#                 pair_dict = pair.to_dict()
                
#                 # Add annotations if available
#                 if pair.pair_id in annotations_by_pair:
#                     pair_annotations = annotations_by_pair[pair.pair_id]
                    
#                     # Add annotation data
#                     pair_dict['annotations'] = []
#                     for ann in pair_annotations:
#                         pair_dict['annotations'].append({
#                             'username': ann['username'],
#                             'cue1': bool(int(ann.get('cue1', 0))),
#                             'cue2': bool(int(ann.get('cue2', 0))),
#                             'label': int(ann.get('label', 0)) if ann.get('label') else None,
#                             'confidence': int(ann.get('confidence', 3)),
#                             'notes': ann.get('notes', ''),
#                             'annotated_at': ann.get('annotated_at', '')
#                         })
                    
#                     # Calculate consensus if multiple annotations
#                     if len(pair_annotations) > 1:
#                         labels = [int(a['label']) for a in pair_annotations if a.get('label')]
#                         if labels:
#                             pair_dict['consensus_label'] = 1 if sum(labels) / len(labels) >= 0.5 else 0
#                             pair_dict['agreement_rate'] = f"{(sum(1 for l in labels if l == pair_dict['consensus_label']) / len(labels) * 100):.1f}%"
                
#                 exported_pairs.append(pair_dict)
            
#             # Build export structure
#             export_data = {
#                 'metadata': {
#                     'dataset_id': dataset_meta.dataset_id,
#                     'name': dataset_meta.name,
#                     'description': dataset_meta.description,
#                     'created_by': dataset_meta.created_by,
#                     'created_at': dataset_meta.created_at,
#                     'exported_at': datetime.now().isoformat(),
#                     'total_pairs': dataset_meta.pair_count,
#                     'original_filename': dataset_meta.original_filename,
#                     'export_format': 'annotated_full'
#                 },
#                 'statistics': {
#                     'total_annotations': len(all_annotations),
#                     'unique_annotators': len(set(a['username'] for a in all_annotations)),
#                     'annotated_pairs': len(annotations_by_pair),
#                     'completion_rate': f"{(len(annotations_by_pair) / len(original_pairs) * 100):.1f}%" if original_pairs else "0%"
#                 },
#                 'pairs': exported_pairs
#             }
            
#             return export_data
            
#         except Exception as e:
#             self.error_message = str(e)
#             return None
    
#     def export_user_annotations(self, username: str, dataset_id: str = None) -> Optional[Dict]:
#         """
#         Export user's annotations only
#         """
#         try:
#             user_annotations = self.get_user_annotations(username, dataset_id)
            
#             if not user_annotations:
#                 self.error_message = "No annotations found"
#                 return None
            
#             # Group by dataset if no specific dataset
#             if dataset_id:
#                 datasets = [self.get_datasets()[0]]  # Get specific dataset
#             else:
#                 datasets = self.get_datasets()
            
#             export_data = {
#                 'metadata': {
#                     'username': username,
#                     'exported_at': datetime.now().isoformat(),
#                     'total_annotations': len(user_annotations)
#                 },
#                 'annotations_by_dataset': {}
#             }
            
#             for ds in datasets:
#                 ds_annotations = [a for a in user_annotations if a.dataset == ds.dataset_id]
#                 if ds_annotations:
#                     export_data['annotations_by_dataset'][ds.dataset_id] = {
#                         'dataset_name': ds.name,
#                         'annotations': [a.to_dict() for a in ds_annotations]
#                     }
            
#             return export_data
            
#         except Exception as e:
#             self.error_message = str(e)
#             return None
    
#     def get_all_users(self) -> List[str]:
#         """Get all registered usernames"""
#         try:
#             users = self.users_sheet.get_all_records()
#             return [user['username'] for user in users]
#         except:
#             return []

# # =============================================================================
# # STREAMLIT APPLICATION
# # =============================================================================

# # Page config
# st.set_page_config(
#     page_title="CausaFr - Multi-Dataset Annotation",
#     page_icon="🔗",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Custom CSS
# st.markdown("""
# <style>
#     .main-header {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         padding: 2rem;
#         border-radius: 10px;
#         margin-bottom: 2rem;
#         text-align: center;
#     }
#     .sentence-box {
#         background: #f8f9fa;
#         border-left: 4px solid #4e73df;
#         padding: 1.5rem;
#         border-radius: 5px;
#         margin: 1rem 0;
#     }
#     .card {
#         background: white;
#         border-radius: 10px;
#         padding: 1.5rem;
#         box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#         margin: 1rem 0;
#         border: 1px solid #e3e6f0;
#     }
#     .progress-bar {
#         background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
#         height: 10px;
#         border-radius: 5px;
#         margin: 1rem 0;
#     }
#     .stat-card {
#         background: #f8f9fa;
#         padding: 1rem;
#         border-radius: 8px;
#         text-align: center;
#         border: 1px solid #e3e6f0;
#     }
#     .alert {
#         padding: 1rem;
#         border-radius: 8px;
#         margin: 1rem 0;
#     }
#     .alert-success {
#         background: #d1e7dd;
#         border: 1px solid #badbcc;
#         color: #0f5132;
#     }
#     .alert-warning {
#         background: #fff3cd;
#         border: 1px solid #ffecb5;
#         color: #664d03;
#     }
#     .alert-error {
#         background: #f8d7da;
#         border: 1px solid #f5c2c7;
#         color: #842029;
#     }
#     .alert-info {
#         background: #cff4fc;
#         border: 1px solid #b6effb;
#         color: #055160;
#     }
#     .dataset-card {
#         background: white;
#         border-radius: 10px;
#         padding: 1.5rem;
#         margin: 1rem 0;
#         border: 2px solid #e3e6f0;
#         transition: all 0.3s;
#     }
#     .dataset-card:hover {
#         border-color: #667eea;
#         box-shadow: 0 6px 12px rgba(102, 126, 234, 0.1);
#     }
#     .tag {
#         display: inline-block;
#         padding: 0.25rem 0.75rem;
#         border-radius: 15px;
#         font-size: 0.85rem;
#         margin-right: 0.5rem;
#         margin-bottom: 0.5rem;
#     }
#     .tag-primary {
#         background: #667eea;
#         color: white;
#     }
#     .tag-success {
#         background: #10b981;
#         color: white;
#     }
#     .tag-warning {
#         background: #f59e0b;
#         color: white;
#     }
#     .tag-info {
#         background: #3b82f6;
#         color: white;
#     }
# </style>
# """, unsafe_allow_html=True)

# # Initialize session state
# if 'authenticated' not in st.session_state:
#     st.session_state.authenticated = False
#     st.session_state.username = None
#     st.session_state.gsheets = None
#     st.session_state.current_dataset = None
#     st.session_state.pair_index = 0
#     st.session_state.current_pairs = []
#     st.session_state.is_admin = False

# # Check configuration
# if GOOGLE_CONFIG is None:
#     st.error("Google Sheets configuration not found. Please check your secrets.")
#     st.stop()

# # Initialize Google Sheets
# if st.session_state.gsheets is None:
#     st.session_state.gsheets = GoogleSheetsManager()
#     if not st.session_state.gsheets.connect():
#         st.error(f"❌ Connection failed: {st.session_state.gsheets.error_message}")
#         st.stop()

# # =============================================================================
# # PAGES
# # =============================================================================

# def login_page():
#     """Login/Register page"""
#     st.markdown("""
#     <div class="main-header">
#         <h1>🔗 CausaFr - Multi-Dataset Annotation Tool</h1>
#         <p>All data stored in Google Sheets - Supports multiple JSON datasets</p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     col1, col2, col3 = st.columns([1, 2, 1])
    
#     with col2:
#         tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Créer un compte"])
        
#         with tab1:
#             st.markdown("### Connexion")
#             username = st.text_input("Nom d'utilisateur")
#             password = st.text_input("Mot de passe", type="password")
            
#             if st.button("Se connecter", type="primary", use_container_width=True):
#                 if username and password:
#                     if st.session_state.gsheets.verify_user(username, password):
#                         st.session_state.authenticated = True
#                         st.session_state.username = username
#                         st.session_state.is_admin = st.session_state.gsheets.is_admin(username)
#                         st.rerun()
#                     else:
#                         st.error("❌ Identifiants incorrects")
#                 else:
#                     st.warning("⚠️ Remplissez tous les champs")
        
#         with tab2:
#             st.markdown("### Créer un compte")
#             new_user = st.text_input("Nouvel utilisateur")
#             new_pass = st.text_input("Nouveau mot de passe", type="password")
#             confirm_pass = st.text_input("Confirmer le mot de passe", type="password")
#             email = st.text_input("Email (optionnel)")
            
#             # Only admins can create admin accounts - removed from public registration
#             # is_admin = st.checkbox("Créer comme administrateur", value=False)
            
#             if st.button("Créer le compte", type="primary", use_container_width=True):
#                 if new_user and new_pass:
#                     if new_pass != confirm_pass:
#                         st.error("❌ Les mots de passe ne correspondent pas")
#                     else:
#                         # Always create as non-admin for public registration
#                         if st.session_state.gsheets.create_user(new_user, new_pass, email, is_admin=False):
#                             st.success("✅ Compte créé !")
#                             st.info("Connectez-vous maintenant")
#                         else:
#                             st.error("❌ Ce nom d'utilisateur existe déjà")
#                 else:
#                     st.warning("⚠️ Remplissez tous les champs obligatoires")

# def dataset_management_page():
#     """Dataset upload and management page - ADMIN ONLY"""
#     # Double-check admin status
#     if not st.session_state.is_admin:
#         st.error("⛔ Accès refusé - Cette section est réservée aux administrateurs")
#         st.info("Veuillez contacter un administrateur si vous avez besoin d'accéder à cette fonctionnalité.")
#         return
    
#     st.markdown("""
#     <div class="main-header">
#         <h1>📁 Gestion des Datasets</h1>
#         <p>Importez et gérez vos datasets JSON dans Google Sheets</p>
#         <p style="color: #f59e0b; font-size: 0.9rem;">👑 Section Administrateur</p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     gsheets = st.session_state.gsheets
    
#     tab1, tab2, tab3 = st.tabs(["📤 Importer Dataset", "📋 Datasets Disponibles", "🗑️ Gestion"])
    
#     with tab1:
#         st.markdown("### Importer un Dataset JSON")
        
#         # Dataset info
#         col1, col2 = st.columns(2)
#         with col1:
#             dataset_id = st.text_input("ID du Dataset*", 
#                                       placeholder="ex: dataset_1, causal_fr, etc.")
#             dataset_name = st.text_input("Nom du Dataset*", 
#                                         placeholder="Nom affiché")
#         with col2:
#             created_by = st.text_input("Créé par*", value=st.session_state.username)
#             original_filename = st.text_input("Nom du fichier original", 
#                                             placeholder="ex: Ya_Tening_Gining.json")
        
#         description = st.text_area("Description", placeholder="Description du dataset")
        
#         # JSON upload
#         st.markdown("### Contenu JSON")
#         json_method = st.radio("Méthode d'import", 
#                               ["📤 Upload fichier", "📝 Coller le JSON"])
        
#         json_content = ""
        
#         if json_method == "📤 Upload fichier":
#             uploaded_file = st.file_uploader("Choisir un fichier JSON", type=['json'])
#             if uploaded_file is not None:
#                 try:
#                     json_content = uploaded_file.getvalue().decode('utf-8')
#                     st.success(f"✅ Fichier chargé: {uploaded_file.name}")
                    
#                     # Auto-fill fields
#                     if not original_filename:
#                         original_filename = uploaded_file.name
                    
#                     if not dataset_id:
#                         dataset_id = uploaded_file.name.replace('.json', '').replace(' ', '_')
                    
#                     if not dataset_name:
#                         dataset_name = uploaded_file.name.replace('.json', '')
                    
#                     # Preview
#                     with st.expander("📄 Aperçu du JSON"):
#                         try:
#                             data = json.loads(json_content)
#                             if isinstance(data, list):
#                                 st.write(f"Format: Liste de {len(data)} paires")
#                                 if data and len(data) > 0:
#                                     st.json(data[0])
#                             elif isinstance(data, dict):
#                                 if 'pairs' in data:
#                                     st.write(f"Format: Dictionnaire avec {len(data['pairs'])} paires")
#                                     if data['pairs'] and len(data['pairs'] > 0):
#                                         st.json(data['pairs'][0])
#                                 else:
#                                     st.write("Format: Dictionnaire")
#                                     st.json(data)
#                         except:
#                             st.code(json_content[:1000] + "..." if len(json_content) > 1000 else json_content)
#                 except Exception as e:
#                     st.error(f"❌ Erreur de lecture: {e}")
        
#         else:  # Paste JSON
#             json_content = st.text_area("Collez votre JSON ici", height=300,
#                                        placeholder='{"pairs": [...]} ou [...]')
#             if json_content:
#                 try:
#                     data = json.loads(json_content)
#                     if isinstance(data, list):
#                         st.success(f"✅ JSON valide: Liste de {len(data)} paires")
#                     elif isinstance(data, dict) and 'pairs' in data:
#                         st.success(f"✅ JSON valide: Dictionnaire avec {len(data['pairs'])} paires")
#                     else:
#                         st.warning("⚠️ Format JSON valide mais structure inattendue")
#                 except json.JSONDecodeError as e:
#                     st.error(f"❌ JSON invalide: {e}")
        
#         # Import button
#         if st.button("🚀 Importer dans Google Sheets", type="primary", 
#                     disabled=not (dataset_id and json_content)):
#             with st.spinner("Importation en cours..."):
#                 success, total_pairs, imported_pairs = gsheets.import_json_dataset(
#                     dataset_id, json_content, 
#                     dataset_name or dataset_id, 
#                     description, created_by, original_filename
#                 )
                
#                 if success:
#                     st.success(f"✅ Dataset importé avec succès !")
#                     st.info(f"📊 {imported_pairs} nouvelles paires importées (sur {total_pairs} total)")
#                     if imported_pairs < total_pairs:
#                         st.warning(f"⚠️ {total_pairs - imported_pairs} paires déjà existantes ignorées")
#                     st.balloons()
#                 else:
#                     st.error(f"❌ Erreur: {gsheets.error_message}")
    
#     with tab2:
#         st.markdown("### Datasets disponibles")
        
#         datasets = gsheets.get_datasets()
        
#         if not datasets:
#             st.info("📭 Aucun dataset disponible")
#             return
        
#         # Statistics
#         total_pairs = sum(d.pair_count for d in datasets)
#         total_datasets = len(datasets)
        
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.metric("Datasets", total_datasets)
#         with col2:
#             st.metric("Paires totales", total_pairs)
#         with col3:
#             st.metric("Dernier import", datasets[-1].created_at[:10] if datasets else "N/A")
        
#         # Dataset cards
#         for dataset in datasets:
#             with st.container():
#                 st.markdown(f"""
#                 <div class="dataset-card">
#                     <h4>📁 {dataset.name}</h4>
#                     <p>{dataset.description}</p>
#                     <div style="margin-top: 1rem;">
#                         <span class="tag tag-primary">ID: {dataset.dataset_id}</span>
#                         <span class="tag tag-success">{dataset.pair_count} paires</span>
#                         <span class="tag tag-info">Créé par: {dataset.created_by}</span>
#                         <span class="tag tag-warning">{dataset.created_at[:10]}</span>
#                     </div>
#                 </div>
#                 """, unsafe_allow_html=True)
                
#                 # Buttons in expander
#                 with st.expander("Actions", expanded=False):
#                     col1, col2, col3 = st.columns(3)
                    
#                     with col1:
#                         if st.button(f"📊 Charger pour annotation", key=f"load_{dataset.dataset_id}"):
#                             st.session_state.current_dataset = dataset.dataset_id
#                             st.session_state.pair_index = 0
#                             st.rerun()
                    
#                     with col2:
#                         # Preview pairs
#                         if st.button(f"👁️ Aperçu", key=f"preview_{dataset.dataset_id}"):
#                             pairs = gsheets.get_dataset_pairs(dataset.dataset_id)
#                             if pairs:
#                                 st.info(f"📋 {len(pairs)} paires chargées")
#                                 # Show first 3 pairs
#                                 for i, pair in enumerate(pairs[:3]):
#                                     with st.expander(f"Paire {i+1}: {pair.event1_text[:50]}..."):
#                                         col_a, col_b = st.columns(2)
#                                         with col_a:
#                                             st.write("**Événement 1:**")
#                                             st.write(pair.event1_text)
#                                             if pair.event1_has_causal_cue:
#                                                 st.info(f"Marqueur causal: {pair.event1_causal_cue_text or pair.event1_causal_cue_type}")
#                                         with col_b:
#                                             st.write("**Événement 2:**")
#                                             st.write(pair.event2_text)
#                                             if pair.event2_has_causal_cue:
#                                                 st.info(f"Marqueur causal: {pair.event2_causal_cue_text or pair.event2_causal_cue_type}")
                                        
#                                         # Metadata
#                                         st.caption(f"Narrative: {pair.narrative_id} | Catégories: {pair.event1_category}/{pair.event2_category}")
                                        
#                                 if len(pairs) > 3:
#                                     st.caption(f"... et {len(pairs)-3} autres paires")
                    
#                     with col3:
#                         # Export button
#                         if st.button(f"📥 Exporter", key=f"export_{dataset.dataset_id}"):
#                             export_data = gsheets.export_annotated_dataset(dataset.dataset_id)
#                             if export_data:
#                                 json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
#                                 st.download_button(
#                                     "⬇️ Télécharger JSON complet",
#                                     json_str,
#                                     file_name=f"causafr_{dataset.dataset_id}_{datetime.now().strftime('%Y%m%d')}.json",
#                                     mime="application/json",
#                                     key=f"download_{dataset.dataset_id}"
#                                 )
#                             else:
#                                 st.error(f"Erreur: {gsheets.error_message}")
    
#     with tab3:
#         st.markdown("### 🗑️ Gestion des Datasets (Admin)")
        
#         datasets = gsheets.get_datasets()
#         if not datasets:
#             st.info("Aucun dataset à gérer")
#             return
        
#         dataset_options = {f"{d.name} ({d.dataset_id})": d.dataset_id for d in datasets}
#         selected_display = st.selectbox("Sélectionner un dataset à gérer", list(dataset_options.keys()))
#         selected_id = dataset_options[selected_display]
        
#         selected_dataset = None
#         for ds in datasets:
#             if ds.dataset_id == selected_id:
#                 selected_dataset = ds
#                 break
        
#         if selected_dataset:
#             st.markdown(f"### Dataset: {selected_dataset.name}")
            
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 st.metric("Paires", selected_dataset.pair_count)
#             with col2:
#                 st.metric("Créé le", selected_dataset.created_at[:10])
#             with col3:
#                 st.metric("Fichier", selected_dataset.original_filename)
            
#             # Get dataset statistics
#             pairs = gsheets.get_dataset_pairs(selected_id)
#             annotations = gsheets.get_all_annotations(selected_id)
#             unique_annotators = len(set(a['username'] for a in annotations))
            
#             st.markdown("#### 📊 Statistiques")
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 st.metric("Annotations totales", len(annotations))
#             with col2:
#                 st.metric("Annotateurs", unique_annotators)
#             with col3:
#                 completion = (len(set(a['pair_id'] for a in annotations)) / selected_dataset.pair_count * 100) if selected_dataset.pair_count > 0 else 0
#                 st.metric("Taux d'annotation", f"{completion:.1f}%")
            
#             # Danger zone
#             st.markdown("#### ⚠️ Zone de danger")
#             st.warning("Les actions suivantes sont irréversibles")
            
#             if st.button("🗑️ Supprimer ce dataset", type="secondary"):
#                 if st.checkbox("Je confirme la suppression de ce dataset et toutes ses données"):
#                     if gsheets.delete_dataset(selected_id):
#                         st.success("✅ Dataset supprimé avec succès")
#                         st.rerun()
#                     else:
#                         st.error(f"❌ Erreur: {gsheets.error_message}")

# def annotate_page():
#     """Main annotation page"""
#     username = st.session_state.username
#     gsheets = st.session_state.gsheets
    
#     # Sidebar
#     with st.sidebar:
#         st.markdown(f"### 👤 {username}")
#         if st.session_state.is_admin:
#             st.markdown("👑 **Administrateur**")
        
#         # Dataset selection
#         st.markdown("### 📁 Dataset")
        
#         datasets = gsheets.get_datasets()
#         if not datasets:
#             st.error("Aucun dataset disponible")
#             st.info("Contactez un administrateur pour importer des datasets")
#             return
        
#         dataset_options = {f"{d.name} ({d.pair_count} paires)": d.dataset_id for d in datasets}
#         selected_display = st.selectbox("Choisir un dataset", list(dataset_options.keys()))
#         selected_id = dataset_options[selected_display]
        
#         # Get dataset name for display
#         dataset_name = ""
#         for ds in datasets:
#             if ds.dataset_id == selected_id:
#                 dataset_name = ds.name
#                 break
        
#         if st.session_state.current_dataset != selected_id:
#             st.session_state.current_dataset = selected_id
#             st.session_state.pair_index = 0
#             st.session_state.current_pairs = []
        
#         # Load dataset pairs
#         if not st.session_state.current_pairs:
#             with st.spinner("Chargement des paires..."):
#                 pairs = gsheets.get_dataset_pairs(selected_id)
#                 if not pairs:
#                     st.error("❌ Erreur de chargement des paires")
#                     return
#                 st.session_state.current_pairs = pairs
        
#         pairs = st.session_state.current_pairs
#         total_pairs = len(pairs)
        
#         # Load progress
#         progress = gsheets.get_user_progress(username, selected_id)
#         current_index = progress.get('current_index', 0)
        
#         if st.session_state.pair_index == 0 and current_index > 0:
#             st.session_state.pair_index = min(current_index, total_pairs - 1)
        
#         # Statistics
#         user_annotations = gsheets.get_user_annotations(username, selected_id)
#         annotated_count = len(user_annotations)
#         causal_count = sum(1 for ann in user_annotations if ann.label == 1)
#         non_causal_count = sum(1 for ann in user_annotations if ann.label == 0)
        
#         st.markdown("### 📊 Vos statistiques")
#         col1, col2 = st.columns(2)
#         with col1:
#             st.metric("Total", total_pairs)
#             st.metric("Causales", causal_count)
#         with col2:
#             st.metric("Annotées", annotated_count)
#             st.metric("Non causales", non_causal_count)
        
#         # Progress
#         st.markdown("### 📍 Progression")
#         progress_pct = (annotated_count / total_pairs * 100) if total_pairs > 0 else 0
#         st.markdown(f'<div class="progress-bar" style="width: {progress_pct}%"></div>', unsafe_allow_html=True)
#         st.caption(f"{annotated_count}/{total_pairs} ({progress_pct:.1f}%)")
        
#         # Navigation
#         st.markdown("### 🧭 Navigation")
#         jump_to = st.number_input("Aller à", 1, total_pairs, st.session_state.pair_index + 1)
#         if st.button("📍 Aller", use_container_width=True):
#             st.session_state.pair_index = jump_to - 1
#             st.rerun()
        
#         # Quick navigation
#         if st.button("⏭️ Prochaine non annotée", use_container_width=True):
#             for i in range(st.session_state.pair_index + 1, total_pairs):
#                 pair_id = pairs[i].pair_id
#                 existing = [ann for ann in user_annotations if ann.pair_id == pair_id]
#                 if not existing:
#                     st.session_state.pair_index = i
#                     st.rerun()
#                     break
        
#         # Export button in sidebar
#         st.markdown("---")
#         if st.button("📥 Exporter ce dataset", use_container_width=True):
#             export_data = gsheets.export_annotated_dataset(selected_id)
#             if export_data:
#                 json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
#                 st.download_button(
#                     "⬇️ Télécharger JSON annoté",
#                     json_str,
#                     file_name=f"causafr_{selected_id}_{datetime.now().strftime('%Y%m%d')}.json",
#                     mime="application/json",
#                     use_container_width=True
#                 )
        
#         st.markdown("---")
#         if st.button("🚪 Déconnexion", use_container_width=True):
#             for key in list(st.session_state.keys()):
#                 del st.session_state[key]
#             st.rerun()
    
#     # Main content
#     if not pairs:
#         st.warning("Aucune paire à annoter")
#         return
    
#     idx = st.session_state.pair_index
#     current_pair = pairs[idx]
    
#     # Header
#     st.markdown(f"""
#     <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
#         <h2>Paire {idx + 1} / {total_pairs}</h2>
#         <div style="display: flex; gap: 1rem; align-items: center;">
#             <span style="background: #e9ecef; padding: 0.5rem 1rem; border-radius: 20px;">
#                 📄 {dataset_name}
#             </span>
#             <span style="background: #d1fae5; padding: 0.5rem 1rem; border-radius: 20px;">
#                 ID: {current_pair.pair_id}
#             </span>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Check if already annotated
#     existing_annotations = [ann for ann in user_annotations 
#                           if ann.pair_id == current_pair.pair_id]
    
#     if existing_annotations:
#         existing = existing_annotations[0]
#         st.markdown(f"""
#         <div class="alert alert-warning">
#             ✏️ <strong>Déjà annotée</strong> le {existing.annotated_at[:16]}
#             (Confidence: {existing.confidence}/5 - { '✅ Causal' if existing.label == 1 else '❌ Non causal'})
#         </div>
#         """, unsafe_allow_html=True)
    
#     # Additional information
#     with st.expander("📊 Informations supplémentaires", expanded=False):
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             st.write("**Identifiants:**")
#             st.write(f"- Narrative: `{current_pair.narrative_id}`")
#             st.write(f"- Event1: `{current_pair.event1_id}`")
#             st.write(f"- Event2: `{current_pair.event2_id}`")
            
#             st.write("**Catégories:**")
#             st.write(f"- E1: `{current_pair.event1_category}`")
#             st.write(f"- E2: `{current_pair.event2_category}`")
        
#         with col2:
#             st.write("**Marqueurs causaux:**")
#             if current_pair.event1_has_causal_cue:
#                 st.info(f"✅ E1: {current_pair.event1_causal_cue_text or current_pair.event1_causal_cue_type}")
#             if current_pair.event2_has_causal_cue:
#                 st.info(f"✅ E2: {current_pair.event2_causal_cue_text or current_pair.event2_causal_cue_type}")
            
#             st.write("**Marqueurs temporels:**")
#             if current_pair.event1_has_temporal:
#                 st.info(f"⏱️ E1: {current_pair.event1_temporal_text or current_pair.event1_temporal_type}")
#             if current_pair.event2_has_temporal:
#                 st.info(f"⏱️ E2: {current_pair.event2_temporal_text or current_pair.event2_temporal_type}")
        
#         with col3:
#             st.write("**Métadonnées:**")
#             if current_pair.is_hard_negative:
#                 st.warning("⚠️ Hard Negative")
#             if current_pair.pair_has_causal_cue:
#                 st.info("🔗 Paire a un marqueur causal")
#             if current_pair.pair_has_temporal:
#                 st.info("⏱️ Paire a un marqueur temporel")
            
#             if current_pair.label is not None:
#                 st.write(f"**Label original:** {'✅ Causal' if current_pair.label == 1 else '❌ Non causal'}")
    
#     # Events display
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.markdown("#### 🔵 Événement 1 (Cause)")
#         st.markdown(f'<div class="sentence-box">{current_pair.event1_text}</div>', unsafe_allow_html=True)
#         cue1 = st.checkbox("Marqueur causal explicite", 
#                           value=existing_annotations[0].cue1 if existing_annotations else False,
#                           key="cue1")
    
#     with col2:
#         st.markdown("#### 🟢 Événement 2 (Effet)")
#         st.markdown(f'<div class="sentence-box">{current_pair.event2_text}</div>', unsafe_allow_html=True)
#         cue2 = st.checkbox("Marqueur causal explicite",
#                           value=existing_annotations[0].cue2 if existing_annotations else False,
#                           key="cue2")
    
#     # Annotation question
#     st.markdown("""
#     <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
#                 padding: 1.5rem; border-radius: 10px; margin: 2rem 0; text-align: center;">
#         <h3 style="color: #1565c0; margin: 0 0 0.5rem 0;">❓ Relation causale ?</h3>
#         <p style="color: #1976d2; margin: 0;">L'événement 1 cause-t-il l'événement 2 ?</p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Annotation controls
#     col1, col2 = st.columns(2)
    
#     with col1:
#         current_label = existing_annotations[0].label if existing_annotations else None
#         label = st.radio(
#             "Décision",
#             [1, 0],
#             index=0 if current_label == 1 else 1,
#             format_func=lambda x: "✅ OUI - Relation causale" if x == 1 else "❌ NON - Pas de relation",
#             key="label"
#         )
    
#     with col2:
#         current_conf = existing_annotations[0].confidence if existing_annotations else 3
#         confidence = st.slider("Confiance", 1, 5, current_conf, key="confidence")
#         notes = st.text_input("Notes", 
#                              value=existing_annotations[0].notes if existing_annotations else '',
#                              placeholder="Notes optionnelles...",
#                              key="notes")
    
#     # Action buttons
#     st.markdown("---")
#     col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
#     with col1:
#         if st.button("⬅️", disabled=idx == 0, use_container_width=True):
#             st.session_state.pair_index -= 1
#             st.rerun()
    
#     with col2:
#         if st.button("💾 Enregistrer", type="primary", use_container_width=True):
#             annotation = UserAnnotation(
#                 id="",
#                 pair_id=current_pair.pair_id,
#                 dataset=selected_id,
#                 username=username,
#                 event1_text=current_pair.event1_text,
#                 event2_text=current_pair.event2_text,
#                 cue1=int(cue1),
#                 cue2=int(cue2),
#                 label=int(label),
#                 confidence=confidence,
#                 notes=notes,
#                 annotated_at=datetime.now().isoformat(),
#                 event1_id=current_pair.event1_id,
#                 event2_id=current_pair.event2_id
#             )
            
#             ann_id = gsheets.save_annotation(annotation)
#             if ann_id:
#                 user_anns = gsheets.get_user_annotations(username, selected_id)
#                 gsheets.update_progress(username, selected_id, idx, len(user_anns), current_pair.pair_id)
#                 st.success("✅ Annotation sauvegardée")
#                 st.rerun()
#             else:
#                 st.error(f"❌ Erreur: {gsheets.error_message}")
    
#     with col3:
#         if st.button("💾 & ⏭️ Suivant", use_container_width=True):
#             annotation = UserAnnotation(
#                 id="",
#                 pair_id=current_pair.pair_id,
#                 dataset=selected_id,
#                 username=username,
#                 event1_text=current_pair.event1_text,
#                 event2_text=current_pair.event2_text,
#                 cue1=int(cue1),
#                 cue2=int(cue2),
#                 label=int(label),
#                 confidence=confidence,
#                 notes=notes,
#                 annotated_at=datetime.now().isoformat(),
#                 event1_id=current_pair.event1_id,
#                 event2_id=current_pair.event2_id
#             )
            
#             ann_id = gsheets.save_annotation(annotation)
#             if ann_id:
#                 user_anns = gsheets.get_user_annotations(username, selected_id)
#                 gsheets.update_progress(username, selected_id, idx, len(user_anns), current_pair.pair_id)
#                 if idx < total_pairs - 1:
#                     st.session_state.pair_index += 1
#                 st.rerun()
#             else:
#                 st.error(f"❌ Erreur: {gsheets.error_message}")
    
#     with col4:
#         if st.button("➡️", disabled=idx >= total_pairs - 1, use_container_width=True):
#             st.session_state.pair_index += 1
#             st.rerun()

# def dashboard_page():
#     """Dashboard page"""
#     username = st.session_state.username
#     gsheets = st.session_state.gsheets
    
#     st.markdown(f"""
#     <div class="main-header">
#         <h1>📊 Tableau de bord</h1>
#         <p>Statistiques et visualisation globale</p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Get all data
#     datasets = gsheets.get_datasets()
#     all_annotations = gsheets.get_all_annotations()
    
#     # Global statistics
#     st.markdown("### 📈 Statistiques globales")
    
#     col1, col2, col3, col4 = st.columns(4)
#     with col1:
#         total_pairs = sum(d.pair_count for d in datasets)
#         st.metric("Paires totales", total_pairs)
#     with col2:
#         st.metric("Datasets", len(datasets))
#     with col3:
#         st.metric("Annotations totales", len(all_annotations))
#     with col4:
#         unique_users = len(set(a['username'] for a in all_annotations))
#         st.metric("Annotateurs uniques", unique_users)
    
#     # User statistics
#     st.markdown(f"### 👤 Vos statistiques")
#     user_annotations = gsheets.get_user_annotations(username)
    
#     if user_annotations:
#         col1, col2, col3, col4 = st.columns(4)
#         with col1:
#             st.metric("Vos annotations", len(user_annotations))
#         with col2:
#             user_datasets = len(set(a.dataset for a in user_annotations))
#             st.metric("Datasets annotés", user_datasets)
#         with col3:
#             causal = sum(1 for a in user_annotations if a.label == 1)
#             st.metric("Vos relations causales", causal)
#         with col4:
#             avg_conf = sum(a.confidence for a in user_annotations) / len(user_annotations) if user_annotations else 0
#             st.metric("Confiance moyenne", f"{avg_conf:.1f}/5")
    
#     # Dataset statistics
#     st.markdown("### 📋 Statistiques par dataset")
    
#     for dataset in datasets:
#         dataset_anns = [a for a in all_annotations if a['dataset'] == dataset.dataset_id]
#         user_ds_anns = [a for a in user_annotations if a.dataset == dataset.dataset_id]
        
#         with st.expander(f"📁 {dataset.name} ({dataset.dataset_id})"):
#             col1, col2, col3, col4 = st.columns(4)
            
#             with col1:
#                 completion = (len(set(a['pair_id'] for a in dataset_anns)) / dataset.pair_count * 100) if dataset.pair_count > 0 else 0
#                 st.metric("Taux d'annotation", f"{completion:.1f}%")
            
#             with col2:
#                 st.metric("Annotations totales", len(dataset_anns))
            
#             with col3:
#                 unique_annotators = len(set(a['username'] for a in dataset_anns))
#                 st.metric("Annotateurs", unique_annotators)
            
#             with col4:
#                 if user_ds_anns:
#                     user_completion = (len(user_ds_anns) / dataset.pair_count * 100) if dataset.pair_count > 0 else 0
#                     st.metric("Votre progression", f"{user_completion:.1f}%")
#                 else:
#                     st.metric("Votre progression", "0%")
            
#             # Export button
#             if st.button(f"📥 Exporter {dataset.name}", key=f"export_dash_{dataset.dataset_id}"):
#                 export_data = gsheets.export_annotated_dataset(dataset.dataset_id)
#                 if export_data:
#                     json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
#                     st.download_button(
#                         "⬇️ Télécharger",
#                         json_str,
#                         file_name=f"causafr_{dataset.dataset_id}_{datetime.now().strftime('%Y%m%d')}.json",
#                         mime="application/json",
#                         key=f"download_dash_{dataset.dataset_id}"
#                     )

# def about_page():
#     """About page"""
#     gsheets = st.session_state.gsheets
    
#     st.markdown(f"""
#     <div class="main-header">
#         <h1>ℹ️ À propos de CausaFr</h1>
#         <p>Outil d'annotation multi-datasets avec Google Sheets</p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     st.markdown("""
#     <div class="card">
#         <h3>🎯 Objectif</h3>
#         <p>CausaFr est un outil collaboratif pour l'annotation de relations causales entre événements dans des textes en français. 
#         Supporte <strong>plusieurs datasets JSON simultanément</strong> avec préservation de tous les champs originaux.</p>
        
#         <h3>🔗 État de la connexion</h3>
#     </div>
#     """, unsafe_allow_html=True)
    
#     if gsheets.connected:
#         st.success("✅ Connecté à Google Sheets")
        
#         # Statistics
#         datasets = gsheets.get_datasets()
#         all_annotations = gsheets.get_all_annotations()
        
#         col1, col2, col3, col4 = st.columns(4)
#         with col1:
#             st.metric("Datasets", len(datasets))
#         with col2:
#             total_pairs = sum(d.pair_count for d in datasets)
#             st.metric("Paires totales", total_pairs)
#         with col3:
#             st.metric("Annotations", len(all_annotations))
#         with col4:
#             users = gsheets.get_all_users()
#             st.metric("Utilisateurs", len(users))
#     else:
#         st.error(f"❌ Non connecté: {gsheets.error_message}")

# def main():
#     """Main application"""
    
#     if not st.session_state.authenticated:
#         login_page()
#         return
    
#     # Sidebar navigation
#     with st.sidebar:
#         st.markdown(f"""
#         <div style="text-align: center; margin-bottom: 2rem;">
#             <h2>🔗 CausaFr</h2>
#             <p style="color: #666; font-size: 0.9rem;">👤 {st.session_state.username}</p>
#             { '<p style="color: #f59e0b; font-size: 0.8rem;">👑 Administrateur</p>' if st.session_state.is_admin else '' }
#         </div>
#         """, unsafe_allow_html=True)
        
#         # Create navigation options based on user role
#         if st.session_state.is_admin:
#             pages = ["📤 Gérer Datasets", "✏️ Annoter", "📊 Tableau de bord", "ℹ️ À propos"]
#         else:
#             pages = ["✏️ Annoter", "📊 Tableau de bord", "ℹ️ À propos"]
        
#         page = st.radio("Navigation", pages, label_visibility="collapsed")
    
#     # Show selected page with admin check
#     if page == "📤 Gérer Datasets":
#         if not st.session_state.is_admin:
#             st.error("⛔ Accès refusé - Cette section est réservée aux administrateurs")
#             st.info("Veuillez contacter un administrateur si vous avez besoin d'accéder à cette fonctionnalité.")
#         else:
#             dataset_management_page()
#     elif page == "✏️ Annoter":
#         annotate_page()
#     elif page == "📊 Tableau de bord":
#         dashboard_page()
#     elif page == "ℹ️ À propos":
#         about_page()

# if __name__ == "__main__":
#     main()





"""
CausaFr - Complete Google Sheets Annotation Tool
Streamlit Cloud Deployment Version
Enhanced with proper JSON export preserving original structure
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
import gspread
from google.oauth2.service_account import Credentials

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
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Annotation:
    """Annotation data for a single pair"""
    annotation_id: str
    pair_id: str
    annotator_id: str
    timestamp: str
    causal_relation: int  # -1: negative, 0: neutral, 1: positive
    confidence: int  # 1-5
    direction: int  # -1: event2 causes event1, 0: bidirectional/no clear direction, 1: event1 causes event2
    notes: str = ""
    rationales: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_export_format(self, original_pair: Optional[Dict] = None) -> Dict:
        """Convert to the expected export format"""
        # Get cue information from original pair metadata
        cue1 = False
        cue2 = False
        if original_pair:
            cue1 = original_pair.get('event1_has_causal_cue', False)
            cue2 = original_pair.get('event2_has_causal_cue', False)
        
        return {
            "username": self.annotator_id,
            "cue1": cue1,
            "cue2": cue2,
            "label": self.causal_relation if self.causal_relation != 0 else None,  # Match your format where 0 becomes null
            "confidence": self.confidence,
            "direction": self.direction,
            "notes": self.notes,
            "rationales": self.rationales,
            "annotated_at": self.timestamp
        }

@dataclass
class Annotator:
    """Annotator information"""
    annotator_id: str
    name: str
    email: str = ""
    expertise_level: str = ""  # beginner, intermediate, expert
    status: str = "active"  # active, inactive
    
@dataclass
class Batch:
    """Batch of pairs assigned to an annotator"""
    batch_id: str
    annotator_id: str
    pair_ids: List[str]
    assigned_date: str
    completed_date: Optional[str] = None
    status: str = "assigned"  # assigned, in_progress, completed

# =============================================================================
# GOOGLE SHEETS SERVICE
# =============================================================================

class GoogleSheetsService:
    """Service for interacting with Google Sheets"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.client = None
        self.spreadsheet = None
        self._connect()
        
    def _connect(self):
        """Establish connection to Google Sheets"""
        try:
            # Define the scope
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            # Create credentials
            credentials = Credentials.from_service_account_info(
                self.config['gcp_credentials'], scopes=scope
            )
            
            # Create client
            self.client = gspread.authorize(credentials)
            
            # Open spreadsheet
            self.spreadsheet = self.client.open_by_key(self.config['spreadsheet_id'])
            st.success("✅ Successfully connected to Google Sheets")
            
        except Exception as e:
            st.error(f"❌ Failed to connect to Google Sheets: {e}")
            self.client = None
            self.spreadsheet = None
    
    def get_or_create_worksheet(self, name: str, headers: List[str]) -> gspread.Worksheet:
        """Get existing worksheet or create new one with headers"""
        try:
            # Try to open existing worksheet
            worksheet = self.spreadsheet.worksheet(name)
            st.info(f"📄 Using existing worksheet: {name}")
        except gspread.exceptions.WorksheetNotFound:
            # Create new worksheet
            worksheet = self.spreadsheet.add_worksheet(title=name, rows=1000, cols=len(headers))
            # Add headers
            worksheet.append_row(headers)
            st.success(f"📝 Created new worksheet: {name}")
        
        return worksheet
    
    def update_annotation(self, annotation: Annotation) -> bool:
        """Update annotation in Google Sheets"""
        try:
            worksheet = self.get_or_create_worksheet(
                "annotations",
                ["annotation_id", "pair_id", "annotator_id", "timestamp", 
                 "causal_relation", "confidence", "direction", "notes", 
                 "rationales", "metadata"]
            )
            
            # Prepare row data
            row = [
                annotation.annotation_id,
                annotation.pair_id,
                annotation.annotator_id,
                annotation.timestamp,
                annotation.causal_relation,
                annotation.confidence,
                annotation.direction,
                annotation.notes,
                "|".join(annotation.rationales) if annotation.rationales else "",
                json.dumps(annotation.metadata) if annotation.metadata else ""
            ]
            
            # Check if annotation already exists
            existing = worksheet.findall(annotation.annotation_id)
            if existing:
                # Update existing row
                row_idx = existing[0].row
                worksheet.update(f"A{row_idx}:J{row_idx}", [row])
                return True, "updated"
            else:
                # Append new row
                worksheet.append_row(row)
                return True, "created"
            
        except Exception as e:
            st.error(f"❌ Failed to save annotation: {e}")
            return False, str(e)
    
    def get_annotations(self, annotator_id: Optional[str] = None) -> List[Dict]:
        """Retrieve annotations from Google Sheets"""
        try:
            worksheet = self.spreadsheet.worksheet("annotations")
            records = worksheet.get_all_records()
            
            if annotator_id:
                records = [r for r in records if r.get('annotator_id') == annotator_id]
            
            # Parse JSON fields
            for record in records:
                if 'rationales' in record and isinstance(record['rationales'], str):
                    record['rationales'] = record['rationales'].split('|') if record['rationales'] else []
                if 'metadata' in record and isinstance(record['metadata'], str) and record['metadata']:
                    try:
                        record['metadata'] = json.loads(record['metadata'])
                    except:
                        record['metadata'] = {}
            
            return records
        except Exception as e:
            st.warning(f"Could not retrieve annotations: {e}")
            return []
    
    def get_pairs(self) -> List[Dict]:
        """Retrieve pairs from Google Sheets"""
        try:
            worksheet = self.spreadsheet.worksheet("pairs")
            records = worksheet.get_all_records()
            
            # Parse metadata JSON if present
            for record in records:
                if 'metadata' in record and isinstance(record['metadata'], str) and record['metadata']:
                    try:
                        metadata = json.loads(record['metadata'])
                        # Merge metadata into record
                        for key, value in metadata.items():
                            if key not in record:
                                record[key] = value
                    except:
                        pass
            
            return records
        except Exception as e:
            st.warning(f"Could not retrieve pairs: {e}")
            return []
    
    def update_batch_status(self, batch_id: str, status: str, completed_date: Optional[str] = None) -> bool:
        """Update batch status in Google Sheets"""
        try:
            worksheet = self.get_or_create_worksheet(
                "batches",
                ["batch_id", "annotator_id", "pair_ids", "assigned_date", 
                 "completed_date", "status"]
            )
            
            # Find and update batch
            cell = worksheet.find(batch_id)
            if cell:
                worksheet.update_cell(cell.row, 6, status)  # Status column
                if completed_date:
                    worksheet.update_cell(cell.row, 5, completed_date)  # Completed date column
                return True
            return False
            
        except Exception as e:
            st.error(f"Failed to update batch status: {e}")
            return False
    
    def import_pairs_from_json(self, json_data: Dict) -> Tuple[int, List[str]]:
        """Import pairs from JSON data to Google Sheets"""
        try:
            worksheet = self.get_or_create_worksheet(
                "pairs",
                ["pair_id", "narrative_id", "event1_id", "event2_id",
                 "event1_text", "event2_text", "event1_category", "event2_category",
                 "label", "dataset", "metadata", "original_data"]
            )
            
            pairs = json_data.get('pairs', [])
            imported_count = 0
            pair_ids = []
            
            # Clear existing data except header
            if len(pairs) > 0:
                worksheet.clear()
                worksheet.append_row(worksheet.row_values(1))  # Keep headers
            
            # Add pairs in batches
            batch_size = 100
            for i in range(0, len(pairs), batch_size):
                batch = pairs[i:i+batch_size]
                rows = []
                for pair in batch:
                    # Create pair_id if not present
                    pair_id = pair.get('pair_id') or \
                             f"{pair.get('narrative_id', 'unk')}_{pair.get('event1_id', 'unk')}_{pair.get('event2_id', 'unk')}"
                    
                    # Extract basic fields
                    narrative_id = pair.get('narrative_id', '')
                    event1_id = pair.get('event1_id', '')
                    event2_id = pair.get('event2_id', '')
                    event1_text = pair.get('event1_text', '')
                    event2_text = pair.get('event2_text', '')
                    event1_category = pair.get('event1_category', '')
                    event2_category = pair.get('event2_category', '')
                    label = pair.get('label', '')
                    dataset = json_data.get('metadata', {}).get('name', 'unknown')
                    
                    # Store original pair data as JSON
                    original_data = json.dumps(pair, ensure_ascii=False)
                    
                    rows.append([
                        pair_id,
                        narrative_id,
                        str(event1_id),
                        str(event2_id),
                        event1_text,
                        event2_text,
                        event1_category,
                        event2_category,
                        str(label) if label is not None else '',
                        dataset,
                        original_data,  # Store full pair as JSON in metadata column
                        ""  # Additional field for future use
                    ])
                    
                    pair_ids.append(pair_id)
                    imported_count += 1
                
                if rows:
                    worksheet.append_rows(rows)
            
            return imported_count, pair_ids
            
        except Exception as e:
            st.error(f"Error importing pairs: {e}")
            return 0, []

# =============================================================================
# EXPORT MANAGER
# =============================================================================

class ExportManager:
    """Handles export of annotations in various formats"""
    
    def __init__(self, sheets_service: GoogleSheetsService):
        self.sheets = sheets_service
    
    def export_annotations_json(self, annotator_id: str, original_json_data: Dict) -> Dict:
        """
        Export annotations in the original JSON format with annotations added/replaced
        Preserves all original data structure
        """
        try:
            # Get annotations from Google Sheets for this annotator
            sheet_annotations = self.sheets.get_annotations(annotator_id)
            
            if not sheet_annotations:
                st.warning(f"No annotations found for annotator {annotator_id}")
                # Return original data unchanged
                return original_json_data
            
            # Create a deep copy of the original data
            export_data = json.loads(json.dumps(original_json_data))
            
            # Create mapping from pair_id to annotations
            annotation_map = {}
            for ann in sheet_annotations:
                pair_id = ann.get('pair_id')
                if pair_id:
                    # Get original pair data to extract cue information
                    original_pair = self._find_original_pair(export_data, pair_id)
                    
                    # Create annotation in export format
                    annotation_obj = Annotation(
                        annotation_id=ann.get('annotation_id', ''),
                        pair_id=pair_id,
                        annotator_id=ann.get('annotator_id', ''),
                        timestamp=ann.get('timestamp', datetime.now().isoformat()),
                        causal_relation=ann.get('causal_relation', 0),
                        confidence=ann.get('confidence', 3),
                        direction=ann.get('direction', 0),
                        notes=ann.get('notes', ''),
                        rationales=ann.get('rationales', []),
                        metadata=ann.get('metadata', {})
                    )
                    
                    annotation_map[pair_id] = annotation_obj.to_export_format(original_pair)
            
            # Update pairs in export data with annotations
            if 'pairs' in export_data:
                updated_count = 0
                for pair in export_data['pairs']:
                    # Try to find pair_id in various possible fields
                    pair_id = self._extract_pair_id(pair)
                    
                    if pair_id in annotation_map:
                        # Initialize annotations array if not present
                        if 'annotations' not in pair:
                            pair['annotations'] = []
                        
                        # Remove existing annotations from this annotator
                        pair['annotations'] = [
                            a for a in pair.get('annotations', []) 
                            if a.get('username') != annotator_id
                        ]
                        
                        # Add new annotation
                        pair['annotations'].append(annotation_map[pair_id])
                        updated_count += 1
                
                st.info(f"Updated {updated_count} pairs with annotations")
            
            # Update metadata
            if 'metadata' in export_data:
                export_data['metadata'].update({
                    "exported_by": annotator_id,
                    "exported_at": datetime.now().isoformat(),
                    "export_format": "annotated_full",
                    "export_tool": "CausaFr Annotation Tool"
                })
            
            # Update statistics
            if 'statistics' in export_data:
                total_pairs = len(export_data.get('pairs', []))
                annotated_pairs = sum(1 for p in export_data.get('pairs', []) 
                                     if 'annotations' in p and any(a.get('username') == annotator_id 
                                                                  for a in p['annotations']))
                
                export_data['statistics'].update({
                    "total_annotations": len(sheet_annotations),
                    "unique_annotators": len(set(a.get('annotator_id') for a in sheet_annotations)),
                    "annotated_pairs": annotated_pairs,
                    "completion_rate": f"{(annotated_pairs/total_pairs*100):.1f}%" if total_pairs > 0 else "0.0%",
                    "export_timestamp": datetime.now().isoformat()
                })
            
            return export_data
            
        except Exception as e:
            st.error(f"Error exporting annotations: {e}")
            # Return original data on error
            return original_json_data
    
    def _find_original_pair(self, export_data: Dict, pair_id: str) -> Optional[Dict]:
        """Find original pair data by pair_id"""
        if 'pairs' not in export_data:
            return None
        
        for pair in export_data['pairs']:
            extracted_id = self._extract_pair_id(pair)
            if extracted_id == pair_id:
                return pair
        
        return None
    
    def _extract_pair_id(self, pair: Dict) -> str:
        """Extract pair_id from pair data, checking multiple possible fields"""
        # Check for explicit pair_id
        if 'pair_id' in pair:
            return str(pair['pair_id'])
        
        # Construct from narrative and event ids
        narrative_id = pair.get('narrative_id', 'unk')
        event1_id = str(pair.get('event1_id', 'unk'))
        event2_id = str(pair.get('event2_id', 'unk'))
        
        return f"{narrative_id}_{event1_id}_{event2_id}"
    
    def export_annotations_csv(self, annotator_id: str) -> pd.DataFrame:
        """Export annotations as CSV for analysis"""
        annotations = self.sheets.get_annotations(annotator_id)
        
        if not annotations:
            return pd.DataFrame()
        
        # Convert to DataFrame with desired columns
        df = pd.DataFrame(annotations)
        
        # Add derived columns if needed
        if 'causal_relation' in df.columns:
            df['causal_label'] = df['causal_relation'].map({
                -1: 'negative',
                0: 'neutral',
                1: 'positive'
            })
        
        # Add direction label
        if 'direction' in df.columns:
            df['direction_label'] = df['direction'].map({
                -1: 'event2_causes_event1',
                0: 'bidirectional',
                1: 'event1_causes_event2'
            })
        
        return df

# =============================================================================
# ANNOTATION MANAGER
# =============================================================================

class AnnotationManager:
    """Manages annotation workflow and data"""
    
    def __init__(self, sheets_service: GoogleSheetsService):
        self.sheets = sheets_service
        self.export_manager = ExportManager(sheets_service)
        self.current_batch = None
        self.current_pair_idx = 0
        
        # Initialize session state
        if 'annotations' not in st.session_state:
            st.session_state.annotations = {}
        if 'current_annotation' not in st.session_state:
            st.session_state.current_annotation = None
        if 'original_json_data' not in st.session_state:
            st.session_state.original_json_data = None
        if 'batch_pairs' not in st.session_state:
            st.session_state.batch_pairs = []
    
    def load_batch(self, batch_id: str) -> List[Dict]:
        """Load a batch of pairs for annotation"""
        try:
            # Try to get batch from Google Sheets
            try:
                batches_ws = self.sheets.spreadsheet.worksheet("batches")
                batch_records = batches_ws.get_all_records()
                batch_record = next((b for b in batch_records if b['batch_id'] == batch_id), None)
                
                if batch_record:
                    self.current_batch = batch_record
                    pair_ids = batch_record['pair_ids'].split(',') if batch_record['pair_ids'] else []
                    
                    # Get pairs
                    pairs = self.sheets.get_pairs()
                    batch_pairs = [p for p in pairs if p['pair_id'] in pair_ids]
                    
                    return batch_pairs
            except:
                pass
            
            # If no batch found, use all pairs
            st.warning(f"Batch {batch_id} not found. Using all available pairs.")
            pairs = self.sheets.get_pairs()
            return pairs[:50]  # Limit to 50 pairs for demo
            
        except Exception as e:
            st.error(f"Failed to load batch: {e}")
            return []
    
    def create_annotation(self, pair: Dict, annotator_id: str) -> Annotation:
        """Create a new annotation for a pair"""
        annotation_id = hashlib.md5(
            f"{pair['pair_id']}_{annotator_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        
        # Extract metadata from pair
        metadata = {}
        if 'metadata' in pair and isinstance(pair['metadata'], str):
            try:
                metadata = json.loads(pair['metadata'])
            except:
                metadata = {}
        
        # Also check for metadata fields directly in pair
        metadata_fields = [
            'event1_has_causal_cue', 'event1_causal_cue_type', 'event1_causal_cue_text',
            'event1_has_temporal', 'event1_temporal_type', 'event1_temporal_text',
            'event2_has_causal_cue', 'event2_causal_cue_type', 'event2_causal_cue_text',
            'event2_has_temporal', 'event2_temporal_type', 'event2_temporal_text',
            'pair_has_causal_cue', 'pair_has_temporal', 'is_hard_negative'
        ]
        
        for field in metadata_fields:
            if field in pair:
                metadata[field] = pair[field]
        
        return Annotation(
            annotation_id=annotation_id,
            pair_id=pair['pair_id'],
            annotator_id=annotator_id,
            timestamp=datetime.now().isoformat(),
            causal_relation=0,
            confidence=3,
            direction=0,
            notes="",
            rationales=[],
            metadata=metadata
        )
    
    def save_annotation(self, annotation: Annotation) -> Tuple[bool, str]:
        """Save annotation to Google Sheets and session state"""
        # Save to session state
        st.session_state.annotations[annotation.pair_id] = annotation
        st.session_state.current_annotation = annotation
        
        # Save to Google Sheets
        success, message = self.sheets.update_annotation(annotation)
        
        if success:
            st.success(f"✅ Annotation {message} successfully!")
        else:
            st.error(f"❌ Failed to save annotation: {message}")
        
        return success, message
    
    def get_progress(self, batch_pairs: List[Dict], annotator_id: str) -> Tuple[int, int]:
        """Get annotation progress for current batch"""
        annotations = self.sheets.get_annotations(annotator_id)
        annotated_ids = {a['pair_id'] for a in annotations}
        
        total = len(batch_pairs)
        completed = sum(1 for p in batch_pairs if p['pair_id'] in annotated_ids)
        
        return completed, total

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_pair_display(pair: Dict):
    """Display a pair of events for annotation"""
    st.markdown("### Event Pair")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Event 1")
        st.info(pair.get('event1_text', 'N/A'))
        if pair.get('event1_category'):
            st.caption(f"Category: {pair['event1_category']}")
        
        # Show causal cues if available
        if pair.get('event1_has_causal_cue'):
            st.caption(f"Causal cue: {pair.get('event1_causal_cue_text', '')}")
    
    with col2:
        st.markdown("#### Event 2")
        st.info(pair.get('event2_text', 'N/A'))
        if pair.get('event2_category'):
            st.caption(f"Category: {pair['event2_category']}")
        
        # Show causal cues if available
        if pair.get('event2_has_causal_cue'):
            st.caption(f"Causal cue: {pair.get('event2_causal_cue_text', '')}")
    
    # Display pair metadata
    with st.expander("📋 Pair Information"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pair ID", pair.get('pair_id', 'N/A'))
        with col2:
            st.metric("Dataset", pair.get('dataset', 'N/A'))
        with col3:
            if pair.get('label') is not None:
                label_map = {-1: "Negative", 0: "Neutral", 1: "Positive"}
                st.metric("Original Label", label_map.get(pair.get('label'), 'N/A'))
        
        # Show temporal information
        if pair.get('pair_has_temporal'):
            st.caption(f"Temporal relation present")
        
        # Show narrative ID if available
        if pair.get('narrative_id'):
            st.caption(f"Narrative: {pair['narrative_id']}")

def render_annotation_controls(existing_annotation: Optional[Dict] = None):
    """Render annotation controls"""
    st.markdown("### ✏️ Annotation")
    
    # Set default values
    defaults = {
        'causal_relation': 0,
        'confidence': 3,
        'direction': 0,
        'rationales': [],
        'notes': ''
    }
    
    if existing_annotation:
        defaults['causal_relation'] = existing_annotation.get('causal_relation', 0)
        defaults['confidence'] = existing_annotation.get('confidence', 3)
        defaults['direction'] = existing_annotation.get('direction', 0)
        defaults['rationales'] = existing_annotation.get('rationales', [])
        defaults['notes'] = existing_annotation.get('notes', '')
    
    # Causal Relation
    st.markdown("**Causal Relation**")
    causal_relation = st.radio(
        "Do these events have a causal relationship?",
        options=[-1, 0, 1],
        format_func=lambda x: {
            -1: "❌ Negative (Events are unrelated or contradictory)",
            0: "⚪ Neutral (No causal relationship)",
            1: "✅ Positive (Causal relationship exists)"
        }[x],
        horizontal=True,
        index=[-1, 0, 1].index(defaults['causal_relation']) if defaults['causal_relation'] in [-1, 0, 1] else 1,
        key=f"causal_relation_{st.session_state.get('current_pair_idx', 0)}"
    )
    
    # Only show direction if there's a causal relationship
    if causal_relation == 1:
        st.markdown("**Direction**")
        direction = st.radio(
            "What is the direction of causality?",
            options=[-1, 0, 1],
            format_func=lambda x: {
                -1: "← Event 2 causes Event 1",
                0: "↔ Bidirectional / No clear direction",
                1: "→ Event 1 causes Event 2"
            }[x],
            horizontal=True,
            index=[-1, 0, 1].index(defaults['direction']) if defaults['direction'] in [-1, 0, 1] else 2,
            key=f"direction_{st.session_state.get('current_pair_idx', 0)}"
        )
    else:
        direction = 0
    
    # Confidence
    st.markdown("**Confidence**")
    confidence = st.slider(
        "How confident are you in this annotation?",
        min_value=1,
        max_value=5,
        value=defaults['confidence'],
        help="1: Very uncertain, 5: Absolutely certain",
        key=f"confidence_{st.session_state.get('current_pair_idx', 0)}"
    )
    
    # Rationales
    st.markdown("**Rationale**")
    rationale_options = [
        "Temporal ordering",
        "Physical causation",
        "Social convention",
        "Psychological motivation",
        "Statistical correlation",
        "Plausible inference",
        "Direct statement",
        "Common sense",
        "Linguistic cues",
        "World knowledge"
    ]
    
    rationales = st.multiselect(
        "Select all applicable rationales (optional):",
        options=rationale_options,
        default=defaults['rationales'],
        key=f"rationales_{st.session_state.get('current_pair_idx', 0)}"
    )
    
    # Notes
    notes = st.text_area(
        "Additional notes (optional):",
        value=defaults['notes'],
        help="Any additional observations or explanations",
        key=f"notes_{st.session_state.get('current_pair_idx', 0)}",
        height=100
    )
    
    return {
        'causal_relation': causal_relation,
        'direction': direction,
        'confidence': confidence,
        'rationales': rationales,
        'notes': notes
    }

def render_annotator_login():
    """Render annotator login form"""
    st.markdown("## 🔐 Annotator Login")
    
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            annotator_id = st.text_input("Annotator ID", placeholder="e.g., annotator_01")
        
        with col2:
            batch_id = st.text_input("Batch ID", placeholder="e.g., batch_001")
        
        submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        
        if submitted:
            if annotator_id and batch_id:
                st.session_state.annotator_id = annotator_id
                st.session_state.batch_id = batch_id
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Please enter both Annotator ID and Batch ID")

def render_progress_bar(completed: int, total: int):
    """Render progress bar"""
    if total > 0:
        progress = completed / total
        st.progress(progress)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Completed", completed)
        with col2:
            st.metric("Total", total)
        with col3:
            st.metric("Progress", f"{progress:.1%}")
    else:
        st.warning("No pairs in batch")

def render_export_section(annotation_manager: AnnotationManager, annotator_id: str):
    """Render export options in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📤 Export Options")
    
    # JSON Export
    if st.sidebar.button("📥 Export JSON", key="export_json", use_container_width=True):
        with st.sidebar:
            with st.spinner("Preparing JSON export..."):
                # Get original data from session state
                original_data = st.session_state.get('original_json_data')
                
                if not original_data:
                    st.warning("No original data loaded. Please upload original JSON file first.")
                    return
                
                export_data = annotation_manager.export_manager.export_annotations_json(
                    annotator_id, 
                    original_data
                )
                
                if export_data:
                    # Create downloadable JSON
                    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    st.download_button(
                        label="⬇️ Download JSON File",
                        data=json_str,
                        file_name=f"causafr_annotations_{annotator_id}_{timestamp}.json",
                        mime="application/json",
                        key="download_json",
                        use_container_width=True
                    )
                    
                    # Show statistics
                    stats = export_data.get('statistics', {})
                    st.success(f"✅ Export ready: {stats.get('annotated_pairs', 0)} annotated pairs")
                    
                    # Show preview
                    with st.expander("📊 Export Preview"):
                        st.json({
                            "metadata": export_data.get('metadata', {}),
                            "statistics": stats,
                            "sample_pair": export_data.get('pairs', [{}])[0] if export_data.get('pairs') else {}
                        })
                else:
                    st.error("Export failed")
    
    # CSV Export
    if st.sidebar.button("📊 Export CSV", key="export_csv", use_container_width=True):
        with st.sidebar:
            with st.spinner("Preparing CSV export..."):
                df = annotation_manager.export_manager.export_annotations_csv(annotator_id)
                
                if not df.empty:
                    csv = df.to_csv(index=False, encoding='utf-8')
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    st.download_button(
                        label="⬇️ Download CSV File",
                        data=csv,
                        file_name=f"causafr_annotations_{annotator_id}_{timestamp}.csv",
                        mime="text/csv",
                        key="download_csv",
                        use_container_width=True
                    )
                    
                    # Show preview
                    with st.expander("📈 Data Preview"):
                        st.dataframe(df.head(10))
                else:
                    st.info("No annotations to export in CSV format")

def render_file_upload():
    """Render file upload for original JSON data"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📁 Upload Original Data")
    
    uploaded_file = st.sidebar.file_uploader(
        "Upload original JSON data",
        type=['json'],
        help="Upload the original JSON file to preserve structure in exports",
        key="original_data_upload"
    )
    
    if uploaded_file is not None:
        try:
            original_data = json.load(uploaded_file)
            st.session_state.original_json_data = original_data
            
            # Store in session state for later use
            st.session_state.uploaded_filename = uploaded_file.name
            
            # Show success message
            st.sidebar.success(f"✅ Loaded {len(original_data.get('pairs', []))} pairs from {uploaded_file.name}")
            
            # Show metadata
            with st.sidebar.expander("📋 Dataset Info"):
                metadata = original_data.get('metadata', {})
                if metadata:
                    for key, value in metadata.items():
                        if key in ['name', 'dataset_id', 'total_pairs', 'created_at']:
                            st.text(f"{key}: {value}")
                else:
                    st.text("No metadata available")
                    
        except Exception as e:
            st.sidebar.error(f"Error loading file: {e}")

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    st.set_page_config(
        page_title="CausaFr Annotation Tool",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
    }
    .pair-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
    }
    .annotation-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Title and description
    st.title("📊 CausaFr Annotation Tool")
    st.markdown("Annotate causal relations between event pairs")
    st.markdown("---")
    
    # Check Google Sheets configuration
    if GOOGLE_CONFIG is None:
        st.error("""
        ⚠️ Google Sheets configuration not found.
        
        Please add your Google Sheets credentials to Streamlit secrets:
        1. Go to Streamlit Cloud → Settings → Secrets
        2. Add your Google Sheets configuration
        """)
        st.stop()
    
    # Initialize services
    try:
        sheets_service = GoogleSheetsService(GOOGLE_CONFIG)
        annotation_manager = AnnotationManager(sheets_service)
    except Exception as e:
        st.error(f"Failed to initialize services: {e}")
        st.stop()
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_pair_idx' not in st.session_state:
        st.session_state.current_pair_idx = 0
    if 'batch_pairs' not in st.session_state:
        st.session_state.batch_pairs = []
    if 'annotator_id' not in st.session_state:
        st.session_state.annotator_id = ""
    if 'batch_id' not in st.session_state:
        st.session_state.batch_id = ""
    
    # Login page
    if not st.session_state.logged_in:
        render_annotator_login()
        
        # Show file upload in login page
        st.markdown("---")
        render_file_upload()
        
        return
    
    # Main annotation interface
    annotator_id = st.session_state.annotator_id
    batch_id = st.session_state.batch_id
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {annotator_id}")
        st.markdown(f"**Batch:** `{batch_id}`")
        
        # File upload section
        render_file_upload()
        
        # Load batch if not loaded
        if not st.session_state.batch_pairs:
            with st.spinner("Loading batch..."):
                batch_pairs = annotation_manager.load_batch(batch_id)
                if batch_pairs:
                    st.session_state.batch_pairs = batch_pairs
                    st.success(f"✅ Loaded {len(batch_pairs)} pairs")
                else:
                    st.error("Failed to load batch")
                    if st.button("🔄 Try Again"):
                        st.rerun()
        
        # Progress
        if st.session_state.batch_pairs:
            completed, total = annotation_manager.get_progress(
                st.session_state.batch_pairs, annotator_id
            )
            render_progress_bar(completed, total)
        
        # Navigation
        st.markdown("---")
        st.markdown("### 🧭 Navigation")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Previous", disabled=st.session_state.current_pair_idx == 0,
                        use_container_width=True):
                st.session_state.current_pair_idx -= 1
                st.rerun()
        with col2:
            if st.button("Next →", 
                        disabled=st.session_state.current_pair_idx >= len(st.session_state.batch_pairs) - 1,
                        use_container_width=True):
                st.session_state.current_pair_idx += 1
                st.rerun()
        
        # Pair selector
        if st.session_state.batch_pairs:
            pair_options = [
                f"#{i+1}: {p.get('pair_id', 'N/A')[:10]}..." 
                for i, p in enumerate(st.session_state.batch_pairs)
            ]
            selected_pair = st.selectbox(
                "Jump to pair:",
                options=range(len(pair_options)),
                format_func=lambda x: pair_options[x],
                index=st.session_state.current_pair_idx
            )
            if selected_pair != st.session_state.current_pair_idx:
                st.session_state.current_pair_idx = selected_pair
                st.rerun()
        
        # Batch actions
        st.markdown("---")
        if st.button("🔄 Refresh Batch", use_container_width=True):
            st.session_state.batch_pairs = annotation_manager.load_batch(batch_id)
            st.session_state.current_pair_idx = 0
            st.rerun()
        
        # Export section
        if st.session_state.get('original_json_data'):
            render_export_section(annotation_manager, annotator_id)
        
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content area
    if not st.session_state.batch_pairs:
        st.warning("No pairs in batch. Please contact administrator.")
        return
    
    # Get current pair
    current_pair = st.session_state.batch_pairs[st.session_state.current_pair_idx]
    pair_num = st.session_state.current_pair_idx + 1
    total_pairs = len(st.session_state.batch_pairs)
    
    # Header with pair info
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### Pair {pair_num} of {total_pairs}")
    with col2:
        st.metric("Pair ID", current_pair.get('pair_id', 'N/A'))
    with col3:
        st.metric("Status", "✅ Annotated" if st.session_state.get(f"annotated_{current_pair['pair_id']}") else "📝 Pending")
    
    st.markdown("---")
    
    # Display pair
    render_pair_display(current_pair)
    
    st.markdown("---")
    
    # Check for existing annotation
    existing_annotations = sheets_service.get_annotations(annotator_id)
    existing_annotation = next(
        (a for a in existing_annotations if a['pair_id'] == current_pair['pair_id']), 
        None
    )
    
    # Annotation form
    with st.form(f"annotation_form_{current_pair['pair_id']}", clear_on_submit=False):
        annotation_data = render_annotation_controls(existing_annotation)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submit_button = st.form_submit_button(
                "💾 Save Annotation",
                use_container_width=True,
                type="primary"
            )
        
        with col2:
            skip_button = st.form_submit_button(
                "⏭️ Skip & Next",
                use_container_width=True
            )
        
        with col3:
            if existing_annotation:
                clear_button = st.form_submit_button(
                    "🗑️ Clear",
                    use_container_width=True,
                    type="secondary"
                )
            else:
                clear_button = False
        
        # Handle form submissions
        if submit_button:
            # Create or update annotation
            annotation = annotation_manager.create_annotation(current_pair, annotator_id)
            annotation.causal_relation = annotation_data['causal_relation']
            annotation.direction = annotation_data['direction']
            annotation.confidence = annotation_data['confidence']
            annotation.rationales = annotation_data['rationales']
            annotation.notes = annotation_data['notes']
            
            # Save annotation
            success, message = annotation_manager.save_annotation(annotation)
            
            if success:
                # Mark as annotated in session state
                st.session_state[f"annotated_{current_pair['pair_id']}"] = True
                
                # Auto-advance if not last pair
                if st.session_state.current_pair_idx < total_pairs - 1:
                    with st.spinner("Saving and moving to next pair..."):
                        st.session_state.current_pair_idx += 1
                        st.rerun()
        
        elif skip_button:
            if st.session_state.current_pair_idx < total_pairs - 1:
                st.session_state.current_pair_idx += 1
                st.rerun()
            else:
                st.info("🎉 This is the last pair in the batch!")
        
        elif clear_button and existing_annotation:
            # TODO: Implement annotation clearing/deletion
            st.warning("Annotation clearing feature coming soon!")
    
    # Display existing annotation if it exists
    if existing_annotation:
        st.markdown("---")
        st.markdown("### 📝 Existing Annotation")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            relation_map = {-1: "❌ Negative", 0: "⚪ Neutral", 1: "✅ Positive"}
            st.metric("Relation", relation_map.get(existing_annotation['causal_relation'], 'N/A'))
        
        with col2:
            if existing_annotation['causal_relation'] == 1:
                dir_map = {-1: "← E2→E1", 0: "↔ Bidirectional", 1: "→ E1→E2"}
                st.metric("Direction", dir_map.get(existing_annotation['direction'], 'N/A'))
        
        with col3:
            st.metric("Confidence", f"{existing_annotation['confidence']}/5")
        
        with col4:
            st.metric("Rationales", len(existing_annotation.get('rationales', [])))
        
        if existing_annotation.get('notes'):
            with st.expander("📝 Annotation Notes"):
                st.write(existing_annotation['notes'])
        
        if existing_annotation.get('rationales'):
            st.caption(f"**Rationales:** {', '.join(existing_annotation['rationales'])}")
        
        st.caption(f"Last updated: {existing_annotation.get('timestamp', 'Unknown')}")

# =============================================================================
# ADMIN INTERFACE
# =============================================================================

def admin_interface():
    """Admin interface for managing batches and annotations"""
    st.title("🔧 Admin Panel")
    
    if GOOGLE_CONFIG is None:
        st.error("Google Sheets not configured")
        return
    
    sheets_service = GoogleSheetsService(GOOGLE_CONFIG)
    export_manager = ExportManager(sheets_service)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Batches", "📁 Data Import", "👥 Annotators", "📊 Statistics"])
    
    with tab1:
        st.subheader("Batch Management")
        
        # Create new batch
        with st.expander("➕ Create New Batch", expanded=True):
            with st.form("create_batch"):
                col1, col2 = st.columns(2)
                with col1:
                    batch_id = st.text_input("Batch ID", value=f"batch_{datetime.now().strftime('%Y%m%d_%H%M')}")
                    annotator_id = st.text_input("Annotator ID")
                with col2:
                    batch_size = st.number_input("Batch Size", min_value=1, max_value=1000, value=50)
                    status = st.selectbox("Status", ["assigned", "in_progress", "completed"])
                
                # Get available pairs
                pairs = sheets_service.get_pairs()
                if pairs:
                    pair_options = [f"{p.get('pair_id', '')} - {p.get('event1_text', '')[:50]}..." for p in pairs]
                    selected_indices = st.multiselect(
                        "Select pairs for batch",
                        options=range(len(pairs)),
                        format_func=lambda x: pair_options[x],
                        default=range(min(batch_size, len(pairs)))
                    )
                    
                    pair_ids = [pairs[i]['pair_id'] for i in selected_indices]
                    
                    if st.form_submit_button("Create Batch"):
                        if batch_id and annotator_id and pair_ids:
                            worksheet = sheets_service.get_or_create_worksheet(
                                "batches",
                                ["batch_id", "annotator_id", "pair_ids", "assigned_date", "completed_date", "status"]
                            )
                            worksheet.append_row([
                                batch_id,
                                annotator_id,
                                ",".join(pair_ids),
                                datetime.now().isoformat(),
                                "",
                                status
                            ])
                            st.success(f"✅ Batch '{batch_id}' created with {len(pair_ids)} pairs for {annotator_id}")
                else:
                    st.info("No pairs available. Import data first.")
        
        # View existing batches
        st.subheader("📋 Existing Batches")
        try:
            batches_ws = sheets_service.get_or_create_worksheet(
                "batches", 
                ["batch_id", "annotator_id", "pair_ids", "assigned_date", "completed_date", "status"]
            )
            batches = batches_ws.get_all_records()
            
            if batches:
                df = pd.DataFrame(batches)
                st.dataframe(df, use_container_width=True)
                
                # Batch actions
                selected_batch = st.selectbox("Select batch for actions:", [""] + df['batch_id'].tolist())
                if selected_batch:
                    batch_info = next((b for b in batches if b['batch_id'] == selected_batch), None)
                    if batch_info:
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"📊 View Progress", key=f"view_{selected_batch}"):
                                # Calculate progress
                                pair_ids = batch_info['pair_ids'].split(',') if batch_info['pair_ids'] else []
                                annotations = sheets_service.get_annotations(batch_info['annotator_id'])
                                annotated = sum(1 for pid in pair_ids if any(a['pair_id'] == pid for a in annotations))
                                
                                st.metric("Progress", f"{annotated}/{len(pair_ids)}")
                                st.progress(annotated / len(pair_ids) if pair_ids else 0)
                        with col2:
                            new_status = st.selectbox("Update Status", 
                                                    ["assigned", "in_progress", "completed"],
                                                    index=["assigned", "in_progress", "completed"].index(batch_info['status']))
                            if st.button("Update Status"):
                                completed_date = datetime.now().isoformat() if new_status == "completed" else None
                                sheets_service.update_batch_status(selected_batch, new_status, completed_date)
                                st.rerun()
            else:
                st.info("No batches found. Create your first batch above.")
        except Exception as e:
            st.error(f"Error loading batches: {e}")
    
    with tab2:
        st.subheader("Data Import")
        
        # Upload original JSON
        uploaded_file = st.file_uploader(
            "Upload original JSON data file",
            type=['json'],
            help="This will import pairs to Google Sheets and be used as the base for exports"
        )
        
        if uploaded_file is not None:
            try:
                original_data = json.load(uploaded_file)
                
                # Display info
                st.success(f"✅ Successfully loaded file: {uploaded_file.name}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Pairs", len(original_data.get('pairs', [])))
                with col2:
                    st.metric("Dataset", original_data.get('metadata', {}).get('name', 'Unknown'))
                with col3:
                    created = original_data.get('metadata', {}).get('created_at', 'Unknown')
                    st.metric("Created", created[:10] if len(created) > 10 else created)
                
                # Preview data
                with st.expander("👁️ Preview Data (first 10 pairs)"):
                    preview_df = pd.DataFrame(original_data.get('pairs', [])[:10])
                    st.dataframe(preview_df)
                
                # Option to push pairs to Google Sheets
                st.markdown("### Import to Google Sheets")
                if st.button("📤 Import Pairs to Google Sheets", type="primary"):
                    with st.spinner("Importing pairs to Google Sheets..."):
                        imported_count, pair_ids = sheets_service.import_pairs_from_json(original_data)
                        
                        if imported_count > 0:
                            st.success(f"✅ Imported {imported_count} pairs to Google Sheets")
                            
                            # Save original data to session state for exports
                            st.session_state.admin_original_data = original_data
                            
                            # Show sample of imported IDs
                            with st.expander("📋 Sample Imported Pair IDs"):
                                st.write(pair_ids[:10])
                        else:
                            st.error("Failed to import pairs")
                
            except Exception as e:
                st.error(f"Error loading file: {e}")
    
    with tab3:
        st.subheader("Annotator Management")
        
        # Get annotators from annotations
        annotations = sheets_service.get_annotations()
        if annotations:
            annotators = set(a['annotator_id'] for a in annotations)
            
            st.metric("Total Annotators", len(annotators))
            
            # Annotator statistics
            annotator_stats = []
            for annotator in sorted(annotators):
                ann_count = sum(1 for a in annotations if a['annotator_id'] == annotator)
                annotator_stats.append({
                    "annotator_id": annotator,
                    "annotation_count": ann_count,
                    "last_annotation": max([a['timestamp'] for a in annotations if a['annotator_id'] == annotator], default="Never")
                })
            
            df_stats = pd.DataFrame(annotator_stats)
            st.dataframe(df_stats, use_container_width=True)
        else:
            st.info("No annotations found. No annotators to display.")
    
    with tab4:
        st.subheader("Annotation Statistics")
        
        # Get all annotations
        annotations = sheets_service.get_annotations()
        
        if annotations:
            df = pd.DataFrame(annotations)
            
            # Overall statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Annotations", len(df))
            with col2:
                st.metric("Unique Annotators", df['annotator_id'].nunique())
            with col3:
                st.metric("Unique Pairs", df['pair_id'].nunique())
            with col4:
                avg_conf = df['confidence'].mean() if 'confidence' in df.columns else 0
                st.metric("Avg Confidence", f"{avg_conf:.1f}/5")
            
            # Distribution charts
            col1, col2 = st.columns(2)
            with col1:
                if 'causal_relation' in df.columns:
                    relation_dist = df['causal_relation'].value_counts().sort_index()
                    st.bar_chart(relation_dist)
                    st.caption("Causal Relation Distribution")
            
            with col2:
                if 'confidence' in df.columns:
                    conf_dist = df['confidence'].value_counts().sort_index()
                    st.bar_chart(conf_dist)
                    st.caption("Confidence Distribution")
            
            # Raw data
            with st.expander("📊 View Raw Data"):
                st.dataframe(df, use_container_width=True)
        else:
            st.info("No annotations found. Statistics will appear here once annotations are made.")

# =============================================================================
# APP SELECTOR
# =============================================================================

if __name__ == "__main__":
    # App mode selection
    st.sidebar.title("🔧 Navigation")
    app_mode = st.sidebar.radio(
        "Select mode:",
        ["Annotation Tool", "Admin Panel"],
        horizontal=True
    )
    
    if app_mode == "Annotation Tool":
        main()
    else:
        admin_interface()
