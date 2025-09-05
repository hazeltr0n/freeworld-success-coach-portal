import pandas as pd
import re

class JobFilters:
    def __init__(self):
        # Spam companies to filter out
        self.spam_companies = ['class a drivers', 'live trucking']
        
        # Spam domains to filter out
        self.spam_domains = ['cdllife.com', 'truckwayjobs.com', 'giggridz.com']
        
        # Owner-operator keywords to filter out
        self.owner_op_keywords = [
            'owner operator', 'lease purchase', 'dispatch service', 
            '1099 driver', 'hotshot', 'power only'
        ]
        
        # School bus keywords to filter out
        self.school_bus_keywords = [
            'school bus', 'isd', 'school district', 'student transport', 'pupil transport'
        ]
    
    def apply_all_filters(self, df):
        """Apply all filtering layers in sequence"""
        
        
        # Ensure job_id column exists
        if 'job_id' not in df.columns:
            print("❌ ERROR: job_id column missing!")
            return df  # Return immediately instead of trying to fix
        
        # Keep track of final status for all jobs
        df['final_status'] = 'included'  # Default: job passes all filters
        df['filtered'] = False
        
        # Apply filters in order
        df = self._md5_dedupe(df)
        df = self._r1_collapse(df) 
        df = self._r2_collapse(df)
        df = self._spam_filter(df)
        df = self._owner_op_filter(df)
        df = self._school_bus_filter(df)
        
        # Show final stats
        remaining = len(df[df['filtered'] == False])
        removed = len(df[df['filtered'] == True])
        
        
        # Return only unfiltered jobs
        return df[df['filtered'] == False].copy()
    
    def _md5_dedupe(self, df):
        """Remove exact MD5 duplicates"""
        active_mask = df['filtered'] == False
        active_df = df[active_mask]
        
        # Find duplicates by job_id (which is MD5 hash)
        duplicate_mask = active_df.duplicated(subset='job_id', keep='first')
        duplicate_indices = active_df[duplicate_mask].index
        
        # Mark duplicates as filtered
        df.loc[duplicate_indices, 'filtered'] = True
        df.loc[duplicate_indices, 'final_status'] = 'filtered: MD5 duplicate'
        
        return df
    
    def _r1_collapse(self, df):
        """Remove duplicates by company + job title + market"""
        # First, we need to add market mapping - simplified version
        df['market'] = df['location'].apply(self._simple_market_mapping)
        
        active_mask = df['filtered'] == False
        active_df = df[active_mask]
        
        # Create R1 key: company + job_title + market (normalized)
        active_df = active_df.copy()
        active_df['r1_key'] = (
            active_df['company'].str.lower().str.strip() + "|" +
            active_df['job_title'].str.lower().str.strip() + "|" +
            active_df['market'].str.lower().str.strip()
        )
        
        # Find duplicates (keep first occurrence)
        has_market_mask = active_df['market'].str.strip() != ""
        r1_candidates = active_df[has_market_mask]
        duplicate_mask = r1_candidates.duplicated(subset='r1_key', keep='first')
        duplicate_indices = r1_candidates[duplicate_mask].index
        
        # Mark duplicates as filtered
        df.loc[duplicate_indices, 'filtered'] = True
        df.loc[duplicate_indices, 'final_status'] = 'filtered: R1 collapse (company+title+market)'
        
        return df
    
    def _r2_collapse(self, df):
        """Remove duplicates by company + market, and similar titles within same market.

        Notes:
        - No fallback to derive markets; if `market` missing, this step is skipped.
        - Safety guard ensures this step never eliminates all jobs for any company.
        """
        active_mask = df['filtered'] == False
        active_df = df[active_mask]
        
        if active_df.empty:
            return df
        
        # Strict requirement: market must already exist (set by upstream logic)
        if 'market' not in df.columns:
            return df

        active_df = active_df.copy()

        # Step 1: R2 collapse by company + market (only when market is mapped)
        active_df['r2_key'] = (
            active_df['company'].fillna('').str.lower().str.strip() + "|" +
            active_df['market'].fillna('').str.lower().str.strip()
        )

        has_market_mask = active_df['market'].fillna('').str.strip() != ""
        r2_candidates = active_df[has_market_mask]
        duplicate_mask = r2_candidates.duplicated(subset='r2_key', keep='first')
        duplicate_indices = r2_candidates[duplicate_mask].index

        df.loc[duplicate_indices, 'filtered'] = True
        df.loc[duplicate_indices, 'final_status'] = 'filtered: R2 collapse (company+market)'
        
        # Step 2: Enhanced R2 collapse for similar titles from same company
        remaining_mask = df['filtered'] == False
        remaining_df = df[remaining_mask].copy()
        
        # Track indices filtered by this method for safety restore if needed
        filtered_by_r2 = set(duplicate_indices.tolist())

        if not remaining_df.empty:
            # Create similarity key: company + simplified job title
            remaining_df['title_simplified'] = (
                remaining_df['job_title'].str.lower()
                .str.replace(r'\s+', ' ', regex=True)  # normalize whitespace
                .str.replace(r'[^\w\s]', '', regex=True)  # remove punctuation
                .str.replace(r'\b(no\s+exp|no\s+experience|entry\s+level|recent\s+grad)\b', 'noexp', regex=True)
                .str.replace(r'\b(class\s+a|cdl\s+a|cdl-a)\b', 'cdla', regex=True)
                .str.replace(r'\b(truck\s+driver|driver)\b', 'driver', regex=True)
                .str.replace(r'\b(dry\s+van|van)\b', 'dryvan', regex=True)
                .str.strip()
            )
            # Similar title collapse scoped within company + market
            remaining_df['similarity_key'] = (
                remaining_df['company'].fillna('').str.lower().str.strip() + "|" +
                remaining_df['market'].fillna('').str.lower().str.strip() + "|" +
                remaining_df['title_simplified']
            )

            has_market_mask = remaining_df['market'].fillna('').str.strip() != ""
            similar_candidates = remaining_df[has_market_mask]
            # Find similar title duplicates from same company within the same market
            similar_duplicate_mask = similar_candidates.duplicated(subset='similarity_key', keep='first')
            similar_duplicate_indices = similar_candidates[similar_duplicate_mask].index

            if len(similar_duplicate_indices) > 0:
                df.loc[similar_duplicate_indices, 'filtered'] = True
                df.loc[similar_duplicate_indices, 'final_status'] = 'filtered: R2 collapse (company+market+similar title)'
                filtered_by_r2.update(similar_duplicate_indices.tolist())

        # Safety: ensure at least one job remains for each company present at entry
        companies_before = active_df['company'].fillna('').str.lower().str.strip()
        companies_before_unique = companies_before.unique().tolist()
        remaining_after = df[df['filtered'] == False]
        remaining_companies = set(remaining_after['company'].fillna('').str.lower().str.strip().unique().tolist())

        # For any company that lost all entries due to this step, restore one earliest from the ones we just filtered
        for comp in companies_before_unique:
            if comp == '':
                continue
            if comp not in remaining_companies:
                # candidate indices filtered by this method for this company
                comp_indices = [idx for idx in filtered_by_r2
                                if isinstance(df.loc[idx, 'company'], str)
                                and df.loc[idx, 'company'].lower().strip() == comp]
                if comp_indices:
                    idx_to_restore = sorted(comp_indices)[0]
                    df.loc[idx_to_restore, 'filtered'] = False
                    df.loc[idx_to_restore, 'final_status'] = 'included'
        
        return df
    
    def _spam_filter(self, df):
        """Remove spam companies and domains"""
        active_mask = df['filtered'] == False
        active_df = df[active_mask]
        
        # Check for spam companies
        spam_company_mask = active_df['company'].str.lower().isin(self.spam_companies)
        
        # Check for spam domains in apply_url
        spam_link_pattern = '|'.join(self.spam_domains)
        spam_link_mask = active_df['apply_url'].str.lower().str.contains(spam_link_pattern, na=False)
        
        # Combine spam filters
        spam_mask = spam_company_mask | spam_link_mask
        spam_indices = active_df[spam_mask].index
        
        # Mark spam as filtered
        df.loc[spam_indices, 'filtered'] = True
        df.loc[spam_indices, 'final_status'] = 'filtered: Spam source'
        
        return df
    
    def _owner_op_filter(self, df):
        """Remove owner-operator jobs"""
        active_mask = df['filtered'] == False
        active_df = df[active_mask]
        
        # Check job titles for owner-op keywords
        owner_op_pattern = '|'.join(self.owner_op_keywords)
        owner_op_mask = active_df['job_title'].str.lower().str.contains(owner_op_pattern, na=False)
        owner_op_indices = active_df[owner_op_mask].index
        
        # Mark owner-op jobs as filtered
        df.loc[owner_op_indices, 'filtered'] = True
        df.loc[owner_op_indices, 'final_status'] = 'filtered: Owner-operator job'
        
        return df
    
    def _school_bus_filter(self, df):
        """Remove school bus driver jobs"""
        active_mask = df['filtered'] == False
        active_df = df[active_mask]
        
        # Check job title, company name, and job description for school bus terms
        school_bus_pattern = '|'.join(self.school_bus_keywords)
        
        school_title_mask = active_df['job_title'].str.lower().str.contains(school_bus_pattern, na=False)
        school_company_mask = active_df['company'].str.lower().str.contains(school_bus_pattern, na=False)
        school_desc_mask = active_df['job_description'].str.lower().str.contains(school_bus_pattern, na=False)
        
        # Combine all school bus indicators
        combined_school_mask = school_title_mask | school_company_mask | school_desc_mask
        school_indices = active_df[combined_school_mask].index
        
        # Mark school bus jobs as filtered
        df.loc[school_indices, 'filtered'] = True
        df.loc[school_indices, 'final_status'] = 'filtered: School bus driver job'
        
        return df
    
    def _simple_market_mapping(self, location):
        """Simplified market mapping - you can expand this later"""
        if not isinstance(location, str):
            return ""
        
        location = location.lower()
        
        # Simple Texas markets
        if 'dallas' in location or 'fort worth' in location or 'arlington' in location:
            return "Dallas"
        elif 'houston' in location or 'harris' in location:
            return "Houston"
        elif 'austin' in location:
            return "Austin"
        elif 'san antonio' in location:
            return "San Antonio"
        elif any(city in location for city in ['phoenix', 'scottsdale', 'mesa', 'tempe']):
            return "Phoenix"
        elif any(city in location for city in ['los angeles', 'long beach', 'pasadena']):
            return "Los Angeles"
        else:
            return ""  # No market mapping
    
    def show_filter_summary(self, original_df, filtered_df):
        """Show detailed filtering summary"""
        print(f"\n📊 Filtering Summary:")
        print(f"  Original jobs: {len(original_df)}")
        print(f"  Jobs remaining: {len(filtered_df)}")
        print(f"  Jobs filtered: {len(original_df) - len(filtered_df)}")
        print(f"  Retention rate: {len(filtered_df)/len(original_df)*100:.1f}%")

if __name__ == "__main__":
    # Test with sample data
    sample_data = [
        {'job_id': '1', 'job_title': 'CDL Driver', 'company': 'ABC Trucking', 'location': 'Dallas, TX', 'apply_url': 'indeed.com/job1'},
        {'job_id': '1', 'job_title': 'CDL Driver', 'company': 'ABC Trucking', 'location': 'Dallas, TX', 'apply_url': 'indeed.com/job1'},  # Duplicate
        {'job_id': '2', 'job_title': 'Owner Operator', 'company': 'XYZ Logistics', 'location': 'Houston, TX', 'apply_url': 'indeed.com/job2'},  # Owner-op
        {'job_id': '3', 'job_title': 'CDL Driver', 'company': 'Class A Drivers', 'location': 'Austin, TX', 'apply_url': 'indeed.com/job3'},  # Spam company
    ]
    
    df = pd.DataFrame(sample_data)
    filters = JobFilters()
    filtered_df = filters.apply_all_filters(df)
    print(f"\nFinal results: {len(filtered_df)} jobs")
