#!/usr/bin/env python3
"""
FreeWorld Pre-Adverse Action Response Helper
AI-powered chatbot to help Free Agents craft professional responses to pre-adverse notifications
"""

import streamlit as st
import base64
import os
from openai import OpenAI
from PIL import Image
import io
from pathlib import Path
from dotenv import load_dotenv
from fpdf import FPDF
from datetime import datetime
import zipfile
try:
    from PyPDF2 import PdfMerger, PdfReader
except ImportError:
    PdfMerger = None
    PdfReader = None

load_dotenv()

# Initialize OpenAI client with Streamlit secrets fallback
def get_openai_client():
    """Get OpenAI client using Streamlit secrets or environment variable"""
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", os.getenv('OPENAI_API_KEY'))
    except:
        api_key = os.getenv('OPENAI_API_KEY')
    return OpenAI(api_key=api_key)

MODEL = "gpt-4o-mini"

# Coach names list
COACH_NAMES = [
    "O'Neal Heard",
    "Chrissy Howard",
    "La'Wanda Olaniran",
    "Bianca Pottinger",
    "Masey Twyman",
    "Emmanuel Martinez"
]

def get_base64_of_image(path):
    """Safe image loading with error handling"""
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except (FileNotFoundError, OSError, PermissionError) as e:
        print(f"Image load error for {path}: {e}")
        return None

def get_background_image():
    """Get the highway background image"""
    possible_paths = [
        "data/highway_background.jpg",
        "assets/highway_background.jpg",
        "data/assets/highway_background.jpg",
        "../data/highway_background.jpg"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            encoded = get_base64_of_image(path)
            if encoded:
                return f"data:image/jpeg;base64,{encoded}"

    return None

def get_freeworld_logo():
    """Get the FreeWorld wordmark logo"""
    possible_paths = [
        "data/FW-Wordmark-Roots@3x.png",
        "assets/FW-Wordmark-Roots@3x.png",
        "data/assets/FW-Wordmark-Roots@3x.png",
        "../data/FW-Wordmark-Roots@3x.png",
        "data/fw_logo.png",
        "assets/fw_logo.png"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            encoded = get_base64_of_image(path)
            if encoded:
                return encoded

    return ""

def extract_text_from_image(image_file):
    """Extract text from uploaded image using OpenAI Vision API"""
    try:
        client = get_openai_client()
        # Convert uploaded file to base64
        image_bytes = image_file.read()
        image_file.seek(0)  # Reset file pointer for display
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this document. Include all relevant details clearly formatted."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_contact_name(notification_text):
    """Extract contact person name from notification for salutation"""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """Extract ONLY the contact person's name from this pre-adverse notification for use in a letter salutation.

If there's a specific person mentioned (e.g., "Contact John Smith" or "Sincerely, Jane Doe"), return just their name.
If there's NO specific contact person mentioned, return exactly: "Hiring Team"

Return ONLY the name, nothing else."""
                },
                {
                    "role": "user",
                    "content": notification_text
                }
            ],
            temperature=0.1,
            max_tokens=50
        )

        name = response.choices[0].message.content.strip()
        return name if name else "Hiring Team"
    except Exception as e:
        print(f"Error extracting contact name: {e}")
        return "Hiring Team"

def analyze_notification(notification_text):
    """Analyze the pre-adverse notification to understand context and instructions"""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at analyzing pre-adverse action notifications. Extract ALL key information:

1. **Employer/Company name**
2. **Specific concerns** mentioned (criminal record, credit, MVR, etc.)
3. **How to respond**: Email address, mailing address, fax, portal, etc.
4. **Deadline**: How many days they have to respond (usually 5-7 business days)
5. **What they're asking for**: Written statement, supporting documents, dispute form, etc.
6. **Contact person**: Name and contact info if provided
7. **Reference numbers**: Case ID, application ID, etc.

Be thorough - Free Agents need clear instructions on HOW and WHERE to send their response."""
                },
                {
                    "role": "user",
                    "content": f"Analyze this pre-adverse notification and extract ALL key information, especially HOW TO RESPOND:\n\n{notification_text}"
                }
            ],
            temperature=0.3,
            max_tokens=800
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing notification: {str(e)}"

def analyze_background_check(background_check_text):
    """Analyze the background check to understand what the employer will see"""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a supportive career counselor analyzing a background check report. Extract key information that will help the Free Agent understand what the employer sees:

1. **Charges/Convictions listed**: What specific offenses appear?
2. **Dates**: When did these occur?
3. **Dispositions**: What was the outcome (convicted, dismissed, pending)?
4. **Severity**: Misdemeanor vs felony
5. **Patterns**: Single incident vs multiple offenses
6. **Time since incident**: How long ago

Be compassionate and factual. This helps the Free Agent understand what they need to address in their response."""
                },
                {
                    "role": "user",
                    "content": f"Analyze this background check and help the Free Agent understand what the employer will see:\n\n{background_check_text}"
                }
            ],
            temperature=0.3,
            max_tokens=800
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing background check: {str(e)}"

def generate_followup_question(question_key, user_answer, previous_context):
    """Generate 1-2 AI follow-up questions based on the user's answer"""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a supportive career counselor helping someone respond to a pre-adverse action letter. Based on their answer, ask 1-2 brief follow-up questions to get MORE SPECIFIC DETAILS that will make their response letter stronger.

Keep follow-up questions:
- SHORT (one sentence)
- FOCUSED on getting concrete details
- SUPPORTIVE in tone
- Aimed at strengthening their response

If their answer is already very detailed, say "Got it, that's helpful!" and don't ask follow-ups."""
                },
                {
                    "role": "user",
                    "content": f"""Question topic: {question_key}

Their answer: {user_answer}

Previous context: {previous_context}

Generate 0-2 brief follow-up questions to get more specific details that will strengthen their response letter. If their answer is already detailed enough, just say "Got it, that's helpful!" and move on."""
                }
            ],
            temperature=0.7,
            max_tokens=150
        )

        followup = response.choices[0].message.content.strip()

        # If AI says it's good enough, return None to skip followup
        if any(phrase in followup.lower() for phrase in ["got it", "that's helpful", "sounds good", "perfect"]):
            return None

        return followup
    except Exception as e:
        print(f"Error generating follow-up: {str(e)}")
        return None

def chat_with_gpt(messages):
    """Have a conversation with GPT"""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Voice/TTS features removed per user request

def generate_response_letter(conversation_history, notification_text, agent_name="", contact_name="Hiring Team", agent_phone="", agent_email=""):
    """Generate a professional response letter based on the conversation"""

    # Extract key points from conversation
    conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])

    framework_prompt = f"""You are an expert employment attorney and career counselor specializing in fair chance hiring and FCRA compliance. You're helping a Free Agent (CDL driver or warehouse worker) craft a compelling, legally-informed response to a pre-adverse action notification.

=== CRITICAL CONTEXT ===
NOTIFICATION TEXT:
{notification_text}

CONVERSATION WITH FREE AGENT:
{conversation_text}

=== YOUR TASK ===
Generate a powerful pre-adverse action response letter that maximizes employment chances while maintaining complete honesty and professionalism.

=== CRITICAL: HONESTY ABOVE ALL ===
**DO NOT FABRICATE OR EXAGGERATE ANYTHING**
- ONLY use information the Free Agent explicitly provided in the conversation
- If they didn't mention specific qualifications, DON'T make them up
- If they didn't mention specific programs or achievements, DON'T invent them
- Vague but honest is INFINITELY better than specific but false
- Getting caught in a lie will destroy their credibility and chances
- When in doubt, leave it out

**What you CAN reasonably infer:**
- They likely received some rehabilitation opportunities during incarceration (but keep it general unless they specified)
- They've had time to reflect if significant time has passed
- They have support from FreeWorld program (this is true for all users)

**What you CANNOT infer or fabricate:**
- Specific job experience they didn't mention
- Specific programs or certifications they didn't mention
- Specific achievements or metrics they didn't provide
- Character references they didn't offer

=== RESEARCH-BACKED BEST PRACTICES YOU MUST FOLLOW ===

**1. IMMEDIATE ACCOUNTABILITY - NO EXCUSES**
- Own the past directly: "I take full responsibility for my past actions"
- Be factual about offense, date, disposition (1-2 sentences max)
- DO NOT blame circumstances, other people, or make excuses
- Pivot quickly from acknowledgment to transformation

**2. ADDRESS KEY FACTORS EMPLOYERS CONSIDER**
Make it easy for them to see you're low-risk:
- Nature & gravity of offense + job relevance (or lack thereof)
- Time passed since conviction + clean record since
- Nature of job sought + why you're low-risk for THIS specific position

**3. BUILD VERIFIABLE EVIDENCE-BASED NARRATIVE**
Use concrete details from the conversation:
- Specific programs completed (with dates, hours, certificates)
- Measurable achievements (e.g., "18 months steady employment, zero incidents")
- Quantifiable community service, training hours, volunteer work
- Named references who can verify change (probation officers, employers, case managers)

**4. CRAFT THE TRANSFORMATION STORY ARC**
- Past (Brief - 1-2 sentences): What happened and when
- Turning Point (1 sentence): "This experience made me realize..."
- Actions Taken (2-3 specific examples): Education, treatment, employment, service
- Current State (1-2 sentences): Stability, achievements, who you are today
- Future Focus (1 sentence): Goals and how this job fits your trajectory

**5. JOB-SPECIFIC RISK MITIGATION**
For CDL/Transportation roles emphasize:
- Clean driving record post-conviction
- Safety training, defensive driving courses
- Understanding of DOT regulations and high safety standards
- Drug & Alcohol Clearinghouse clearance (if applicable)

For Warehouse/Logistics emphasize:
- Reliability, attendance, safety compliance track record
- Certifications (forklift, OSHA, safety training)
- Prior warehouse experience with zero incidents

**6. REQUEST FAIR CONSIDERATION OF YOUR INDIVIDUAL CIRCUMSTANCES**
Use humble, non-threatening language:
"I respectfully ask that you consider my individual circumstances - the specific nature of my offense, the significant time that has passed, my rehabilitation efforts, and the requirements of this position. I believe a complete review of my situation will show that I can be a reliable, dedicated member of your team."

**7. MAINTAIN PROFESSIONAL, FORWARD-LOOKING TONE**
- Confident but not defensive
- Grateful for the opportunity to respond
- Enthusiastic about the role and company
- Professional acknowledgment of employer's legitimate concerns

**8. CRITICAL MISTAKES TO AVOID**
- ❌ Defensive or angry tone
- ❌ Vague claims without proof ("I've changed" vs "I completed 300 hours of CDL training")
- ❌ Dwelling on the past instead of current readiness
- ❌ Making excuses or blaming others
- ❌ Being dishonest about the conviction
- ❌ Writing too much (keep to 250-350 words max)

=== LETTER STRUCTURE (FOLLOW EXACTLY) ===

**CRITICAL: NO PLACEHOLDERS OR BRACKETS**
- DO NOT include [bracketed text] or placeholder text like [Company Name], [Position], [Date], etc.
- DO NOT include employer address at the top
- START with the salutation: "Dear {contact_name},"
- Then begin the first paragraph of content
- Use actual information from the conversation or leave it general
- If you don't know the company name or position, write around it naturally without brackets

**SALUTATION:**
Dear {contact_name},

**PARAGRAPH 1 (Acknowledgment):**
- Thank employer for opportunity to respond
- Express appreciation for fair hiring practices
- If position name was mentioned in conversation, state it. Otherwise, be general ("the position I applied for")

**PARAGRAPH 2 (Accountability):**
- Confirm accuracy of background check OR dispute specific errors
- Take immediate accountability with factual statement (1-2 sentences max)
- "I take full responsibility for my past actions"

**PARAGRAPH 3 (Rehabilitation - THE HEART):**
- "Since my conviction [X years ago], I have made significant changes..."
- ONLY include rehabilitation efforts they ACTUALLY mentioned in the conversation
- Use their EXACT words and details when possible
- If they mentioned vague things, keep them vague (e.g., "worked on myself" not "completed extensive rehabilitation program")
- If they only mentioned 1-2 things, that's okay - quality over fabricated quantity
- Examples of what to include ONLY if they mentioned it:
  * Education/training completed (ONLY if they specified it)
  * Employment (ONLY if they mentioned it - use their words)
  * Treatment/programs (ONLY if they specified)
  * Community service/volunteer work (ONLY if they mentioned it)
  * Family support (ONLY if they mentioned it)
- State clean record length ONLY if they mentioned it or it's clear from dates
- DO NOT invent stability indicators they didn't mention

**PARAGRAPH 4 (Job Fit + Key Factors):**
- ONLY restate qualifications they ACTUALLY mentioned
- If they didn't mention experience, certifications, or skills - DON'T make them up
- Focus on key factors (time passed, nature of offense, job requirements) which are factual
- If they lack qualifications, emphasize willingness to learn and commitment instead
- Connect factors honestly: "My [offense type] occurred [X years ago] and is unrelated to the [safety/trust/responsibility] requirements of this [position type]"
- Express confidence in ability to meet standards (this is okay even without specific qualifications)

**PARAGRAPH 5 (Request + Closing):**
- Humbly request consideration of individual circumstances (NOT EEOC language)
- Keep it humble and grateful, not legalistic or threatening
- Reaffirm strong interest in position
- Express gratitude for consideration

**SIGNATURE:**
"Sincerely,"
Then on separate lines:
{agent_name}
{agent_phone}
{agent_email}

=== OUTPUT REQUIREMENTS ===
- Length: 200-250 words MAX (must fit on one page with signature)
- Tone: Professional, grateful, humble (NOT defensive or legalistic)
- Evidence: ONLY what they actually mentioned (quality over fabricated quantity)
- Key Factors: Time passed, offense nature, job fit addressed naturally
- Call to Action: Humble request for fair consideration
- Format: START with "Dear {contact_name}," then professional business letter body (NO letterhead, NO date line, NO employer address at top)
- NO EEOC REFERENCES: Keep it personal, not legal
- NO PLACEHOLDERS: Never use brackets [like this] or placeholder text. Use actual info or write generically.

=== FORMAT EXAMPLE ===
The letter should start like this:

"Dear {contact_name},

Thank you for the opportunity to respond to the pre-adverse action notification regarding my application. I appreciate your commitment to fair hiring practices..."

NOT like this:
"[Date]

[Employer Address]

Dear [Hiring Manager],

Thank you for..."

=== IMPORTANT ===
This letter can determine whether this person gets a second chance at employment. Make it COMPELLING, EVIDENCE-BASED, and LEGALLY-INFORMED. Balance accountability with hope. Show transformation through concrete proof, not vague claims. Make the employer's decision easy by addressing their concerns proactively.

=== FINAL REMINDER: DO NOT FABRICATE ===
Before you write, review the conversation one more time. ONLY include information they explicitly provided. If the conversation was light on details, write a shorter, more general letter. An honest letter with less detail is INFINITELY better than a detailed letter with fabricated information. Getting caught in a lie will destroy their chances completely.

Generate the letter now."""

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert career counselor helping individuals with criminal records craft professional, compelling responses to pre-adverse action notifications. Your responses are sincere, professional, and show accountability while emphasizing growth."
                },
                {
                    "role": "user",
                    "content": framework_prompt
                }
            ],
            temperature=0.7,
            max_tokens=800
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating letter: {str(e)}"

def generate_coach_letter(agent_name, coach_name, conversation_history, notification_analysis, contact_name="Hiring Team"):
    """Generate a supportive letter from the coach"""
    try:
        client = get_openai_client()

        conversation_summary = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-10:]])

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a FreeWorld Success Coach writing a professional, compelling letter of support for a Free Agent (program participant) who received a pre-adverse action notice. Your letter provides critical THIRD-PARTY VALIDATION that strengthens their response package.

⚠️ === CRITICAL WORD COUNT REQUIREMENT === ⚠️
**MAXIMUM LENGTH: 200-250 WORDS TOTAL - NO EXCEPTIONS**
This letter MUST fit on one page with the signature. If you exceed 250 words, the signature will spill onto page 2 and look unprofessional.
Count every word carefully. Be concise and impactful. Quality over quantity.

=== CRITICAL: HONESTY IN THIRD-PARTY VALIDATION ===
**DO NOT FABRICATE OBSERVATIONS OR ACHIEVEMENTS**
- ONLY reference information from the conversation that the Free Agent actually provided
- You are writing based on the conversation, not direct long-term observation
- Be general about your support role rather than making up specific observations
- It's okay to speak generally about their participation in the FreeWorld program
- DO NOT invent specific achievements, program completions, or character traits they didn't mention
- If the conversation was brief, keep your letter appropriately general

**What you CAN truthfully say:**
- You work with them through the FreeWorld program
- You've assisted them in preparing this response
- You will provide ongoing retention coaching support
- FreeWorld is committed to supporting their success
- They've demonstrated accountability by taking this process seriously

**What you CANNOT say without evidence:**
- Specific observations of their character over time (you just met them in this conversation)
- Specific achievements or milestones unless they mentioned them
- Claims about their work ethic or reliability unless they provided examples
- Made-up stories about their participation in FreeWorld programs

=== WHAT MAKES AN EFFECTIVE COACH SUPPORT LETTER ===

**1. ESTABLISH YOUR CREDIBILITY IMMEDIATELY**
- Introduce yourself as a FreeWorld Success Coach
- Briefly explain FreeWorld's mission (reentry support for CDL drivers and warehouse workers)
- State your role and relationship to the candidate (how long you've worked with them)

**2. PROVIDE SPECIFIC, VERIFIABLE OBSERVATIONS**
Based on the conversation context, highlight:
- Concrete examples of their work ethic, reliability, and accountability
- Specific program milestones they've achieved (training completed, certifications earned)
- Observable character traits with examples (punctuality, taking initiative, helping others)
- Measurable progress they've made (employment stability, skill development)

**3. ADDRESS THE ELEPHANT IN THE ROOM**
- Acknowledge that you're aware of their background
- Emphasize how they've used it as motivation for growth
- Compare their past choices to their current demonstrated values
- Speak to their accountability and insight into past mistakes

**4. CONNECT TO JOB REQUIREMENTS**
- Reference the specific position they're applying for
- Explain why their skills and character make them well-suited
- Address job-specific concerns (safety for CDL, reliability for warehouse)
- Provide context on their readiness for this type of work

**5. MAKE A DIRECT ADVOCACY REQUEST**
- Humbly ask employer to consider the whole person, not just the background check
- Keep it personal and supportive, NOT legalistic (no EEOC references)
- Express confidence in their ability to succeed
- Offer to serve as a reference or provide additional information

**6. MAINTAIN PROFESSIONAL CREDIBILITY**
- Be honest and realistic (don't oversell or make unrealistic claims)
- Use professional, warm tone (compassionate but not emotional)
- Include your contact information for verification
- Sign with your full title and FreeWorld affiliation

=== CRITICAL DO'S AND DON'TS ===

✅ DO:
- Provide specific examples with concrete details
- Acknowledge the employer's legitimate concerns
- Speak to character traits you've personally observed
- Offer to serve as a reference or provide more info
- Use professional business letter format

❌ DON'T:
- Make vague claims without proof ("they're a good person")
- Minimize the seriousness of their offense
- Be defensive or emotional
- Oversell or make unrealistic promises
- Ignore the employer's concerns

=== LETTER STRUCTURE ===

**CRITICAL: NO PLACEHOLDERS OR BRACKETS**
- DO NOT include [bracketed text] or placeholder text
- DO NOT include employer address at the top
- START with the salutation: "Dear {contact_name},"
- Then begin with the first paragraph of content
- Use the actual agent name provided, not [Agent Name]
- If you don't know specific details, write around it naturally without brackets

**SALUTATION:**
Dear {contact_name},

**PARAGRAPH 1 (Introduction):**
- Introduce yourself with actual coach name: "My name is [actual coach name], and I am a Success Coach with FreeWorld..."
- Explain FreeWorld's mission: "FreeWorld is a nonprofit organization that helps individuals with criminal histories obtain their CDL license and secure employment in the transportation industry"
- Subtly convey organizational credibility (established, professional, well-resourced)
- State relationship naturally: "I have been working with [actual agent name] through our program..."
- Purpose: "I am writing to provide context and strong support for their application..."

**PARAGRAPH 2 (Observed Character & Rehabilitation):**
- Specific examples of their work ethic, accountability, reliability
- Concrete rehabilitation achievements you've witnessed
- How they've demonstrated growth and maturity
- Observable character traits with real examples

**PARAGRAPH 3 (Job Fit & Advocacy):**
- Reference the specific position and why they're qualified
- Connect their demonstrated traits to job requirements
- Address any job-specific concerns (safety, reliability, trust)
- Acknowledge their background while emphasizing transformation

**PARAGRAPH 4 (Ongoing Support & FreeWorld Backing):**
- Explain your role as their retention coach who will check in regularly throughout their employment
- Tactfully convey FreeWorld's institutional strength: "FreeWorld is an established nonprofit organization dedicated to workforce development"
- Emphasize ongoing support structure: "I will maintain regular contact with [Agent Name] to ensure their continued success and address any workplace challenges"
- Make it clear this candidate has substantial professional backing and support

**PARAGRAPH 5 (Request & Closing):**
- Humbly request fair consideration of the whole person (NO EEOC language)
- Keep it warm and supportive, not legalistic
- Express confidence in their ability to succeed
- Offer to serve as reference or provide additional information
- Thank employer for taking time to consider

**SIGNATURE:**
"Respectfully,"
Then on separate lines:
{coach_name}
(408) 668-3608
{coach_name.split()[0].lower().replace("'", "")}@freeworld.org

=== TONE GUIDELINES ===
- Professional and credible (not emotional or defensive)
- Warm and supportive (but not overly familiar)
- Honest and realistic (don't oversell)
- Advocacy-focused (clear call to action for employer)

=== OUTPUT REQUIREMENTS ===
- Length: 200-250 words MAX (must fit on one page with signature)
- Tone: Professional, supportive, credible (NOT legalistic)
- Evidence: ONLY what they actually mentioned in conversation
- Format: START with "Dear {contact_name}," then professional business letter body (NO letterhead, NO date at top, NO employer address at top)
- Contact info: Will be added in signature block by PDF generator
- MUST include retention coaching and organizational support paragraph
- NO EEOC REFERENCES: Keep it warm and personal, not threatening
- NO PLACEHOLDERS: Use actual names and information, not brackets

=== FORMAT EXAMPLE ===
Start with salutation, like this:

"Dear {contact_name},

My name is [actual coach name], and I am a Success Coach with FreeWorld, a nonprofit organization that helps individuals with criminal histories obtain their CDL license and secure employment..."

NOT like this:
"[Date]

[Employer Name]
[Address]

Dear Hiring Manager,

My name is..."

=== CRITICAL ===
The retention coaching paragraph is essential. Employers need to know this candidate has ongoing professional support and isn't just being sent out alone. This demonstrates FreeWorld's commitment and reduces perceived risk for the employer.

DO NOT reference EEOC, legal requirements, or make this sound threatening. The goal is to be a warm, credible advocate - not to lecture the employer about compliance. Keep it humble and supportive.

Generate a powerful coach support letter that provides third-party validation and strengthens the candidate's response package."""
                },
                {
                    "role": "user",
                    "content": f"""Write a compelling letter of support for {agent_name}, a FreeWorld program participant.

COACH INFORMATION:
Name: {coach_name}
Role: Success Coach at FreeWorld

TODAY'S DATE: {datetime.now().strftime("%B %d, %Y")}

CANDIDATE CONTEXT:
{conversation_summary}

EMPLOYER'S CONCERNS (from notification):
{notification_analysis}

Generate a powerful, credible support letter that provides third-party validation and advocates for giving {agent_name} a fair chance. Be specific, honest, and professional."""
                }
            ],
            temperature=0.7,
            max_tokens=800
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating coach letter: {str(e)}"

class FreeWorldLetterPDF(FPDF):
    """Professional legal letterhead generator for FreeWorld"""

    def __init__(self):
        super().__init__(orientation='P', unit='pt', format='Letter')
        self.set_margins(72, 90, 72)  # Professional margins with extra top space
        self.set_auto_page_break(True, margin=90)

        # FreeWorld Brand Colors
        self.fw_roots = (0, 71, 81)
        self.fw_midnight = (25, 25, 49)
        self.fw_gray = (100, 100, 100)

    def header(self):
        """Professional letterhead with round logo"""
        # Try to load round FreeWorld logo
        logo_paths = [
            "assets/FW-Logo-Roots@2x.png",
            "assets/FW-Logo-Roots.svg",
            "assets/fw_logo.png",
            "fw_logo.png"
        ]

        logo_loaded = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    # Place logo at top left - professional size
                    self.image(logo_path, 72, 36, 45)
                    logo_loaded = True
                    break
                except Exception as e:
                    print(f"Failed to load {logo_path}: {e}")
                    continue

        # Organization name and contact info next to logo
        self.set_xy(125, 40)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(*self.fw_roots)
        self.cell(0, 12, 'FreeWorld', align='L')

        self.set_xy(125, 55)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*self.fw_gray)
        self.cell(0, 10, 'Career Services & Workforce Development', align='L')

        self.set_xy(125, 67)
        self.cell(0, 10, '(408) 668-3608  |  www.freeworld.org', align='L')

        # Professional divider line
        self.set_draw_color(*self.fw_roots)
        self.set_line_width(0.5)
        self.line(72, 95, 540, 95)

        if not logo_loaded:
            # Fallback: Just use text header
            self.set_xy(72, 40)
            self.set_font('Helvetica', 'B', 18)
            self.set_text_color(*self.fw_roots)
            self.cell(0, 20, 'FreeWorld', align='L')

        self.ln(20)

    def footer(self):
        """Professional footer with confidentiality notice"""
        self.set_y(-65)

        # Top line
        self.set_draw_color(*self.fw_gray)
        self.set_line_width(0.25)
        self.line(72, self.get_y(), 540, self.get_y())

        self.ln(8)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self.fw_gray)
        self.cell(0, 10, 'FreeWorld  |  Building Pathways to Economic Freedom', align='C')
        self.ln(10)
        self.set_font('Helvetica', 'I', 7)
        self.multi_cell(0, 9,
            'This document contains confidential information intended solely for the named recipient. '
            'If you have received this in error, please notify FreeWorld immediately.',
            align='C')

    def add_letter_content(self, content):
        """Add letter content with professional legal document formatting"""
        self.set_font('Times', '', 11)
        self.set_text_color(*self.fw_midnight)

        # Sanitize Unicode characters for Times font (latin-1 encoding)
        def sanitize_unicode(text):
            """Replace Unicode characters that Times font doesn't support"""
            replacements = {
                '\u2018': "'",   # Left single quote
                '\u2019': "'",   # Right single quote/apostrophe
                '\u201C': '"',   # Left double quote
                '\u201D': '"',   # Right double quote
                '\u2013': '-',   # En dash
                '\u2014': '--',  # Em dash
                '\u2026': '...'  # Ellipsis
            }
            for unicode_char, ascii_char in replacements.items():
                text = text.replace(unicode_char, ascii_char)
            return text

        # Split content into paragraphs
        paragraphs = content.split('\n\n')

        for para in paragraphs:
            if para.strip():
                # Sanitize paragraph content
                clean_para = sanitize_unicode(para.strip())

                # Ensure x position is at left margin before each paragraph
                self.set_x(self.l_margin)

                # Handle special formatting
                if clean_para.startswith('Dear'):
                    self.set_font('Times', '', 11)
                    self.multi_cell(0, 16, clean_para)
                    self.ln(12)
                elif clean_para.startswith('Sincerely'):
                    self.ln(12)
                    self.set_font('Times', '', 11)
                    self.multi_cell(0, 16, clean_para)
                else:
                    self.set_font('Times', '', 11)
                    # Professional line spacing
                    self.multi_cell(0, 16, clean_para)
                    self.ln(10)

class FreeWorldCertificatePDF(FPDF):
    """Professional certificate generator - law school diploma quality"""

    def __init__(self):
        super().__init__(orientation='L', unit='pt', format='Letter')  # Landscape
        self.set_margins(60, 60, 60)
        self.set_auto_page_break(False)

        # Professional colors - understated elegance
        self.fw_roots = (0, 71, 81)
        self.fw_midnight = (25, 25, 49)
        self.fw_gold = (180, 151, 90)  # Professional gold accent
        self.fw_gray = (100, 100, 100)

    def create_certificate(self, agent_name, coach_name, completion_date=None):
        """Create a highly professional certificate - law school quality"""
        if not completion_date:
            completion_date = datetime.now().strftime("%B %d, %Y")

        self.add_page()

        # Professional double border - elegant, not corny
        self.set_line_width(1.5)
        self.set_draw_color(*self.fw_roots)
        self.rect(40, 40, 792-80, 612-80, 'D')

        self.set_line_width(0.5)
        self.set_draw_color(*self.fw_gold)
        self.rect(48, 48, 792-96, 612-96, 'D')

        # Round FreeWorld logo at top center - professional size
        logo_paths = [
            "assets/FW-Logo-Roots@2x.png",
            "assets/FW-Logo-Roots.svg",
            "assets/fw_logo.png"
        ]

        logo_loaded = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    # Centered, professional size
                    self.image(logo_path, 346, 70, 100)
                    logo_loaded = True
                    break
                except Exception as e:
                    print(f"Failed to load {logo_path}: {e}")
                    continue

        # Organization name under logo
        self.set_xy(100, 180)
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(*self.fw_roots)
        self.cell(592, 15, 'FreeWorld', align='C')

        self.set_xy(100, 198)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*self.fw_gray)
        self.cell(592, 12, 'Career Services & Workforce Development', align='C')

        # Elegant divider
        self.set_line_width(0.5)
        self.set_draw_color(*self.fw_gold)
        self.line(296, 220, 496, 220)

        # Certificate title - understated
        self.set_xy(100, 240)
        self.set_font('Times', 'B', 22)
        self.set_text_color(*self.fw_midnight)
        self.cell(592, 25, 'Certificate of Program Completion', align='C')

        # "This is to certify that" - formal legal language
        self.set_xy(100, 275)
        self.set_font('Times', 'I', 12)
        self.set_text_color(*self.fw_gray)
        self.cell(592, 18, 'This is to certify that', align='C')

        # Participant name - elegant, prominent
        self.set_xy(100, 305)
        self.set_font('Times', 'B', 26)
        self.set_text_color(*self.fw_midnight)
        self.cell(592, 30, agent_name, align='C')

        # Thin line under name - professional, not heavy
        self.set_line_width(0.5)
        self.set_draw_color(*self.fw_midnight)
        name_width = self.get_string_width(agent_name)
        center_x = 396  # Center of page
        line_start = center_x - (name_width / 2) - 20
        line_end = center_x + (name_width / 2) + 20
        self.line(line_start, 342, line_end, 342)

        # Achievement description - formal, professional
        self.set_xy(150, 360)
        self.set_font('Times', '', 11)
        self.set_text_color(*self.fw_midnight)
        self.multi_cell(492, 16,
            'has successfully completed the FreeWorld CDL Training Program,\n'
            'demonstrating the knowledge, skill, and determination required\n'
            'to begin a successful career in the trucking industry.',
            align='C')

        # Signature section - law school style with three signatures
        # Coach signature (left)
        self.set_xy(100, 450)
        self.set_font('Times', 'BI', 20)  # Larger, fancier handwritten style
        self.set_text_color(*self.fw_roots)
        self.cell(180, 12, coach_name, align='C')

        self.set_line_width(0.5)
        self.set_draw_color(*self.fw_midnight)
        self.line(120, 467, 260, 467)

        self.set_xy(100, 470)
        self.set_font('Times', 'I', 8)
        self.set_text_color(*self.fw_gray)
        self.cell(180, 10, 'Success Coach', align='C')

        # CEO signature (center)
        self.set_xy(306, 450)
        self.set_font('Times', 'BI', 20)  # Larger, fancier handwritten style
        self.set_text_color(*self.fw_roots)
        self.cell(180, 12, 'Jason Wang', align='C')

        self.set_line_width(0.5)
        self.set_draw_color(*self.fw_midnight)
        self.line(326, 467, 466, 467)

        self.set_xy(306, 470)
        self.set_font('Times', 'I', 8)
        self.set_text_color(*self.fw_gray)
        self.cell(180, 10, 'CEO, FreeWorld', align='C')

        # Date (right)
        self.set_xy(512, 450)
        self.set_font('Times', '', 10)
        self.set_text_color(*self.fw_midnight)
        self.cell(180, 12, completion_date, align='C')

        self.set_line_width(0.5)
        self.set_draw_color(*self.fw_midnight)
        self.line(532, 467, 672, 467)

        self.set_xy(512, 470)
        self.set_font('Times', 'I', 8)
        self.set_text_color(*self.fw_gray)
        self.cell(180, 10, 'Date', align='C')

        # Seal/emblem placeholder text at bottom - subtle
        self.set_xy(100, 530)
        self.set_font('Times', 'I', 8)
        self.set_text_color(*self.fw_gray)
        self.cell(592, 10, 'Building Pathways to Economic Freedom', align='C')

        # Document authenticity line - very professional
        self.set_xy(100, 545)
        self.set_font('Times', '', 7)
        self.set_text_color(150, 150, 150)
        self.cell(592, 8, 'This certificate verifies completion of FreeWorld CDL training and career development programs  |  www.freeworld.org', align='C')

def format_phone_number(phone):
    """Format phone number to (XXX) XXX-XXXX format"""
    if not phone:
        return ""
    # Remove all non-numeric characters
    digits = ''.join(filter(str.isdigit, phone))
    # Format as (XXX) XXX-XXXX if we have 10 digits
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    # Return original if not 10 digits
    return phone

def generate_pdfs(agent_name, coach_name, response_letter, coach_letter, agent_phone="", agent_email=""):
    """Generate all three PDFs and return as bytes"""
    pdfs = {}

    # Format phone number for professional display
    formatted_phone = format_phone_number(agent_phone)

    # 1. Free Agent Response Letter
    try:
        pdf1 = FreeWorldLetterPDF()
        pdf1.add_page()
        pdf1.set_xy(72, 120)
        pdf1.set_font('Times', '', 11)
        pdf1.cell(0, 15, datetime.now().strftime("%B %d, %Y"))
        pdf1.ln(30)
        pdf1.set_x(72)  # Reset x position to left margin before adding content
        pdf1.add_letter_content(response_letter)

        # Use modern fpdf API (v2.x) - output() returns bytearray, convert to bytes
        pdf_output = pdf1.output()
        pdfs['agent_letter'] = bytes(pdf_output) if isinstance(pdf_output, bytearray) else pdf_output
    except Exception as e:
        print(f"Error generating agent letter PDF: {e}")
        import traceback
        traceback.print_exc()
        pdfs['agent_letter'] = None

    # 2. Coach Support Letter with handwritten-style coach signature
    try:
        pdf2 = FreeWorldLetterPDF()
        pdf2.add_page()
        pdf2.set_xy(72, 120)
        pdf2.set_font('Times', '', 11)
        pdf2.cell(0, 15, datetime.now().strftime("%B %d, %Y"))
        pdf2.ln(30)
        pdf2.set_x(72)  # Reset x position to left margin before adding content
        pdf2.add_letter_content(coach_letter)

        # Signature is now generated in the letter text by AI - no PDF additions needed

        # Use modern fpdf API (v2.x) - output() returns bytearray, convert to bytes
        pdf_output = pdf2.output()
        pdfs['coach_letter'] = bytes(pdf_output) if isinstance(pdf_output, bytearray) else pdf_output
    except Exception as e:
        print(f"Error generating coach letter PDF: {e}")
        import traceback
        traceback.print_exc()
        pdfs['coach_letter'] = None

    # 3. Certificate
    try:
        pdf3 = FreeWorldCertificatePDF()
        pdf3.create_certificate(agent_name, coach_name)
        # Use modern fpdf API (v2.x) - output() returns bytearray, convert to bytes
        pdf_output = pdf3.output()
        pdfs['certificate'] = bytes(pdf_output) if isinstance(pdf_output, bytearray) else pdf_output
    except Exception as e:
        print(f"Error generating certificate PDF: {e}")
        import traceback
        traceback.print_exc()
        pdfs['certificate'] = None

    return pdfs

def create_combined_package(agent_name, pdfs):
    """Create a single PDF containing all three documents as separate pages"""
    # This now uses merge_pdfs instead of creating a ZIP
    return merge_pdfs(pdfs)

def merge_pdfs(pdfs):
    """Merge all three PDFs into a single PDF document"""
    try:
        if not PdfMerger:
            print("PyPDF2 not installed - cannot merge PDFs")
            return None

        # Create PDF merger
        merger = PdfMerger()

        # Add each PDF in order
        if pdfs.get('agent_letter'):
            agent_pdf = io.BytesIO(pdfs['agent_letter'])
            merger.append(agent_pdf)

        if pdfs.get('coach_letter'):
            coach_pdf = io.BytesIO(pdfs['coach_letter'])
            merger.append(coach_pdf)

        if pdfs.get('certificate'):
            cert_pdf = io.BytesIO(pdfs['certificate'])
            merger.append(cert_pdf)

        # Write merged PDF to bytes
        merged_buffer = io.BytesIO()
        merger.write(merged_buffer)
        merger.close()

        merged_buffer.seek(0)
        return merged_buffer.getvalue()
    except Exception as e:
        print(f"Error merging PDFs: {e}")
        import traceback
        traceback.print_exc()
        return None

def initialize_session_state():
    """Initialize session state variables"""
    if 'step' not in st.session_state:
        st.session_state.step = 'coach_select'
    if 'coach_name' not in st.session_state:
        st.session_state.coach_name = ""
    if 'agent_name' not in st.session_state:
        st.session_state.agent_name = ""
    if 'agent_phone' not in st.session_state:
        st.session_state.agent_phone = ""
    if 'agent_email' not in st.session_state:
        st.session_state.agent_email = ""
    if 'notification_text' not in st.session_state:
        st.session_state.notification_text = ""
    if 'notification_analysis' not in st.session_state:
        st.session_state.notification_analysis = ""
    if 'contact_name' not in st.session_state:
        st.session_state.contact_name = "Hiring Team"
    if 'background_check_text' not in st.session_state:
        st.session_state.background_check_text = ""
    if 'background_check_analysis' not in st.session_state:
        st.session_state.background_check_analysis = ""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'awaiting_followup' not in st.session_state:
        st.session_state.awaiting_followup = False
    if 'followup_question' not in st.session_state:
        st.session_state.followup_question = ""
    if 'generated_letter' not in st.session_state:
        st.session_state.generated_letter = ""
    if 'coach_letter' not in st.session_state:
        st.session_state.coach_letter = ""
    if 'pdfs' not in st.session_state:
        st.session_state.pdfs = {}
    if 'text_input_key' not in st.session_state:
        st.session_state.text_input_key = 0

# Conversation flow questions
CONVERSATION_QUESTIONS = [
    {
        "question": "First, I want to understand your situation. Can you tell me what the notification says the employer is concerned about? Just give me a brief description in your own words.",
        "question_if_bg_analyzed": "I've reviewed your background check and can see what the employer will see. Is there anything about your record that you think needs clarification or context?",
        "key": "concern",
        "context": "We're starting the conversation to understand the situation",
        "skip_if_bg_analyzed": True  # This question can be skipped if we already have background check info
    },
    {
        "question": "Thanks for sharing that. Now, can you briefly explain what happened and when it occurred? Keep it simple - just the basic facts.",
        "question_if_bg_analyzed": "Thanks. Based on your background check, I can see the dates and charges. Can you briefly tell me in your own words what happened? Keep it simple - just the context around the situation.",
        "key": "context",
        "context": "Getting context about the incident"
    },
    {
        "question": "I appreciate your honesty. What have you done since then to move forward and grow as a person? This could be completing CDL training, staying employed, counseling, community service, or anything else.",
        "key": "growth",
        "context": "Understanding rehabilitation and growth"
    },
    {
        "question": "That's great progress. Now, why do you think this past issue won't affect your ability to do this job safely and professionally?",
        "key": "job_performance",
        "context": "Connecting past to future job performance"
    },
    {
        "question": "Last question: Is there anything else you'd like the employer to know about you? This could be references, work ethic, reliability, or anything that shows who you are today.",
        "key": "additional",
        "context": "Optional additional information"
    }
]

def render_header():
    """Render the mobile-optimized header with FreeWorld branding"""
    bg_image = get_background_image()
    bg_style = f"background-image: url({bg_image});" if bg_image else "background: linear-gradient(135deg, #004751, #593CBC);"
    logo_data = get_freeworld_logo()

    header_html = f"""
    <style>
    /* FreeWorld Brand Colors */
    :root {{
        --fw-roots: #004751;
        --fw-midnight: #191931;
        --fw-freedom-green: #CDF95C;
        --fw-visionary-violet: #593CBC;
        --fw-horizon-grey: #F4F4F4;
    }}

    .header-container {{
        {bg_style}
        background-size: cover;
        background-position: center 15%;
        padding: 40px 20px 30px 20px;
        text-align: center;
        border-radius: 20px;
        margin: -1rem -1rem 2rem -1rem;
    }}

    .header-logo {{
        height: 50px;
        margin-bottom: 15px;
    }}

    .header-title {{
        color: white;
        font-size: 26px;
        font-weight: bold;
        margin: 15px 0 10px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}

    .header-subtitle {{
        color: var(--fw-freedom-green);
        font-size: 16px;
        font-weight: 500;
        margin: 0;
        padding: 0 10px;
    }}
    </style>

    <div class="header-container">
        <img src="data:image/png;base64,{logo_data}" alt="FreeWorld" class="header-logo">
        <h1 class="header-title">Pre-Adverse Response Helper</h1>
        <p class="header-subtitle">AI-powered assistance for crafting professional responses</p>
    </div>
    """

    st.markdown(header_html, unsafe_allow_html=True)


# Streamlit configuration
try:
    from PIL import Image
    production_favicon = Image.open("fw_logo.png")
except (ImportError, FileNotFoundError):
    production_favicon = "📝"

st.set_page_config(
    page_title="FreeWorld Pre-Adverse Response Helper",
    page_icon=production_favicon,
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile optimization
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    padding: 0 !important;
    max-width: 100% !important;
}
.block-container {
    padding: 1rem !important;
    max-width: 600px !important;
    margin: 0 auto !important;
}

/* Card styling */
.stCard {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    margin: 15px 0;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, #004751, #593CBC);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    font-size: 16px;
    font-weight: 600;
    width: 100%;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(89, 60, 188, 0.4);
}

/* Text area styling */
.stTextArea > div > div > textarea {
    border-radius: 12px;
    border: 2px solid #E0E0E0;
    padding: 12px;
    font-size: 15px;
}

.stTextArea > div > div > textarea:focus {
    border-color: #004751;
    box-shadow: 0 0 0 2px rgba(0, 71, 81, 0.1);
}

/* File uploader styling */
.stFileUploader {
    border: 2px dashed #004751;
    border-radius: 12px;
    padding: 20px;
    background: #F4F4F4;
}
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function with conversational chat interface"""
    initialize_session_state()
    render_header()

    # Step 0: Coach and Agent Name Selection
    if st.session_state.step == 'coach_select':
        st.markdown("### 👋 Welcome!")

        st.info("""
        **What is a Pre-Adverse Action Notice?**

        A pre-adverse action notice means an employer found something on your background check that concerns them, but **this is NOT a rejection**. By law, they must give you a chance to respond before making a final decision.

        **Your Rights:**
        - You have 5-7 days to respond (sometimes more)
        - You can explain your situation and show how you've changed
        - You can dispute any errors on your background check
        - The employer must consider your response before deciding

        **How We Help:**
        This tool will guide you through writing a powerful response letter that shows accountability, demonstrates your growth, and gives you the best chance at getting the job. We'll ask you some questions, then generate a professional letter package for you to send.

        Let's get started!
        """)

        st.markdown("---")
        st.markdown("### Your Information")

        # Agent name input
        agent_name = st.text_input(
            "Your Full Name",
            value=st.session_state.agent_name,
            placeholder="First and Last Name",
            key="agent_name_input"
        )

        # Phone number input
        agent_phone = st.text_input(
            "Your Phone Number",
            value=st.session_state.agent_phone,
            placeholder="(555) 555-5555",
            key="agent_phone_input"
        )

        # Email input
        agent_email = st.text_input(
            "Your Email Address",
            value=st.session_state.agent_email,
            placeholder="your.email@example.com",
            key="agent_email_input"
        )

        # Coach selection with "Not sure" option
        coach_options = COACH_NAMES + ["Not sure"]

        # Determine the index for the selectbox
        if st.session_state.coach_name and st.session_state.coach_name in COACH_NAMES:
            coach_index = COACH_NAMES.index(st.session_state.coach_name)
        else:
            # Default to O'Neal Heard (first coach)
            coach_index = 0

        coach_selection = st.selectbox(
            "Select your FreeWorld Success Coach:",
            options=coach_options,
            index=coach_index,
            key="coach_select_dropdown"
        )

        # Map "Not sure" to O'Neal Heard
        if coach_selection == "Not sure":
            coach_name = "O'Neal Heard"
        else:
            coach_name = coach_selection

        if st.button("Continue ➡️", use_container_width=True):
            # Validate all fields are filled
            if not agent_name or not agent_phone or not agent_email or not coach_name:
                st.error("⚠️ Please fill out all fields before continuing.")
            else:
                st.session_state.agent_name = agent_name
                st.session_state.agent_phone = agent_phone
                st.session_state.agent_email = agent_email
                st.session_state.coach_name = coach_name
                st.session_state.step = 'upload'
                st.rerun()

    # Step 1: Upload notification
    elif st.session_state.step == 'upload':
        st.markdown(f"### 👋 Hi {st.session_state.agent_name}!")
        st.markdown("Let's start by looking at your pre-adverse action notification.")

        # Initialize temp storage for this step
        if 'temp_notification_text' not in st.session_state:
            st.session_state.temp_notification_text = ""

        tab1, tab2 = st.tabs(["📝 Paste Text", "📸 Upload Image/File"])

        with tab1:
            notification_text = st.text_area(
                "Paste your notification text here:",
                height=250,
                value=st.session_state.temp_notification_text,
                placeholder="Paste the full text of your pre-adverse action notification here...",
                key="notification_text_area"
            )
            # Store in temp session state
            st.session_state.temp_notification_text = notification_text

        with tab2:
            uploaded_files = st.file_uploader(
                "Take photos or upload screenshots of your notification (you can upload multiple pages)",
                type=['png', 'jpg', 'jpeg', 'pdf', 'txt'],
                accept_multiple_files=True,
                help="You can upload multiple photos if your notification has several pages",
                key="notification_file_uploader"
            )

            if uploaded_files:
                st.success(f"✅ {len(uploaded_files)} file(s) uploaded!")

                # Show preview for images
                for i, uploaded_file in enumerate(uploaded_files):
                    if uploaded_file.type.startswith('image'):
                        st.image(uploaded_file, caption=f"Page {i+1}", use_container_width=True)

        # Always-present buttons outside tabs
        st.markdown("---")
        col1, col2 = st.columns([2, 1])

        with col1:
            if st.button("✅ Submit & Continue", use_container_width=True, key="submit_notification"):
                # Check if we have text or files
                has_text = bool(st.session_state.temp_notification_text.strip())
                has_files = uploaded_files is not None and len(uploaded_files) > 0

                if has_text:
                    # Use pasted text
                    with st.spinner("🔍 Analyzing your notification..."):
                        st.session_state.notification_text = st.session_state.temp_notification_text
                        analysis = analyze_notification(st.session_state.temp_notification_text)
                        st.session_state.notification_analysis = analysis
                        # Extract contact name for letter salutation
                        contact_name = extract_contact_name(st.session_state.temp_notification_text)
                        st.session_state.contact_name = contact_name
                    st.success("✅ Notification analyzed!")
                    st.session_state.step = 'notification_explanation'
                    st.rerun()

                elif has_files:
                    # Extract text from uploaded files
                    with st.spinner("🔍 Reading your notification..."):
                        all_text = []
                        for uploaded_file in uploaded_files:
                            if uploaded_file.type.startswith('image'):
                                text = extract_text_from_image(uploaded_file)
                                all_text.append(text)
                            else:
                                text = uploaded_file.read().decode('utf-8')
                                all_text.append(text)

                        extracted_text = "\n\n---\n\n".join(all_text)
                        st.session_state.notification_text = extracted_text

                        # Analyze the notification
                        analysis = analyze_notification(extracted_text)
                        st.session_state.notification_analysis = analysis

                        # Extract contact name for letter salutation
                        contact_name = extract_contact_name(extracted_text)
                        st.session_state.contact_name = contact_name

                    st.success("✅ Notification analyzed!")
                    st.session_state.step = 'notification_explanation'
                    st.rerun()
                else:
                    st.warning("⚠️ Please paste text or upload files before continuing.")

        with col2:
            if st.button("⏭️ Skip", use_container_width=True, key="skip_notification"):
                st.session_state.notification_text = "No notification provided"
                st.session_state.notification_analysis = "Notification not provided by user"
                st.session_state.step = 'notification_explanation'
                st.rerun()

    # Step 1.25: Explain what the notification means (NEW)
    elif st.session_state.step == 'notification_explanation':
        st.markdown("### 📋 What This Notice Means")

        st.success("""
        **Good News: This is NOT a Rejection!**

        A pre-adverse action notice is actually a **positive sign**. It means:
        - The employer is interested in hiring you
        - They found something on your background check that gave them pause
        - **By law, they MUST give you a chance to respond before making a final decision**
        - Your response could change their mind
        """)

        st.markdown("### 📄 Here's What the Employer Found:")
        st.info(st.session_state.notification_analysis)

        st.markdown("### ✍️ How We'll Help You Respond")
        st.markdown("""
        We're going to help you write a powerful response package that includes:

        1. **Your Response Letter** - Shows accountability and growth
        2. **Coach Support Letter** - Third-party validation from FreeWorld
        3. **Program Completion Certificate** - Proves your commitment

        To write the strongest possible letter, we need to understand your full situation. That's why the next step is important...
        """)

        st.markdown("### 🔍 Why We Ask About Your Background Check")
        st.info("""
        **Optional but Recommended:** If you have a copy of your background check, it helps us:
        - See exactly what the employer sees
        - Identify any errors or outdated information
        - Craft a response that directly addresses their concerns
        - Make sure we don't miss anything important

        **Don't have it?** No problem - we can still help you write a great response!
        """)

        if st.button("➡️ Continue to Background Check", use_container_width=True):
            st.session_state.step = 'background_check'
            st.rerun()

    # Step 1.5: Background Check Upload (NEW)
    elif st.session_state.step == 'background_check':
        st.markdown("### 📄 Your Background Check Report")

        st.info("""
        **By law, the employer must provide you with a copy of your background check report.** It's often included with your pre-adverse notice.

        📋 **How to get your report:**
        - Check if it was attached to your pre-adverse notice email
        - Look for a link or instructions in the notice on how to access it online
        - If you can't find it, contact your Success Coach at **(408) 668-3608** for help
        """)

        # Check if notification has links to background report
        if st.session_state.notification_analysis and st.session_state.notification_text:
            if "checkr" in st.session_state.notification_text.lower() or "background check" in st.session_state.notification_text.lower():
                st.success("💡 **Tip:** We found references to your background check in your notification. Look for links or instructions in the notice above on how to access your full report.")

        st.markdown("**Having your background report helps us write a stronger response, but it's optional.**")

        # Initialize temp storage for this step
        if 'temp_bg_text' not in st.session_state:
            st.session_state.temp_bg_text = ""

        tab1, tab2 = st.tabs(["📝 Paste Text", "📸 Upload Image/File"])

        with tab1:
            bg_text = st.text_area(
                "Paste your background check text here:",
                height=250,
                value=st.session_state.temp_bg_text,
                placeholder="Paste your background check report here...",
                key="bg_text_area"
            )
            # Store in temp session state
            st.session_state.temp_bg_text = bg_text

        with tab2:
            bg_uploaded_files = st.file_uploader(
                "Upload your background check report",
                type=['png', 'jpg', 'jpeg', 'pdf', 'txt'],
                accept_multiple_files=True,
                help="Upload photos or PDFs of your background check",
                key="bg_check_uploader"
            )

            if bg_uploaded_files:
                st.success(f"✅ {len(bg_uploaded_files)} file(s) uploaded!")

                for i, uploaded_file in enumerate(bg_uploaded_files):
                    if uploaded_file.type.startswith('image'):
                        st.image(uploaded_file, caption=f"Page {i+1}", use_container_width=True)

        # Always-present buttons outside tabs
        st.markdown("---")
        col1, col2 = st.columns([2, 1])

        with col1:
            if st.button("✅ Submit & Continue", use_container_width=True, key="submit_bg"):
                # Check if we have text or files
                has_text = bool(st.session_state.temp_bg_text.strip())
                has_files = bg_uploaded_files is not None and len(bg_uploaded_files) > 0

                if has_text:
                    # Use pasted text
                    with st.spinner("🔍 Analyzing your background check..."):
                        st.session_state.background_check_text = st.session_state.temp_bg_text
                        analysis = analyze_background_check(st.session_state.temp_bg_text)
                        st.session_state.background_check_analysis = analysis

                    # Initialize conversation - background check was analyzed
                    if CONVERSATION_QUESTIONS[0].get("skip_if_bg_analyzed", False):
                        starting_question_idx = 1
                        intro_text = "Thanks for sharing that information. I have a good understanding of what the employer will see. Now I'll ask you some questions to understand the full story."
                    else:
                        starting_question_idx = 0
                        intro_text = "Thanks for sharing that information. I've reviewed your background check and I'll ask you a few questions to help craft your response."

                    first_question = CONVERSATION_QUESTIONS[starting_question_idx].get("question_if_bg_analyzed", CONVERSATION_QUESTIONS[starting_question_idx]["question"])

                    st.session_state.messages = [
                        {"role": "assistant", "content": first_question}
                    ]
                    st.session_state.current_question = starting_question_idx
                    st.session_state.step = 'ready_for_questions'
                    st.rerun()

                elif has_files:
                    # Extract text from uploaded files
                    with st.spinner("🔍 Reading your background check..."):
                        all_text = []
                        for uploaded_file in bg_uploaded_files:
                            if uploaded_file.type.startswith('image'):
                                text = extract_text_from_image(uploaded_file)
                                all_text.append(text)
                            else:
                                text = uploaded_file.read().decode('utf-8')
                                all_text.append(text)

                        extracted_text = "\n\n---\n\n".join(all_text)
                        st.session_state.background_check_text = extracted_text

                        # Analyze the background check
                        analysis = analyze_background_check(extracted_text)
                        st.session_state.background_check_analysis = analysis

                    # Initialize conversation - background check was analyzed
                    if CONVERSATION_QUESTIONS[0].get("skip_if_bg_analyzed", False):
                        starting_question_idx = 1
                        intro_text = "Thanks for sharing that information. I have a good understanding of what the employer will see. Now I'll ask you some questions to understand the full story."
                    else:
                        starting_question_idx = 0
                        intro_text = "Thanks for sharing that information. I've reviewed your background check and I'll ask you a few questions to help craft your response."

                    first_question = CONVERSATION_QUESTIONS[starting_question_idx].get("question_if_bg_analyzed", CONVERSATION_QUESTIONS[starting_question_idx]["question"])

                    st.session_state.messages = [
                        {"role": "assistant", "content": first_question}
                    ]
                    st.session_state.current_question = starting_question_idx
                    st.session_state.step = 'ready_for_questions'
                    st.rerun()
                else:
                    st.warning("⚠️ Please paste text or upload files, or click Skip to continue without background check.")

        with col2:
            if st.button("⏭️ Skip", use_container_width=True, key="skip_bg"):
                # Initialize conversation - no background check analyzed
                first_question = CONVERSATION_QUESTIONS[0]["question"]
                st.session_state.messages = [
                    {"role": "assistant", "content": first_question}
                ]
                st.session_state.current_question = 0
                st.session_state.step = 'ready_for_questions'
                st.rerun()

    # Step 1.75: Ready to start questions (clear break)
    elif st.session_state.step == 'ready_for_questions':
        st.markdown("### ✅ Great! Now Let's Get Your Story")

        # Show background check summary if available
        if st.session_state.background_check_analysis:
            with st.expander("📋 Background Check Summary", expanded=False):
                st.info(st.session_state.background_check_analysis)

        st.success("""
        **Next Step: A Few Questions**

        I'm going to ask you some questions about your situation. Your answers will help me write a strong, honest response letter.

        Just answer naturally - we're having a conversation. There are no wrong answers.
        """)

        if st.button("➡️ Start Questions", use_container_width=True, type="primary"):
            st.session_state.step = 'chat'
            st.rerun()

    # Step 2: Chat conversation
    elif st.session_state.step == 'chat':
        st.markdown("### 💬 Your Story")

        # Calculate question number for display
        # If we have background check, we skip question 0, so adjust count
        has_bg = bool(st.session_state.background_check_analysis)
        if has_bg and CONVERSATION_QUESTIONS[0].get("skip_if_bg_analyzed", False):
            # Question 0 was skipped, so total is 4, and we're on (current_question)
            total_questions = len(CONVERSATION_QUESTIONS) - 1
            current_q_num = st.session_state.current_question  # Don't add 1 since we started at 1
        else:
            # All questions asked
            total_questions = len(CONVERSATION_QUESTIONS)
            current_q_num = st.session_state.current_question + 1

        # Display chat history
        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "assistant":
                # Display assistant questions in a styled box
                # Check if this is a question (not intro text)
                is_question = i > 0 or not message["content"].startswith("Thanks for sharing")

                if is_question and i == len(st.session_state.messages) - 1:
                    # This is the current question - show it in a prominent box with numbering
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #004751, #593CBC); color: white; padding: 20px; border-radius: 12px; margin: 20px 0;">
                        <div style="font-size: 14px; opacity: 0.9; margin-bottom: 10px;">Question {current_q_num} of {total_questions}</div>
                        <div style="font-size: 16px; line-height: 1.6;">{message["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Previous messages - show normally
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
            else:
                # User messages - show normally
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Helper function to get the appropriate question text
        def get_question_text(question_idx):
            """Get the appropriate question text based on whether we have background check analysis"""
            question = CONVERSATION_QUESTIONS[question_idx]
            has_bg_analysis = bool(st.session_state.background_check_analysis)

            if has_bg_analysis and "question_if_bg_analyzed" in question:
                return question["question_if_bg_analyzed"]
            else:
                return question["question"]

        # Helper function to process responses
        def process_user_response(user_input):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})

            # If we're awaiting a followup answer
            if st.session_state.awaiting_followup:
                # Move to next main question
                st.session_state.awaiting_followup = False
                st.session_state.followup_question = ""
                question_num = st.session_state.current_question

                if question_num < len(CONVERSATION_QUESTIONS) - 1:
                    # Ask next question (use appropriate version based on background check)
                    next_question = get_question_text(question_num + 1)
                    st.session_state.messages.append({"role": "assistant", "content": next_question})
                    st.session_state.current_question += 1
                else:
                    # All questions answered
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Perfect! I have everything I need. Would you like me to generate your response letter now?"
                    })
                    st.session_state.step = 'ready_to_generate'

                # Clear input and rerun
                st.session_state.text_input_key += 1
                st.rerun()

            else:
                # Check if we should ask a followup
                question_num = st.session_state.current_question
                question_key = CONVERSATION_QUESTIONS[question_num]["key"]

                # Get previous context
                recent_messages = st.session_state.messages[-6:]
                context = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])

                # Try to generate followup
                followup = generate_followup_question(question_key, user_input, context)

                if followup:
                    # Ask the followup
                    st.session_state.messages.append({"role": "assistant", "content": followup})
                    st.session_state.awaiting_followup = True
                    st.session_state.followup_question = followup
                else:
                    # No followup, move to next main question
                    if question_num < len(CONVERSATION_QUESTIONS) - 1:
                        # Ask next question (use appropriate version based on background check)
                        next_question = get_question_text(question_num + 1)
                        st.session_state.messages.append({"role": "assistant", "content": next_question})
                        st.session_state.current_question += 1
                    else:
                        # All questions answered
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": "Perfect! I have everything I need. Would you like me to generate your response letter now?"
                        })
                        st.session_state.step = 'ready_to_generate'

                # Clear input and rerun
                st.session_state.text_input_key += 1
                st.rerun()

        st.markdown("---")
        st.markdown("### ✍️ Your Response")
        st.markdown("💡 *Tip: On mobile, you can use your device's voice input feature to speak your answer.*")

        user_response = st.text_area(
            "Type or speak your answer:",
            height=150,
            key=f"response_area_{st.session_state.text_input_key}",
            placeholder="Type your answer here, or use your device's voice input..."
        )

        if st.button("📤 Submit Response", use_container_width=True, key="submit_response"):
            if user_response.strip():
                process_user_response(user_response.strip())
            else:
                st.warning("⚠️ Please enter a response before submitting.")

        st.markdown("---")

        # Option to go back
        if st.button("⬅️ Start Over", key="back_to_upload"):
            st.session_state.step = 'coach_select'
            st.session_state.messages = []
            st.session_state.current_question = 0
            st.session_state.awaiting_followup = False
            st.rerun()

    # Step 3: Ready to generate
    elif st.session_state.step == 'ready_to_generate':
        st.markdown("### 💬 Let's Talk")

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✨ Generate My Letters", use_container_width=True):
                st.session_state.step = 'generating'
                st.rerun()
        with col2:
            if st.button("⬅️ Start Over", key="restart", use_container_width=True):
                st.session_state.step = 'coach_select'
                st.session_state.messages = []
                st.session_state.current_question = 0
                st.rerun()

    # Step 4: Generating letters
    elif st.session_state.step == 'generating':
        st.markdown("### ✨ Creating Your Response Package")

        if not st.session_state.generated_letter:
            with st.spinner("Writing your professional response letter..."):
                letter = generate_response_letter(
                    st.session_state.messages,
                    st.session_state.notification_text,
                    st.session_state.agent_name,
                    st.session_state.contact_name,
                    st.session_state.agent_phone,
                    st.session_state.agent_email
                )
                st.session_state.generated_letter = letter

        if not st.session_state.coach_letter:
            with st.spinner("Generating your support letter..."):
                coach_letter = generate_coach_letter(
                    st.session_state.agent_name,
                    st.session_state.coach_name,
                    st.session_state.messages,
                    st.session_state.notification_analysis,
                    st.session_state.contact_name
                )
                st.session_state.coach_letter = coach_letter

        st.success("✅ Your letters are ready for review!")
        st.session_state.step = 'review_letter'
        st.rerun()

    # Step 4.5: Review and edit letter
    elif st.session_state.step == 'review_letter':
        st.markdown("### ✏️ Review Your Response Letter")
        st.info("📝 **Before we create the final PDFs**, take a moment to review and edit your response letter. You can tweak any part of it to make sure it sounds just right.")

        # Editable text area for Free Agent letter
        st.markdown("#### Your Response Letter (Editable)")
        edited_letter = st.text_area(
            "Edit your letter below:",
            value=st.session_state.generated_letter,
            height=400,
            key="edit_agent_letter",
            help="Feel free to edit any part of this letter to better express your situation"
        )

        # Update session state with edited content
        st.session_state.generated_letter = edited_letter

        st.markdown("---")

        # Editable text area for Coach letter
        st.markdown(f"#### Letter from Coach {st.session_state.coach_name} (Editable)")
        edited_coach_letter = st.text_area(
            "Edit the coach letter below:",
            value=st.session_state.coach_letter,
            height=400,
            key="edit_coach_letter",
            help="Feel free to edit any part of the coach's support letter"
        )

        # Update session state with edited content
        st.session_state.coach_letter = edited_coach_letter

        st.markdown("---")

        # Action buttons
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("✅ Looks Good - Generate PDFs", use_container_width=True):
                with st.spinner("🎨 Creating your beautiful professional documents..."):
                    pdfs = generate_pdfs(
                        st.session_state.agent_name,
                        st.session_state.coach_name,
                        st.session_state.generated_letter,
                        st.session_state.coach_letter,
                        st.session_state.agent_phone,
                        st.session_state.agent_email
                    )
                    st.session_state.pdfs = pdfs
                st.session_state.step = 'complete'
                st.rerun()

        with col2:
            if st.button("⬅️ Start Over", key="restart_from_review", use_container_width=True):
                st.session_state.step = 'coach_select'
                st.session_state.messages = []
                st.session_state.current_question = 0
                st.session_state.generated_letter = ""
                st.session_state.coach_letter = ""
                st.rerun()

    # Step 5: Complete
    elif st.session_state.step == 'complete':
        st.markdown("### ✅ Your Response Package is Ready!")

        st.success(f"🎉 Great work, {st.session_state.agent_name}! Here's your complete professional response package.")

        # Combined download button (prominent placement)
        st.markdown("---")
        if all(st.session_state.pdfs.get(key) for key in ['agent_letter', 'coach_letter', 'certificate']):
            combined_package = create_combined_package(st.session_state.agent_name, st.session_state.pdfs)
            if combined_package:
                st.download_button(
                    label="📦 Download Complete Package (All 3 Documents)",
                    data=combined_package,
                    file_name=f"{st.session_state.agent_name.replace(' ', '_')}_Complete_Response_Package.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
                st.caption("💡 This single PDF contains all three documents (3 pages). You can also download them individually below.")

        # Show all three documents with preview and download
        st.markdown("---")
        st.markdown("### 📄 Individual Documents")

        # 1. Free Agent Response Letter
        st.markdown("#### 1️⃣ Your Response Letter")
        with st.expander("📖 Preview Your Letter", expanded=True):
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 20px; border-left: 4px solid #004751;">
                <div style="white-space: pre-wrap; line-height: 1.8; font-size: 15px; color: #191931;">
{st.session_state.generated_letter}
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.session_state.pdfs.get('agent_letter'):
            st.download_button(
                label="📥 Download Your Response Letter (PDF)",
                data=st.session_state.pdfs['agent_letter'],
                file_name=f"{st.session_state.agent_name.replace(' ', '_')}_Response_Letter.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.markdown("---")

        # 2. Coach Support Letter
        st.markdown(f"#### 2️⃣ Letter from Coach {st.session_state.coach_name}")
        with st.expander("📖 Preview Coach Letter"):
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 20px; border-left: 4px solid #593CBC;">
                <div style="white-space: pre-wrap; line-height: 1.8; font-size: 15px; color: #191931;">
{st.session_state.coach_letter}
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.session_state.pdfs.get('coach_letter'):
            st.download_button(
                label="📥 Download Coach Letter (PDF)",
                data=st.session_state.pdfs['coach_letter'],
                file_name=f"Coach_{st.session_state.coach_name.replace(' ', '_')}_Support_Letter.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.markdown("---")

        # 3. Certificate
        st.markdown("#### 3️⃣ FreeWorld CDL Training Program Certificate")
        st.info("🏆 This certificate shows you completed our CDL Training Program and demonstrates your commitment to professional development and career advancement.")

        if st.session_state.pdfs.get('certificate'):
            st.download_button(
                label="📥 Download Certificate (PDF)",
                data=st.session_state.pdfs['certificate'],
                file_name=f"{st.session_state.agent_name.replace(' ', '_')}_FreeWorld_Certificate.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.markdown("---")

        # Show how to send based on analysis
        if st.session_state.notification_analysis:
            st.markdown("### 📮 How to Send Your Response")
            st.info(f"**Based on your notification:**\n\n{st.session_state.notification_analysis}")
            st.markdown("---")

        st.warning("""
        **⏰ IMPORTANT - Don't Wait!**

        Pre-adverse notifications usually have a **5-7 day deadline**. Send your response TODAY!
        """)

        st.info("""
        **📋 Recommended: Send All Three Documents**
        1. Your response letter (shows accountability and growth)
        2. Coach support letter (third-party validation)
        3. Program completion certificate (demonstrates commitment)

        Sending all three creates a complete picture of who you are today.
        """)

        st.markdown("""
        ### 📞 Need Help?

        **Call FreeWorld:** (408) 668-3608

        Remember: You have rights! Pre-adverse notifications give you the chance to respond before a final decision is made.
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Create Another Package", use_container_width=True):
                for key in ['notification_text', 'notification_analysis', 'background_check_text', 'background_check_analysis',
                           'messages', 'generated_letter', 'coach_letter', 'pdfs', 'step', 'current_question',
                           'awaiting_followup', 'agent_name', 'coach_name']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

        with col2:
            if st.button("📧 Email Package to Myself", use_container_width=True, disabled=True):
                st.info("Coming soon! For now, use the download buttons above.")

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; color: #666;">
        <img src="data:image/png;base64,{get_freeworld_logo()}" alt="FreeWorld" style="height: 20px; margin-bottom: 10px;">
        <div style="font-size: 14px;">
            For support, call <a href="tel:4086683608" style="color: #004751; font-weight: 600;">(408) 668-3608</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
