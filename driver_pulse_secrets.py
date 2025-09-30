#!/usr/bin/env python3
"""
DriverPulse Secrets Management
Loads authentication credentials from Streamlit secrets or local files
"""

import json
import os
from typing import Dict, Any, Optional
import streamlit as st


def load_auth_data() -> Optional[Dict[str, Any]]:
    """
    Load auth.json data from Streamlit secrets or local file
    Returns None if not found
    """
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets') and 'DRIVER_PULSE_AUTH' in st.secrets:
            auth_data = st.secrets['DRIVER_PULSE_AUTH']
            if isinstance(auth_data, str):
                return json.loads(auth_data)
            return dict(auth_data)
    except Exception:
        pass

    # Fallback to local file
    auth_file = "auth.json"
    if os.path.exists(auth_file):
        try:
            with open(auth_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass

    return None


def load_gmail_credentials() -> Optional[Dict[str, Any]]:
    """
    Load gmail_credentials.json from Streamlit secrets or local file
    Returns None if not found
    """
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets') and 'DRIVER_PULSE_GMAIL_CREDENTIALS' in st.secrets:
            creds_data = st.secrets['DRIVER_PULSE_GMAIL_CREDENTIALS']
            if isinstance(creds_data, str):
                return json.loads(creds_data)
            return dict(creds_data)
    except Exception:
        pass

    # Fallback to local file
    creds_file = "gmail_credentials.json"
    if os.path.exists(creds_file):
        try:
            with open(creds_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass

    return None


def load_gmail_token() -> Optional[Dict[str, Any]]:
    """
    Load gmail_token.json from Streamlit secrets or local file
    Returns None if not found
    """
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets') and 'DRIVER_PULSE_GMAIL_TOKEN' in st.secrets:
            token_data = st.secrets['DRIVER_PULSE_GMAIL_TOKEN']
            if isinstance(token_data, str):
                return json.loads(token_data)
            return dict(token_data)
    except Exception:
        pass

    # Fallback to local file
    token_file = "gmail_token.json"
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass

    return None


def save_auth_data(auth_data: Dict[str, Any]) -> bool:
    """
    Save auth data to local file (for development/testing)
    In production, this should be stored in Streamlit secrets
    """
    try:
        with open("auth.json", 'w') as f:
            json.dump(auth_data, f, indent=2)
        return True
    except Exception:
        return False


def save_gmail_token(token_data: Dict[str, Any]) -> bool:
    """
    Save Gmail token to local file (for development/testing)
    In production, this should be stored in Streamlit secrets
    """
    try:
        with open("gmail_token.json", 'w') as f:
            json.dump(token_data, f, indent=2)
        return True
    except Exception:
        return False


def get_secrets_template() -> str:
    """
    Return template for .streamlit/secrets.toml with DriverPulse secrets
    """
    return """
# DriverPulse Authentication Secrets
# Copy the contents of your local files to these fields:

DRIVER_PULSE_AUTH = '''
{
  "cookies": [...],
  "created_at": "...",
  "portal_user_id": null,
  "user_info": {...}
}
'''

DRIVER_PULSE_GMAIL_CREDENTIALS = '''
{
  "installed": {
    "client_id": "...",
    "project_id": "...",
    "auth_uri": "...",
    "token_uri": "...",
    "auth_provider_x509_cert_url": "...",
    "client_secret": "...",
    "redirect_uris": [...]
  }
}
'''

DRIVER_PULSE_GMAIL_TOKEN = '''
{
  "token": "...",
  "refresh_token": "...",
  "token_uri": "...",
  "client_id": "...",
  "client_secret": "...",
  "scopes": [...],
  "universe_domain": "...",
  "account": "",
  "expiry": "..."
}
'''
"""