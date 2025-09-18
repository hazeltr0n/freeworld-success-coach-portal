import os
import json
import asyncio
import aiohttp
import time
import queue
import concurrent.futures
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class JobClassifier:
    def __init__(self):
        # OpenAI client with connection reuse (let OpenAI SDK handle HTTP pooling)
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            timeout=30.0,  # Adequate timeout for complex responses
            max_retries=0  # Handle retries manually for better control
        )
        self.model = "gpt-4o-mini"  # Single model constant
        
        # Retriable status codes
        self.RETRIABLE = {429, 500, 502, 503, 504}
        
        # Shared schema object for prompt caching (CRITICAL for performance)
        self.CLASSIFICATION_SCHEMA = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "job_id": {"type": "string"},
                "match": {"type": "string", "enum": ["good", "so-so", "bad"]},
                "reason": {"type": "string", "maxLength": 120},
                "summary": {"type": "string", "maxLength": 1000},
                "normalized_location": {"type": "string", "maxLength": 100},
                "fair_chance": {"type": "string", "enum": ["fair_chance_employer", "background_check_required", "clean_record_required", "no_requirements_mentioned"]},
                "career_pathway": {"type": "string", "enum": [
                    "dock_to_driver",
                    "internal_cdl_training",
                    "warehouse_to_driver",
                    "logistics_progression",
                    "non_cdl_driving",
                    "general_warehouse",
                    "stepping_stone",
                    "no_pathway"
                ]},
                "training_provided": {"type": "boolean"}
            },
            "required": ["job_id", "match", "reason", "summary", "fair_chance", "career_pathway", "training_provided"]
        }
    
    def _retry_request(self, do_req, max_retries=5, base=0.5, cap=30.0):
        import time
        backoff = base
        for attempt in range(1, max_retries + 1):
            try:
                return do_req()
            except Exception as e:
                status = getattr(e, 'status_code', None) or getattr(e, 'status', None)
                if status not in self.RETRIABLE or attempt == max_retries:
                    raise
                
                # Check for Retry-After header (proper implementation)
                retry_after = None
                if hasattr(e, 'response') and hasattr(e.response, 'headers'):
                    retry_after = e.response.headers.get('retry-after') or e.response.headers.get('Retry-After')
                
                if retry_after:
                    sleep_for = float(retry_after)
                    print(f"  ⏱️ Rate limited, sleeping {sleep_for}s (Retry-After header)")
                else:
                    sleep_for = backoff
                    backoff = min(backoff * 2, cap)
                    print(f"  ⏱️ Retrying in {sleep_for:.1f}s (attempt {attempt}/{max_retries})")
                
                time.sleep(sleep_for)
    
    def _call_one(self, system_prompt, content):
        return self._retry_request(lambda: self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            max_tokens=500,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "job_classification",
                    "schema": self.CLASSIFICATION_SCHEMA,  # Shared schema for caching!
                    "strict": True
                }
            },
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
        ))
    
    def _classify_single_batch_DEPRECATED_UNUSED(self, batch, batch_num):
        """Classify a single batch of jobs"""
        # Build the jobs block for this batch AND track which jobs actually get sent
        jobs_block = ""
        actually_sent_jobs = []  # Track jobs that actually get sent to OpenAI
        
        print(f"🔢 STEP 1: Received batch with {len(batch)} jobs")
        
        for job in batch:
            # Add safety check for job data format
            if not isinstance(job, dict):
                print(f"❌ Error in batch {batch_num}: Invalid job format - {type(job)}")
                continue
                
            # Use raw job description for OpenAI (like Colab version)
            # Character cleaning is handled elsewhere for filtering, not for classification
            clean_description = job.get('job_description', 'UNKNOWN')
            
            jobs_block += f"""
---
Job ID: {job.get('job_id', 'UNKNOWN')}
Job Title: {job.get('job_title', 'UNKNOWN')}
Company: {job.get('company', 'UNKNOWN')}
Location: {job.get('location', 'UNKNOWN')}

Job Description:
{clean_description}
"""
            # IMPORTANT: Only add jobs that actually get sent to OpenAI (after safety checks pass)
            actually_sent_jobs.append(job)
        
        print(f"🔢 STEP 2: Actually sent {len(actually_sent_jobs)} jobs to OpenAI")

        # Handle jobs that were skipped (not sent to OpenAI)
        skipped_jobs = []
        for job in batch:
            if isinstance(job, dict) and job not in actually_sent_jobs:
                skipped_jobs.append(job)

        if skipped_jobs:
            print(f"⚠️ Batch {batch_num}: Skipped {len(skipped_jobs)} malformed jobs")

        system_prompt = """
FreeWorld is a non-profit that helps Americans with low incomes find career pathway jobs that lead to living wage opportunities in transportation and logistics.
Our candidates are looking for entry-level positions that provide clear advancement opportunities, especially pathways to CDL driving careers. Many have limited work experience, criminal backgrounds, and need employers who provide training and career development.
We focus on connecting candidates to jobs that offer genuine career growth potential - from warehouse/dock work to driving, from non-CDL delivery to CDL opportunities, and logistics roles that provide industry experience.

**CLASSIFICATION PRIORITY SYSTEM:**

1. **CAREER PATHWAY POTENTIAL**: Jobs with clear advancement paths are top priority
2. **TRAINING PROVIDED**: Jobs that offer CDL training, skills development, or advancement opportunities
3. **ENTRY-LEVEL FRIENDLY**: Jobs that hire candidates with limited experience or criminal backgrounds

**PATHWAY CATEGORIES:**
- **dock_to_driver**: Warehouse/dock positions with explicit CDL training or driver advancement
- **internal_cdl_training**: Companies offering paid CDL training programs
- **warehouse_to_driver**: General warehouse roles at transportation companies with driver pathways
- **logistics_progression**: Dispatcher, coordinator roles that lead to management opportunities
- **non_cdl_driving**: Delivery, local driving that doesn't require CDL but provides driving experience
- **general_warehouse**: Standard warehouse work at logistics companies (stepping stone potential)
- **stepping_stone**: Other roles that provide industry experience and advancement potential

Jobs should be classified as **good** if they:
- Explicitly offer CDL training or driver pathways
- Provide clear advancement opportunities
- Are entry-level friendly with training provided
- Welcome candidates with criminal backgrounds

3. **AUTOMATIC DISQUALIFIERS**:
   - Owner-operator/1099 (must own truck/trailer) → BAD
   - School bus driving → BAD  

**ENDORSEMENT REQUIREMENTS:**
FreeWorld candidates have CDL-A with basic training on air brakes, combination vehicles, and manual transmissions. ENDORSEMENTS ARE NOT A BARRIER. FreeWorld helps Free Agents get ANY endorsement they need to get work. They also have very good driving records, we screen for that. "A good driving history or record in trucking DOES NOT indicate an experience requirement. It is referring to a motor vehicle record."

IMPORTANT: For each job, you MUST create a detailed summary that is EXACTLY 6-8 sentences long. 

- Don't make all jobs sound the same!**
- Preserve specific phrases that detail the nature of the work.
- Maintain their exact pay ranges, bonuses, and incentives as stated

These elements are also very relevant to our job seekers and should be included IF there is actual text from the ad that mentions them:
1) What the job role entails and main duties (using their language)
2) Pay/benefits offered (their exact wording and specific numbers)
3) Route and schedule information (preserve their exact terms: "home daily", "out 5 days", "weekends off", specific routes, territories, etc.)
4) Physical demands of the job (mention if it's "no-touch freight", requires loading/unloading, heavy lifting, dock work, etc.)
5) Key requirements and qualifications
7) Any training provided or growth opportunities (their exact promises)

Don't standardize everything - each company should sound different! 

**IMPORTANT DETAILS TO PRESERVE WHEN PRESENT:**
- Route information
- Schedule details
- Physical demands

If criminal background requirements are actually mentioned, include them clearly using the company's exact language when possible.

Return your results as a JSON object with a "job_classifications" array like this:
{
  "job_classifications": [
    { "job_id": "abc123", "match": "good", "reason": "Quote from job post", "summary": "This local delivery driver position offers $55,000-$65,000 annually with no prior experience required. The role involves delivering packages within the metro area using company-provided trucks and equipment. Benefits include full health insurance, dental, vision, and paid time off starting on day one. The company provides comprehensive 2-week training including vehicle operation and route planning. Drivers work Monday-Friday with occasional Saturday shifts and are typically home every night. This is an excellent opportunity for new CDL holders to gain experience while earning competitive wages.", "fair_chance": "no_requirements_mentioned", "endorsements": "none_required" },
    { "job_id": "xyz456", "match": "bad", "reason": "Requires own truck", "summary": "This owner-operator position requires drivers to provide their own truck and trailer along with 5+ years of verifiable experience. Pay is percentage-based ranging from 70-85% of gross revenue with drivers responsible for fuel, maintenance, and insurance costs. The role involves long-haul routes covering 48 states with 2-3 weeks out and 2-3 days home. While earnings potential can reach $200,000+ annually for experienced operators, the significant equipment investment and experience requirements make this unsuitable for entry-level drivers.", "fair_chance": "no_requirements_mentioned", "endorsements": "none_required" },
    { "job_id": "def789", "match": "bad", "reason": "Requires clean criminal record", "summary": "This regional trucking position offers $60,000-$70,000 annually for drivers to haul freight across multiple states. The company provides late-model equipment and offers health benefits after 90 days. However, the position requires a completely clean criminal background with no felonies or misdemeanors ever, making it unsuitable for many FreeWorld candidates. Routes typically involve 5 days out and 2 days home with some weekend work required. While the pay is competitive, the strict background requirements eliminate most candidates with criminal histories.", "fair_chance": "clean_record_required", "endorsements": "none_required" },
    { "job_id": "ghi012", "match": "so-so", "reason": "Requires Hazmat endorsement", "summary": "This regional tanker driver position offers $70,000-$80,000 annually transporting liquid chemicals. The role requires a valid Hazmat endorsement in addition to CDL-A, which candidates can obtain with company support. Routes cover multiple states with 4-5 days out and 2-3 days home. The company provides specialized training for hazmat transport and safety protocols. While the endorsement requirement adds complexity, the company assists with testing and the pay is above average for the region.", "fair_chance": "no_requirements_mentioned", "endorsements": "hazmat" }
  ]
}

**CLASSIFICATION STANDARDS - USE EXACT VALUES ONLY:**

**FAIR CHANCE CLASSIFICATION (fair_chance field):**
- "fair_chance_employer": Fair chance employer - welcomes applicants with criminal records
- "background_check_required": Background check required - may disqualify applicants with records
- "clean_record_required": Clean driving/criminal record explicitly required
- "no_requirements_mentioned": No background check requirements mentioned

**ENDORSEMENT CLASSIFICATION (endorsements field):**
- "none_required": No special CDL endorsements required
- "hazmat": Hazmat endorsement required
- "passenger": Passenger endorsement required
- "school_bus": School bus endorsement required
- "tanker": Tanker endorsement required
- "double_triple": Double/Triple trailer endorsement required
- "combination": Multiple endorsements required

**CLASSIFICATION RULES:**
1. Use ONLY the exact values listed above
2. For fair_chance: Look for explicit policies about criminal records/background checks
3. For endorsements: Look for REQUIRED CDL endorsements (not preferred or helpful)
4. If unclear or not mentioned, use appropriate default values
5. Be conservative - only classify as fair_chance_employer if explicitly stated

**EXAMPLES:**
- "We welcome applicants with criminal records" → fair_chance: "fair_chance_employer"
- "Clean criminal record required" or "no felonies" → fair_chance: "clean_record_required"
- "Background check required" (criminal) → fair_chance: "background_check_required"
- "Clean driving record required" → fair_chance: "no_requirements_mentioned" (driving record ≠ criminal background)
- No mention of background → fair_chance: "no_requirements_mentioned"
- "Hazmat endorsement required" → endorsements: "hazmat"
- "No special endorsements needed" → endorsements: "none_required"

**NOTE:** Location normalization is handled by the pipeline, focus on job quality and requirements assessment.
"""

        # Lean JSON Schema for speed - minimal properties
        classification_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "jobs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "id": {"type": "string"},
                            "match": {"type": "string", "enum": ["good", "so-so", "bad"]},
                            "reason": {"type": "string", "maxLength": 100},
                            "summary": {"type": "string", "maxLength": 200},
                            "bg": {"type": "string", "enum": ["ok", "check", "clean", "none"]},
                            "cdl": {"type": "string", "enum": ["none", "haz", "pass", "bus", "tank", "combo"]}
                        },
                        "required": ["id", "match", "reason", "summary", "bg", "cdl"]
                    }
                }
            },
            "required": ["jobs"]
        }

        try:
            
            # Simple approach like working version
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": jobs_block.strip()}
                ],
                temperature=0
            )
            content = response.choices[0].message.content.strip()


            # Clean and parse like working version
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            parsed = json.loads(content)
            print(f"🔢 STEP 3: OpenAI returned {len(parsed)} job results")
            
            # Process results for this batch
            batch_results = []
            
            # Track which jobs we received vs actually sent to OpenAI
            sent_job_ids = {job['job_id'] for job in actually_sent_jobs}
            received_job_ids = set()
            
            # DEBUG: Show what jobs we sent to OpenAI
            print(f"   DEBUG Sent {len(actually_sent_jobs)} jobs:")
            for i, job in enumerate(actually_sent_jobs):
                job_id = job.get('job_id', 'NO_ID')
                title = job.get('job_title', 'NO_TITLE')[:50]
                company = job.get('company', 'NO_COMPANY')[:30]
                print(f"     {i+1}. {job_id} | {title} | {company}")
                if i >= 4:  # Show first 5
                    print(f"     ... and {len(actually_sent_jobs) - 5} more")
                    break
            
            # Don't show full debug for every item, just key info
            print(f"   DEBUG OpenAI returned {len(parsed)} items")
            
            for i, item in enumerate(parsed):
                job_id = item.get("id")  # Match the schema field name
                match = item.get("match", "error")
                route_type = "Unknown"  # Will be set by route classifier later
                reason = item.get("reason", "No reason returned")
                summary = item.get("summary", "No summary provided")
                fair_chance = "no_requirements_mentioned"  # Default
                endorsements = "none_required"  # Default
                
                # Set final_status for all jobs to track their processing outcome
                final_status = ""
                if match == "bad":
                    final_status = f"AI classified as bad: {reason}"
                elif match in ["good", "so-so"]:
                    final_status = "included"
                elif match == "error":
                    final_status = "processing_error"
                else:
                    final_status = "unknown_classification"
                
                batch_results.append({
                    'job_id': job_id,
                    'match': match,
                    'route_type': route_type,
                    'reason': reason,
                    'summary': summary,
                    'fair_chance': fair_chance,
                    'endorsements': endorsements,
                    'final_status': final_status
                })
                received_job_ids.add(job_id)
                print(f"Batch {batch_num}: {job_id} → {match} ({route_type}): {reason}")
            
            # Check for missing jobs and create error entries
            missing_job_ids = sent_job_ids - received_job_ids
            
            # Log ID mismatches for debugging if needed
            if missing_job_ids or len(received_job_ids) != len(sent_job_ids):
                # Check for exact type/format differences
                sent_sample = list(sent_job_ids)[0] if sent_job_ids else None
                received_sample = list(received_job_ids)[0] if received_job_ids else None
                print(f"   Sample sent ID: '{sent_sample}' (type: {type(sent_sample)})")
                print(f"   Sample received ID: '{received_sample}' (type: {type(received_sample)})")
                
                # Check for None/empty job_ids in received
                none_or_empty_received = [job_id for job_id in received_job_ids if job_id is None or job_id == '']
                if none_or_empty_received:
                    print(f"   ⚠️ WARNING: Found None/empty job_ids in received: {none_or_empty_received}")
                    
                # Check for whitespace/encoding issues
                if sent_sample and received_sample:
                    if sent_sample.strip() == received_sample.strip():
                        print(f"   💡 IDs match after strip() - whitespace issue!")
                    if sent_sample.lower() == received_sample.lower():
                        print(f"   💡 IDs match after lower() - case sensitivity issue!")
            
            if missing_job_ids:
                print(f"⚠️ Batch {batch_num}: Missing {len(missing_job_ids)} jobs from OpenAI response")
                print(f"   DEBUG Missing job_ids: {list(missing_job_ids)}")
                
                # Show details of the missing jobs
                print(f"   DEBUG Details of missing jobs:")
                for missing_id in list(missing_job_ids)[:3]:  # Show first 3 missing
                    missing_job = next((job for job in actually_sent_jobs if job['job_id'] == missing_id), None)
                    if missing_job:
                        title = missing_job.get('job_title', 'NO_TITLE')[:50]
                        company = missing_job.get('company', 'NO_COMPANY')[:30]
                        desc_len = len(str(missing_job.get('job_description', '')))
                        print(f"     Missing: {missing_id} | {title} | {company} | desc_len: {desc_len}")
                        
                print(f"   DEBUG Received job_ids: {list(received_job_ids)[:5]}...")  # Show first 5 received
                for missing_job_id in missing_job_ids:
                    batch_results.append({
                        'job_id': missing_job_id,
                        'match': 'error',
                        'route_type': 'Unknown',
                        'reason': 'Missing from OpenAI response',
                        'summary': 'Job not returned by AI classifier',
                        'fair_chance': 'no_requirements_mentioned',
                        'endorsements': 'none_required',
                        'final_status': 'processing_error: Missing from OpenAI response'
                    })
                    print(f"Batch {batch_num}: {missing_job_id} → error (Unknown): Missing from OpenAI response")

            # Add error results for any jobs that were skipped (malformed)
            for skipped_job in skipped_jobs:
                batch_results.append({
                    'job_id': skipped_job.get('job_id', 'unknown'),
                    'match': 'error',
                    'route_type': 'Unknown',
                    'reason': 'Malformed job data - skipped before OpenAI',
                    'summary': 'Job data was malformed and could not be processed',
                    'fair_chance': 'unknown',
                    'endorsements': 'unknown',
                    'final_status': 'processing_error: Malformed job data'
                })
                print(f"Batch {batch_num}: {skipped_job.get('job_id', 'unknown')} → error (Unknown): Malformed job data - skipped before OpenAI")

            print(f"🔢 STEP 4: Built {len(batch_results)} batch results")
            print(f"✅ Batch {batch_num}: Sent {len(actually_sent_jobs)} jobs, received {len(parsed)} results, returning {len(batch_results)} total")
            return batch_results

        except Exception as e:
            import traceback
            print(f"❌ Error in batch {batch_num}: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            if "timeout" in str(e).lower():
                print(f"❌ This is a TIMEOUT error - OpenAI API took longer than 45 seconds")
            elif "rate limit" in str(e).lower():
                print(f"❌ This is a RATE LIMIT error - hitting API limits")
            elif "connection" in str(e).lower():
                print(f"❌ This is a CONNECTION error - network issue")
            else:
                print(f"❌ Full traceback:")
                traceback.print_exc()
            # Return error results for this batch - use original batch to ensure all jobs get error results
            error_results = []
            for job in batch:
                if isinstance(job, dict) and 'job_id' in job:
                    error_results.append({
                        'job_id': job['job_id'],
                        'match': 'error',
                        'route_type': 'Unknown',
                        'reason': str(e),
                        'summary': 'Error processing job description',
                        'fair_chance': 'unknown',
                        'endorsements': 'unknown'
                    })
            return error_results

    def classify_jobs(self, df):
        """
        Classify jobs in a DataFrame - wrapper method for compatibility
        
        Args:
            df: DataFrame with job data
            
        Returns:
            DataFrame with classification results added
        """
        
        # Convert DataFrame to jobs list format (use direct access like working Colab version)
        jobs_list = []
        for _, row in df.iterrows():
            jobs_list.append({
                'job_id': row['job_id'],
                'job_title': row['job_title'], 
                'company': row['company'],
                'location': row['location'],
                'job_description': row['job_description']
            })
        
        # Classify using batch method
        results = self.classify_jobs_in_batches(jobs_list)
        
        # Merge results back to DataFrame
        results_dict = {result['job_id']: result for result in results}
        
        # Add classification results to DataFrame
        df['match'] = df['job_id'].map(lambda x: results_dict.get(x, {}).get('match', 'unknown'))
        df['reason'] = df['job_id'].map(lambda x: results_dict.get(x, {}).get('reason', ''))
        df['summary'] = df['job_id'].map(lambda x: results_dict.get(x, {}).get('summary', ''))
        
        # Preserve existing route_type if already classified, otherwise use AI result
        def get_route_type(row):
            existing_route = row.get('route_type', 'unknown') if 'route_type' in df.columns else 'unknown'
            if existing_route and existing_route not in ['unknown', 'Unknown', '']:
                return existing_route  # Keep existing classification
            else:
                return results_dict.get(row['job_id'], {}).get('route_type', 'unknown')  # Use AI result
        
        df['route_type'] = df.apply(get_route_type, axis=1)
        df['fair_chance'] = df['job_id'].map(lambda x: results_dict.get(x, {}).get('fair_chance', 'unknown'))
        df['endorsements'] = df['job_id'].map(lambda x: results_dict.get(x, {}).get('endorsements', 'unknown'))
        
        return df

    def classify_jobs_in_batches(self, jobs_list, batch_size=25, max_parallel=2, max_retries=2):
        """
        Process jobs using fast async implementation with backward compatibility
        """
        
        # Validate jobs
        valid_jobs = []
        for job in jobs_list:
            if isinstance(job, dict) and 'job_id' in job:
                valid_jobs.append(job)
            else:
                print(f"⚠️ Skipping malformed job data: {type(job)} - {job}")
        
        if not valid_jobs:
            print("❌ No valid jobs to process")
            return []
            
        # Use new async implementation for speed
        print(f"🚀 Using async classification for {len(valid_jobs)} jobs...")
        try:
            # Run async method in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(self._classify_jobs_async(valid_jobs, concurrency=50))
                print("✅ Async classification completed successfully")
                return results
            finally:
                loop.close()
        except Exception as e:
            print(f"⚠️ Async classification failed: {e}")
            print("🔄 Falling back to original sync implementation...")
            # Fallback to original sync implementation
            results = self._run_work_queue(valid_jobs, concurrency=50)
            print("✅ Fallback sync classification completed")
            return results
    
    def _run_work_queue(self, jobs_list, concurrency=8):
        """
        Fast structured outputs with global work queue - proper implementation
        """
        import time
        
        # Shared system prompt and schema (byte-identical for prompt caching)
        # Single job per request for proper work queue
        # Use the good system prompt with explicit field mapping
        system_prompt = """
FreeWorld is a non-profit that helps Americans with low incomes find career pathway jobs that lead to living wage opportunities in transportation and logistics.
Our candidates are looking for entry-level positions that provide clear advancement opportunities, especially pathways to CDL driving careers. Many have limited work experience, criminal backgrounds, and need employers who provide training and career development.
We focus on connecting candidates to jobs that offer genuine career growth potential - from warehouse/dock work to driving, from non-CDL delivery to CDL opportunities, and logistics roles that provide industry experience.

**CLASSIFICATION PRIORITY SYSTEM:**

1. **CAREER PATHWAY POTENTIAL**: Jobs with clear advancement paths are top priority
2. **TRAINING PROVIDED**: Jobs that offer CDL training, skills development, or advancement opportunities
3. **ENTRY-LEVEL FRIENDLY**: Jobs that hire candidates with limited experience or criminal backgrounds

**PATHWAY CATEGORIES:**
- **dock_to_driver**: Warehouse/dock positions with explicit CDL training or driver advancement
- **internal_cdl_training**: Companies offering paid CDL training programs
- **warehouse_to_driver**: General warehouse roles at transportation companies with driver pathways
- **logistics_progression**: Dispatcher, coordinator roles that lead to management opportunities
- **non_cdl_driving**: Delivery, local driving that doesn't require CDL but provides driving experience
- **general_warehouse**: Standard warehouse work at logistics companies (stepping stone potential)
- **stepping_stone**: Other roles that provide industry experience and advancement potential

Jobs should be classified as **good** if they:
- Explicitly offer CDL training or driver pathways
- Provide clear advancement opportunities
- Are entry-level friendly with training provided
- Welcome candidates with criminal backgrounds

3. **AUTOMATIC DISQUALIFIERS**:
   - Owner-operator/1099 (must own truck/trailer) → BAD
   - School bus driving → BAD  
   - Requires "no felonies AND no misdemeanors" combined → BAD

**ENDORSEMENT REQUIREMENTS:**
FreeWorld candidates have CDL-A with basic training on air brakes, combination vehicles, and manual transmissions. ENDORSEMENTS ARE NOT A BARRIER. FreeWorld helps Free Agents get ANY endorsement they need to get work.

IMPORTANT: For each job, you MUST create a detailed summary that is EXACTLY 6-8 sentences long. 

- Don't make all jobs sound the same!**
- Preserve specific phrases that detail the nature of the work.
- Maintain their exact pay ranges, bonuses, and incentives as stated

These elements are also very relevant to our job seekers and should be included IF there is actual text from the ad that mentions them:
1) What the job role entails and main duties (using their language)
2) Pay/benefits offered (their exact wording and specific numbers)
3) Route and schedule information (preserve their exact terms: "home daily", "out 5 days", "weekends off", specific routes, territories, etc.)
4) Physical demands of the job (mention if it's "no-touch freight", requires loading/unloading, heavy lifting, dock work, etc.)
5) Key requirements and qualifications (including criminal background requirements if mentioned)
7) Any training provided or growth opportunities (their exact promises)

Don't standardize everything - each company should sound different! 

**IMPORTANT DETAILS TO PRESERVE WHEN PRESENT:**
- Route information
- Schedule details
- Physical demands

If criminal background requirements are actually mentioned, include them clearly using the company's exact language when possible.

Return your results as a JSON object with a "job_classifications" array like this:
{
  "job_classifications": [
    { "job_id": "abc123", "match": "good", "reason": "Quote from job post", "summary": "This local delivery driver position offers $55,000-$65,000 annually with no prior experience required. The role involves delivering packages within the metro area using company-provided trucks and equipment. Benefits include full health insurance, dental, vision, and paid time off starting on day one. The company provides comprehensive 2-week training including vehicle operation and route planning. Drivers work Monday-Friday with occasional Saturday shifts and are typically home every night. This is an excellent opportunity for new CDL holders to gain experience while earning competitive wages.", "fair_chance": "no_requirements_mentioned", "endorsements": "none_required" },
    { "job_id": "xyz456", "match": "bad", "reason": "Requires own truck", "summary": "This owner-operator position requires drivers to provide their own truck and trailer along with 5+ years of verifiable experience. Pay is percentage-based ranging from 70-85% of gross revenue with drivers responsible for fuel, maintenance, and insurance costs. The role involves long-haul routes covering 48 states with 2-3 weeks out and 2-3 days home. While earnings potential can reach $200,000+ annually for experienced operators, the significant equipment investment and experience requirements make this unsuitable for entry-level drivers.", "fair_chance": "no_requirements_mentioned", "endorsements": "none_required" },
    { "job_id": "def789", "match": "bad", "reason": "Requires clean criminal record", "summary": "This regional trucking position offers $60,000-$70,000 annually for drivers to haul freight across multiple states. The company provides late-model equipment and offers health benefits after 90 days. However, the position requires a completely clean criminal background with no felonies or misdemeanors ever, making it unsuitable for many FreeWorld candidates. Routes typically involve 5 days out and 2 days home with some weekend work required. While the pay is competitive, the strict background requirements eliminate most candidates with criminal histories.", "fair_chance": "clean_record_required", "endorsements": "none_required" },
    { "job_id": "ghi012", "match": "so-so", "reason": "Requires Hazmat endorsement", "summary": "This regional tanker driver position offers $70,000-$80,000 annually transporting liquid chemicals. The role requires a valid Hazmat endorsement in addition to CDL-A, which candidates can obtain with company support. Routes cover multiple states with 4-5 days out and 2-3 days home. The company provides specialized training for hazmat transport and safety protocols. While the endorsement requirement adds complexity, the company assists with testing and the pay is above average for the region.", "fair_chance": "no_requirements_mentioned", "endorsements": "hazmat" }
  ]
}

**CLASSIFICATION STANDARDS - USE EXACT VALUES ONLY:**

**FAIR CHANCE CLASSIFICATION (fair_chance field):**
- "fair_chance_employer": Fair chance employer - welcomes applicants with criminal records
- "background_check_required": Background check required - may disqualify applicants with records
- "clean_record_required": Clean driving/criminal record explicitly required
- "no_requirements_mentioned": No background check requirements mentioned

**ENDORSEMENT CLASSIFICATION (endorsements field):**
- "none_required": No special CDL endorsements required
- "hazmat": Hazmat endorsement required
- "passenger": Passenger endorsement required
- "school_bus": School bus endorsement required
- "tanker": Tanker endorsement required
- "double_triple": Double/Triple trailer endorsement required
- "combination": Multiple endorsements required

**CLASSIFICATION RULES:**
1. Use ONLY the exact values listed above
2. For fair_chance: Look for explicit policies about criminal records/background checks
3. For endorsements: Look for REQUIRED CDL endorsements (not preferred or helpful)
4. If unclear or not mentioned, use appropriate default values
5. Be conservative - only classify as fair_chance_employer if explicitly stated

**EXAMPLES:**
- "We welcome applicants with criminal records" → fair_chance: "fair_chance_employer"
- "Clean criminal record required" or "no felonies" → fair_chance: "clean_record_required"
- "Background check required" (criminal) → fair_chance: "background_check_required"
- "Clean driving record required" → fair_chance: "no_requirements_mentioned" (driving record ≠ criminal background)
- No mention of background → fair_chance: "no_requirements_mentioned"
- "Hazmat endorsement required" → endorsements: "hazmat"
- "No special endorsements needed" → endorsements: "none_required"

**NOTE:** Location normalization is handled by the pipeline, focus on job quality and requirements assessment.
"""
        # Use shared schema object for prompt caching
        schema = self.CLASSIFICATION_SCHEMA
        
        # Convert jobs to work items
        items = []
        for job in jobs_list:
            job_content = f"""
Job ID: {job['job_id']}
Job Title: {job['job_title']}
Company: {job['company']}
Location: {job['location']}

Job Description:
{job['job_description']}
"""
            items.append({
                'id': job['job_id'],
                'content': job_content.strip()
            })
        
        start_time = time.time()
        
        # Run the work queue synchronously
        results_map = self._run_sync_queue(items, system_prompt, schema, concurrency)
        
        # Convert results back to expected format
        final_results = []
        elapsed = time.time() - start_time
        success_count = sum(1 for r in results_map.values() if r['ok'])
        
        
        for job in jobs_list:
            job_id = job['job_id']
            result = results_map.get(job_id, {'ok': False, 'error': 'Missing result'})
            
            if result['ok'] and 'data' in result:
                # Parse the structured output (single job format)
                try:
                    job_result = result['data']  # Direct access since it's single job
                    final_results.append({
                        'job_id': job_id,
                        'match': job_result.get('match', 'error'),
                        'reason': job_result.get('reason', 'No reason provided'),
                        'summary': job_result.get('summary', 'No summary provided'),
                        'normalized_location': job_result.get('normalized_location', job_data.get('location', '')),
                        'route_type': 'Unknown',
                        'fair_chance': job_result.get('fair_chance', 'no_requirements_mentioned'),
                        'endorsements': job_result.get('endorsements', 'none_required'),
                        'final_status': ''
                    })
                except Exception as e:
                    final_results.append({
                        'job_id': job_id,
                        'match': 'error',
                        'reason': f'Parse error: {e}',
                        'summary': 'Error parsing response',
                        'normalized_location': '',
                        'route_type': 'Unknown',
                        'fair_chance': 'unknown',
                        'endorsements': 'unknown',
                        'final_status': 'processing_error'
                    })
            else:
                # Handle error case
                final_results.append({
                    'job_id': job_id,
                    'match': 'error',
                    'reason': result.get('error', 'API error'),
                    'summary': 'API call failed',
                    'normalized_location': '',
                    'route_type': 'Unknown',
                    'fair_chance': 'unknown',
                    'endorsements': 'unknown',
                    'final_status': 'processing_error'
                })
        
        return final_results
    
    def _run_sync_queue(self, items, system_prompt, schema, concurrency):
        """
        Synchronous work queue with proper concurrency - NO artificial delays
        """
        import threading
        from queue import Queue
        import time
        
        results = {}
        work_queue = Queue()
        results_lock = threading.Lock()
        
        # Add all items to queue
        for item in items:
            work_queue.put(item)
        
        # Statistics
        start_time = time.time()
        latencies = []
        status_counts = {'success': 0, 'error': 0}
        
        def worker():
            while True:
                try:
                    item = work_queue.get_nowait()
                except queue.Empty:
                    break
                
                # Make API call with timing
                item_start = time.time()
                try:
                    result = self._make_single_request(item, system_prompt)
                    with results_lock:
                        results[item['id']] = {'ok': True, 'data': result}
                        status_counts['success'] += 1
                        latencies.append(time.time() - item_start)
                except Exception as e:
                    with results_lock:
                        results[item['id']] = {'ok': False, 'error': str(e)}
                        status_counts['error'] += 1
                        latencies.append(time.time() - item_start)
                finally:
                    work_queue.task_done()
                    # NO artificial sleep - let the API handle its own rate limits
        
        # Start workers
        threads = []
        for i in range(min(concurrency, len(items))):
            t = threading.Thread(target=worker, name=f"worker-{i}")
            t.start()
            threads.append(t)
        
        # Wait for completion
        for t in threads:
            t.join()
            
        # Print enhanced telemetry with performance insights
        total_time = time.time() - start_time
        if latencies:
            latencies.sort()
            p50 = latencies[len(latencies)//2]
            p95 = latencies[int(len(latencies)*0.95)] if len(latencies) > 1 else p50
            
            print(f"  📊 Performance: P50={p50:.1f}s, P95={p95:.1f}s, Total={total_time:.1f}s")
            print(f"  📊 Status: {status_counts['success']} success, {status_counts['error']} errors")
            
            # Auto-tune warning for high variance
            if p95 > 2 * p50:
                print(f"  ⚠️ High latency variance detected (P95={p95:.1f}s > 2×P50={p50:.1f}s) - consider reducing concurrency")
            
            # Connection reuse effectiveness
            avg_latency = sum(latencies) / len(latencies)
            if avg_latency < 2.0:
                print(f"  ✅ Connection reuse working well (avg {avg_latency:.1f}s/request)")
            else:
                print(f"  ⚠️ High average latency ({avg_latency:.1f}s) - check connection pooling")
        
        return results
    
    def __del__(self):
        """Cleanup HTTP connections on object destruction"""
        try:
            if hasattr(self, 'http_client'):
                self.http_client.close()
        except Exception:
            pass  # Ignore cleanup errors
    
    def _make_single_request(self, item, system_prompt, max_retries=3):
        """
        Make a single API request with proper retry logic and Retry-After support
        """
        import time
        import json
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,  # Use consistent model constant
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": item['content']}
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "job_classification",
                            "schema": self.CLASSIFICATION_SCHEMA,  # Shared schema for caching!
                            "strict": True
                        }
                    },
                    temperature=0,
                    max_tokens=500,  # Increased for full 4-6 sentence summaries
                    timeout=30  # Adequate timeout for 500-token responses
                )
                
                content = response.choices[0].message.content.strip()
                return json.loads(content)
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                    
                # Check for rate limit with Retry-After
                status = getattr(e, "status", None) or getattr(getattr(e, "response", None), "status_code", None)
                if status in self.RETRIABLE:
                    # Honor Retry-After when present
                    retry_after = None
                    try:
                        retry_after = getattr(e, "response", None) and e.response.headers.get("Retry-After")
                    except Exception:
                        pass
                    
                    if retry_after:
                        wait_time = float(retry_after)
                        print(f"⏳ Rate limited, waiting {wait_time}s (Retry-After header)")
                    else:
                        # Exponential backoff
                        wait_time = (2 ** attempt) * 0.1  # Much shorter backoff
                        
                    time.sleep(wait_time)
                else:
                    # Non-retriable error, fail fast
                    raise e
        
        raise Exception("Max retries exceeded")
    
    
    async def _call_openai_async(self, session, job_id, job_content, system_prompt, semaphore, max_retries=3):
        """
        Make async OpenAI API call with GUARD 5: Robust JSON parsing and fallback
        """
        async with semaphore:
            api_url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "temperature": 0,
                "max_tokens": 500,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "job_classification",
                        "schema": self.CLASSIFICATION_SCHEMA,
                        "strict": True
                    }
                },
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": job_content}
                ],
            }
            
            for attempt in range(max_retries):
                try:
                    async with session.post(api_url, headers=headers, json=payload, timeout=30) as response:
                        response_text = await response.text()
                        
                        if response.status == 200:
                            data = await response.json()
                            try:
                                # GUARD 5: Handle structured outputs correctly
                                # With json_schema + strict: True, OpenAI returns parsed object directly
                                message = data['choices'][0]['message']
                                
                                # Check if we have parsed content (structured outputs) or need to parse JSON
                                if 'parsed' in message and message['parsed']:
                                    # Structured outputs - already parsed
                                    parsed_result = message['parsed']
                                elif message.get('content'):
                                    # Fallback to content parsing for non-structured responses
                                    raw_content = message['content']
                                    
                                    # Try direct JSON parse first
                                    try:
                                        parsed_result = json.loads(raw_content)
                                    except json.JSONDecodeError:
                                        # Fallback: strip common JSON wrapper artifacts
                                        if raw_content.startswith("```json"):
                                            raw_content = raw_content.replace("```json", "").replace("```", "").strip()
                                        if raw_content.startswith("```"):
                                            raw_content = raw_content.replace("```", "").strip()
                                        parsed_result = json.loads(raw_content)
                                else:
                                    raise ValueError("No parsed content or content field in response")
                                
                                # Validate required fields are present
                                required_fields = ['match', 'reason', 'summary', 'fair_chance', 'endorsements']
                                if not all(key in parsed_result for key in required_fields):
                                    missing_fields = [key for key in required_fields if key not in parsed_result]
                                    
                                    # GUARD 5: Create fallback result instead of failing
                                    print(f"⚠️ GUARD 5: Missing fields {missing_fields} for job {job_id} - using fallback")
                                    return {
                                        "job_id": job_id,  # GUARD 1: Always use original job_id
                                        "match": parsed_result.get("match", "error"),
                                        "reason": parsed_result.get("reason", "Missing required fields"),
                                        "summary": parsed_result.get("summary", "API response incomplete"),
                                        "fair_chance": parsed_result.get("fair_chance", "no_requirements_mentioned"),
                                        "endorsements": parsed_result.get("endorsements", "none_required")
                                    }
                                
                                # GUARD 1: Never trust model's job_id - always use original
                                return {
                                    "job_id": job_id,  # Always use the original job_id
                                    **parsed_result    # Overlay parsed results
                                }
                                
                            except (json.JSONDecodeError, KeyError, ValueError) as e:
                                # GUARD 5: Final fallback - return error result instead of raising
                                print(f"⚠️ GUARD 5: JSON parse failed for job {job_id}: {e} - using error fallback")
                                return {
                                    "job_id": job_id,
                                    "match": "error",
                                    "reason": f"JSON parse error: {str(e)[:100]}",
                                    "summary": "Failed to parse API response",
                                    "fair_chance": "no_requirements_mentioned",
                                    "endorsements": "none_required"
                                }
                        elif response.status == 429:
                            # Rate limit - check Retry-After header
                            retry_after = response.headers.get('Retry-After')
                            if retry_after:
                                wait_time = float(retry_after)
                            else:
                                wait_time = (2 ** attempt) * 0.5
                            await asyncio.sleep(wait_time)
                        elif response.status in [500, 502, 503, 504]:
                            # Server errors - retry with backoff
                            wait_time = (2 ** attempt) * 0.5
                            await asyncio.sleep(wait_time)
                        else:
                            # Client errors - don't retry
                            raise Exception(f"OpenAI API error {response.status}: {response_text}")
                            
                except asyncio.TimeoutError:
                    if attempt == max_retries - 1:
                        raise Exception("OpenAI API timeout after retries")
                    await asyncio.sleep((2 ** attempt) * 0.5)
                except aiohttp.ClientError as e:
                    if attempt == max_retries - 1:
                        raise Exception(f"Connection error: {e}")
                    await asyncio.sleep((2 ** attempt) * 0.5)
            
            raise Exception("Max retries exceeded")
    
    async def _classify_jobs_async(self, jobs_list, concurrency=50):
        # Define the system prompt here for the async method  
        # Use the good system prompt with explicit field mapping (same as line 137)
        system_prompt = """
FreeWorld is a non-profit that helps Americans with low incomes find career pathway jobs that lead to living wage opportunities in transportation and logistics.
Our candidates are looking for entry-level positions that provide clear advancement opportunities, especially pathways to CDL driving careers. Many have limited work experience, criminal backgrounds, and need employers who provide training and career development.
We focus on connecting candidates to jobs that offer genuine career growth potential - from warehouse/dock work to driving, from non-CDL delivery to CDL opportunities, and logistics roles that provide industry experience.

**CLASSIFICATION PRIORITY SYSTEM:**

1. **CAREER PATHWAY POTENTIAL**: Jobs with clear advancement paths are top priority
2. **TRAINING PROVIDED**: Jobs that offer CDL training, skills development, or advancement opportunities
3. **ENTRY-LEVEL FRIENDLY**: Jobs that hire candidates with limited experience or criminal backgrounds

**PATHWAY CATEGORIES:**
- **dock_to_driver**: Warehouse/dock positions with explicit CDL training or driver advancement
- **internal_cdl_training**: Companies offering paid CDL training programs
- **warehouse_to_driver**: General warehouse roles at transportation companies with driver pathways
- **logistics_progression**: Dispatcher, coordinator roles that lead to management opportunities
- **non_cdl_driving**: Delivery, local driving that doesn't require CDL but provides driving experience
- **general_warehouse**: Standard warehouse work at logistics companies (stepping stone potential)
- **stepping_stone**: Other roles that provide industry experience and advancement potential

Jobs should be classified as **good** if they:
- Explicitly offer CDL training or driver pathways
- Provide clear advancement opportunities
- Are entry-level friendly with training provided
- Welcome candidates with criminal backgrounds

3. **AUTOMATIC DISQUALIFIERS**:
   - Owner-operator/1099 (must own truck/trailer) → BAD
   - School bus driving → BAD  
   - Requires "no felonies AND no misdemeanors" combined → BAD

**ENDORSEMENT REQUIREMENTS:**
FreeWorld candidates have CDL-A with basic training on air brakes, combination vehicles, and manual transmissions. ENDORSEMENTS ARE NOT A BARRIER. FreeWorld helps Free Agents get ANY endorsement they need to get work.

IMPORTANT: For each job, you MUST create a detailed summary that is EXACTLY 6-8 sentences long. 

- Don't make all jobs sound the same!**
- Preserve specific phrases that detail the nature of the work.
- Maintain their exact pay ranges, bonuses, and incentives as stated

These elements are also very relevant to our job seekers and should be included IF there is actual text from the ad that mentions them:
1) What the job role entails and main duties (using their language)
2) Pay/benefits offered (their exact wording and specific numbers)
3) Route and schedule information (preserve their exact terms: "home daily", "out 5 days", "weekends off", specific routes, territories, etc.)
4) Physical demands of the job (mention if it's "no-touch freight", requires loading/unloading, heavy lifting, dock work, etc.)
5) Key requirements and qualifications (including criminal background requirements if mentioned)
7) Any training provided or growth opportunities (their exact promises)

Don't standardize everything - each company should sound different! 

**IMPORTANT DETAILS TO PRESERVE WHEN PRESENT:**
- Route information
- Schedule details
- Physical demands

If criminal background requirements are actually mentioned, include them clearly using the company's exact language when possible.

Return your results as a JSON object with a "job_classifications" array like this:
{
  "job_classifications": [
    { "job_id": "abc123", "match": "good", "reason": "Quote from job post", "summary": "This local delivery driver position offers $55,000-$65,000 annually with no prior experience required. The role involves delivering packages within the metro area using company-provided trucks and equipment. Benefits include full health insurance, dental, vision, and paid time off starting on day one. The company provides comprehensive 2-week training including vehicle operation and route planning. Drivers work Monday-Friday with occasional Saturday shifts and are typically home every night. This is an excellent opportunity for new CDL holders to gain experience while earning competitive wages.", "fair_chance": "no_requirements_mentioned", "endorsements": "none_required" },
    { "job_id": "xyz456", "match": "bad", "reason": "Requires own truck", "summary": "This owner-operator position requires drivers to provide their own truck and trailer along with 5+ years of verifiable experience. Pay is percentage-based ranging from 70-85% of gross revenue with drivers responsible for fuel, maintenance, and insurance costs. The role involves long-haul routes covering 48 states with 2-3 weeks out and 2-3 days home. While earnings potential can reach $200,000+ annually for experienced operators, the significant equipment investment and experience requirements make this unsuitable for entry-level drivers.", "fair_chance": "no_requirements_mentioned", "endorsements": "none_required" },
    { "job_id": "def789", "match": "bad", "reason": "Requires clean criminal record", "summary": "This regional trucking position offers $60,000-$70,000 annually for drivers to haul freight across multiple states. The company provides late-model equipment and offers health benefits after 90 days. However, the position requires a completely clean criminal background with no felonies or misdemeanors ever, making it unsuitable for many FreeWorld candidates. Routes typically involve 5 days out and 2 days home with some weekend work required. While the pay is competitive, the strict background requirements eliminate most candidates with criminal histories.", "fair_chance": "clean_record_required", "endorsements": "none_required" },
    { "job_id": "ghi012", "match": "so-so", "reason": "Requires Hazmat endorsement", "summary": "This regional tanker driver position offers $70,000-$80,000 annually transporting liquid chemicals. The role requires a valid Hazmat endorsement in addition to CDL-A, which candidates can obtain with company support. Routes cover multiple states with 4-5 days out and 2-3 days home. The company provides specialized training for hazmat transport and safety protocols. While the endorsement requirement adds complexity, the company assists with testing and the pay is above average for the region.", "fair_chance": "no_requirements_mentioned", "endorsements": "hazmat" }
  ]
}

**CLASSIFICATION STANDARDS - USE EXACT VALUES ONLY:**

**FAIR CHANCE CLASSIFICATION (fair_chance field):**
- "fair_chance_employer": Fair chance employer - welcomes applicants with criminal records
- "background_check_required": Background check required - may disqualify applicants with records
- "clean_record_required": Clean driving/criminal record explicitly required
- "no_requirements_mentioned": No background check requirements mentioned

**ENDORSEMENT CLASSIFICATION (endorsements field):**
- "none_required": No special CDL endorsements required
- "hazmat": Hazmat endorsement required
- "passenger": Passenger endorsement required
- "school_bus": School bus endorsement required
- "tanker": Tanker endorsement required
- "double_triple": Double/Triple trailer endorsement required
- "combination": Multiple endorsements required

**CLASSIFICATION RULES:**
1. Use ONLY the exact values listed above
2. For fair_chance: Look for explicit policies about criminal records/background checks
3. For endorsements: Look for REQUIRED CDL endorsements (not preferred or helpful)
4. If unclear or not mentioned, use appropriate default values
5. Be conservative - only classify as fair_chance_employer if explicitly stated

**EXAMPLES:**
- "We welcome applicants with criminal records" → fair_chance: "fair_chance_employer"
- "Clean criminal record required" or "no felonies" → fair_chance: "clean_record_required"
- "Background check required" (criminal) → fair_chance: "background_check_required"
- "Clean driving record required" → fair_chance: "no_requirements_mentioned" (driving record ≠ criminal background)
- No mention of background → fair_chance: "no_requirements_mentioned"
- "Hazmat endorsement required" → endorsements: "hazmat"
- "No special endorsements needed" → endorsements: "none_required"

**NOTE:** Location normalization is handled by the pipeline, focus on job quality and requirements assessment.
"""
        """
        Fast async classification with 6 NON-NEGOTIABLE GUARDS to prevent job loss
        """
        # Connection pooling configuration  
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False  # Disable hostname verification
        ssl_context.verify_mode = ssl.CERT_NONE  # Disable certificate verification
        
        connector = aiohttp.TCPConnector(
            limit=200,
            limit_per_host=100,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
            ssl=ssl_context
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        semaphore = asyncio.Semaphore(concurrency)
        
        # GUARD 1: Prepare input job IDs list for exact tracking
        input_job_ids = [job['job_id'] for job in jobs_list]
        print(f"🔒 GUARD 1: Tracking {len(input_job_ids)} input job IDs")
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Prepare tasks - ONE JOB PER REQUEST (GUARD 6)
            tasks = []
            for job in jobs_list:
                job_content = f"""
Job ID: {job['job_id']}
Job Title: {job['job_title']}
Company: {job['company']}
Location: {job['location']}

Job Description:
{job['job_description']}
"""
                task = self._process_single_job_async(session, job, job_content.strip(), system_prompt, semaphore)
                tasks.append(task)
            
            # Execute all tasks concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # GUARD 3: Key results by job_id from input list - dict keyed by job_id
            results_by_job_id = {}
            success_count = 0
            error_count = 0
            latencies = []
            
            for i, result in enumerate(results):
                job = jobs_list[i]  # Get the corresponding job
                job_id = job['job_id']  # Original job_id from input
                
                if isinstance(result, Exception):
                    # GUARD 2: Always return error record on failure
                    job_result = {
                        'job_id': job_id,  # GUARD 1: Never trust model's job_id - use original
                        'match': 'error',
                        'reason': str(result),
                        'summary': 'Error processing job',
                        'route_type': 'Unknown',
                        'fair_chance': 'unknown',
                        'endorsements': 'unknown',
                        'final_status': 'processing_error'
                    }
                    results_by_job_id[job_id] = job_result
                    error_count += 1
                else:
                    job_result = result['result']
                    # GUARD 1: Never trust model's job_id - always stamp original
                    job_result['job_id'] = job_id  # Force original job_id
                    results_by_job_id[job_id] = job_result
                    success_count += 1
                    if 'latency' in result:
                        latencies.append(result['latency'])
            
            # GUARD 4: End-of-batch reconciliation - ensure every input job has a result
            print(f"🔒 GUARD 4: Reconciliation check")
            final_results = []
            
            for job_id in input_job_ids:
                if job_id in results_by_job_id:
                    final_results.append(results_by_job_id[job_id])
                else:
                    # Create error result for missing job
                    print(f"🚨 GUARD 4: Missing job_id {job_id} - creating error record")
                    missing_job_result = {
                        'job_id': job_id,
                        'match': 'error',
                        'reason': 'Job missing from async processing',
                        'summary': 'Job lost during async processing',
                        'route_type': 'Unknown',
                        'fair_chance': 'unknown',
                        'endorsements': 'unknown',
                        'final_status': 'processing_error: missing_from_async'
                    }
                    final_results.append(missing_job_result)
                    error_count += 1
            
            # GUARD 4: Critical validation - must have exact count match
            if len(final_results) != len(input_job_ids):
                raise Exception(f"GUARD 4 VIOLATION: Expected {len(input_job_ids)} results, got {len(final_results)}")
            
            print(f"🔒 GUARD 4: SUCCESS - {len(final_results)} results for {len(input_job_ids)} input jobs")
            
            # Print performance stats
            if latencies:
                latencies.sort()
                p50 = latencies[len(latencies)//2]
                p95 = latencies[int(len(latencies)*0.95)] if len(latencies) > 1 else p50
                avg_latency = sum(latencies) / len(latencies)
                
                print(f"  📊 Async Performance: P50={p50:.1f}s, P95={p95:.1f}s, Avg={avg_latency:.1f}s, Total={total_time:.1f}s")
                print(f"  📊 Status: {success_count} success, {error_count} errors")
                print(f"  📊 Concurrency: {concurrency}, Jobs/sec: {len(jobs_list)/total_time:.1f}")
                
                if error_count == 0:
                    print(f"  ✅ PERFECT: 0% job loss rate")
                else:
                    error_rate = (error_count / len(jobs_list)) * 100
                    print(f"  ⚠️ Error rate: {error_rate:.1f}% ({error_count}/{len(jobs_list)} jobs)")
            
            return final_results
    
    async def _process_single_job_async(self, session, job, job_content, system_prompt, semaphore):
        """
        Process a single job with GUARD 1 & 2: Never trust model's job_id, always return error record
        """
        start_time = time.time()
        original_job_id = job['job_id']  # GUARD 1: Store original job_id
        
        try:
            api_result = await self._call_openai_async(session, original_job_id, job_content, system_prompt, semaphore)
            latency = time.time() - start_time
            
            return {
                'result': {
                    'job_id': original_job_id,  # GUARD 1: Always use original job_id
                    'match': api_result.get('match', 'error'),
                    'reason': api_result.get('reason', 'No reason provided'),
                    'summary': api_result.get('summary', 'No summary provided'),
                    'normalized_location': api_result.get('normalized_location', ''),
                    'route_type': 'Unknown',
                    'fair_chance': api_result.get('fair_chance', 'no_requirements_mentioned'),
                    'endorsements': api_result.get('endorsements', 'none_required'),
                    'final_status': ''
                },
                'latency': latency
            }
        except Exception as e:
            # GUARD 2: Always return error record on failure - NEVER skip/drop jobs
            latency = time.time() - start_time
            return {
                'result': {
                    'job_id': original_job_id,  # GUARD 1: Always use original job_id
                    'match': 'error',
                    'reason': str(e),
                    'summary': 'API call failed',
                    'normalized_location': '',
                    'route_type': 'Unknown',
                    'fair_chance': 'unknown',
                    'endorsements': 'unknown',
                    'final_status': 'processing_error'
                },
                'latency': latency
            }

    def test_batch_classification(self):
        # Test with sample jobs
        test_jobs = [
            {
                'job_id': 'test1',
                'job_title': 'CDL Driver - No Experience Required',
                'company': 'ABC Trucking',
                'location': 'Dallas, TX',
                'job_description': 'We are looking for CDL-A drivers. No experience required! We provide training and equipment. Must have clean driving record.'
            },
            {
                'job_id': 'test2', 
                'job_title': 'Owner Operator CDL Driver',
                'company': 'XYZ Logistics',
                'location': 'Houston, TX',
                'job_description': 'Must own your own truck and trailer. 5+ years experience required. Lease purchase available.'
            }
        ]
        
        print("Testing batch job classification...")
        results = self.classify_jobs_in_batches(test_jobs)
        
        print(f"\n📊 Results Summary:")
        for result in results:
            print(f"  {result['job_id']}: {result['match']} - {result['reason']}")
            if 'summary' in result:
                print(f"    Summary: {result['summary']}")
            print()

if __name__ == "__main__":
    classifier = JobClassifier()
    classifier.test_batch_classification()
