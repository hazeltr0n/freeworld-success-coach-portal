from html_pdf_generator import env
from test_template_system import SAMPLE_JOBS

agent_params = {
    'agent_name': 'Test Agent',
    'location': 'Houston',
    'fair_chance_only': True
}

try:
    template = env.get_template("debug_minimal.html")
    html = template.render(
        jobs=SAMPLE_JOBS[:1],  # Just one job
        agent_params=agent_params,
        total_jobs=1
    )
    print("✅ Minimal template rendered successfully")
    print(f"Length: {len(html)} chars")
except Exception as e:
    print(f"❌ Minimal template error: {e}")
    import traceback
    traceback.print_exc()