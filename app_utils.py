# app_utils.py
"""
Utility functions extracted from app.py to eliminate code duplication
and improve maintainability.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, Tuple


def filter_quality_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Single source of truth for quality job filtering.
    
    Priority:
    1. Use route.final_status if available (jobs starting with 'included')
    2. Fall back to ai.match filtering ('good', 'so-so')
    3. Return original df if neither field exists
    
    Args:
        df: DataFrame with job data
        
    Returns:
        Filtered DataFrame containing only quality jobs
    """
    try:
        if df.empty:
            return df
            
        # Primary filter: route.final_status  
        # Include both 'included*' and 'passed_all_filters' statuses
        if 'route.final_status' in df.columns:
            # Handle NaN values properly before string operations
            status_col = df['route.final_status'].fillna('').astype(str)
            mask = (status_col.str.startswith('included') | (status_col == 'passed_all_filters'))
            if mask.any():
                return df[mask]
        
        # Fallback filter: ai.match
        if 'ai.match' in df.columns:
            return df[df['ai.match'].isin(['good', 'so-so'])]
        
        # No filtering available
        return df
        
    except Exception:
        return df


def calculate_search_metrics(df: pd.DataFrame) -> Dict[str, int]:
    """
    Calculate standardized search metrics for job data.
    
    Args:
        df: DataFrame with job data
        
    Returns:
        Dictionary with counts for good, so-so, local, otr jobs
    """
    metrics = {
        'total': len(df),
        'good': 0,
        'so_so': 0, 
        'local': 0,
        'otr': 0
    }
    
    try:
        if 'ai.match' in df.columns:
            metrics['good'] = int((df['ai.match'] == 'good').sum())
            metrics['so_so'] = int((df['ai.match'] == 'so-so').sum())
        
        if 'ai.route_type' in df.columns:
            metrics['local'] = int((df['ai.route_type'] == 'Local').sum())
            metrics['otr'] = int((df['ai.route_type'] == 'OTR').sum())
            
    except Exception:
        pass
        
    return metrics


def generate_pdf_from_dataframe(df: pd.DataFrame, metadata: Dict[str, Any], 
                               agent_params: Optional[Dict[str, Any]] = None) -> Optional[bytes]:
    """
    Generate PDF from DataFrame with consistent logic across all search types.
    
    Args:
        df: DataFrame with job data
        metadata: Pipeline metadata
        agent_params: Agent/coach parameters for PDF generation
        
    Returns:
        PDF bytes if successful, None if failed
    """
    try:
        # Import here to avoid circular imports
        from pipeline_wrapper import StreamlitPipelineWrapper
        
        if df.empty:
            return None
            
        # Ensure we have a pipeline instance
        if 'pipeline' not in st.session_state:
            st.session_state.pipeline = StreamlitPipelineWrapper()
        
        pipeline = st.session_state.pipeline
        
        # Generate PDF with consistent parameters
        pdf_bytes = pipeline.generate_pdf_from_dataframe(
            df=df,
            metadata=metadata,
            agent_params=agent_params or {}
        )
        
        return pdf_bytes
        
    except Exception as e:
        st.error(f"PDF generation failed: {e}")
        return None


def display_market_section(market: str, df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """
    Display a standardized market section with job table and metrics.
    
    Args:
        market: Market name
        df: DataFrame filtered to this market
        metadata: Pipeline metadata for PDF generation
    """
    try:
        # Market header
        st.markdown("---")
        col_h, col_btn = st.columns([8, 2])
        
        with col_h:
            st.markdown(f"## 📍 **{market}**")
            st.caption(f"Jobs found in {market}")
            
        with col_btn:
            # PDF download button if available
            if metadata.get('pdf_path') and 'pipeline' in st.session_state:
                try:
                    pdf_bytes = st.session_state.pipeline.get_pdf_bytes(metadata['pdf_path'])
                    if pdf_bytes:
                        st.download_button(
                            label="📄 Download PDF",
                            data=pdf_bytes,
                            file_name="freeworld_jobs_report.pdf",
                            mime="application/pdf",
                            key=f"download_pdf_{market}",
                            use_container_width=True
                        )
                except Exception:
                    st.caption("PDF unavailable")
        
        # Filter for quality jobs
        quality_df = filter_quality_jobs(df)
        
        # Display job table
        cols_pref = ['source.title', 'source.company', 'ai.summary', 'ai.match', 'ai.route_type', 'ai.fair_chance', 'source.indeed_url']
        cols_show = [c for c in cols_pref if c in quality_df.columns]
        
        st.dataframe(
            quality_df[cols_show] if cols_show else quality_df,
            use_container_width=True,
            height=400
        )
        
        # Display metrics
        metrics = calculate_search_metrics(df)
        quality_metrics = calculate_search_metrics(quality_df)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Quality Jobs", quality_metrics['total'])
        with col2:
            st.metric("Excellent", quality_metrics['good'])
        with col3:
            st.metric("Possible Fit", quality_metrics['so_so'])
        with col4:
            st.metric("Local Routes", quality_metrics['local'])
            
    except Exception as e:
        st.error(f"Error displaying market {market}: {e}")


def process_search_results(df: pd.DataFrame, metadata: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Process search results with consistent logic across all search types.
    
    Args:
        df: Raw search results DataFrame
        metadata: Pipeline metadata
        
    Returns:
        Tuple of (processed_df, updated_metadata)
    """
    try:
        if df.empty:
            return df, metadata
        
        # Calculate overall metrics
        total_metrics = calculate_search_metrics(df)
        quality_df = filter_quality_jobs(df)
        quality_metrics = calculate_search_metrics(quality_df)
        
        # Update metadata with metrics
        metadata.update({
            'total_jobs': total_metrics['total'],
            'quality_jobs': quality_metrics['total'],
            'good_jobs': quality_metrics['good'],
            'so_so_jobs': quality_metrics['so_so'],
            'local_jobs': quality_metrics['local'],
            'otr_jobs': quality_metrics['otr']
        })
        
        # Store processed dataframe in session state
        st.session_state.current_df = df.copy()
        st.session_state.current_metadata = metadata.copy()
        
        return df, metadata
        
    except Exception as e:
        st.error(f"Error processing search results: {e}")
        return df, metadata


def get_ordered_markets(df: pd.DataFrame) -> list:
    """
    Get markets from DataFrame in consistent order.
    
    Args:
        df: DataFrame with meta.market column
        
    Returns:
        List of market names ordered by job count
    """
    try:
        if df.empty or 'meta.market' not in df.columns:
            return []
        
        # Count jobs per market and sort by count (descending)
        market_counts = df['meta.market'].value_counts()
        return market_counts.index.tolist()
        
    except Exception:
        return []


def debug_dataframe_info(df: pd.DataFrame, name: str = "DataFrame") -> None:
    """
    Display debug information about a DataFrame.
    Debug output disabled - function kept for backwards compatibility.
    
    Args:
        df: DataFrame to analyze
        name: Name to display in debug output
    """
    # Debug output disabled for cleaner UI
    pass