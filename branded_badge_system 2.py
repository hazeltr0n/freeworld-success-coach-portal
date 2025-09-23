"""
FreeWorld Branded Badge System for PDF Generation
Creates professional branded badges instead of emoji-based ones
"""

from reportlab.lib.colors import Color
from reportlab.platypus import Flowable
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

# FreeWorld Official Brand Colors
FW_ROOTS = Color(0.0, 71/255, 81/255)  # #004751 - Primary teal
FW_FREEDOM_GREEN = Color(205/255, 249/255, 92/255)  # #CDF95C - Bright green
FW_VISIONARY_VIOLET = Color(197/255, 199/255, 228/255)  # #C5C7E4 - Light purple
FW_MIDNIGHT = Color(25/255, 25/255, 49/255)  # #191931 - Dark navy
FW_HORIZON_GREY = Color(244/255, 244/255, 244/255)  # #F4F4F4 - Light grey
FW_WHITE = Color(1, 1, 1)  # White for text

class FreeWorldBadge(Flowable):
    """Custom badge component with FreeWorld branding"""
    
    def __init__(self, text, badge_type="default", width=None, height=None):
        Flowable.__init__(self)
        self.text = text
        self.badge_type = badge_type
        self.width = width or self._get_default_width()
        self.height = height or 0.5 * inch
        
    def _get_default_width(self):
        """Calculate width based on text length"""
        base_width = len(self.text) * 0.08 * inch
        return max(base_width, 1.6 * inch)  # Minimum width
        
    def _get_badge_colors(self):
        """Get colors based on badge type"""
        color_map = {
            "excellent": (FW_FREEDOM_GREEN, FW_MIDNIGHT),  # Green bg, dark text
            "good": (FW_FREEDOM_GREEN, FW_MIDNIGHT),
            "possible": (FW_VISIONARY_VIOLET, FW_MIDNIGHT),  # Purple bg, dark text
            "so-so": (FW_VISIONARY_VIOLET, FW_MIDNIGHT),
            "warning": (Color(1, 0.8, 0), FW_MIDNIGHT),  # Yellow bg, dark text
            "danger": (Color(0.9, 0.3, 0.3), FW_WHITE),  # Red bg, white text
            "local": (FW_ROOTS, FW_WHITE),  # Teal bg, white text
            "regional": (FW_VISIONARY_VIOLET, FW_MIDNIGHT),  # Purple bg, dark text
            "otr": (Color(1, 0.5, 0), FW_WHITE),  # Orange bg, white text
            "fair_chance": (FW_FREEDOM_GREEN, FW_MIDNIGHT),  # Green bg, dark text
            "conditional": (Color(1, 0.8, 0), FW_MIDNIGHT),  # Yellow bg, dark text
            "salary": (FW_ROOTS, FW_WHITE),  # Teal bg, white text
            "default": (FW_HORIZON_GREY, FW_MIDNIGHT),  # Gray bg, dark text
        }
        return color_map.get(self.badge_type, color_map["default"])
    
    def draw(self):
        """Draw the badge"""
        bg_color, text_color = self._get_badge_colors()
        
        # Draw rounded rectangle background
        self.canv.setFillColor(bg_color)
        self.canv.setStrokeColor(bg_color)
        self.canv.roundRect(0, 0, self.width, self.height, 0.05 * inch, fill=1)
        
        # Add text
        self.canv.setFillColor(text_color)
        font_name = "Outfit-Bold"
        try:
            self.canv.setFont("Outfit-Bold", 12)  # Try FreeWorld font
        except:
            font_name = "Helvetica-Bold"
            self.canv.setFont("Helvetica-Bold", 12)  # Fallback to standard font
        text_width = self.canv.stringWidth(self.text, font_name, 12)
        x_center = (self.width - text_width) / 2
        y_center = (self.height - 12) / 2
        self.canv.drawString(x_center, y_center, self.text)

class BadgeFactory:
    """Factory for creating different types of FreeWorld badges"""
    
    @staticmethod
    def create_match_badge(match_value):
        """Create match quality badge"""
        badge_map = {
            "good": FreeWorldBadge("EXCELLENT MATCH", "excellent"),
            "so-so": FreeWorldBadge("POSSIBLE FIT", "possible"),
            "bad": FreeWorldBadge("NOT RECOMMENDED", "danger")
        }
        return badge_map.get(match_value, FreeWorldBadge("UNKNOWN", "default"))
    
    @staticmethod
    def create_route_badge(route_type):
        """Create route type badge"""
        badge_map = {
            "Local": FreeWorldBadge("LOCAL ROUTES", "local"),
            "Regional": FreeWorldBadge("REGIONAL", "regional"),
            "OTR": FreeWorldBadge("LONG-HAUL", "otr"),
            "Unknown": FreeWorldBadge("ROUTE TBD", "default")
        }
        return badge_map.get(route_type, FreeWorldBadge("UNKNOWN ROUTE", "default"))
    
    @staticmethod
    def create_fair_chance_badge(fair_chance_value):
        """Create fair chance badge"""
        if not fair_chance_value or fair_chance_value in ['unknown', 'no_requirements_mentioned']:
            return FreeWorldBadge("POLICY UNKNOWN", "default")
        elif fair_chance_value == 'excludes_all_records':
            return FreeWorldBadge("CLEAN RECORD REQUIRED", "danger")
        elif fair_chance_value == 'excludes_felonies_only':
            return FreeWorldBadge("NO FELONIES", "warning")
        elif fair_chance_value.startswith('time_limited_'):
            years = fair_chance_value.replace('time_limited_', '').replace('_years', '')
            return FreeWorldBadge(f"NO FELONIES - {years} YEARS", "warning")
        elif fair_chance_value == 'fair_chance_employer':
            return FreeWorldBadge("FAIR CHANCE FRIENDLY", "fair_chance")
        elif fair_chance_value == 'case_by_case':
            return FreeWorldBadge("CASE-BY-CASE", "conditional")
        elif fair_chance_value == 'dot_regulated_only':
            return FreeWorldBadge("DOT REGULATED ONLY", "warning")
        else:
            return FreeWorldBadge(fair_chance_value.replace('_', ' ').upper(), "warning")
    
    @staticmethod
    def create_endorsement_badge(endorsement_value):
        """Create CDL endorsement badge"""
        if not endorsement_value or endorsement_value in ['none required', 'unknown']:
            return FreeWorldBadge("CLASS A CDL ONLY", "excellent")
        elif 'hazmat' in endorsement_value.lower():
            if 'preferred' in endorsement_value.lower():
                return FreeWorldBadge("HAZMAT PREFERRED", "conditional")
            else:
                return FreeWorldBadge("HAZMAT REQUIRED", "warning")
        elif 'passenger' in endorsement_value.lower():
            return FreeWorldBadge("PASSENGER ENDORSEMENT", "warning")
        elif 'school' in endorsement_value.lower():
            return FreeWorldBadge("SCHOOL BUS", "warning")
        elif 'tanker' in endorsement_value.lower():
            return FreeWorldBadge("TANKER", "warning")
        else:
            return FreeWorldBadge("ENDORSEMENTS REQUIRED", "warning")
    
    @staticmethod
    def create_salary_badge(salary_text):
        """Create salary display badge"""
        if not salary_text:
            return FreeWorldBadge("SALARY TBD", "default")
        elif 'hour' in salary_text.lower():
            return FreeWorldBadge("HOURLY PAY", "salary")
        elif 'week' in salary_text.lower():
            return FreeWorldBadge("WEEKLY PAY", "salary")
        elif 'year' in salary_text.lower() or 'annual' in salary_text.lower():
            return FreeWorldBadge("ANNUAL SALARY", "salary")
        else:
            return FreeWorldBadge("PERFORMANCE PAY", "salary")
    
    @staticmethod
    def create_context_badges(reason, summary=""):
        """Create context badges based on job reason/summary"""
        badges = []
        
        # Handle NaN values
        reason = str(reason) if reason is not None and str(reason) != 'nan' else ""
        summary = str(summary) if summary is not None and str(summary) != 'nan' else ""
        
        reason_lower = reason.lower() if reason else ""
        summary_lower = summary.lower() if summary else ""
        full_text = f"{reason_lower} {summary_lower}"
        
        # Entry level friendly
        if any(phrase in full_text for phrase in ['no experience', 'entry level', 'will train']):
            badges.append(FreeWorldBadge("ENTRY-LEVEL FRIENDLY", "excellent"))
        elif any(phrase in full_text for phrase in ['1 year', 'experience required', 'minimum experience']):
            badges.append(FreeWorldBadge("EXPERIENCE PREFERRED", "conditional"))
        
        # Benefits
        if any(phrase in full_text for phrase in ['benefits', 'health', 'insurance', 'dental']):
            badges.append(FreeWorldBadge("BENEFITS INCLUDED", "excellent"))
        
        # Immediate hiring
        if any(phrase in full_text for phrase in ['immediate', 'urgent', 'hiring now', 'asap']):
            badges.append(FreeWorldBadge("IMMEDIATE START", "warning"))
        
        # Home time
        if any(phrase in full_text for phrase in ['home daily', 'home every', 'local']):
            badges.append(FreeWorldBadge("HOME DAILY", "excellent"))
        elif any(phrase in full_text for phrase in ['weekends home', 'home weekends']):
            badges.append(FreeWorldBadge("HOME WEEKENDS", "possible"))
        
        return badges[:3]  # Limit to 3 context badges max