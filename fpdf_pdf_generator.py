"""
FreeWorld FPDF2 PDF Generator - Template-Compatible Version
Uses same parameters as HTML template system for consistency
"""
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from fpdf import FPDF
import textwrap

class FreeWorldPDF(FPDF):
    def __init__(self, agent_params: Dict[str, Any]):
        super().__init__()
        self.agent_params = agent_params
        
    def header(self):
        """Add header with FreeWorld branding"""
        # Add logo if available
        logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'FW-Wordmark-Roots@3x.png')
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 50)
        
        self.set_font('Arial', 'B', 24)
        self.set_text_color(0, 71, 81)  # FreeWorld midnight color
        self.cell(0, 20, f"{self.agent_params.get('location', 'Unknown')} CDL Jobs", 0, 1, 'C')
        
        # Add prepared for message if enabled
        if self.agent_params.get('show_prepared_for', True):
            agent_name = self.agent_params.get('agent_name', '')
            coach_name = self.agent_params.get('coach_name', '')
            
            if agent_name and coach_name:
                prepared_msg = f"Prepared for {agent_name} by Coach {coach_name}"
            elif agent_name:
                prepared_msg = f"Prepared for {agent_name}"
            else:
                prepared_msg = ""
                
            if prepared_msg:
                self.set_font('Arial', '', 12)
                self.set_text_color(100, 100, 100)
                self.cell(0, 10, prepared_msg, 0, 1, 'C')
        
        self.ln(10)

def generate_fpdf_job_cards_from_template_data(jobs: List[Dict], agent_params: Dict[str, Any], output_path: str):
    """
    Generate PDF from job data using same parameters as HTML template system
    
    Args:
        jobs: List of job dictionaries (from jobs_dataframe_to_dicts)
        agent_params: Same parameters used by HTML template:
            - location: Location name
            - agent_name: Free agent name  
            - agent_uuid: Free agent ID
            - coach_name: Coach name
            - coach_username: Coach username
            - show_prepared_for: Whether to show prepared message
        output_path: Path to save PDF
    """
    pdf = FreeWorldPDF(agent_params)
    pdf.add_page()
    
    # Title page info
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 0, 1, 'C')
    pdf.cell(0, 10, f"Total Jobs: {len(jobs)}", 0, 1, 'C')
    pdf.ln(10)
    
    # Job cards
    for i, job in enumerate(jobs):
        if i > 0 and i % 3 == 0:  # New page every 3 jobs
            pdf.add_page()
            
        # Job card
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(0, 71, 81)
        
        # EXACTLY MIRROR HTML template fields
        title = job.get('title', 'Unknown Title')[:60] + ('...' if len(job.get('title', '')) > 60 else '')
        pdf.cell(0, 10, title, 0, 1)
        
        # Company and location - EXACTLY like HTML template
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(0, 0, 0)
        company = job.get('company', 'Unknown Company')
        city = job.get('city', '')
        state = job.get('state', '')
        
        # Build location string like HTML template does
        if city and state:
            location_str = f"{city}, {state}"
        elif job.get('location'):
            location_str = job.get('location')
        else:
            location_str = 'Unknown Location'
            
        pdf.cell(0, 8, f"{company} - {location_str}", 0, 1)
        
        # Match badge and route type - EXACTLY like HTML template
        match_badge = job.get('match_badge', '')  # 'Excellent Match', 'Possible Fit', or ''
        route_type = job.get('route_type', 'Unknown')
        
        if match_badge:
            pdf.cell(0, 8, f"{match_badge} - {route_type} Route", 0, 1)
        else:
            pdf.cell(0, 8, f"{route_type} Route", 0, 1)
        
        # Fair chance employer - EXACTLY like HTML template
        if job.get('fair_chance', False):
            pdf.cell(0, 8, "Fair Chance Employer", 0, 1)
        
        # Description - use AI summary (description_summary field) - EXACTLY like HTML template
        description = job.get('description_summary', job.get('description', ''))
        if description and description.strip():
            # AI summary is clean text, no bullets or Unicode
            desc_clean = str(description).strip()
            desc_short = desc_clean[:300] + ('...' if len(desc_clean) > 300 else '')
            
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(60, 60, 60)
            
            # Wrap text for PDF
            lines = textwrap.wrap(desc_short, width=100)
            for line in lines[:3]:  # Max 3 lines
                pdf.cell(0, 6, line, 0, 1)
        
        # Separator line
        pdf.ln(5)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(8)
    
    # Save PDF
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    print(f"✅ FPDF2 PDF generated: {output_path}")

def clean_unicode_text(text: str) -> str:
    """Clean Unicode characters that FPDF2 can't handle"""
    if not text:
        return ""
    
    # Replace Unicode characters with ASCII alternatives
    text = str(text)
    text = text.replace('•', '- ')  # Replace bullet points
    text = text.replace('💰', '$')  # Replace money emoji
    text = text.replace('🟢', '[GOOD]')  # Replace green circle
    text = text.replace('🟡', '[OK]')  # Replace yellow circle  
    text = text.replace('🔴', '[POOR]')  # Replace red circle
    text = text.replace('⚪', '[?]')  # Replace white circle
    text = text.replace('\u2022', '- ')  # Unicode bullet point
    text = text.replace('\u00A0', ' ')  # Non-breaking space
    
    # Remove any remaining non-ASCII characters
    text = ''.join(char if ord(char) < 128 else '?' for char in text)
    
    return text

def generate_pdf_from_dataframe(df: pd.DataFrame, agent_params: Dict[str, Any], output_path: str):
    """
    Main function to generate PDF from DataFrame using HTML template system data
    
    Args:
        df: Job DataFrame
        agent_params: Same parameters as HTML template system
        output_path: Where to save PDF
    """
    # Use the HTML template system to convert DataFrame to job dictionaries
    from pdf.html_pdf_generator import jobs_dataframe_to_dicts
    
    # Get job data using the same method as HTML template
    jobs = jobs_dataframe_to_dicts(df)
    
    # Clean Unicode characters from job data
    for job in jobs:
        for key, value in job.items():
            if isinstance(value, str):
                job[key] = clean_unicode_text(value)
    
    # Generate PDF using template-compatible function
    generate_fpdf_job_cards_from_template_data(jobs, agent_params, output_path)