#!/usr/bin/env python3
"""
Test rule-based formatting on a sample job description
"""

import re

def auto_format_description(text: str) -> str:
    """
    Apply rule-based formatting to plain text descriptions
    """
    # Detect section headers (all caps or title case followed by colon)
    text = re.sub(r'\n([A-Z][A-Z\s]+):?\n', r'\n<h3>\1</h3>\n', text)
    text = re.sub(r'^([A-Z][A-Z\s]+):?\n', r'<h3>\1</h3>\n', text)

    # Split into lines for processing
    lines = text.split('\n')
    formatted_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append('<br>')
            continue

        # Check if already a heading
        if stripped.startswith('<h3>'):
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append(stripped)
            continue

        # Check if line is a numbered or bulleted list item
        is_list_item = (
            re.match(r'^\d+[\.)]\s', stripped) or  # 1. or 1)
            re.match(r'^[-*•]\s', stripped)  # -, *, •
        )

        if is_list_item:
            if not in_list:
                formatted_lines.append('<ul>')
                in_list = True
            # Remove bullet/number
            content = re.sub(r'^[-*•]\s|^\d+[\.)]\s', '', stripped)
            formatted_lines.append(f'<li>{content}</li>')
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False

            # Regular paragraph
            formatted_lines.append(f'<p>{stripped}</p>')

    # Close any open list
    if in_list:
        formatted_lines.append('</ul>')

    return '\n'.join(formatted_lines)


# Sample job description (the one user provided)
sample_description = """TRANSPORT SPECIALISTJOB DESCRIPTIONREPORTS TO: Warehouse & Distribution ACJOB PURPOSE: Transports finished products to customers as well as transporting materials to and from designated sites in a safe and efficient manner.OBJECTIVES:1. Assist AC in maximizing efficiency of transport systems.2. Ensure compliance with DOT and other highway regulations.3. Maintain accurate safety & maintenance records for transport vehicles.4. Ensure safe working conditions for self & others.5. Maintain regular & effective communication with supervisor & co-workers.DUTIES AND RESPONSIBILITIES:1. Utilize manual and/or mechanical material handling equipment to loadand unload finished products & other materials as required in an efficient manner.2. Ensure regular & documented safety checks are occurring on company vehicles.3. Operate primarily company vehicles with greater than two axles topick-up and deliver finished goods and other materials todesignated locales.4. Assist supervisor with adjusting workload for transport shifts as needed.5. Maintain working knowledge of regulations regarding highway operation of vehicles to ensure compliance under corresponding transport laws (e.g. DOT, CHP, etc.)6. Accurately prepare, obtain and complete inspection documents, shipping receipts, packing slips and similar documents as required.7. Perform all duties within safety policies & procedures.8. Maintain possession of a current class 'A' license and documentable safe driving record.9. Maintain accurate and organized maintenance records for all company transport vehicles.10. Assist supervisor in training co-workers on transport tasks as needed.11. Perform limited maintenance on vehicles such as fueling, minor service, and washing as necessary. Schedule regular maintenance of all company transport vehicles with AC approval.12. Keep supervisor and co-workers informed of changes or updatedinformation which may affect their jobs.13. Attend all required meetings & perform other administrative duties as required.14. Other duties as assigned.QUALIFICATIONS1. Valid class 'A' license2. Current DMV record within company standards3. Ability to lift 20-50 lbs occasionally4. Ability to understand and follow oral and written instructions and to expressideas effectively, orally and in writing.5. Ability to work within all company policies and procedures.WORKING CONDITIONS1. Late night or early morning start times. Subject to change.2. 3. Majority of job function is driving.4. Normal work days are every day, except Sundays.5. All-weather conditionsJob Type: Full-timePay: $29.00 - $33.00 per hourExpected hours: 30 – 36 per weekBenefits:401(k)Dental insuranceHealth insurancePaid time offVision insuranceAbility to Commute:Petaluma, CA 94954 (Required)Work Location: In person"""

print('🔍 ORIGINAL (PLAIN TEXT):')
print('=' * 100)
print(sample_description[:500] + '...\n')

formatted = auto_format_description(sample_description)

print('\n✨ RULE-BASED FORMATTED (HTML):')
print('=' * 100)
print(formatted)

print('\n\n📊 RENDERED VIEW (simulated):')
print('=' * 100)
# Simulate how it would look rendered
rendered = formatted.replace('<h3>', '\n━━━ ').replace('</h3>', ' ━━━')
rendered = rendered.replace('<ul>', '\n').replace('</ul>', '')
rendered = rendered.replace('<li>', '  • ').replace('</li>', '')
rendered = rendered.replace('<p>', '').replace('</p>', '')
rendered = rendered.replace('<br>', '\n')
print(rendered)
