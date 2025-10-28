#!/usr/bin/env python3
"""
Test AI-based formatting on a sample job description
"""

import os
import sys

# Get OpenAI API key
try:
    import streamlit as st
    OPENAI_API_KEY = st.secrets.get('OPENAI_API_KEY')
except:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    print("❌ No OpenAI API key found")
    sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def format_plain_description_ai(description: str) -> str:
    """
    Enhance plain text job descriptions with natural formatting using AI
    """

    prompt = f"""You are a job description formatter. Take this plain text job description and add natural HTML formatting to make it more readable.

Rules:
- Use <h3> for major sections (like REPORTS TO, JOB PURPOSE, OBJECTIVES, DUTIES AND RESPONSIBILITIES, QUALIFICATIONS, WORKING CONDITIONS, Benefits, etc.)
- Use <ul><li> for lists of items
- Use <p> for paragraphs
- Use <br> for single line breaks
- Keep the original text content exactly the same
- Only add structural HTML tags, don't change the wording

Plain text description:
{description}

Return ONLY the formatted HTML version, no explanation or markdown code blocks."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a job description formatter. Return only HTML, no markdown."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    return response.choices[0].message.content


# Sample job description (the one user provided - no newlines!)
sample_description = """TRANSPORT SPECIALISTJOB DESCRIPTIONREPORTS TO: Warehouse & Distribution ACJOB PURPOSE: Transports finished products to customers as well as transporting materials to and from designated sites in a safe and efficient manner.OBJECTIVES:1. Assist AC in maximizing efficiency of transport systems.2. Ensure compliance with DOT and other highway regulations.3. Maintain accurate safety & maintenance records for transport vehicles.4. Ensure safe working conditions for self & others.5. Maintain regular & effective communication with supervisor & co-workers.DUTIES AND RESPONSIBILITIES:1. Utilize manual and/or mechanical material handling equipment to loadand unload finished products & other materials as required in an efficient manner.2. Ensure regular & documented safety checks are occurring on company vehicles.3. Operate primarily company vehicles with greater than two axles topick-up and deliver finished goods and other materials todesignated locales.4. Assist supervisor with adjusting workload for transport shifts as needed.5. Maintain working knowledge of regulations regarding highway operation of vehicles to ensure compliance under corresponding transport laws (e.g. DOT, CHP, etc.)6. Accurately prepare, obtain and complete inspection documents, shipping receipts, packing slips and similar documents as required.7. Perform all duties within safety policies & procedures.8. Maintain possession of a current class 'A' license and documentable safe driving record.9. Maintain accurate and organized maintenance records for all company transport vehicles.10. Assist supervisor in training co-workers on transport tasks as needed.11. Perform limited maintenance on vehicles such as fueling, minor service, and washing as necessary. Schedule regular maintenance of all company transport vehicles with AC approval.12. Keep supervisor and co-workers informed of changes or updatedinformation which may affect their jobs.13. Attend all required meetings & perform other administrative duties as required.14. Other duties as assigned.QUALIFICATIONS1. Valid class 'A' license2. Current DMV record within company standards3. Ability to lift 20-50 lbs occasionally4. Ability to understand and follow oral and written instructions and to expressideas effectively, orally and in writing.5. Ability to work within all company policies and procedures.WORKING CONDITIONS1. Late night or early morning start times. Subject to change.2. 3. Majority of job function is driving.4. Normal work days are every day, except Sundays.5. All-weather conditionsJob Type: Full-timePay: $29.00 - $33.00 per hourExpected hours: 30 – 36 per weekBenefits:401(k)Dental insuranceHealth insurancePaid time offVision insuranceAbility to Commute:Petaluma, CA 94954 (Required)Work Location: In person"""

print('🔍 ORIGINAL (PLAIN TEXT, NO NEWLINES):')
print('=' * 100)
print(sample_description[:400] + '...\n')

print('\n🤖 Calling GPT-4o-mini for formatting...')
formatted = format_plain_description_ai(sample_description)

print('\n✨ AI-FORMATTED (HTML):')
print('=' * 100)
print(formatted)

print('\n\n📊 RENDERED VIEW (simulated):')
print('=' * 100)
# Simulate how it would look rendered
rendered = formatted.replace('<h3>', '\n\n━━━ ').replace('</h3>', ' ━━━\n')
rendered = rendered.replace('<ul>', '\n').replace('</ul>', '\n')
rendered = rendered.replace('<li>', '  • ').replace('</li>', '')
rendered = rendered.replace('<p>', '\n').replace('</p>', '')
rendered = rendered.replace('<br>', '\n')
rendered = rendered.replace('<br/>', '\n')
print(rendered)
