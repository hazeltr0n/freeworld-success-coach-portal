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
        
        title = job.get('job_title', 'Unknown Title')[:60] + ('...' if len(job.get('job_title', '')) > 60 else '')
        pdf.cell(0, 10, title, 0, 1)
        
        # Company and location
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(0, 0, 0)
        company = job.get('company_name', 'Unknown Company')
        location = job.get('job_location', 'Unknown Location')
        pdf.cell(0, 8, f"{company} • {location}", 0, 1)
        
        # Salary if available
        salary = job.get('salary_display', job.get('salary', ''))
        if salary and salary.strip() and salary.lower() not in ['nan', 'none', '']:
            pdf.cell(0, 8, f"💰 {salary}", 0, 1)
        
        # Match quality and route type
        match_quality = job.get('match_quality', 'unknown')
        route_type = job.get('route_type', 'Unknown')
        
        match_emoji = {'good': '🟢', 'so-so': '🟡', 'bad': '🔴'}.get(match_quality, '⚪')
        pdf.cell(0, 8, f"{match_emoji} {match_quality.title()} Match • {route_type} Route", 0, 1)
        
        # Job description (truncated)
        description = job.get('job_description', job.get('description', ''))
        if description and description.strip():
            # Clean and truncate description
            desc_clean = description.replace('\n', ' ').replace('\r', ' ')
            desc_short = desc_clean[:200] + ('...' if len(desc_clean) > 200 else '')
            
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(60, 60, 60)
            
            # Wrap text
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

def convert_dataframe_to_job_dicts(df: pd.DataFrame) -> List[Dict]:
    """Convert DataFrame to job dictionaries compatible with template system"""
    jobs = []
    
    for _, row in df.iterrows():
        # Map DataFrame columns to template-expected fields
        job = {
            'job_title': row.get('source.title', row.get('norm.title', 'Unknown Title')),
            'company_name': row.get('source.company', row.get('norm.company', 'Unknown Company')),
            'job_location': row.get('source.location_raw', row.get('norm.location', 'Unknown Location')),
            'job_description': row.get('source.description_raw', row.get('norm.description', '')),
            'salary_display': row.get('norm.salary_display', ''),
            'salary': row.get('source.salary_raw', ''),
            'match_quality': row.get('ai.match', 'unknown'),
            'route_type': row.get('ai.route_type', 'Unknown'),
            'fair_chance': row.get('ai.fair_chance', ''),
            'posted_date': row.get('source.posted_date', ''),
            'job_url': row.get('meta.tracked_url', row.get('source.url', '')),
        }
        jobs.append(job)
    
    return jobs

def generate_pdf_from_dataframe(df: pd.DataFrame, agent_params: Dict[str, Any], output_path: str):
    """
    Main function to generate PDF from DataFrame using template-compatible approach
    
    Args:
        df: Job DataFrame
        agent_params: Same parameters as HTML template system
        output_path: Where to save PDF
    """
    # Convert DataFrame to job dictionaries
    jobs = convert_dataframe_to_job_dicts(df)
    
    # Generate PDF using template-compatible function
    generate_fpdf_job_cards_from_template_data(jobs, agent_params, output_path)