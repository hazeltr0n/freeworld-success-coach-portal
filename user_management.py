"""
FreeWorld Job Scraper - Internal Success Coach Management
Simple user system for internal FreeWorld Success Coaches with personalized PDFs
"""

import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Optional
import json
import os
try:
    from supabase_utils import load_coaches_json, upsert_coaches_json, delete_coach_row
except Exception:
    load_coaches_json = None
    upsert_coaches_json = None
    delete_coach_row = None

@dataclass
class SuccessCoach:
    username: str
    full_name: str  # For PDF personalization "Prepared by Sarah Johnson, Success Coach"
    email: str
    password_hash: str
    role: str  # "admin" or "coach"
    
    # Feature permissions (admin can toggle these for each coach)
    can_generate_pdf: bool
    can_generate_csv: bool
    can_sync_airtable: bool
    can_sync_supabase: bool
    can_use_custom_locations: bool
    can_access_full_mode: bool  # 1000 jobs vs limited to 250
    can_access_google_jobs: bool  # Google Jobs API access (99% cost savings)
    can_access_batches: bool  # Access to Batches & Scheduling page
    
    # Advanced admin features
    can_edit_ai_prompt: bool  # Modify AI system prompt
    can_edit_filters: bool    # Modify business rules and filters
    can_manage_users: bool    # Add/remove/edit other coaches
    
    # API usage limitations
    can_pull_fresh_jobs: bool  # Can use outscraper/openai for fresh job pulls
    can_force_fresh_classification: bool  # Can bypass AI classification cache
    
    # Usage tracking
    total_searches: int
    total_jobs_processed: int
    created_date: str
    last_login: str
    
    # Monthly budget tracking
    monthly_budget: float  # Admin-set budget limit
    current_month_spending: float
    spending_alerts: bool  # Email alerts when approaching budget

class CoachManager:
    def __init__(self):
        self.coaches_file = "success_coaches.json"
        self.load_coaches()
        # Prefer Supabase persistence if available
        self.use_supabase = bool(load_coaches_json and upsert_coaches_json)
    
    def load_coaches(self):
        """Load Success Coaches from JSON file"""
        # Try Supabase first
        if load_coaches_json:
            try:
                data = load_coaches_json() or {}
                if data:  # Only process if we actually have coach data
                    # Fill missing fields default and remove deprecated fields
                    for username, coach_data in data.items():
                        if 'can_pull_fresh_jobs' not in coach_data:
                            coach_data['can_pull_fresh_jobs'] = True
                        if 'can_force_fresh_classification' not in coach_data:
                            coach_data['can_force_fresh_classification'] = coach_data.get('role') == 'admin'
                        # Add new Google Jobs field for existing coaches
                        if 'can_access_google_jobs' not in coach_data:
                            coach_data['can_access_google_jobs'] = True  # Enable by default for cost savings
                        # Add new Batches access field for existing coaches
                        if 'can_access_batches' not in coach_data:
                            coach_data['can_access_batches'] = True  # Enable by default
                        # Remove deprecated fields that are no longer in the dataclass
                        if 'can_use_multi_search' in coach_data:
                            del coach_data['can_use_multi_search']
                    self.coaches = {k: SuccessCoach(**v) for k, v in data.items()}
                    return
                # If Supabase returned empty data, fall through to local fallback
            except Exception as e:
                import streamlit as st
                st.error(f"🔍 Debug - Supabase coach loading failed: {e}")
                pass
        # Fallback: local JSON file
        if os.path.exists(self.coaches_file):
            try:
                with open(self.coaches_file, 'r') as f:
                    data = json.load(f)
                    for username, coach_data in data.items():
                        if 'can_pull_fresh_jobs' not in coach_data:
                            coach_data['can_pull_fresh_jobs'] = True
                        if 'can_force_fresh_classification' not in coach_data:
                            coach_data['can_force_fresh_classification'] = coach_data.get('role') == 'admin'
                        # Add new Google Jobs field for existing coaches
                        if 'can_access_google_jobs' not in coach_data:
                            coach_data['can_access_google_jobs'] = True  # Enable by default for cost savings
                        # Add new Batches access field for existing coaches
                        if 'can_access_batches' not in coach_data:
                            coach_data['can_access_batches'] = True  # Enable by default
                        # Remove deprecated fields that are no longer in the dataclass
                        if 'can_use_multi_search' in coach_data:
                            del coach_data['can_use_multi_search']
                    self.coaches = {k: SuccessCoach(**v) for k, v in data.items()}
            except Exception as e:
                st.error(f"Error loading coaches: {e}")
                self.coaches = {}
        else:
            self.coaches = {}
            self.create_default_coaches()
    
    def save_coaches(self):
        """Save coaches to JSON file"""
        data = {k: asdict(v) for k, v in self.coaches.items()}
        # Try Supabase first
        if upsert_coaches_json:
            count, err = upsert_coaches_json(data)
            if err:
                st.warning(f"Supabase coach save error: {err}")
            if count:
                return
        # Fallback to local JSON
        try:
            with open(self.coaches_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            st.error(f"Error saving coaches: {e}")
    
    def delete_coach(self, username: str) -> bool:
        """Delete a coach by username. Protect admin and non-existent users."""
        if username not in self.coaches:
            return False
        if username == 'admin' or self.coaches[username].role == 'admin':
            return False
        try:
            del self.coaches[username]
            # Try Supabase delete first
            if delete_coach_row:
                ok, err = delete_coach_row(username)
                if not ok and err:
                    st.warning(f"Supabase delete warning: {err}")
            self.save_coaches()
            return True
        except Exception as e:
            st.error(f"Error deleting coach: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        return hashlib.sha256(f"{password}_freeworld_success_salt".encode()).hexdigest()
    
    def create_default_coaches(self):
        """Create default admin and sample coaches"""
        # Admin account
        admin = SuccessCoach(
            username="admin",
            full_name="FreeWorld Administrator",
            email="admin@freeworld.com",
            password_hash=self.hash_password("admin123"),
            role="admin",
            can_generate_pdf=True,
            can_generate_csv=True,
            can_sync_airtable=True,
            can_sync_supabase=True,
            can_use_custom_locations=True,
            can_access_full_mode=True,
            can_access_google_jobs=True,
            can_edit_ai_prompt=True,
            can_edit_filters=True,
            can_manage_users=True,
            can_pull_fresh_jobs=True,
            can_force_fresh_classification=True,
            can_access_batches=True,
            total_searches=0,
            total_jobs_processed=0,
            created_date=datetime.now().isoformat(),
            last_login=datetime.now().isoformat(),
            monthly_budget=1000.00,
            current_month_spending=0.00,
            spending_alerts=True
        )
        
        # Sample Success Coach
        coach = SuccessCoach(
            username="sarah.johnson",
            full_name="Sarah Johnson",
            email="sarah@freeworld.com",
            password_hash=self.hash_password("coach123"),
            role="coach",
            can_generate_pdf=True,
            can_generate_csv=True,
            can_sync_airtable=False,
            can_sync_supabase=False,
            can_use_custom_locations=True,
            can_access_full_mode=False,
            can_access_google_jobs=True,  # Enable Google Jobs for cost savings
            can_edit_ai_prompt=False,
            can_edit_filters=False,
            can_manage_users=False,
            can_pull_fresh_jobs=True,
            can_force_fresh_classification=True,
            can_access_batches=True,
            total_searches=0,
            total_jobs_processed=0,
            created_date=datetime.now().isoformat(),
            last_login=datetime.now().isoformat(),
            monthly_budget=200.00,
            current_month_spending=0.00,
            spending_alerts=True
        )
        
        self.coaches["admin"] = admin
        self.coaches["sarah.johnson"] = coach
        self.save_coaches()
    
    def create_coach(self, username: str, full_name: str, email: str, password: str, role: str = 'coach', can_pull_fresh_jobs: bool = True) -> bool:
        """Create new Success Coach"""
        if username in self.coaches:
            return False
        
        # Set permissions based on role
        if role == "admin":
            coach = SuccessCoach(
                username=username,
                full_name=full_name,
                email=email,
                password_hash=self.hash_password(password),
                role=role,
                can_generate_pdf=True,
                can_generate_csv=True,
                can_sync_airtable=True,
                can_sync_supabase=True,
                can_use_custom_locations=True,
                can_access_full_mode=True,
                can_access_google_jobs=True,
                can_edit_ai_prompt=True,
                can_edit_filters=True,
                can_manage_users=True,
                can_pull_fresh_jobs=can_pull_fresh_jobs,
                can_force_fresh_classification=True,  # Admins get force classification by default
                can_access_batches=True,  # Admins get batches access by default
                total_searches=0,
                total_jobs_processed=0,
                created_date=datetime.now().isoformat(),
                last_login=datetime.now().isoformat(),
                monthly_budget=1000.00,  # Higher budget for admins
                current_month_spending=0.00,
                spending_alerts=True
            )
        else:
            coach = SuccessCoach(
                username=username,
                full_name=full_name,
                email=email,
                password_hash=self.hash_password(password),
                role=role,
                can_generate_pdf=True,
                can_generate_csv=True,
                can_sync_airtable=False,
                can_sync_supabase=False,
                can_use_custom_locations=False,
                can_access_full_mode=False,
                can_access_google_jobs=False,  # Disabled by default for test coaches
                can_edit_ai_prompt=False,
                can_edit_filters=False,
                can_manage_users=False,
                can_pull_fresh_jobs=can_pull_fresh_jobs,
                can_force_fresh_classification=False,  # Regular coaches need explicit permission
                can_access_batches=True,  # Enable batches access by default for regular coaches
                total_searches=0,
                total_jobs_processed=0,
                created_date=datetime.now().isoformat(),
                last_login=datetime.now().isoformat(),
                monthly_budget=100.00,
                current_month_spending=0.00,
                spending_alerts=True
            )
        
        self.coaches[username] = coach
        self.save_coaches()
        return True
    
    def authenticate(self, username: str, password: str) -> Optional[SuccessCoach]:
        """Authenticate Success Coach"""
        if username not in self.coaches:
            return None
        
        coach = self.coaches[username]
        if coach.password_hash == self.hash_password(password):
            # Update last login
            coach.last_login = datetime.now().isoformat()
            self.save_coaches()
            return coach
        return None
    
    def change_password(self, username: str, current_password: str, new_password: str) -> tuple[bool, str]:
        """Change coach password"""
        if username not in self.coaches:
            return False, "Coach not found"
        
        coach = self.coaches[username]
        
        # Verify current password
        if coach.password_hash != self.hash_password(current_password):
            return False, "Current password is incorrect"
        
        # Validate new password
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters"
        
        # Update password
        coach.password_hash = self.hash_password(new_password)
        self.save_coaches()
        
        return True, "Password changed successfully"
    
    def admin_reset_password(self, admin_username: str, target_username: str, new_password: str) -> tuple[bool, str]:
        """Admin-only function to reset any coach's password without requiring current password"""
        # Verify admin permissions - added for Streamlit Cloud refresh
        if admin_username not in self.coaches:
            return False, "Admin user not found"
        
        admin_coach = self.coaches[admin_username]
        if admin_coach.role != 'admin' or not admin_coach.can_manage_users:
            return False, "Insufficient permissions. Only admins with user management rights can reset passwords."
        
        # Check if target coach exists
        if target_username not in self.coaches:
            return False, f"Coach '{target_username}' not found"
        
        # Validate new password
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters"
        
        # Reset password
        target_coach = self.coaches[target_username]
        target_coach.password_hash = self.hash_password(new_password)
        self.save_coaches()
        
        # Log the password reset
        print(f"🔧 Admin {admin_username} reset password for coach {target_username}")
        
        return True, f"Password reset successfully for coach '{target_username}'"
    
    def can_coach_search(self, username: str, estimated_cost: float) -> tuple[bool, str]:
        """Check if coach can perform search"""
        if username not in self.coaches:
            return False, "Coach not found"
        
        coach = self.coaches[username]
        
        # Check spending limit
        if coach.current_month_spending + estimated_cost > coach.monthly_budget:
            return False, f"Monthly budget would be exceeded. Current: ${coach.current_month_spending:.2f}, Budget: ${coach.monthly_budget:.2f}"
        
        return True, "OK"
    
    def record_search(self, username: str, job_count: int, cost: float):
        """Record a completed search"""
        if username in self.coaches:
            coach = self.coaches[username]
            coach.total_searches += 1
            coach.total_jobs_processed += job_count
            coach.current_month_spending += cost
            self.save_coaches()
    
    def get_coach_stats(self, username: str) -> Dict:
        """Get Success Coach statistics"""
        if username not in self.coaches:
            return {}
        
        coach = self.coaches[username]
        
        return {
            'full_name': coach.full_name,
            'role': coach.role,
            'total_searches': coach.total_searches,
            'total_jobs_processed': coach.total_jobs_processed,
            'current_spending': coach.current_month_spending,
            'monthly_budget': coach.monthly_budget,
            'budget_remaining': coach.monthly_budget - coach.current_month_spending,
            'created_date': coach.created_date,
            'permissions': {
                'PDF Generation': coach.can_generate_pdf,
                'CSV Export': coach.can_generate_csv,
                'Airtable Sync': coach.can_sync_airtable,
                'Supabase Sync': coach.can_sync_supabase,
                'Custom Locations': coach.can_use_custom_locations,
                'Full Mode (1000 jobs)': coach.can_access_full_mode,
                'Edit AI Prompt': coach.can_edit_ai_prompt,
                'Edit Filters': coach.can_edit_filters,
                'Manage Users': coach.can_manage_users,
                'Force Fresh Classification': coach.can_force_fresh_classification
            }
        }
    
    def update_coach_permissions(self, username: str, permissions: Dict[str, any]):
        """Update coach permissions (admin only)"""
        if username in self.coaches:
            coach = self.coaches[username]
            
            # Update all permissions that might be provided
            coach.can_generate_pdf = permissions.get('can_generate_pdf', coach.can_generate_pdf)
            coach.can_generate_csv = permissions.get('can_generate_csv', coach.can_generate_csv)
            coach.can_sync_airtable = permissions.get('can_sync_airtable', coach.can_sync_airtable)
            coach.can_sync_supabase = permissions.get('can_sync_supabase', coach.can_sync_supabase)
            coach.can_use_custom_locations = permissions.get('can_use_custom_locations', coach.can_use_custom_locations)
            coach.can_access_full_mode = permissions.get('can_access_full_mode', coach.can_access_full_mode)
            coach.can_edit_filters = permissions.get('can_edit_filters', coach.can_edit_filters)
            coach.can_pull_fresh_jobs = permissions.get('can_pull_fresh_jobs', getattr(coach, 'can_pull_fresh_jobs', True))
            coach.can_force_fresh_classification = permissions.get('can_force_fresh_classification', getattr(coach, 'can_force_fresh_classification', coach.role == 'admin'))
            coach.can_access_batches = permissions.get('can_access_batches', getattr(coach, 'can_access_batches', True))
            
            # Handle budget (numeric value, not boolean)
            if 'monthly_budget' in permissions:
                coach.monthly_budget = float(permissions['monthly_budget'])
            
            self.save_coaches()
            return True
        return False

def get_coach_manager():
    """Get or create coach manager singleton"""
    if 'coach_manager' not in st.session_state:
        st.session_state.coach_manager = CoachManager()
    return st.session_state.coach_manager

def check_coach_permission(permission: str) -> bool:
    """Check if current coach has a specific permission"""
    if 'current_coach' not in st.session_state:
        return False
    
    coach = st.session_state.current_coach
    return getattr(coach, permission, False)

def require_permission(permission: str, feature_name: str = None):
    """Check permission and show error if not allowed"""
    if not check_coach_permission(permission):
        feature_name = feature_name or permission.replace('can_', '').replace('_', ' ').title()
        st.error(f"❌ {feature_name} is not enabled for your account")
        st.info("💡 Contact your administrator to enable this feature")
        return False
    return True

def get_current_coach_name() -> str:
    """Get current coach's full name for PDF personalization"""
    if 'current_coach' not in st.session_state:
        return "FreeWorld Success Coach"
    return st.session_state.current_coach.full_name
