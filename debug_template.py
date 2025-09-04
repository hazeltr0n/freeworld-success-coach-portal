import traceback
from html_pdf_generator import render_jobs_html
from test_template_system import SAMPLE_JOBS

agent_params = {
    'agent_name': 'Test Agent',
    'location': 'Houston',
    'fair_chance_only': True
}

# Debug: check what data normalization does
from html_pdf_generator import normalize_job_data
print("Sample job before normalization:")
print(SAMPLE_JOBS[0])
print("\nAfter normalization:")
normalized = normalize_job_data(SAMPLE_JOBS[0])
print(normalized)

html = render_jobs_html(SAMPLE_JOBS, agent_params)
print(f"\nHTML length: {len(html)}")
print(f"HTML content: {html}")

if "Error rendering jobs" in html:
    print("❌ Template had errors (caught and handled)")
else:
    print("✅ Template rendered successfully")