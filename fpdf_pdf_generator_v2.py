#!/usr/bin/env python3
"""
Clean FPDF2 PDF Generator - EXACT parameter alignment with pipeline functions
NO parameter confusion, NO overrides, NO ambiguity
GUARANTEES show_prepared_for works every time
"""

import pandas as pd
import os
from fpdf_pdf_generator import generate_fpdf_job_cards

def generate_pdf_from_dataframe(
    df: pd.DataFrame,
    output_path: str,
    market: str = "Unknown",
    coach_name: str = "",
    coach_username: str = "",  
    candidate_name: str = "",
    candidate_id: str = "",
    show_prepared_for: bool = True
) -> dict:
    """
    Clean wrapper for FPDF generation with EXACT parameter alignment
    
    Parameters:
    - df: DataFrame with jobs
    - output_path: Where to save PDF
    - market: Market name for title
    - coach_name: Coach display name
    - coach_username: Coach username 
    - candidate_name: Free Agent name
    - candidate_id: Free Agent UUID
    - show_prepared_for: TRUE = show "Prepared for" message, FALSE = hide it
    
    Returns:
    - dict with success status and file info
    """
    
    # EXACT parameter pass-through - NO modification, NO overrides
    print(f"🔧 FPDF v2 Generator - EXACT parameters:")
    print(f"   📊 Jobs: {len(df)}")
    print(f"   📍 Market: '{market}'")
    print(f"   👨‍🏫 Coach: '{coach_name}'")
    print(f"   👨‍💼 Coach Username: '{coach_username}'") 
    print(f"   👤 Candidate: '{candidate_name}'")
    print(f"   🆔 Candidate ID: '{candidate_id}'")
    print(f"   🎛️ Show Prepared For: {show_prepared_for}")
    
    # Call original FPDF generator with EXACT parameters
    result = generate_fpdf_job_cards(
        jobs_df=df,
        output_path=output_path,
        market=market,
        coach_name=coach_name,
        coach_username=coach_username,
        candidate_name=candidate_name, 
        candidate_id=candidate_id,
        show_prepared_for=show_prepared_for  # CRITICAL: Pass exactly as received
    )
    
    return result

def generate_pdf_bytes_from_dataframe(
    df: pd.DataFrame,
    market: str = "Unknown",
    coach_name: str = "",
    coach_username: str = "",  
    candidate_name: str = "",
    candidate_id: str = "",
    show_prepared_for: bool = True
) -> bytes:
    """
    Generate PDF and return as bytes (for Streamlit download)
    """
    
    import tempfile
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        temp_path = tmp_file.name
    
    try:
        # Generate PDF to temp file
        result = generate_pdf_from_dataframe(
            df=df,
            output_path=temp_path,
            market=market,
            coach_name=coach_name,
            coach_username=coach_username,
            candidate_name=candidate_name,
            candidate_id=candidate_id,
            show_prepared_for=show_prepared_for
        )
        
        if result and result.get('success'):
            # Read PDF as bytes
            with open(temp_path, 'rb') as f:
                pdf_bytes = f.read()
            return pdf_bytes
        else:
            return b""
            
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except (OSError, FileNotFoundError):
            pass  # Ignore cleanup failures
    
    return b""