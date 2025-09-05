import pandas as pd
import re
from bs4 import BeautifulSoup
import hashlib
from airtable_uploader import AirtableUploader

class FileProcessor:
    """Process various job file formats (CSV, Excel) from different sources"""
    
    def __init__(self):
        pass
    
    def clean_html(self, raw_html):
        """Clean HTML from job descriptions"""
        return BeautifulSoup(str(raw_html), "html.parser").get_text().strip()
    
    def clean_location(self, location):
        """Basic location cleaning - remove zip codes"""
        return re.sub(r'\s+\d{5}(-\d{4})?, ', '', str(location)).strip()
    
    def extract_first_url(self, apply_urls):
        """Extract first URL from apply_urls field"""
        matches = re.findall(r'https?://[^\s"\']+', str(apply_urls))
        return matches[0] if matches else ""
    
    def generate_job_id(self, company, location, job_title):
        """Generate MD5 hash ID for job deduplication"""
        base_string = f"{str(company).lower().strip()}|{str(location).lower().strip()}|{str(job_title).lower().strip()}"
        return hashlib.md5(base_string.encode()).hexdigest()
    
    def _process_indeed_salary_fields(self, job_df, raw_df):
        """Process comprehensive salary data from Indeed salarySnippet"""
        # Initialize all salary columns
        salary_columns = [
            'salary', 'salary_estimated_currency', 'salary_estimated_unit', 'salary_estimated_min', 'salary_estimated_max',
            'salary_base_currency', 'salary_base_unit', 'salary_base_min', 'salary_base_max', 'salary_display_text'
        ]
        
        for col in salary_columns:
            job_df[col] = ""
        
        # Process each job's salary data
        for idx in job_df.index:
            salary_snippet = raw_df.loc[idx, 'salarySnippet'] if 'salarySnippet' in raw_df.columns else {}
            
            if not salary_snippet or not isinstance(salary_snippet, dict):
                continue
            
            # Extract estimated salary (Indeed's algorithm)
            if 'estimated' in salary_snippet and salary_snippet['estimated']:
                estimated = salary_snippet['estimated']
                job_df.loc[idx, 'salary_estimated_currency'] = estimated.get('currencyCode', '')
                
                if 'baseSalary' in estimated and estimated['baseSalary']:
                    base_salary = estimated['baseSalary']
                    job_df.loc[idx, 'salary_estimated_unit'] = base_salary.get('unitOfWork', '')
                    
                    if 'range' in base_salary and base_salary['range']:
                        salary_range = base_salary['range']
                        job_df.loc[idx, 'salary_estimated_min'] = str(salary_range.get('min', ''))
                        job_df.loc[idx, 'salary_estimated_max'] = str(salary_range.get('max', ''))
            
            # Extract base salary (employer-provided)  
            if 'baseSalary' in salary_snippet and salary_snippet['baseSalary']:
                base_salary = salary_snippet['baseSalary']
                job_df.loc[idx, 'salary_base_unit'] = base_salary.get('unitOfWork', '')
                
                if 'range' in base_salary and base_salary['range']:
                    salary_range = base_salary['range']
                    job_df.loc[idx, 'salary_base_min'] = str(salary_range.get('min', ''))
                    job_df.loc[idx, 'salary_base_max'] = str(salary_range.get('max', ''))
            
            # Set base currency from snippet level
            job_df.loc[idx, 'salary_base_currency'] = salary_snippet.get('currencyCode', '')
            
            # Create display text
            display_text = self._format_salary_display_text(job_df.loc[idx])
            job_df.loc[idx, 'salary_display_text'] = display_text
            job_df.loc[idx, 'salary'] = display_text  # Backwards compatibility
    
    def _format_salary_display_text(self, job_row):
        """Create human-readable salary display text from salary data"""
        display_parts = []
        
        # Prioritize employer-provided salary over estimated
        if job_row['salary_base_min'] and job_row['salary_base_max']:
            unit = job_row['salary_base_unit'].lower() if job_row['salary_base_unit'] else 'year'
            
            try:
                min_val = float(job_row['salary_base_min'])
                max_val = float(job_row['salary_base_max'])
                
                if unit == 'hour':
                    display_parts.append(f"${min_val:,.0f}-${max_val:,.0f}/hour")
                elif unit == 'week':
                    display_parts.append(f"${min_val:,.0f}-${max_val:,.0f}/week")
                elif unit == 'year':
                    display_parts.append(f"${min_val:,.0f}-${max_val:,.0f}/year")
                else:
                    display_parts.append(f"${min_val:,.0f}-${max_val:,.0f}/{unit}")
            except (ValueError, TypeError):
                pass
        
        # Add estimated if different or if no base salary
        if job_row['salary_estimated_min'] and job_row['salary_estimated_max']:
            unit = job_row['salary_estimated_unit'].lower() if job_row['salary_estimated_unit'] else 'year'
            
            try:
                min_val = float(job_row['salary_estimated_min'])
                max_val = float(job_row['salary_estimated_max'])
                
                estimated_text = ""
                if unit == 'hour':
                    estimated_text = f"${min_val:,.0f}-${max_val:,.0f}/hour"
                elif unit == 'week':
                    estimated_text = f"${min_val:,.0f}-${max_val:,.0f}/week"  
                elif unit == 'year':
                    estimated_text = f"${min_val:,.0f}-${max_val:,.0f}/year"
                else:
                    estimated_text = f"${min_val:,.0f}-${max_val:,.0f}/{unit}"
                
                # Only add estimated if we don't have base salary or if it's different
                if not display_parts:
                    display_parts.append(f"{estimated_text} (estimated)")
                elif estimated_text not in display_parts[0]:
                    display_parts.append(f"{estimated_text} (estimated)")
            except (ValueError, TypeError):
                pass
        
        return " | ".join(display_parts) if display_parts else ""
    
    def process_outscraper_csv(self, filepath):
        """Process Indeed CSV files from Outscraper"""
        print(f"📄 Processing Indeed CSV: {filepath}")
        
        df = pd.read_csv(filepath)
        job_df = pd.DataFrame()
        
        # Check if this is already a processed file (has job_title column)
        if 'job_title' in df.columns:
            print("  📋 Detected pre-processed file format")
            job_df = df.copy()
            
            # Ensure all required columns exist
            required_columns = ['job_title', 'company', 'location', 'apply_url', 'job_description', 'source', 
                              'salary', 'salary_estimated_currency', 'salary_estimated_unit', 'salary_estimated_min', 'salary_estimated_max',
                              'salary_base_currency', 'salary_base_unit', 'salary_base_min', 'salary_base_max', 'salary_display_text']
            for col in required_columns:
                if col not in job_df.columns:
                    job_df[col] = ""
            
            # Initialize missing classification fields
            classification_fields = ['match', 'reason', 'summary', 'route_type', 'market', 'final_status', 'fair_chance', 'endorsements']
            for field in classification_fields:
                if field not in job_df.columns:
                    job_df[field] = ""
            
            # Generate job ID if missing
            if 'job_id' not in job_df.columns:
                job_df['job_id'] = job_df.apply(
                    lambda x: self.generate_job_id(x['company'], x['location'], x['job_title']), 
                    axis=1
                )
        
        else:
            # Standard Outscraper format with 'title', 'formattedLocation', etc.
            print("  📋 Detected standard Outscraper format")
            
            # Map fields to standard format
            job_df['job_title'] = df['title']
            job_df['company'] = df['company']
            job_df['location'] = df['formattedLocation'].apply(self.clean_location)
            job_df['apply_url'] = df['viewJobLink']
            job_df['job_description'] = df['snippet'].apply(self.clean_html)
            job_df['source'] = 'Indeed'
            
            # Process comprehensive salary data
            self._process_indeed_salary_fields(job_df, df)
            
            # Initialize classification fields - DO NOT add match/reason/summary as empty strings!
            # These should only be added by the AI classifier to avoid bypassing classification
            job_df['route_type'] = ""
            job_df['market'] = ""
            job_df['final_status'] = ""
            job_df['fair_chance'] = ""
            job_df['endorsements'] = ""
            job_df['removal_reason'] = ""
            job_df['filtered'] = False
            job_df['classification_source'] = ""
            
            # Generate job IDs for deduplication
            job_df['job_id'] = job_df.apply(
                lambda x: self.generate_job_id(x['company'], x['location'], x['job_title']), 
                axis=1
            )
        
        print(f"✅ Processed {len(job_df)} jobs from CSV")
        return job_df
    
    def process_outscraper_excel(self, filepath):
        """Process Google Careers Excel files from Outscraper"""
        print(f"📄 Processing Google Careers Excel: {filepath}")
        
        try:
            # Try different sheet names that Outscraper uses
            try:
                df = pd.read_excel(filepath, sheet_name='Generated by Outscraper ©')
            except:
                df = pd.read_excel(filepath, sheet_name='Generated by Outscraper \xa9')
        except Exception as e:
            print(f"❌ Error reading Excel file: {e}")
            # Try reading without specifying sheet name
            df = pd.read_excel(filepath)
        
        job_df = pd.DataFrame()
        
        # Map fields to standard format  
        job_df['job_title'] = df['title']
        job_df['company'] = df['company']
        job_df['location'] = df['location'].apply(self.clean_location)
        job_df['apply_url'] = df['apply_urls'].apply(self.extract_first_url)
        job_df['job_description'] = df['description']
        job_df['salary'] = df.get('salary', '')
        job_df['source'] = 'Google Careers'
        
        # Initialize classification fields - DO NOT add match/reason/summary as empty strings!
        # These should only be added by the AI classifier to avoid bypassing classification
        job_df['route_type'] = ""
        job_df['market'] = ""
        job_df['final_status'] = ""
        job_df['fair_chance'] = ""
        job_df['endorsements'] = ""
        job_df['removal_reason'] = ""
        job_df['filtered'] = False
        job_df['classification_source'] = ""
        
        # Generate job IDs for deduplication
        job_df['job_id'] = job_df.apply(
            lambda x: self.generate_job_id(x['company'], x['location'], x['job_title']), 
            axis=1
        )
        
        print(f"✅ Processed {len(job_df)} Google Careers jobs from Excel")
        return job_df
    
    def process_file(self, filepath):
        """Auto-detect file type and process accordingly"""
        if filepath.endswith('.csv'):
            return self.process_outscraper_csv(filepath)
        elif filepath.endswith('.xlsx') or filepath.endswith('.xls'):
            return self.process_outscraper_excel(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath}")
    
    def process_multiple_files(self, file_paths):
        """Process multiple files and combine into single DataFrame"""
        print(f"📋 Processing {len(file_paths)} files...")
        
        all_dfs = []
        
        for filepath in file_paths:
            try:
                df = self.process_file(filepath)
                all_dfs.append(df)
            except Exception as e:
                print(f"❌ Error processing {filepath}: {e}")
                continue
        
        if not all_dfs:
            print("❌ No files were successfully processed")
            return pd.DataFrame()
        
        # Combine all DataFrames
        combined_df = pd.concat(all_dfs, ignore_index=True)
        print(f"✅ Combined {len(combined_df)} total jobs from {len(all_dfs)} files")
        
        return combined_df
    
    def _map_to_pipeline_format(self, df):
        """Map our field names to clean pipeline format"""
        pipeline_df = pd.DataFrame()
        
        # Core job fields
        pipeline_df['job_title'] = df.get('job_title', '')
        pipeline_df['company'] = df.get('company', '')  
        pipeline_df['location'] = df.get('location', '')
        pipeline_df['job_description'] = df.get('job_description', '')
        pipeline_df['apply_url'] = df.get('apply_url', '')
        pipeline_df['job_id'] = df.get('job_id', '')
        pipeline_df['source'] = df.get('source', '')
        
        # Comprehensive salary fields for wage analysis
        pipeline_df['salary'] = df.get('salary', '')  # Display text (backwards compatible)
        pipeline_df['salary_display_text'] = df.get('salary_display_text', '')
        pipeline_df['salary_estimated_currency'] = df.get('salary_estimated_currency', '')
        pipeline_df['salary_estimated_unit'] = df.get('salary_estimated_unit', '')
        pipeline_df['salary_estimated_min'] = df.get('salary_estimated_min', '')
        pipeline_df['salary_estimated_max'] = df.get('salary_estimated_max', '')
        pipeline_df['salary_base_currency'] = df.get('salary_base_currency', '')
        pipeline_df['salary_base_unit'] = df.get('salary_base_unit', '')
        pipeline_df['salary_base_min'] = df.get('salary_base_min', '')
        pipeline_df['salary_base_max'] = df.get('salary_base_max', '')
        
        # Classification fields
        if 'match' in df.columns:
            pipeline_df['match'] = df['match']
        if 'reason' in df.columns:
            pipeline_df['reason'] = df['reason']
        if 'summary' in df.columns:
            pipeline_df['summary'] = df['summary']
        if 'route_type' in df.columns:
            pipeline_df['route_type'] = df['route_type']
        if 'market' in df.columns:
            pipeline_df['market'] = df['market']
        if 'final_status' in df.columns:
            pipeline_df['final_status'] = df['final_status']
        
        # New fields from classification
        if 'fair_chance' in df.columns:
            pipeline_df['fair_chance'] = df['fair_chance']
        if 'endorsements' in df.columns:
            pipeline_df['endorsements'] = df['endorsements']
        
        # Filtering and removal tracking fields
        if 'removal_reason' in df.columns:
            pipeline_df['removal_reason'] = df['removal_reason']
        if 'filtered' in df.columns:
            pipeline_df['filtered'] = df['filtered']
        if 'classification_source' in df.columns:
            pipeline_df['classification_source'] = df['classification_source']
        
        # Additional tracking fields that might exist
        if 'created_at' in df.columns:
            pipeline_df['created_at'] = df['created_at']
        if 'processed_at' in df.columns:
            pipeline_df['processed_at'] = df['processed_at']
        if 'viewJobLink' in df.columns:
            pipeline_df['indeed_job_url'] = df['viewJobLink']
        if 'query' in df.columns:
            pipeline_df['search_query'] = df['query']
            
        return pipeline_df

    def _chunk_csv_by_size(self, df, base_filepath, max_size_mb=4.5):
        """Split CSV into chunks if it exceeds max_size_mb"""
        import os
        
        # First, save the full CSV to check size
        test_file = base_filepath.replace('.csv', '_temp.csv')
        df.to_csv(test_file, index=False)
        
        # Check file size
        file_size_mb = os.path.getsize(test_file) / (1024 * 1024)
        
        if file_size_mb <= max_size_mb:
            # File is small enough, just rename it
            os.rename(test_file, base_filepath)
            print(f"    💾 Single file: {os.path.basename(base_filepath)} ({file_size_mb:.1f} MB)")
            return [base_filepath]
        else:
            # File is too large, need to chunk it
            os.remove(test_file)  # Remove temp file
            
            # Calculate approximate rows per chunk
            rows_per_mb = len(df) / file_size_mb
            rows_per_chunk = int(rows_per_mb * max_size_mb * 0.9)  # Leave some buffer
            
            chunk_files = []
            total_chunks = (len(df) + rows_per_chunk - 1) // rows_per_chunk  # Round up
            
            print(f"    📦 File too large ({file_size_mb:.1f} MB), splitting into {total_chunks} chunks...")
            
            for i in range(0, len(df), rows_per_chunk):
                chunk_num = (i // rows_per_chunk) + 1
                chunk_df = df.iloc[i:i + rows_per_chunk]
                
                chunk_file = base_filepath.replace('.csv', f'_part{chunk_num:02d}.csv')
                chunk_df.to_csv(chunk_file, index=False)
                chunk_files.append(chunk_file)
                
                chunk_size_mb = os.path.getsize(chunk_file) / (1024 * 1024)
                print(f"       Part {chunk_num:02d}: {os.path.basename(chunk_file)} ({len(chunk_df)} jobs, {chunk_size_mb:.1f} MB)")
            
            return chunk_files

    def export_results(self, df, base_filename="freeworld_jobs", output_dir="data", combined_csv_data=None, push_to_airtable=False):
        """Export processed results to CSV files with Airtable-compatible format and chunking"""
        import os
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        
        # Create CSV directory for centralized CSV storage
        csv_dir = os.path.join(output_dir, "CSVs")
        os.makedirs(csv_dir, exist_ok=True)
        
        # For multi-market searches, combine data and save once
        if combined_csv_data is not None:
            # This is a multi-market search - save combined CSV
            pipeline_formatted = self._map_to_pipeline_format(combined_csv_data)
            
            combined_file = os.path.join(csv_dir, f"{base_filename}_combined_{timestamp}.csv")
            chunk_files = self._chunk_csv_by_size(pipeline_formatted, combined_file)
            
            # Check if final_status column exists in combined data
            if 'final_status' in combined_csv_data.columns:
                total_included = len(combined_csv_data[combined_csv_data['final_status'] == 'included'])
                total_filtered = len(combined_csv_data[combined_csv_data['final_status'] != 'included'])
                print(f"📁 Exported combined multi-market results ({len(chunk_files)} files)")
                print(f"    ✅ {total_included} included jobs across all markets")
                print(f"    🚫 {total_filtered} filtered jobs")
            else:
                print(f"📁 Exported combined multi-market results ({len(chunk_files)} files)")
                print(f"    📋 {len(combined_csv_data)} total jobs across all markets (not yet classified)")
            print(f"    📋 Clean pipeline format with all classification fields")
            
            result = {
                'full': chunk_files[0] if len(chunk_files) == 1 else chunk_files
            }
            
            # Push to Airtable if requested (multi-market)
            # NOTE: Airtable upload now happens in hybrid_memory_classifier.py
            # immediately after fresh AI classification to avoid uploading memory jobs
            if False:  # Disabled old airtable upload - now handled in classifier
                try:
                    # Filter to only quality jobs for Airtable (exclude bad jobs and continuity jobs)
                    if 'final_status' in combined_csv_data.columns:
                        airtable_jobs = combined_csv_data[
                            combined_csv_data['final_status'] == 'included'
                        ].copy()
                        print(f"📤 Filtering for Airtable: {len(airtable_jobs)} quality jobs out of {len(combined_csv_data)} total")
                    else:
                        airtable_jobs = combined_csv_data
                    
                    if len(airtable_jobs) > 0:
                        uploader = AirtableUploader()
                        airtable_result = uploader.upload_jobs(airtable_jobs)
                        result['airtable'] = airtable_result
                        if airtable_result['success']:
                            print(f"🚀 {airtable_result['message']}")
                        else:
                            print(f"❌ Airtable upload failed: {airtable_result['message']}")
                    else:
                        print("ℹ️ No quality jobs to upload to Airtable")
                        result['airtable'] = {'success': False, 'message': 'No quality jobs to upload'}
                except Exception as e:
                    print(f"❌ Airtable upload error: {e}")
                    result['airtable'] = {'success': False, 'error': str(e)}
            
            return result
        else:
            # Single market search - save individual CSV
            pipeline_formatted = self._map_to_pipeline_format(df)
            
            full_file = os.path.join(csv_dir, f"{base_filename}_full_{timestamp}.csv")
            chunk_files = self._chunk_csv_by_size(pipeline_formatted, full_file)
            
            # Check if final_status column exists
            if 'final_status' in df.columns:
                # Count quality jobs that will be included (including memory-based ones)
                included_statuses = ['included', '_from_memory', 'included_from_memory']
                quality_included = df[df['final_status'].isin(included_statuses) & df['match'].isin(['good', 'so-so'])]
                included_count = len(quality_included)
                filtered_count = len(df) - included_count
                print(f"📁 Exported {len(df)} total jobs ({len(chunk_files)} files)")
                print(f"    ✅ {included_count} included jobs")
                print(f"    🚫 {filtered_count} filtered jobs")
            else:
                print(f"📁 Exported {len(df)} total jobs ({len(chunk_files)} files)")
                print(f"    📋 Jobs not yet classified (no final_status column)") 
            print(f"    📋 Clean pipeline format with all classification fields")
            
            result = {
                'full': chunk_files[0] if len(chunk_files) == 1 else chunk_files
            }
            
            # Push to Airtable if requested (single market)
            # NOTE: Airtable upload now happens in hybrid_memory_classifier.py
            # immediately after fresh AI classification to avoid uploading memory jobs
            if False:  # Disabled old airtable upload - now handled in classifier
                try:
                    # Filter to only quality jobs for Airtable (exclude bad jobs and continuity jobs)
                    if 'final_status' in df.columns:
                        airtable_jobs = df[
                            df['final_status'] == 'included'
                        ].copy()
                        print(f"📤 Filtering for Airtable: {len(airtable_jobs)} quality jobs out of {len(df)} total")
                    else:
                        airtable_jobs = df
                    
                    if len(airtable_jobs) > 0:
                        uploader = AirtableUploader()
                        airtable_result = uploader.upload_jobs(airtable_jobs)
                        result['airtable'] = airtable_result
                        if airtable_result['success']:
                            print(f"🚀 {airtable_result['message']}")
                        else:
                            print(f"❌ Airtable upload failed: {airtable_result['message']}")
                    else:
                        print("ℹ️ No quality jobs to upload to Airtable")
                        result['airtable'] = {'success': False, 'message': 'No quality jobs to upload'}
                except Exception as e:
                    print(f"❌ Airtable upload error: {e}")
                    result['airtable'] = {'success': False, 'error': str(e)}
            
            return result

if __name__ == "__main__":
    # Test file processing
    processor = FileProcessor()
    
    # Test with sample data
    sample_data = {
        'title': ['CDL Driver', 'Owner Operator', 'Local Driver'],
        'company': ['ABC Trucking Inc.', 'XYZ Logistics LLC', 'Local Delivery Co'],
        'formattedLocation': ['Dallas, TX 75201', 'Houston, TX 77001', 'Austin, TX 78701'],
        'viewJobLink': ['https://indeed.com/job1', 'https://indeed.com/job2', 'https://indeed.com/job3'],
        'snippet': ['<p>Great <strong>CDL</strong> opportunity!</p>', 'Own truck required', 'Home daily driving']
    }
    
    # Create test CSV
    test_df = pd.DataFrame(sample_data)
    test_file = 'test_jobs.csv'
    test_df.to_csv(test_file, index=False)
    
    # Process the test file
    print("Testing CSV processing:")
    result_df = processor.process_outscraper_csv(test_file)
    print(f"Processed {len(result_df)} test jobs")
    print(f"Columns: {list(result_df.columns)}")
    
    # Clean up test file
    import os
    os.remove(test_file)