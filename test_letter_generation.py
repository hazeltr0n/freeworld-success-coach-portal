#!/usr/bin/env python3
"""
Rapid Letter Generation Test Script
Generates pre-adverse response letters directly without Streamlit UI
For rapid iteration and debugging
"""

import sys
from datetime import datetime
from pre_adverse_response_helper import (
    extract_contact_name,
    analyze_notification,
    analyze_background_check,
    generate_response_letter,
    generate_coach_letter,
    generate_pdfs
)

# Test Data from Martin Duran Case
NOTIFICATION_TEXT = """Danny Herman Trucking
339 Cold Springs Road
Mountain City, TN 37683
March 26, 2025, 5:22 pm

Martin Duran
5130 Chromite Street
El Paso, TX 79932

Dear Martin Duran,

Enclosed please find a copy of your background report(s) and information about your rights. We have not made a final hiring decision or, if you applied to contract with the Company as an independent contractor, a final decision regarding that contracting opportunity. As required by law, we are notifying you that we may decide not to hire or engage you based in whole or in part on the information in the report(s) obtained.

If the records are inaccurate or incomplete, or if you would like to provide us with information about rehabilitation or mitigating circumstances, please contact Safety Dept. at dhtaa1805@dannyherman.com. In your contact, it may be helpful to include additional information about your record that you would like the company to consider. You must do so within ten (10) business days from the date that this letter was mailed to you.

Sincerely,
Steve E. Frantz
VP of Safety
Danny Herman Trucking"""

BACKGROUND_CHECK_TEXT = """Background Screening Report
Simpliverified

FILE NUMBER 0000000-TST
REPORT TO Freeworld (Freeworld)
REPORT DATE 10-01-2025
ORDER DATE 09-29-2025 Freeworld_Tenstreet
TYPE Freeworld Background Check ONLY

APPLICANT: DURAN, MARTIN SSN XXX-XX-0000 DOB 01-01-1989

*** Abstract ***
NAME ON RECORD DURAN, MARTIN CASE NUMBER 17-000000-HTX
DOB ON RECORD XXXX-01-01 COURT TX; Example District Court
FILE DATE 2017-06-15

Count
TYPE FELONY OFFENSE AGGRAVATED ASSAULT WITH A DEADLY WEAPON

DISPOSITION
CONVICTION
GUILTY

DISPOSITION DATE 2017-09-12 OFFENSE DATE 2017-06-14
SENTENCE: See court record

OTHER INFO
Example County

*** End Abstract ***"""

# Simulated conversation history
CONVERSATION_HISTORY = [
    {
        "role": "assistant",
        "content": "I've reviewed your background check and can see what the employer will see. Is there anything about your record that you think needs clarification or context?"
    },
    {
        "role": "user",
        "content": "I was running with a bad crowd back then. We went to a party, and a fight broke out, which we were pulled into. I made the mistake of pulling a knife. I regret what it did, but I'm glad it got me out of that environment."
    },
    {
        "role": "assistant",
        "content": "Thanks. Based on your background check, I can see the dates and charges. Can you briefly tell me in your own words what happened? Keep it simple - just the context around the situation."
    },
    {
        "role": "user",
        "content": "In 2017, I was convicted of aggravated assault with a deadly weapon. I was young and made a terrible mistake. The conviction happened in September 2017 and I served 6 years."
    },
    {
        "role": "assistant",
        "content": "I appreciate your honesty. What have you done since then to move forward and grow as a person? This could be completing CDL training, staying employed, counseling, community service, or anything else."
    },
    {
        "role": "user",
        "content": "I served 6 years inside, where I took extensive anger management counseling, and worked on myself. Once I got out, I joined my church, where I met my wife. We have 2 kids now. FreeWorld has been a blessing, helping me get my CDL. I volunteer at my church's food bank every week."
    },
    {
        "role": "assistant",
        "content": "That's great progress. Now, why do you think this past issue won't affect your ability to do this job safely and professionally?"
    },
    {
        "role": "user",
        "content": "I have the tools I need now to deal with tense situations, and the wisdom to keep myself out of them in the first place. I MUST get home to my family at the end of every day, so DHT can count on me to be a safe driver."
    },
    {
        "role": "assistant",
        "content": "Last question: Is there anything else you'd like the employer to know about you? This could be references, work ethic, reliability, or anything that shows who you are today."
    },
    {
        "role": "user",
        "content": "I got my current job within 2 days of getting out of jail. I haven't missed a day since, other than the time I took off for trucking school. If Danny Herman gives me this shot, and helps me take care of my family, I will do the same, and take good care of the company's reputation and customers."
    }
]

# Agent details
AGENT_NAME = "Martin Duran"
AGENT_PHONE = "(915) 555-0123"
AGENT_EMAIL = "martin.duran@email.com"
COACH_NAME = "O'Neal Heard"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def main():
    """Generate letters and PDFs for rapid testing"""
    print_section("🚀 RAPID LETTER GENERATION TEST")

    # Step 1: Extract contact name
    print("📋 Step 1: Extracting contact name from notification...")
    contact_name = extract_contact_name(NOTIFICATION_TEXT)
    print(f"✅ Contact Name: {contact_name}")

    # Step 2: Analyze notification
    print("\n📋 Step 2: Analyzing notification...")
    notification_analysis = analyze_notification(NOTIFICATION_TEXT)
    print(f"✅ Analysis:\n{notification_analysis}")

    # Step 3: Analyze background check
    print("\n📋 Step 3: Analyzing background check...")
    background_analysis = analyze_background_check(BACKGROUND_CHECK_TEXT)
    print(f"✅ Analysis:\n{background_analysis}")

    # Step 4: Generate agent response letter
    print("\n📋 Step 4: Generating agent response letter...")
    response_letter = generate_response_letter(
        CONVERSATION_HISTORY,
        NOTIFICATION_TEXT,
        AGENT_NAME,
        contact_name,
        AGENT_PHONE,
        AGENT_EMAIL
    )
    print("✅ Agent Letter Generated!")
    print_section("AGENT RESPONSE LETTER")
    print(response_letter)

    # Step 5: Generate coach support letter
    print("\n📋 Step 5: Generating coach support letter...")
    coach_letter = generate_coach_letter(
        AGENT_NAME,
        COACH_NAME,
        CONVERSATION_HISTORY,
        notification_analysis,
        contact_name
    )
    print("✅ Coach Letter Generated!")
    print_section("COACH SUPPORT LETTER")
    print(coach_letter)

    # Step 6: Generate PDFs
    print("\n📋 Step 6: Generating PDF documents...")
    pdfs = generate_pdfs(
        AGENT_NAME,
        COACH_NAME,
        response_letter,
        coach_letter,
        agent_signature=None  # No signature for rapid testing
    )

    # Save PDFs to test output directory
    import os
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if pdfs.get('agent_letter'):
        agent_path = f"{output_dir}/agent_letter_{timestamp}.pdf"
        with open(agent_path, 'wb') as f:
            f.write(pdfs['agent_letter'])
        print(f"✅ Agent Letter PDF: {agent_path}")

    if pdfs.get('coach_letter'):
        coach_path = f"{output_dir}/coach_letter_{timestamp}.pdf"
        with open(coach_path, 'wb') as f:
            f.write(pdfs['coach_letter'])
        print(f"✅ Coach Letter PDF: {coach_path}")

    if pdfs.get('certificate'):
        cert_path = f"{output_dir}/certificate_{timestamp}.pdf"
        with open(cert_path, 'wb') as f:
            f.write(pdfs['certificate'])
        print(f"✅ Certificate PDF: {cert_path}")

    print_section("✅ GENERATION COMPLETE")
    print(f"📁 All files saved to: {output_dir}/")
    print(f"⏱️  Timestamp: {timestamp}")
    print("\n💡 TIP: Open the PDFs to review the output and iterate quickly!")

    return {
        'contact_name': contact_name,
        'notification_analysis': notification_analysis,
        'background_analysis': background_analysis,
        'response_letter': response_letter,
        'coach_letter': coach_letter,
        'pdfs': pdfs,
        'output_dir': output_dir,
        'timestamp': timestamp
    }

if __name__ == "__main__":
    try:
        results = main()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
