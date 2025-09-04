from html_pdf_generator import env, normalize_job_data
from test_template_system import SAMPLE_JOBS

agent_params = {
    'agent_name': 'Test Agent',
    'location': 'Houston',
    'fair_chance_only': True
}

# Normalize jobs
normalized_jobs = [normalize_job_data(job) for job in SAMPLE_JOBS]

try:
    template = env.get_template("debug_step_by_step.html")
    html = template.render(
        jobs=normalized_jobs,
        agent_params=agent_params,
        total_jobs=len(normalized_jobs)
    )
    print("✅ Step-by-step template rendered successfully")
    print(f"Length: {len(html)} chars")
    if len(html) < 500:
        print(f"Content preview:\n{html[:200]}...")
except Exception as e:
    print(f"❌ Step-by-step template error: {e}")
    import traceback
    traceback.print_exc()