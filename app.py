
# """
# CausaFr - Complete Google Sheets Annotation Tool
# Streamlit Cloud Deployment Version
# With Enhanced Export and Performance Optimizations
# """

# import streamlit as st
# import pandas as pd
# import json
# import os
# import hashlib
# import uuid
# import re
# import time
# from datetime import datetime, timedelta
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
#         data = {
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
#         # Remove None values for cleaner JSON
#         return {k: v for k, v in data.items() if v is not None}

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
# # OPTIMIZED GOOGLE SHEETS MANAGER WITH CACHING
# # =============================================================================

# try:
#     import gspread
#     from google.oauth2.service_account import Credentials
#     GSHEETS_AVAILABLE = True
# except ImportError:
#     GSHEETS_AVAILABLE = False
#     st.error("⚠️ Install dependencies: pip install gspread google-auth")

# class OptimizedGoogleSheetsManager:
#     """Complete Google Sheets management with performance optimizations"""
    
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
        
#         # Cache system
#         self._cache = {
#             'datasets': {'data': None, 'timestamp': 0},
#             'pairs': {},  # dataset_id -> {'data': [], 'timestamp': 0}
#             'annotations': {},  # (username, dataset_id) -> {'data': [], 'timestamp': 0}
#             'all_annotations': {},  # dataset_id -> {'data': [], 'timestamp': 0}
#             'progress': {}  # (username, dataset_id) -> {'data': {}, 'timestamp': 0}
#         }
#         self._cache_ttl = 300  # 5 minutes cache TTL
    
#     def _is_cache_valid(self, cache_entry: Dict) -> bool:
#         """Check if cache entry is still valid"""
#         if cache_entry['data'] is None:
#             return False
#         return (time.time() - cache_entry['timestamp']) < self._cache_ttl
    
#     def _clear_cache(self, cache_key: str = None):
#         """Clear cache or specific cache entry"""
#         if cache_key:
#             if cache_key in self._cache:
#                 self._cache[cache_key] = {'data': None, 'timestamp': 0}
#         else:
#             for key in self._cache:
#                 self._cache[key] = {'data': None, 'timestamp': 0}
    
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
    
#     def _validate_pair_structure(self, pair: Dict) -> Tuple[bool, str]:
#         """Validate pair structure"""
#         # Required fields
#         required_fields = ['event1_text', 'event2_text']
#         for field in required_fields:
#             if field not in pair or not pair[field]:
#                 return False, f"Missing required field: {field}"
        
#         # Validate text length
#         if len(pair.get('event1_text', '')) > 1000 or len(pair.get('event2_text', '')) > 1000:
#             return False, "Text too long (max 1000 characters)"
        
#         # Validate label if present
#         if 'label' in pair and pair['label'] is not None:
#             try:
#                 label = int(pair['label'])
#                 if label not in [0, 1]:
#                     return False, "Label must be 0 or 1"
#             except (ValueError, TypeError):
#                 return False, "Invalid label format"
        
#         return True, ""
    
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
#             invalid_count = 0
            
#             # Batch rows for efficiency
#             batch_rows = []
            
#             # Import pairs
#             for i, pair in enumerate(pairs):
#                 # Validate pair structure
#                 is_valid, error_msg = self._validate_pair_structure(pair)
#                 if not is_valid:
#                     invalid_count += 1
#                     continue
                
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
                
#                 # Prepare row for batch insertion
#                 batch_rows.append([
#                     pair_id,
#                     dataset_id,
#                     pair.get('event1_text', '')[:500],
#                     pair.get('event2_text', '')[:500],
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
                
#                 # Batch insert every 50 rows
#                 if len(batch_rows) >= 50:
#                     self.dataset_pairs_sheet.append_rows(batch_rows)
#                     batch_rows = []
            
#             # Insert remaining rows
#             if batch_rows:
#                 self.dataset_pairs_sheet.append_rows(batch_rows)
            
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
            
#             # Clear cache for this dataset
#             self._clear_cache('datasets')
#             if dataset_id in self._cache['pairs']:
#                 del self._cache['pairs'][dataset_id]
            
#             # Log import results
#             if invalid_count > 0:
#                 self.error_message = f"Imported with warnings: {invalid_count} invalid pairs skipped"
            
#             return True, len(pairs), imported_count
            
#         except json.JSONDecodeError as e:
#             self.error_message = f"Invalid JSON: {str(e)}"
#             return False, 0, 0
#         except Exception as e:
#             self.error_message = str(e)
#             return False, 0, 0
    
#     def get_datasets(self, force_refresh: bool = False) -> List[DatasetMetadata]:
#         """Get all available datasets with caching"""
#         cache_entry = self._cache['datasets']
        
#         if not force_refresh and self._is_cache_valid(cache_entry):
#             return cache_entry['data']
        
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
            
#             self._cache['datasets'] = {
#                 'data': datasets,
#                 'timestamp': time.time()
#             }
#             return datasets
#         except Exception as e:
#             self.error_message = str(e)
#             return []
    
#     def get_dataset_pairs(self, dataset_id: str, force_refresh: bool = False) -> List[OriginalPair]:
#         """Get all pairs for a dataset with caching"""
#         if dataset_id not in self._cache['pairs']:
#             self._cache['pairs'][dataset_id] = {'data': None, 'timestamp': 0}
        
#         cache_entry = self._cache['pairs'][dataset_id]
        
#         if not force_refresh and self._is_cache_valid(cache_entry):
#             return cache_entry['data']
        
#         try:
#             # Use batch reading for better performance
#             all_values = self.dataset_pairs_sheet.get_all_values()
#             pairs = []
            
#             # Skip header row
#             for row in all_values[1:]:
#                 if len(row) < 2 or row[1] != dataset_id:  # row[1] = dataset column
#                     continue
                
#                 # Helper function to convert string to bool
#                 def str_to_bool(value):
#                     if isinstance(value, str):
#                         return value.strip().lower() in ['true', '1', 'yes', 'y']
#                     return bool(value)
                
#                 # Helper function to convert to int if possible
#                 def to_int(value):
#                     try:
#                         return int(value)
#                     except:
#                         return None
                
#                 # Map row indices to fields
#                 pairs.append(OriginalPair(
#                     pair_id=row[0] if len(row) > 0 else "",
#                     dataset=row[1] if len(row) > 1 else "",
#                     event1_text=row[2] if len(row) > 2 else "",
#                     event2_text=row[3] if len(row) > 3 else "",
#                     event1_id=row[4] if len(row) > 4 else "",
#                     event2_id=row[5] if len(row) > 5 else "",
#                     narrative_id=row[6] if len(row) > 6 else "",
#                     event1_category=row[7] if len(row) > 7 else "",
#                     event2_category=row[8] if len(row) > 8 else "",
#                     label=to_int(row[9]) if len(row) > 9 else None,
#                     is_hard_negative=str_to_bool(row[10]) if len(row) > 10 else False,
#                     event1_has_causal_cue=str_to_bool(row[11]) if len(row) > 11 else False,
#                     event1_causal_cue_type=row[12] if len(row) > 12 else None,
#                     event1_causal_cue_text=row[13] if len(row) > 13 else None,
#                     event1_has_temporal=str_to_bool(row[14]) if len(row) > 14 else False,
#                     event1_temporal_type=row[15] if len(row) > 15 else None,
#                     event1_temporal_text=row[16] if len(row) > 16 else None,
#                     event2_has_causal_cue=str_to_bool(row[17]) if len(row) > 17 else False,
#                     event2_causal_cue_type=row[18] if len(row) > 18 else None,
#                     event2_causal_cue_text=row[19] if len(row) > 19 else None,
#                     event2_has_temporal=str_to_bool(row[20]) if len(row) > 20 else False,
#                     event2_temporal_type=row[21] if len(row) > 21 else None,
#                     event2_temporal_text=row[22] if len(row) > 22 else None,
#                     pair_has_causal_cue=str_to_bool(row[23]) if len(row) > 23 else False,
#                     pair_has_temporal=str_to_bool(row[24]) if len(row) > 24 else False,
#                     row_index=int(row[25]) if len(row) > 25 and row[25] else 0
#                 ))
            
#             # Sort by row_index
#             pairs.sort(key=lambda x: x.row_index)
            
#             self._cache['pairs'][dataset_id] = {
#                 'data': pairs,
#                 'timestamp': time.time()
#             }
#             return pairs
#         except Exception as e:
#             self.error_message = str(e)
#             return []
    
#     def get_single_pair(self, dataset_id: str, pair_id: str) -> Optional[OriginalPair]:
#         """Get a single pair directly without loading all pairs"""
#         try:
#             # Try to find in cache first
#             if dataset_id in self._cache['pairs'] and self._cache['pairs'][dataset_id]['data']:
#                 pairs = self._cache['pairs'][dataset_id]['data']
#                 for pair in pairs:
#                     if pair.pair_id == pair_id:
#                         return pair
            
#             # If not in cache, search directly in Google Sheets
#             records = self.dataset_pairs_sheet.get_all_records()
#             for record in records:
#                 if record['dataset'] == dataset_id and record['pair_id'] == pair_id:
#                     # Convert record to OriginalPair
#                     def str_to_bool(value):
#                         if isinstance(value, str):
#                             return value.strip().lower() in ['true', '1', 'yes', 'y']
#                         return bool(value)
                    
#                     def to_int(value):
#                         try:
#                             return int(value)
#                         except:
#                             return None
                    
#                     return OriginalPair(
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
#                     )
#             return None
#         except Exception as e:
#             self.error_message = str(e)
#             return None
    
#     def search_pairs(self, dataset_id: str, query: str) -> List[OriginalPair]:
#         """Search pairs by text content"""
#         all_pairs = self.get_dataset_pairs(dataset_id)
        
#         if not query:
#             return all_pairs
        
#         query = query.lower()
#         results = []
        
#         for pair in all_pairs:
#             if (query in pair.event1_text.lower() or 
#                 query in pair.event2_text.lower() or
#                 query in str(pair.event1_id).lower() or
#                 query in str(pair.event2_id).lower() or
#                 query in pair.narrative_id.lower()):
#                 results.append(pair)
        
#         return results
    
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
            
#             # Clear cache
#             self._clear_cache()
            
#             return True
#         except Exception as e:
#             self.error_message = str(e)
#             return False
    
#     # ========== OPTIMIZED ANNOTATION MANAGEMENT ==========
    
#     def get_user_annotations(self, username: str, dataset_id: str = None, force_refresh: bool = False) -> List[UserAnnotation]:
#         """Get annotations for a user with caching"""
#         cache_key = f"{username}_{dataset_id}" if dataset_id else f"{username}_all"
        
#         if cache_key not in self._cache['annotations']:
#             self._cache['annotations'][cache_key] = {'data': None, 'timestamp': 0}
        
#         cache_entry = self._cache['annotations'][cache_key]
        
#         if not force_refresh and self._is_cache_valid(cache_entry):
#             return cache_entry['data']
        
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
            
#             self._cache['annotations'][cache_key] = {
#                 'data': annotations,
#                 'timestamp': time.time()
#             }
#             return annotations
#         except Exception as e:
#             self.error_message = str(e)
#             return []
    
#     def get_user_annotation_for_pair(self, username: str, pair_id: str) -> Optional[UserAnnotation]:
#         """Get user's annotation for a specific pair (optimized)"""
#         # Check cache first
#         cache_key = f"{username}_all"
#         if cache_key in self._cache['annotations'] and self._cache['annotations'][cache_key]['data']:
#             annotations = self._cache['annotations'][cache_key]['data']
#             for ann in annotations:
#                 if ann.pair_id == pair_id:
#                     return ann
        
#         # If not in cache, search directly
#         try:
#             # Use Google Sheets API to find specific annotation
#             cell = self.annotations_sheet.find(pair_id)
#             if cell:
#                 # Get rows around this cell to find the user's annotation
#                 start_row = max(2, cell.row - 10)
#                 end_row = cell.row + 10
#                 rows = self.annotations_sheet.get(f"A{start_row}:P{end_row}")
                
#                 for row in rows:
#                     if len(row) >= 4 and row[1] == pair_id and row[3] == username:  # row[1] = pair_id, row[3] = username
#                         return UserAnnotation(
#                             id=row[0] if len(row) > 0 else "",
#                             pair_id=row[1] if len(row) > 1 else "",
#                             dataset=row[2] if len(row) > 2 else "",
#                             username=row[3] if len(row) > 3 else "",
#                             event1_text=row[4] if len(row) > 4 else "",
#                             event2_text=row[5] if len(row) > 5 else "",
#                             cue1=int(row[6]) if len(row) > 6 and row[6] else 0,
#                             cue2=int(row[7]) if len(row) > 7 and row[7] else 0,
#                             label=int(row[8]) if len(row) > 8 and row[8] else None,
#                             confidence=int(row[9]) if len(row) > 9 and row[9] else 3,
#                             notes=row[10] if len(row) > 10 else "",
#                             annotated_at=row[11] if len(row) > 11 else "",
#                             event1_id=row[12] if len(row) > 12 else "",
#                             event2_id=row[13] if len(row) > 13 else ""
#                         )
#             return None
#         except Exception as e:
#             # Fall back to searching in all records
#             annotations = self.get_user_annotations(username)
#             for ann in annotations:
#                 if ann.pair_id == pair_id:
#                     return ann
#             return None
    
#     def save_annotation(self, annotation: UserAnnotation) -> str:
#         """Save an annotation and update cache"""
#         try:
#             ann_id = str(uuid.uuid4())[:8]
            
#             # Generate hash for duplicate detection
#             hash_string = f"{annotation.pair_id}_{annotation.username}_{annotation.annotated_at}"
#             annotation_hash = hashlib.md5(hash_string.encode()).hexdigest()[:8]
            
#             # Check if annotation already exists
#             existing = self.get_user_annotation_for_pair(annotation.username, annotation.pair_id)
            
#             if existing:
#                 # Update existing annotation
#                 # Find the row in the sheet
#                 try:
#                     cell = self.annotations_sheet.find(annotation.pair_id)
#                     if cell:
#                         # Get all annotations for this pair
#                         annotations = self.annotations_sheet.get_all_records()
#                         for i, ann in enumerate(annotations):
#                             if ann['pair_id'] == annotation.pair_id and ann['username'] == annotation.username:
#                                 row_num = i + 2  # +2 because 1-indexed and header row
#                                 self.annotations_sheet.update(f'A{row_num}:P{row_num}', [[
#                                     ann_id,
#                                     annotation.pair_id,
#                                     annotation.dataset,
#                                     annotation.username,
#                                     annotation.event1_text[:500],
#                                     annotation.event2_text[:500],
#                                     annotation.cue1,
#                                     annotation.cue2,
#                                     annotation.label if annotation.label is not None else "",
#                                     annotation.confidence,
#                                     annotation.notes[:200],
#                                     annotation.annotated_at or datetime.now().isoformat(),
#                                     annotation.event1_id,
#                                     annotation.event2_id,
#                                     "0",
#                                     annotation_hash
#                                 ]])
#                                 break
#                 except:
#                     # If find fails, use alternative method
#                     annotations = self.annotations_sheet.get_all_records()
#                     for i, ann in enumerate(annotations):
#                         if ann['pair_id'] == annotation.pair_id and ann['username'] == annotation.username:
#                             row_num = i + 2
#                             self.annotations_sheet.update(f'A{row_num}:P{row_num}', [[
#                                 ann_id,
#                                 annotation.pair_id,
#                                 annotation.dataset,
#                                 annotation.username,
#                                 annotation.event1_text[:500],
#                                 annotation.event2_text[:500],
#                                 annotation.cue1,
#                                 annotation.cue2,
#                                 annotation.label if annotation.label is not None else "",
#                                 annotation.confidence,
#                                 annotation.notes[:200],
#                                 annotation.annotated_at or datetime.now().isoformat(),
#                                 annotation.event1_id,
#                                 annotation.event2_id,
#                                 "0",
#                                 annotation_hash
#                             ]])
#                             break
#             else:
#                 # Create new annotation
#                 self.annotations_sheet.append_row([
#                     ann_id,
#                     annotation.pair_id,
#                     annotation.dataset,
#                     annotation.username,
#                     annotation.event1_text[:500],
#                     annotation.event2_text[:500],
#                     annotation.cue1,
#                     annotation.cue2,
#                     annotation.label if annotation.label is not None else "",
#                     annotation.confidence,
#                     annotation.notes[:200],
#                     annotation.annotated_at or datetime.now().isoformat(),
#                     annotation.event1_id,
#                     annotation.event2_id,
#                     "0",
#                     annotation_hash
#                 ])
            
#             # Clear annotation cache for this user/dataset
#             cache_key = f"{annotation.username}_{annotation.dataset}"
#             if cache_key in self._cache['annotations']:
#                 del self._cache['annotations'][cache_key]
            
#             # Clear all_annotations cache for this dataset
#             if annotation.dataset in self._cache['all_annotations']:
#                 del self._cache['all_annotations'][annotation.dataset]
            
#             return ann_id
#         except Exception as e:
#             self.error_message = str(e)
#             return ""
    
#     def get_all_annotations(self, dataset_id: str = None, force_refresh: bool = False) -> List[Dict]:
#         """Get all annotations with caching"""
#         cache_key = f"all_{dataset_id}" if dataset_id else "all"
        
#         if cache_key not in self._cache['all_annotations']:
#             self._cache['all_annotations'][cache_key] = {'data': None, 'timestamp': 0}
        
#         cache_entry = self._cache['all_annotations'][cache_key]
        
#         if not force_refresh and self._is_cache_valid(cache_entry):
#             return cache_entry['data']
        
#         try:
#             records = self.annotations_sheet.get_all_records()
#             if dataset_id:
#                 filtered = [r for r in records if r['dataset'] == dataset_id]
#                 self._cache['all_annotations'][cache_key] = {
#                     'data': filtered,
#                     'timestamp': time.time()
#                 }
#                 return filtered
#             else:
#                 self._cache['all_annotations'][cache_key] = {
#                     'data': records,
#                     'timestamp': time.time()
#                 }
#                 return records
#         except Exception as e:
#             self.error_message = str(e)
#             return []
    
#     def get_annotations_by_pair(self, pair_id: str) -> List[UserAnnotation]:
#         """Get all annotations for a specific pair"""
#         try:
#             # Check cache first
#             for cache_key in self._cache['annotations']:
#                 if self._cache['annotations'][cache_key]['data']:
#                     annotations = []
#                     for ann in self._cache['annotations'][cache_key]['data']:
#                         if ann.pair_id == pair_id:
#                             annotations.append(ann)
#                     if annotations:
#                         return annotations
            
#             # If not in cache, search directly
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
    
#     # ========== OPTIMIZED PROGRESS MANAGEMENT ==========
    
#     def get_user_progress(self, username: str, dataset_id: str, force_refresh: bool = False) -> Dict:
#         """Get user progress with caching"""
#         cache_key = f"{username}_{dataset_id}"
        
#         if cache_key not in self._cache['progress']:
#             self._cache['progress'][cache_key] = {'data': None, 'timestamp': 0}
        
#         cache_entry = self._cache['progress'][cache_key]
        
#         if not force_refresh and self._is_cache_valid(cache_entry):
#             return cache_entry['data']
        
#         try:
#             records = self.progress_sheet.get_all_records()
            
#             for record in records:
#                 if record['username'] == username and record['dataset'] == dataset_id:
#                     progress_data = {
#                         'current_index': int(record['current_index']) if record['current_index'] else 0,
#                         'total_annotated': int(record['total_annotated']) if record['total_annotated'] else 0,
#                         'last_updated': record['last_updated'],
#                         'last_pair_id': record.get('last_pair_id', ''),
#                         'completion_rate': record.get('completion_rate', '0%')
#                     }
                    
#                     self._cache['progress'][cache_key] = {
#                         'data': progress_data,
#                         'timestamp': time.time()
#                     }
#                     return progress_data
            
#             # Return default if not found
#             default_data = {
#                 'current_index': 0,
#                 'total_annotated': 0,
#                 'last_updated': '',
#                 'last_pair_id': '',
#                 'completion_rate': '0%'
#             }
            
#             self._cache['progress'][cache_key] = {
#                 'data': default_data,
#                 'timestamp': time.time()
#             }
#             return default_data
#         except Exception as e:
#             self.error_message = str(e)
#             return {'current_index': 0, 'total_annotated': 0, 'last_updated': ''}
    
#     def update_progress(self, username: str, dataset_id: str, current_index: int, 
#                        total_annotated: int, last_pair_id: str = "") -> bool:
#         """Update user progress and clear cache"""
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
            
#             # Clear progress cache
#             cache_key = f"{username}_{dataset_id}"
#             if cache_key in self._cache['progress']:
#                 del self._cache['progress'][cache_key]
            
#             return True
#         except Exception as e:
#             self.error_message = str(e)
#             return False
    
#     # ========== ENHANCED EXPORT FUNCTIONALITY ==========
    
#     def _calculate_consensus(self, annotations: List[Dict]) -> Dict:
#         """Calculate consensus metrics"""
#         if not annotations:
#             return None
        
#         labels = [int(a['label']) for a in annotations if a.get('label') is not None]
#         confidences = [int(a.get('confidence', 3)) for a in annotations]
        
#         if not labels:
#             return None
        
#         consensus = 1 if sum(labels) / len(labels) >= 0.5 else 0
#         agreement = sum(1 for l in labels if l == consensus) / len(labels)
        
#         return {
#             'consensus_label': consensus,
#             'agreement_rate': agreement,
#             'total_votes': len(labels),
#             'confidence_avg': sum(confidences) / len(confidences),
#             'distribution': {
#                 'causal': sum(labels),
#                 'non_causal': len(labels) - sum(labels)
#             }
#         }
    
#     def export_annotated_dataset(self, dataset_id: str, mode: str = "replace") -> Optional[Dict]:
#         """
#         Export annotated dataset with different modes:
#         - "replace": Replace original fields with annotated values (for training)
#         - "append": Keep original and add annotations as separate field (for review)
#         - "consensus": Use majority vote consensus
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
            
#             # Build exported pairs based on mode
#             exported_pairs = []
            
#             for original_pair in original_pairs:
#                 # Start with original pair data
#                 pair_dict = original_pair.to_dict()
                
#                 # Get annotations for this pair if they exist
#                 pair_annotations = annotations_by_pair.get(original_pair.pair_id, [])
                
#                 if mode == "replace":
#                     # REPLACE MODE: For training compatibility
#                     if pair_annotations:
#                         if len(pair_annotations) == 1:
#                             # Single annotation - use it
#                             ann = pair_annotations[0]
#                             # Update only the label field
#                             if ann.get('label') is not None:
#                                 pair_dict['label'] = int(ann['label'])
                            
#                             # Update causal cue flags based on annotation
#                             pair_dict['event1_has_causal_cue'] = bool(int(ann.get('cue1', 0)))
#                             pair_dict['event2_has_causal_cue'] = bool(int(ann.get('cue2', 0)))
                            
#                             # Add annotation metadata as separate fields if needed
#                             pair_dict['annotated_by'] = ann['username']
#                             pair_dict['annotation_confidence'] = int(ann.get('confidence', 3))
#                             pair_dict['annotation_notes'] = ann.get('notes', '')
#                             pair_dict['annotated_at'] = ann.get('annotated_at', '')
                        
#                         elif len(pair_annotations) > 1:
#                             # Multiple annotations - use consensus
#                             consensus = self._calculate_consensus(pair_annotations)
#                             if consensus:
#                                 pair_dict['label'] = consensus['consensus_label']
                                
#                                 # Add consensus metadata
#                                 pair_dict['consensus_label'] = consensus['consensus_label']
#                                 pair_dict['agreement_rate'] = consensus['agreement_rate']
#                                 pair_dict['total_annotators'] = consensus['total_votes']
#                                 pair_dict['annotation_summary'] = consensus
                    
#                     # Remove any existing annotations field
#                     if 'annotations' in pair_dict:
#                         del pair_dict['annotations']
                
#                 elif mode == "append":
#                     # APPEND MODE: Keep original and add annotations as separate field
#                     if pair_annotations:
#                         pair_dict['annotations'] = []
#                         for ann in pair_annotations:
#                             pair_dict['annotations'].append({
#                                 'username': ann['username'],
#                                 'cue1': bool(int(ann.get('cue1', 0))),
#                                 'cue2': bool(int(ann.get('cue2', 0))),
#                                 'label': int(ann.get('label', 0)) if ann.get('label') is not None else None,
#                                 'confidence': int(ann.get('confidence', 3)),
#                                 'notes': ann.get('notes', ''),
#                                 'annotated_at': ann.get('annotated_at', '')
#                             })
                
#                 elif mode == "consensus":
#                     # CONSENSUS MODE: Only update if strong consensus exists
#                     if pair_annotations:
#                         consensus = self._calculate_consensus(pair_annotations)
#                         if consensus and consensus['agreement_rate'] >= 0.7:
#                             pair_dict['label'] = consensus['consensus_label']
#                             pair_dict['consensus_confidence'] = consensus['agreement_rate']
                
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
#                     'export_mode': mode,
#                     'export_format': 'annotated_replaced' if mode == "replace" else 'annotated_appended'
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
    
#     def export_training_dataset(self, dataset_id: str, username: str = None) -> Optional[List[Dict]]:
#         """
#         Export for training - replaces original labels with user's annotations
#         Returns list of pairs in original format with updated labels
#         """
#         try:
#             # Get original pairs
#             original_pairs = self.get_dataset_pairs(dataset_id)
            
#             # Get annotations
#             if username:
#                 # Single user export
#                 user_annotations = self.get_user_annotations(username, dataset_id)
#                 ann_dict = {ann.pair_id: ann for ann in user_annotations}
#             else:
#                 # Multi-user consensus
#                 all_annotations = self.get_all_annotations(dataset_id)
#                 # Group by pair_id for consensus
#                 ann_by_pair = {}
#                 for ann in all_annotations:
#                     pair_id = ann['pair_id']
#                     if pair_id not in ann_by_pair:
#                         ann_by_pair[pair_id] = []
#                     ann_by_pair[pair_id].append(ann)
            
#             training_pairs = []
            
#             for pair in original_pairs:
#                 pair_data = pair.to_dict()
                
#                 if username:
#                     # Single user mode
#                     if pair.pair_id in ann_dict:
#                         ann = ann_dict[pair.pair_id]
#                         if ann.label is not None:
#                             pair_data['label'] = ann.label
#                 else:
#                     # Consensus mode
#                     if pair.pair_id in ann_by_pair:
#                         annotations = ann_by_pair[pair.pair_id]
#                         labels = [int(a['label']) for a in annotations if a.get('label') is not None]
#                         if labels:
#                             # Majority vote
#                             pair_data['label'] = 1 if sum(labels) / len(labels) >= 0.5 else 0
                
#                 # Clean up any annotation fields that might have been added
#                 for key in list(pair_data.keys()):
#                     if key.startswith('annotation_') or key in ['annotations', 'annotated_by', 'consensus_label', 'agreement_rate']:
#                         if key in pair_data:
#                             del pair_data[key]
                
#                 training_pairs.append(pair_data)
            
#             return training_pairs
            
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
#                 datasets = [d for d in self.get_datasets() if d.dataset_id == dataset_id]
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
    
#     def create_backup(self) -> str:
#         """Create a backup of all data"""
#         try:
#             backup_data = {
#                 'timestamp': datetime.now().isoformat(),
#                 'users': self.users_sheet.get_all_records(),
#                 'datasets': self.datasets_sheet.get_all_records(),
#                 'pairs_count': len(self.dataset_pairs_sheet.get_all_records()),
#                 'annotations_count': len(self.annotations_sheet.get_all_records()),
#                 'progress_count': len(self.progress_sheet.get_all_records())
#             }
            
#             backup_json = json.dumps(backup_data, indent=2)
#             return backup_json
#         except Exception as e:
#             self.error_message = str(e)
#             return ""
    
#     def calculate_annotator_quality(self, username: str) -> Dict:
#         """Calculate annotator quality metrics"""
#         annotations = self.get_user_annotations(username)
        
#         if not annotations:
#             return None
        
#         # Get all annotations for comparison
#         all_annotations = self.get_all_annotations()
        
#         # Group by pair_id
#         pair_annotations = {}
#         for ann in all_annotations:
#             pair_id = ann['pair_id']
#             if pair_id not in pair_annotations:
#                 pair_annotations[pair_id] = []
#             pair_annotations[pair_id].append(ann)
        
#         # Calculate agreement
#         user_agreements = []
#         for ann in annotations:
#             if ann.pair_id in pair_annotations:
#                 other_anns = [a for a in pair_annotations[ann.pair_id] 
#                              if a['username'] != username]
#                 if len(other_anns) >= 2:  # Need at least 2 other annotators
#                     # Calculate consensus among others
#                     labels = [int(a['label']) for a in other_anns if a.get('label') is not None]
#                     if labels:
#                         consensus = 1 if sum(labels) / len(labels) >= 0.5 else 0
#                         if ann.label == consensus:
#                             user_agreements.append(1)
#                         else:
#                             user_agreements.append(0)
        
#         quality_metrics = {
#             'total_annotations': len(annotations),
#             'avg_confidence': sum(a.confidence for a in annotations) / len(annotations),
#             'causal_ratio': sum(1 for a in annotations if a.label == 1) / len(annotations) if annotations else 0,
#             'agreement_rate': sum(user_agreements) / len(user_agreements) if user_agreements else 0,
#             'datasets_annotated': len(set(a.dataset for a in annotations))
#         }
        
#         return quality_metrics

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

# # Custom CSS with enhancements
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
#         line-height: 1.6;
#     }
#     .sentence-box-causal {
#         background: #e8f5e9;
#         border-left: 4px solid #4caf50;
#     }
#     .sentence-box-effect {
#         background: #e3f2fd;
#         border-left: 4px solid #2196f3;
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
#     .tag-danger {
#         background: #ef4444;
#         color: white;
#     }
#     .keyboard-shortcut {
#         background: #e5e7eb;
#         border-radius: 4px;
#         padding: 2px 6px;
#         font-family: monospace;
#         font-size: 0.9em;
#         margin: 0 2px;
#     }
#     .export-card {
#         background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%);
#         border-radius: 10px;
#         padding: 1.5rem;
#         margin: 1rem 0;
#     }
#     .cache-indicator {
#         position: fixed;
#         bottom: 10px;
#         right: 10px;
#         background: rgba(0,0,0,0.7);
#         color: white;
#         padding: 5px 10px;
#         border-radius: 5px;
#         font-size: 0.8em;
#         z-index: 1000;
#     }
# </style>
# """, unsafe_allow_html=True)

# # Add keyboard shortcuts script
# st.markdown("""
# <script>
# document.addEventListener('keydown', function(e) {
#     // Only trigger if not in an input field
#     if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
#         if (e.key === 'ArrowLeft' || e.key === 'a') {
#             // Previous button
#             const prevBtn = document.querySelector('button:has(div:contains("⬅️"))');
#             if (prevBtn && !prevBtn.disabled) prevBtn.click();
#         } else if (e.key === 'ArrowRight' || e.key === 'd') {
#             // Next button
#             const nextBtn = document.querySelector('button:has(div:contains("➡️"))');
#             if (nextBtn && !nextBtn.disabled) nextBtn.click();
#         } else if (e.key === '1') {
#             // Mark as causal
#             const yesBtn = document.querySelector('input[value="1"]');
#             if (yesBtn) yesBtn.click();
#         } else if (e.key === '0') {
#             // Mark as non-causal
#             const noBtn = document.querySelector('input[value="0"]');
#             if (noBtn) noBtn.click();
#         } else if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
#             // Save annotation (Ctrl+S or Cmd+S)
#             e.preventDefault();
#             const saveBtn = document.querySelector('button:has(div:contains("💾 Enregistrer"))');
#             if (saveBtn) saveBtn.click();
#         } else if (e.key === ' ') {
#             // Space for save and next
#             e.preventDefault();
#             const saveNextBtn = document.querySelector('button:has(div:contains("💾 & ⏭️"))');
#             if (saveNextBtn) saveNextBtn.click();
#         }
#     }
# });
# </script>
# """, unsafe_allow_html=True)

# # Initialize session state with optimization flags
# if 'authenticated' not in st.session_state:
#     st.session_state.authenticated = False
#     st.session_state.username = None
#     st.session_state.gsheets = None
#     st.session_state.current_dataset = None
#     st.session_state.pair_index = 0
#     st.session_state.current_pairs = []
#     st.session_state.current_pairs_cache = {'data': None, 'timestamp': 0}
#     st.session_state.user_annotations_cache = {}
#     st.session_state.user_annotation_count = 0
#     st.session_state.is_admin = False
#     st.session_state.last_activity = datetime.now()
#     st.session_state.performance_monitor = {'last_load_time': 0, 'load_count': 0}

# # Session timeout check
# def check_session_timeout():
#     if 'last_activity' in st.session_state:
#         elapsed = (datetime.now() - st.session_state.last_activity).seconds
#         if elapsed > 3600:  # 1 hour timeout
#             st.warning("Session expirée. Veuillez vous reconnecter.")
#             for key in list(st.session_state.keys()):
#                 del st.session_state[key]
#             st.rerun()
    
#     st.session_state.last_activity = datetime.now()

# # Check configuration
# if GOOGLE_CONFIG is None:
#     st.error("Google Sheets configuration not found. Please check your secrets.")
#     st.stop()

# # Initialize optimized Google Sheets manager
# if st.session_state.gsheets is None:
#     st.session_state.gsheets = OptimizedGoogleSheetsManager()
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
#                         st.session_state.last_activity = datetime.now()
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
    
#     check_session_timeout()
    
#     st.markdown("""
#     <div class="main-header">
#         <h1>📁 Gestion des Datasets</h1>
#         <p>Importez et gérez vos datasets JSON dans Google Sheets</p>
#         <p style="color: #f59e0b; font-size: 0.9rem;">👑 Section Administrateur</p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     gsheets = st.session_state.gsheets
    
#     tab1, tab2, tab3, tab4 = st.tabs(["📤 Importer Dataset", "📋 Datasets Disponibles", "🧠 Export Training", "🗑️ Gestion"])
    
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
#                             st.session_state.current_pairs = []  # Clear cache to force reload
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
#                             with st.expander("Options d'export"):
#                                 export_mode = st.selectbox(
#                                     "Format",
#                                     ["Replace (for training)", "Append (for review)", "Consensus"],
#                                     key=f"mode_{dataset.dataset_id}"
#                                 )
                                
#                                 mode_map = {
#                                     "Replace (for training)": "replace",
#                                     "Append (for review)": "append",
#                                     "Consensus": "consensus"
#                                 }
                                
#                                 export_data = gsheets.export_annotated_dataset(dataset.dataset_id, mode=mode_map[export_mode])
#                                 if export_data:
#                                     json_str = json.dumps(export_data['pairs'], indent=2, ensure_ascii=False)
#                                     st.download_button(
#                                         "⬇️ Télécharger JSON complet",
#                                         json_str,
#                                         file_name=f"causafr_{dataset.dataset_id}_{mode_map[export_mode]}_{datetime.now().strftime('%Y%m%d')}.json",
#                                         mime="application/json",
#                                         key=f"download_{dataset.dataset_id}"
#                                     )
                                    
#                                     # Show statistics
#                                     st.json(export_data['statistics'])
#                                 else:
#                                     st.error(f"Erreur: {gsheets.error_message}")
    
#     with tab3:
#         st.markdown("### 🧠 Export pour Entraînement")
#         st.markdown("""
#         <div class="export-card">
#             <h4>📊 Export Format</h4>
#             <p>Exportez des données prêtes pour l'entraînement de modèle:</p>
#             <ul>
#                 <li><strong>Structure originale</strong> préservée</li>
#                 <li><strong>Labels remplacés</strong> par annotations</li>
#                 <li><strong>Pas de champs supplémentaires</strong></li>
#                 <li><strong>JSON identique</strong> à l'import original</li>
#             </ul>
#         </div>
#         """, unsafe_allow_html=True)
        
#         datasets = gsheets.get_datasets()
#         if not datasets:
#             st.info("Aucun dataset disponible")
#             return
        
#         dataset_options = {f"{d.name} ({d.pair_count} paires)": d.dataset_id for d in datasets}
#         selected_display = st.selectbox("Sélectionner un dataset", list(dataset_options.keys()))
#         selected_id = dataset_options[selected_display]
        
#         selected_dataset = None
#         for ds in datasets:
#             if ds.dataset_id == selected_id:
#                 selected_dataset = ds
#                 break
        
#         if selected_dataset:
#             # Export options
#             col1, col2 = st.columns(2)
#             with col1:
#                 export_mode = st.selectbox(
#                     "Mode d'export",
#                     ["Consensus (tous les utilisateurs)", "Utilisateur spécifique"],
#                     help="Consensus: vote majoritaire de tous les annotateurs. Spécifique: annotations d'un utilisateur"
#                 )
            
#             with col2:
#                 if export_mode == "Utilisateur spécifique":
#                     users = gsheets.get_all_users()
#                     export_user = st.selectbox("Annotateur", users)
#                 else:
#                     export_user = None
            
#             # Statistics
#             annotations = gsheets.get_all_annotations(selected_id)
#             unique_users = len(set(a['username'] for a in annotations))
            
#             st.markdown("#### 📊 Statistiques du dataset")
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 st.metric("Paires totales", selected_dataset.pair_count)
#             with col2:
#                 st.metric("Annotations", len(annotations))
#             with col3:
#                 st.metric("Annotateurs", unique_users)
            
#             # Export button
#             if st.button("🎯 Exporter pour l'entraînement", type="primary"):
#                 with st.spinner("Génération de l'export..."):
#                     if export_user:
#                         training_data = gsheets.export_training_dataset(selected_id, export_user)
#                         user_label = export_user
#                     else:
#                         training_data = gsheets.export_training_dataset(selected_id)
#                         user_label = "consensus"
                    
#                     if training_data:
#                         # Count updated labels
#                         original_pairs = gsheets.get_dataset_pairs(selected_id)
#                         updated_count = 0
#                         for i, pair in enumerate(training_data):
#                             if i < len(original_pairs):
#                                 if pair.get('label') != original_pairs[i].label:
#                                     updated_count += 1
                        
#                         json_str = json.dumps(training_data, indent=2, ensure_ascii=False)
                        
#                         st.download_button(
#                             "⬇️ Télécharger JSON d'entraînement",
#                             json_str,
#                             file_name=f"causafr_training_{selected_id}_{user_label}_{datetime.now().strftime('%Y%m%d')}.json",
#                             mime="application/json",
#                             key=f"training_download_{selected_id}"
#                         )
                        
#                         st.success(f"✅ {updated_count}/{len(training_data)} labels mis à jour")
                        
#                         # Show sample
#                         with st.expander("👁️ Aperçu des données"):
#                             st.json(training_data[0] if training_data else {})
#                     else:
#                         st.error(f"Erreur: {gsheets.error_message}")
    
#     with tab4:
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
            
#             # Backup option
#             st.markdown("#### 💾 Sauvegarde")
#             if st.button("📋 Créer une sauvegarde", key=f"backup_{selected_id}"):
#                 backup = gsheets.create_backup()
#                 if backup:
#                     st.download_button(
#                         "⬇️ Télécharger la sauvegarde",
#                         backup,
#                         file_name=f"causafr_backup_{selected_id}_{datetime.now().strftime('%Y%m%d')}.json",
#                         mime="application/json"
#                     )
#                 else:
#                     st.error(f"Erreur: {gsheets.error_message}")
            
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

# def optimized_annotate_page():
#     """Optimized annotation page with reduced latency"""
#     check_session_timeout()
    
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
        
#         # Check if dataset changed
#         if st.session_state.current_dataset != selected_id:
#             st.session_state.current_dataset = selected_id
#             st.session_state.pair_index = 0
#             st.session_state.current_pairs = []
#             st.session_state.current_pairs_cache = {'data': None, 'timestamp': 0}
        
#         # Search functionality
#         with st.expander("🔍 Recherche", expanded=False):
#             search_query = st.text_input("Rechercher dans le texte")
#             if search_query:
#                 search_results = gsheets.search_pairs(selected_id, search_query)
#                 if search_results:
#                     st.info(f"📋 {len(search_results)} résultats trouvés")
#                     for i, pair in enumerate(search_results[:5]):
#                         if st.button(f"{pair.event1_text[:50]}...", key=f"search_{i}_{pair.pair_id}"):
#                             st.session_state.pair_index = pair.row_index
#                             st.rerun()
#                 else:
#                     st.warning("Aucun résultat")
        
#         # Load dataset pairs ONCE and cache in session state
#         if not st.session_state.current_pairs:
#             start_time = time.time()
#             with st.spinner("Chargement initial des paires..."):
#                 pairs = gsheets.get_dataset_pairs(selected_id)
#                 if not pairs:
#                     st.error("❌ Erreur de chargement des paires")
#                     return
#                 st.session_state.current_pairs = pairs
#                 st.session_state.current_pairs_cache = {
#                     'data': pairs,
#                     'timestamp': time.time()
#                 }
#                 load_time = time.time() - start_time
#                 st.session_state.performance_monitor['last_load_time'] = load_time
#                 st.session_state.performance_monitor['load_count'] = 1
#                 st.success(f"✅ {len(pairs)} paires chargées en {load_time:.2f}s")
        
#         pairs = st.session_state.current_pairs
#         total_pairs = len(pairs)
        
#         # Load progress - cached
#         progress = gsheets.get_user_progress(username, selected_id)
#         current_index = progress.get('current_index', 0)
        
#         if st.session_state.pair_index == 0 and current_index > 0:
#             st.session_state.pair_index = min(current_index, total_pairs - 1)
        
#         # Load user annotations - cached (but do it in background)
#         if 'user_annotations_loaded' not in st.session_state:
#             st.session_state.user_annotations_loaded = False
        
#         if not st.session_state.user_annotations_loaded:
#             # Load annotations once
#             user_annotations = gsheets.get_user_annotations(username, selected_id)
#             st.session_state.user_annotations_cache = {ann.pair_id: ann for ann in user_annotations}
#             st.session_state.user_annotation_count = len(user_annotations)
#             st.session_state.user_annotations_loaded = True
        
#         # Statistics from cache
#         annotated_count = st.session_state.user_annotation_count
#         causal_count = sum(1 for ann in st.session_state.user_annotations_cache.values() if ann.label == 1)
#         non_causal_count = sum(1 for ann in st.session_state.user_annotations_cache.values() if ann.label == 0)
        
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
        
#         # Keyboard shortcuts help
#         with st.expander("⌨️ Raccourcis clavier", expanded=False):
#             st.markdown("""
#             - **← / A** : Paire précédente
#             - **→ / D** : Paire suivante  
#             - **1** : Marquer comme causal
#             - **0** : Marquer comme non-causal
#             - **Ctrl+S / Cmd+S** : Sauvegarder
#             - **Espace** : Sauvegarder et suivant
#             """)
        
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
#                 if pair_id not in st.session_state.user_annotations_cache:
#                     st.session_state.pair_index = i
#                     st.rerun()
#                     break
        
#         # Export section
#         st.markdown("---")
#         with st.expander("📥 Export", expanded=False):
#             export_mode = st.selectbox(
#                 "Format d'export",
#                 ["Replace (pour entraînement)", "Append (pour revue)", "Consensus"],
#                 help="Replace: Met à jour les labels directement. Append: Garde les annotations séparées."
#             )
            
#             mode_map = {
#                 "Replace (pour entraînement)": "replace",
#                 "Append (pour revue)": "append",
#                 "Consensus": "consensus"
#             }
            
#             if st.button("📤 Exporter ce dataset", use_container_width=True):
#                 export_data = gsheets.export_annotated_dataset(selected_id, mode=mode_map[export_mode])
#                 if export_data:
#                     json_str = json.dumps(export_data['pairs'], indent=2, ensure_ascii=False)
                    
#                     # Create download button
#                     st.download_button(
#                         "⬇️ Télécharger JSON",
#                         json_str,
#                         file_name=f"causafr_{selected_id}_{mode_map[export_mode]}_{datetime.now().strftime('%Y%m%d')}.json",
#                         mime="application/json",
#                         use_container_width=True
#                     )
                    
#                     # Show statistics
#                     with st.expander("📊 Statistiques d'export"):
#                         st.json(export_data['statistics'])
#                 else:
#                     st.error(f"Erreur: {gsheets.error_message}")
        
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
    
#     # Performance indicator
#     if st.session_state.performance_monitor['load_count'] > 0:
#         st.markdown(f'<div class="cache-indicator">⚡ Cache: {len(pairs)} paires | Temps: {st.session_state.performance_monitor["last_load_time"]:.2f}s</div>', unsafe_allow_html=True)
    
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
    
#     # Check if already annotated - OPTIMIZED (from cache)
#     existing_annotation = st.session_state.user_annotations_cache.get(current_pair.pair_id)
    
#     if existing_annotation:
#         label_text = "✅ Causal" if existing_annotation.label == 1 else "❌ Non causal" if existing_annotation.label == 0 else "❓ Non décidé"
#         st.markdown(f"""
#         <div class="alert alert-warning">
#             ✏️ <strong>Déjà annotée</strong> le {existing_annotation.annotated_at[:16]}
#             (Confiance: {existing_annotation.confidence}/5 - {label_text})
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
#         st.markdown(f'<div class="sentence-box sentence-box-causal">{current_pair.event1_text}</div>', unsafe_allow_html=True)
#         cue1_key = f"cue1_{current_pair.pair_id}"
#         if cue1_key not in st.session_state:
#             st.session_state[cue1_key] = existing_annotation.cue1 if existing_annotation else False
#         cue1 = st.checkbox("Marqueur causal explicite", 
#                           value=st.session_state[cue1_key],
#                           key=cue1_key)
    
#     with col2:
#         st.markdown("#### 🟢 Événement 2 (Effet)")
#         st.markdown(f'<div class="sentence-box sentence-box-effect">{current_pair.event2_text}</div>', unsafe_allow_html=True)
#         cue2_key = f"cue2_{current_pair.pair_id}"
#         if cue2_key not in st.session_state:
#             st.session_state[cue2_key] = existing_annotation.cue2 if existing_annotation else False
#         cue2 = st.checkbox("Marqueur causal explicite",
#                           value=st.session_state[cue2_key],
#                           key=cue2_key)
    
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
#         label_key = f"label_{current_pair.pair_id}"
#         if label_key not in st.session_state:
#             st.session_state[label_key] = existing_annotation.label if existing_annotation else None
        
#         current_label = st.session_state[label_key]
#         label = st.radio(
#             "Décision",
#             [1, 0],
#             index=0 if current_label == 1 else (1 if current_label == 0 else 0),
#             format_func=lambda x: "✅ OUI - Relation causale" if x == 1 else "❌ NON - Pas de relation",
#             key=label_key
#         )
#         # Update session state
    
#     with col2:
#         confidence_key = f"confidence_{current_pair.pair_id}"
#         if confidence_key not in st.session_state:
#             st.session_state[confidence_key] = existing_annotation.confidence if existing_annotation else 3
        
#         current_conf = st.session_state[confidence_key]
#         confidence = st.slider("Confiance", 1, 5, current_conf, key=confidence_key)
        
        
#         notes_key = f"notes_{current_pair.pair_id}"
#         if notes_key not in st.session_state:
#             st.session_state[notes_key] = existing_annotation.notes if existing_annotation else ''
        
#         notes = st.text_input("Notes", 
#                              value=st.session_state[notes_key],
#                              placeholder="Notes optionnelles...",
#                              key=notes_key)
    
#     # Action buttons with OPTIMIZED navigation
#     st.markdown("---")
#     col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
#     with col1:
#         if st.button("⬅️", disabled=idx == 0, use_container_width=True, help="Paire précédente (← ou A)"):
#             st.session_state.pair_index -= 1
#             st.rerun()
    
#     with col2:
#         if st.button("💾 Enregistrer", type="primary", use_container_width=True, help="Sauvegarder (Ctrl+S)"):
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
#                 # Update local cache
#                 st.session_state.user_annotations_cache[current_pair.pair_id] = annotation
#                 st.session_state.user_annotation_count = len(st.session_state.user_annotations_cache)
                
#                 # Update progress in background
#                 gsheets.update_progress(username, selected_id, idx, 
#                                        st.session_state.user_annotation_count, 
#                                        current_pair.pair_id)
                
#                 st.success("✅ Annotation sauvegardée")
#                 st.rerun()
#             else:
#                 st.error(f"❌ Erreur: {gsheets.error_message}")
    
#     with col3:
#         if st.button("💾 & ⏭️ Suivant", use_container_width=True, help="Sauvegarder et suivant (Espace)"):
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
#                 # Update local cache
#                 st.session_state.user_annotations_cache[current_pair.pair_id] = annotation
#                 st.session_state.user_annotation_count = len(st.session_state.user_annotations_cache)
                
#                 # Navigate to next pair
#                 if idx < total_pairs - 1:
#                     st.session_state.pair_index += 1
                
#                 # Update progress in background
#                 gsheets.update_progress(username, selected_id, 
#                                        st.session_state.pair_index,
#                                        st.session_state.user_annotation_count,
#                                        current_pair.pair_id)
                
#                 st.rerun()
#             else:
#                 st.error(f"❌ Erreur: {gsheets.error_message}")
    
#     with col4:
#         if st.button("➡️", disabled=idx >= total_pairs - 1, use_container_width=True, help="Paire suivante (→ ou D)"):
#             st.session_state.pair_index += 1
#             st.rerun()

# def dashboard_page():
#     """Dashboard page"""
#     check_session_timeout()
    
#     username = st.session_state.username
#     gsheets = st.session_state.gsheets
    
#     st.markdown(f"""
#     <div class="main-header">
#         <h1>📊 Tableau de bord</h1>
#         <p>Statistiques et visualisation globale</p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Get all data with caching
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
#         # Calculate quality metrics
#         quality_metrics = gsheets.calculate_annotator_quality(username)
        
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
        
#         if quality_metrics and quality_metrics['agreement_rate'] > 0:
#             st.markdown("#### 🎯 Qualité d'annotation")
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 st.metric("Taux d'accord", f"{quality_metrics['agreement_rate']*100:.1f}%")
#             with col2:
#                 st.metric("Ratio causal", f"{quality_metrics['causal_ratio']*100:.1f}%")
#             with col3:
#                 st.metric("Confiance moyenne", f"{quality_metrics['avg_confidence']:.1f}/5")
    
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
            
#             # Export buttons
#             col1, col2 = st.columns(2)
#             with col1:
#                 if st.button(f"📥 Exporter {dataset.name}", key=f"export_dash_{dataset.dataset_id}"):
#                     export_data = gsheets.export_annotated_dataset(dataset.dataset_id, mode="replace")
#                     if export_data:
#                         json_str = json.dumps(export_data['pairs'], indent=2, ensure_ascii=False)
#                         st.download_button(
#                             "⬇️ Télécharger",
#                             json_str,
#                             file_name=f"causafr_{dataset.dataset_id}_training_{datetime.now().strftime('%Y%m%d')}.json",
#                             mime="application/json",
#                             key=f"download_dash_{dataset.dataset_id}"
#                         )
#             with col2:
#                 if st.button(f"🧠 Export entraînement", key=f"training_dash_{dataset.dataset_id}"):
#                     training_data = gsheets.export_training_dataset(dataset.dataset_id)
#                     if training_data:
#                         json_str = json.dumps(training_data, indent=2, ensure_ascii=False)
#                         st.download_button(
#                             "⬇️ Télécharger",
#                             json_str,
#                             file_name=f"causafr_training_{dataset.dataset_id}_{datetime.now().strftime('%Y%m%d')}.json",
#                             mime="application/json",
#                             key=f"training_download_dash_{dataset.dataset_id}"
#                         )

# def about_page():
#     """About page"""
#     check_session_timeout()
    
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
        
#         # System info
#         st.markdown("### ⚙️ Informations système")
#         st.code(f"""
#         Dernière vérification: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#         Nombre de feuilles: {len(gsheets.spreadsheet.worksheets())}
#         Connecté en tant que: {st.session_state.username}
#         Rôle: {'Administrateur' if st.session_state.is_admin else 'Annotateur'}
#         Performance: {st.session_state.performance_monitor['load_count']} chargement(s)
#         """)
        
#         # Cache info
#         st.markdown("### 🚀 Performances")
#         cache_info = []
#         for key, value in gsheets._cache.items():
#             if isinstance(value, dict) and 'data' in value and value['data'] is not None:
#                 if key == 'pairs':
#                     cache_info.append(f"{key}: {len(value)} datasets")
#                 elif key in ['annotations', 'all_annotations', 'progress']:
#                     cache_info.append(f"{key}: {len(value)} entrées")
#                 else:
#                     cache_info.append(f"{key}: en cache")
        
#         if cache_info:
#             st.success("Cache actif: " + ", ".join(cache_info))
#         else:
#             st.info("Cache vide - premier chargement")
        
#         # Backup
#         st.markdown("### 💾 Sauvegarde")
#         if st.button("Créer une sauvegarde complète"):
#             backup = gsheets.create_backup()
#             if backup:
#                 st.download_button(
#                     "⬇️ Télécharger la sauvegarde",
#                     backup,
#                     file_name=f"causafr_full_backup_{datetime.now().strftime('%Y%m%d')}.json",
#                     mime="application/json"
#                 )
#             else:
#                 st.error(f"Erreur: {gsheets.error_message}")
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
        
#         # Show loading spinner only on initial load
#         if st.session_state.current_pairs_cache['data'] is None:
#             with st.spinner("Chargement initial..."):
#                 pass
        
#         # Create navigation options
#         if st.session_state.is_admin:
#             pages = ["📤 Gérer Datasets", "✏️ Annoter", "📊 Tableau de bord", "ℹ️ À propos"]
#         else:
#             pages = ["✏️ Annoter", "📊 Tableau de bord", "ℹ️ À propos"]
        
#         page = st.radio("Navigation", pages, label_visibility="collapsed")
    
#     # Show selected page
#     if page == "📤 Gérer Datasets":
#         if not st.session_state.is_admin:
#             st.error("⛔ Accès refusé - Cette section est réservée aux administrateurs")
#             st.info("Veuillez contacter un administrateur si vous avez besoin d'accéder à cette fonctionnalité.")
#         else:
#             dataset_management_page()
#     elif page == "✏️ Annoter":
#         optimized_annotate_page()
#     elif page == "📊 Tableau de bord":
#         dashboard_page()
#     elif page == "ℹ️ À propos":
#         about_page()

# if __name__ == "__main__":
#     main()
