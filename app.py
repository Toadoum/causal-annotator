"""
CausaFr - Google Sheets Annotation Tool
Streamlit Cloud Deployment Version
"""

import streamlit as st
import pandas as pd
import json
import os
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Optional

# Try to get from Streamlit secrets
try:
    # Load config from Streamlit secrets
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
# STREAMLIT APPLICATION
# =============================================================================

st.set_page_config(
    page_title="CausaFr - Annotation Tool",
    page_icon="🔗",
    layout="wide"
)

def main():
    """Main application"""
    st.title("🔗 CausaFr - Annotation Tool")
    
    if GOOGLE_CONFIG is None:
        st.error("""
        ## ⚠️ Configuration Required
        
        Google Sheets is not properly configured.
        
        **For Streamlit Cloud Deployment:**
        
        1. Go to your Streamlit Cloud app
        2. Click on "Settings" (gear icon)
        3. Go to "Secrets" tab
        4. Add the following secrets:
        
        ```toml
        [GOOGLE_SHEETS]
        spreadsheet_id = "1K4zUiRVOnyDuEAjzoZ5qb7B5fg9dKOdaJJjbQfDsBKw"
        type = "service_account"
        project_id = "machine-translation-375907"
        private_key_id = "887c96056fc68e0e2eb9b740176735bfe7db003f"
        private_key = \"\"\"-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQCSWZ9wD1lxSVls\nIy/olVuIDnDGbttm16jBqFlRXHDmBn5yn7YuCRoKlqoCadJL/7MuE+xPiS17WYI3\nIhcWssMJfdD2DMYk+F0wGdS2FZUzNrIqWg+NiX/mUs8U3/kytxBqK8kpi1yrr/b0\nsTi1ZmvJd60f8o5UcCQ2CLbI6VZhH0shmE07q1wO8yMz4HnbSHyTyFizWxFCXqMN\n0Y6+WPBUsfj7G5pcNFtyHAsqIzoEFRuScebrPHrB2f2uvznnuODxUSJKKr+I/9NE\ndcExK3vdKvKWz84lGxxeVL5Jdw0SCH9zJFbrG/YxJixBYPtc/QsbjHs/pnoiS/tl\naRvJQU/tAgMBAAECggEACdE1wwpgjVsmgrzEhrVYL8MKOSFwGdC/Kwh8P1s0XpXS\nbyV8DtAA/XNYYbOQDhWPwzhGappw4NyjAchJZLYmo7EbLpoyQ4IenC6raHB/svEJ\nGBK1BuFRoVVuO0AAAzEpCno38w+8bm7uIcFupKqDcf8Tb7hxaEQihbZlbopKh1a8\nVVDR5AS1Cy1rPRDphckYPH+MNN/VO5AWUsV1hoEMY7b2G+mADUduzdAAyeHGH2Te\nGlRs4+I02PdDHokMZRej4lbo5CkUQ5YlwoV9zJ3PJBHRatpGWfQ0XGxynTINRGbJ\nIU/bmjA8xXbYC7FESkPBaFVdQMY/kthcFRAbg/qKsQKBgQDGTcxZp+iVv/l1hvPa\n4LdPdvEO8nSdeYuJ/4q0dg0zny+xoaBAKhyqYUWAsYIhU2pTHmQteffEYmxEG2GO\nKttH//1klVsltk+sjKYiAGdHFj4ErEqeQKpV+d8ybiFL6mtbux+AHhmFhhA5U1s9\nt5SyQp46FZG5y1r5BdwN1T9F0QKBgQC87iqnJK28I6c9/QrAKMCavhT1NLwcnjln\nEKXXCcP6CmAXsciRvyx1/YB7xkNBloHYs/YC6ZzVDPsmSn55SVyLGW50scyXf6e7\nLw3s5OJxQemnk76ExBM8pyynJPk6FvEmrtVmZZmNlUG9CNHfReBSq2+jyStW5D5y\nXxL3u5uDXQKBgQC2KgN9nLQY1EhpgTYDrAhYtC+PBoS/oEbh1uBpFETeVe4vJAUc\nzFKW5VI+fVHIIWN7xWBLMk67lZpVGj4MpivXwT3ZpyYax5X7MRzwASTedX01N7w4\nEbknz6kMH4TwwwAqPQQb4gqZ0OSYdI1NbZXoBzBotSWv4jHIrmxOPMWp8QKBgQCr\nSOGylzZLk6dUM81DWa8Em8A0bpL8/xXbsuQniNr8Hdvwn2XPfRq5/hI2JRFkrScb\naExpZ5KgNRydInx3SWN1WKEjeu6Zi0puEcL2OqxxMei73N6lT36BRq7c+lBZseL/\nxxIBu6rzCZaH4y8i1R8C1Bpqyz9Xj6Zt2nQ/1P6woQKBgQCePFKM+mTxpeADpVEF\npnGN3cQJGvC22FyjIhOOXI5JfkgzL/Ae2Q40/t15WrW/Q3737YxEm7vPbfZDfajQ\nnDpTfKxIe9mDB/MBi7IQjzwdhCdMj7gzk2TPM2XflK3CsWOtQiKYAak6QJJXjKzz\nI7HHSEOBRuAsvaYHD7nOg6KdMg==\n-----END PRIVATE KEY-----\"\"\"
        client_email = "annotation-bot@machine-translation-375907.iam.gserviceaccount.com"
        client_id = "107890068241269374646"
        auth_uri = "https://accounts.google.com/o/oauth2/auth"
        token_uri = "https://oauth2.googleapis.com/token"
        auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
        client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/annotation-bot%40machine-translation-375907.iam.gserviceaccount.com"
        ```
        
        5. Click "Save"
        6. Restart your app
        """)
        return
    
    # Show app content
    st.success("✅ Google Sheets configured successfully!")
    st.write(f"**Spreadsheet ID**: {GOOGLE_CONFIG['spreadsheet_id']}")
    st.write(f"**Service Account**: {GOOGLE_CONFIG['gcp_credentials']['client_email']}")

if __name__ == "__main__":
    main()
