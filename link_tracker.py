import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class LinkTracker:
    """
    Short.io integration for creating trackable short links to measure engagement
    with job opportunities. Allows FreeWorld to track how many Free Agents
    click on job listings.
    """
    
    def __init__(self, domain: str = "freeworldjobs.short.gy"):
        """
        Initialize LinkTracker with Short.io API credentials
        
        Args:
            domain: Short.io domain to use for shortened links
        """
        self.api_key = os.getenv('SHORT_API_KEY', '') or os.getenv('SHORT_IO_API_KEY', '')
        self.base_url = "https://api.short.io"
        self.statistics_base_url = "https://statistics.short.io"
        self.domain = os.getenv('SHORT_DOMAIN', domain)
        self.domain_id = None  # Will be set during domain validation
        self.is_available = False  # Track if service is available
        self.use_supabase_edge_function = os.getenv('USE_SUPABASE_EDGE_FUNCTION', 'false').lower() == 'true'
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        if self.use_supabase_edge_function:
            self.logger.info("Using Supabase Edge Function for link tracking.")
            self.is_available = True
            # Still initialize session for hybrid mode (edge function + short.io)
            if self.api_key:
                self.session = requests.Session()
                self.session.headers.update({
                    'authorization': self.api_key,
                    'Content-Type': 'application/json',
                    'accept': '*/*'
                })
        elif not self.api_key:
            self.logger.warning("SHORT_API_KEY not found in environment variables - link shortening disabled")
            self.is_available = False
            return
        
        if not self.use_supabase_edge_function:
            self.session = requests.Session()
            self.session.headers.update({
                'authorization': self.api_key,  # lowercase as per docs
                'Content-Type': 'application/json',
                'accept': '*/*'  # as per docs
            })
            
            # Try to validate domain - if it fails, gracefully disable service
            try:
                self._validate_domain()
                if self.domain_id:
                    self.is_available = True
                    self.logger.info(f"LinkTracker initialized successfully with domain: {self.domain}")
                else:
                    self.is_available = False
                    self.logger.warning(f"LinkTracker domain validation failed - link shortening disabled")
            except Exception as e:
                self.is_available = False
                self.logger.warning(f"LinkTracker initialization failed: {e} - link shortening disabled")
        
        # Initialize analytics dashboard for logging (skip in web environments)
        self.analytics_dashboard = None
        
        # Skip analytics dashboard in web environments (no tkinter support)
        if ('STREAMLIT_SERVER_PORT' in os.environ or 
            'DYNO' in os.environ or 
            '/mount/src/' in os.getcwd()):
            self.logger.info("Web environment detected - skipping analytics dashboard")
            return
            
        try:
            # Try importing from same directory first
            try:
                from .analytics_dashboard import AnalyticsDashboard
            except ImportError:
                # Fallback to direct import
                from analytics_dashboard import AnalyticsDashboard
            
            self.analytics_dashboard = AnalyticsDashboard()
            self.logger.info("Analytics dashboard initialized successfully")
        except Exception as e:
            self.logger.warning(f"Could not initialize analytics dashboard: {e}")

        try:
            # Prefer top-level supabase_utils in this app
            from supabase_utils import get_client  # type: ignore
            self.supabase = get_client()
        except Exception:
            self.supabase = None

        # Optional Zapier webhook for link events
        self.zapier_webhook_url = os.getenv('ZAPIER_WEBHOOK_URL', '').strip()

    def _notify_zapier(self, event: str, payload: Dict[str, Any]) -> None:
        """Best-effort Zapier notification (non-blocking)."""
        try:
            if not getattr(self, 'zapier_webhook_url', ''):
                return
            body = {
                "event": event,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": payload,
            }
            # Fire-and-forget; ignore network errors
            try:
                requests.post(self.zapier_webhook_url, json=body, timeout=5)
            except Exception:
                pass
        except Exception:
            pass

    def _parse_tags_dict(self, tags: Optional[List[str]]) -> Dict[str, Any]:
        parsed: Dict[str, Any] = {}
        try:
            for t in (tags or []):
                if not t or ':' not in t:
                    continue
                key, val = t.split(':', 2)[0:2]
                key = (key or '').strip().lower()
                val = (val or '').strip()
                if not key or not val:
                    continue
                if key == 'coach':
                    parsed['coach'] = val
                elif key == 'candidate':
                    parsed['candidate_id'] = val
                elif key == 'agent':
                    # Convert dashed name back to human-readable
                    parsed['candidate_name'] = val.replace('-', ' ')
                elif key == 'market':
                    parsed['market'] = val
                elif key == 'route':
                    parsed['route'] = val
                elif key == 'match':
                    parsed['match'] = val
                elif key == 'fair':
                    parsed['fair'] = val
        except Exception:
            pass
        return parsed
    
    def create_short_link(self, original_url: str, title: Optional[str] = None, 
                         tags: Optional[list] = None, expires_hours: int = 0, 
                         candidate_id: Optional[str] = None) -> Optional[str]:
        """
        Create a tracked short link for a job URL with no expiration
        
        Args:
            original_url: The original job application URL
            title: Optional title for the link (job title)
            tags: Optional tags for categorization (e.g., ['job', 'cdl', 'dallas'])
            expires_hours: Hours until link expires (0 = no expiration)
            candidate_id: Optional candidate ID for Supabase edge function tracking
            
        Returns:
            Short URL string if successful, None if failed
        """
        # Check if service is available or if using Supabase edge function
        if not self.is_available and not self.use_supabase_edge_function:
            # Service is disabled and not using Supabase, return original URL
            return original_url
        
        if not original_url or not original_url.strip():
            self.logger.warning("Empty URL provided to create_short_link")
            return original_url
        
        # Validate URL format
        if not original_url.startswith(('http://', 'https://')):
            self.logger.warning(f"Invalid URL format: {original_url}")
            return original_url
        
        if self.use_supabase_edge_function:
            # Construct Supabase Edge Function URL correctly using the functions domain
            # SUPABASE_URL is usually like: https://<ref>.supabase.co[/rest/v1]
            import urllib.parse as _up
            import os  # Local import to avoid shadowing issues
            raw = os.getenv('SUPABASE_URL', 'https://project.supabase.co')
            try:
                pu = _up.urlparse(raw)
                host = pu.netloc or ''
                # Extract project ref from host (prefix before .supabase.*)
                ref = host.split('.')[0] if host else ''
                tld = '.'.join(host.split('.')[1:]) if host else 'supabase.co'
                # Build functions base (works for supabase.co and supabase.in)
                functions_host = f"{ref}.functions.{tld}" if ref else 'project.functions.supabase.co'
                functions_base = f"{pu.scheme or 'https'}://{functions_host}"
            except Exception:
                functions_base = 'https://project.functions.supabase.co'

            # Build query string safely (URL-encode target + attribution params)
            import urllib.parse as _up
            q: Dict[str, Any] = {"target": original_url}

            # Add candidate_id - edge function will lookup more data from agent_profiles
            parsed_tags = self._parse_tags_dict(tags)
            if candidate_id:
                q["candidate_id"] = candidate_id
            elif parsed_tags.get('candidate_id'):
                q["candidate_id"] = parsed_tags['candidate_id']

            # Pass through additional attribution fields if present
            # Support candidate_name pass-through under a stable key
            if parsed_tags.get('candidate_name'):
                q['candidate_name'] = parsed_tags['candidate_name']

            for key in ("coach", "market", "route", "match", "fair"):
                if parsed_tags.get(key) is not None and parsed_tags.get(key) != "":
                    q[key] = parsed_tags[key]

            supabase_url = f"{functions_base}/click-redirect-lite?{_up.urlencode(q)}"

            self.logger.info(f"Generated Supabase edge function URL: {supabase_url}")

            # Now shorten the edge function URL with Short.io for clean links
            if self.api_key:
                try:
                    # Use the existing Short.io logic but pass the edge function URL as the target
                    short_url = self._create_shortio_link_internal(supabase_url, title, tags, expires_hours)
                    # Notify Zapier about link creation
                    self._notify_zapier("link_created", {
                        "mode": "supabase+shortio",
                        "original_url": original_url,
                        "edge_url": supabase_url,
                        "short_url": short_url or supabase_url,
                        "title": title,
                        "tags": tags or [],
                        "candidate_id": candidate_id,
                    })
                    return short_url if short_url else supabase_url
                except Exception as e:
                    self.logger.warning(f"Failed to shorten edge function URL: {e}")
                    # Notify Zapier fallback
                    self._notify_zapier("link_created", {
                        "mode": "supabase-edge",
                        "original_url": original_url,
                        "edge_url": supabase_url,
                        "short_url": supabase_url,
                        "title": title,
                        "tags": tags or [],
                        "candidate_id": candidate_id,
                    })
                    return supabase_url

            # Edge-only path
            self._notify_zapier("link_created", {
                "mode": "supabase-edge",
                "original_url": original_url,
                "edge_url": supabase_url,
                "short_url": supabase_url,
                "title": title,
                "tags": tags or [],
                "candidate_id": candidate_id,
            })
            return supabase_url

        # Ensure a candidate tag is present so Short.io webhook can identify the agent
        if candidate_id:
            try:
                tag_str = f"candidate:{candidate_id}"
                if tags is None:
                    tags = [tag_str]
                elif not any(str(t).startswith('candidate:') for t in tags):
                    tags = [*tags, tag_str]
            except Exception:
                pass
        # Use internal method for Short.io logic
        short = self._create_shortio_link_internal(original_url, title, tags, expires_hours)
        self._notify_zapier("link_created", {
            "mode": "shortio",
            "original_url": original_url,
            "short_url": short or original_url,
            "title": title,
            "tags": tags or [],
        })
        return short or original_url

    def generate_edge_function_url(self, target_url: str, candidate_id: Optional[str] = None,
                                 tags: Optional[list] = None) -> str:
        """
        Generate edge function URL for click tracking (separate from Short.io link creation)
        Used for hyperlinking Short.io display text to actual tracking URLs

        Args:
            target_url: The URL to redirect to after tracking
            candidate_id: Agent UUID for tracking
            tags: Tags for context (coach, market, route, etc.)

        Returns:
            Edge function URL for click tracking
        """
        import urllib.parse as _up
        import os  # Local import to avoid shadowing issues
        raw = os.getenv('SUPABASE_URL', 'https://project.supabase.co')
        try:
            pu = _up.urlparse(raw)
            host = pu.netloc or ''
            # Extract project ref from host (prefix before .supabase.*)
            ref = host.split('.')[0] if host else ''
            tld = '.'.join(host.split('.')[1:]) if host else 'supabase.co'
            # Build functions base (works for supabase.co and supabase.in)
            functions_host = f"{ref}.functions.{tld}" if ref else 'project.functions.supabase.co'
            functions_base = f"{pu.scheme or 'https'}://{functions_host}"
        except Exception:
            functions_base = 'https://project.functions.supabase.co'

        # Build query string safely (URL-encode target + attribution params)
        q: Dict[str, Any] = {"target": target_url}

        # Add candidate_id - edge function will lookup more data from agent_profiles
        parsed_tags = self._parse_tags_dict(tags)
        if candidate_id:
            q["candidate_id"] = candidate_id
        elif parsed_tags.get('candidate_id'):
            q["candidate_id"] = parsed_tags['candidate_id']

        # Pass through additional attribution fields if present
        if parsed_tags.get('candidate_name'):
            q['candidate_name'] = parsed_tags['candidate_name']

        for key in ("coach", "market", "route", "match", "fair"):
            if parsed_tags.get(key) is not None and parsed_tags.get(key) != "":
                q[key] = parsed_tags[key]

        edge_function_url = f"{functions_base}/click-redirect-lite?{_up.urlencode(q)}"
        self.logger.info(f"Generated edge function URL for hyperlinking: {edge_function_url}")
        return edge_function_url

    def create_clickable_link(self, display_url: str, target_url: str, candidate_id: Optional[str] = None,
                            tags: Optional[list] = None, link_text: Optional[str] = None) -> str:
        """
        Create HTML link with Short.io display text but edge function href for tracking

        Args:
            display_url: Short.io URL to show as text (e.g., "https://freeworldjobs.short.gy/abc123")
            target_url: Actual URL to redirect to after tracking
            candidate_id: Agent UUID for tracking
            tags: Tags for context
            link_text: Optional custom text (defaults to display_url)

        Returns:
            HTML <a> tag with Short.io display text and edge function href
        """
        # Generate edge function URL for actual clicking
        edge_url = self.generate_edge_function_url(target_url, candidate_id, tags)

        # Use display_url as link text unless custom text provided
        text = link_text or display_url

        # Create HTML link
        html_link = f'<a href="{edge_url}" target="_blank">{text}</a>'

        self.logger.info(f"Created clickable link: display='{text}' href='{edge_url[:100]}...'")
        return html_link

    def _create_shortio_link_internal(self, original_url: str, title: Optional[str] = None, 
                                    tags: Optional[list] = None, expires_hours: int = 0) -> Optional[str]:
        """Internal method to create Short.io links"""
        payload = {
            "originalURL": original_url.strip(),
            "domain": self.domain,
            "allowDuplicates": False  # Reuse existing short links for same URL
        }
        
        # Add automatic expiration (Short.io Pro feature)
        if expires_hours and expires_hours > 0:
            expiration_time = datetime.now() + timedelta(hours=expires_hours)
            expires_at = int(expiration_time.timestamp() * 1000)  # Convert to milliseconds
            
            payload["expiresAt"] = expires_at
            payload["expiredURL"] = "https://freeworld.org/job-expired"  # Redirect after expiration
            
            self.logger.info(f"Link will expire in {expires_hours} hours: {expiration_time.isoformat()}")
        else:
            self.logger.info("Creating permanent link with no expiration")
        
        # Add optional metadata
        if title:
            payload["title"] = title[:100]  # Limit title length
        
        if tags:
            payload["tags"] = tags[:5]  # Limit number of tags
        
        try:
            response = self.session.post(f"{self.base_url}/links", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                short_url = data.get('shortURL')
                self.logger.info(f"Created short link: {original_url} -> {short_url}")
                
                # Extract domain ID if we don't have it yet
                if not self.domain_id and "DomainId" in data:
                    self.domain_id = data["DomainId"]
                    self.logger.info(f"Found domain ID: {self.domain_id}")
                
                # Log link creation for analytics
                if self.analytics_dashboard and short_url:
                    metadata = {
                        "title": title,
                        "tags": tags
                    }
                    self.analytics_dashboard.log_link_creation(original_url, short_url, metadata)
                
                # Also notify Zapier on creation
                self._notify_zapier("shortio_created", {
                    "short_url": short_url,
                    "original_url": original_url,
                    "title": title,
                    "tags": tags or [],
                })
                return short_url
            
            elif response.status_code == 409:
                # Link already exists, try to get existing short URL
                self.logger.info(f"Link already exists for: {original_url}")
                short_url = self._get_existing_link(original_url)
                return short_url
            
            else:
                self.logger.error(f"Failed to create short link: {response.status_code} - {response.text}")
                return original_url
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error creating short link: {e}")
            return original_url
        except Exception as e:
            self.logger.error(f"Unexpected error creating short link: {e}")
            return original_url
    
    def _get_existing_link(self, original_url: str) -> Optional[str]:
        """
        Attempt to retrieve an existing short link for the given URL
        
        Args:
            original_url: The original URL to search for
            
        Returns:
            Existing short URL if found, original URL otherwise
        """
        try:
            # Short.io doesn't have a direct "get by original URL" endpoint
            # so we'll just return the original URL for now
            # In production, you might want to maintain a local cache
            self.logger.info(f"Returning original URL for existing link: {original_url}")
            return original_url
        except Exception as e:
            self.logger.error(f"Error retrieving existing link: {e}")
            return original_url
    
    def get_link_analytics(self, short_url: str, period: str = "total") -> Optional[Dict[str, Any]]:
        """
        Retrieve click analytics for a short link
        
        Args:
            short_url: The short URL to get analytics for
            period: Time period ("total", "today", "yesterday", "week", "month", "last7", "last30")
            
        Returns:
            Dictionary with analytics data or None if failed
        """
        try:
            # Need to get the actual link ID, not just the path
            # First, get link info to find the proper link ID
            path = short_url.split('/')[-1]
            
            # Get link info to find the idString
            link_info_response = self.session.get(f"{self.base_url}/links/expand", params={"domain": self.domain, "path": path})
            if link_info_response.status_code != 200:
                self.logger.error(f"Could not get link info for analytics: {link_info_response.status_code}")
                return None
                
            link_info = link_info_response.json()
            link_id = link_info.get('idString')
            if not link_id:
                self.logger.error("Could not find link ID for analytics")
                return None
            
            # Use the correct statistics endpoint with proper parameters
            params = {
                "period": period,
                "tz": "UTC"
            }
            response = self.session.get(f"{self.statistics_base_url}/statistics/link/{link_id}", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get link analytics: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting link analytics: {e}")
            return None
    
    def get_domain_analytics(self, period: str = "total") -> Optional[Dict[str, Any]]:
        """
        Retrieve analytics for the entire domain
        
        Args:
            period: Time period ("total", "month", "week", "day")
            
        Returns:
            Dictionary with domain analytics data
        """
        try:
            # We need domain ID, not domain name - get it if we don't have it
            if not self.domain_id:
                # Create a temporary link to get domain ID
                temp_link = self.create_short_link("https://www.google.com", "temp")
                if not self.domain_id:
                    self.logger.error("Could not get domain ID")
                    return None
            
            params = {
                "period": period,
                "tz": "UTC"
            }
            # Use the correct statistics API endpoint with domain ID
            response = self.session.get(f"{self.statistics_base_url}/statistics/domain/{self.domain_id}", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get domain analytics: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting domain analytics: {e}")
            return None
    
    def get_all_links_analytics(self, limit: int = 100) -> Optional[Dict[str, Any]]:
        """
        Retrieve analytics for all links in the domain
        
        Args:
            limit: Maximum number of links to retrieve
            
        Returns:
            Dictionary with all links analytics data
        """
        if not self.domain_id:
            self.logger.error("Domain ID not available - cannot get links")
            return None
            
        try:
            params = {"limit": limit, "domainId": self.domain_id}
            response = self.session.get(f"{self.base_url}/links", params=params)
            
            if response.status_code == 200:
                links_data = response.json()
                analytics_summary = {
                    "total_links": len(links_data.get("links", [])),
                    "links": []
                }
                
                # Get basic info for each link (detailed analytics might be too slow)
                for link in links_data.get("links", [])[:limit]:
                    link_info = {
                        "id": link.get("idString"),
                        "original_url": link.get("originalURL"),
                        "short_url": f"https://{self.domain}/{link.get('idString', '')}",
                        "title": link.get("title", ""),
                        "tags": link.get("tags", []),
                        "created": link.get("createdAt"),
                        "clicks": link.get("totalClicks", 0)  # If available in basic response
                    }
                    analytics_summary["links"].append(link_info)
                
                return analytics_summary
            else:
                self.logger.error(f"Failed to get all links: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting all links analytics: {e}")
            return None
    
    def bulk_create_links(self, urls_with_metadata: list) -> Dict[str, str]:
        """
        Create multiple short links in bulk for efficiency
        
        Args:
            urls_with_metadata: List of dicts with 'url', 'title', 'tags' keys
            
        Returns:
            Dictionary mapping original URLs to short URLs
        """
        result_map = {}
        
        # Short.io supports bulk creation but for simplicity, 
        # we'll create links individually with error handling
        for item in urls_with_metadata:
            original_url = item.get('url')
            title = item.get('title')
            tags = item.get('tags', [])
            
            short_url = self.create_short_link(original_url, title, tags)
            result_map[original_url] = short_url
        
        return result_map
    
    def _validate_domain(self):
        """Validate domain by creating a test link"""
        try:
            # Test API with a simple link creation
            test_payload = {
                "originalURL": "https://www.google.com",
                "domain": self.domain
            }
            
            response = self.session.post(f"{self.base_url}/links", json=test_payload)
            
            if response.status_code == 200:
                data = response.json()
                self.domain_id = data.get('domainId') or data.get('DomainId')
                self.logger.info(f"Domain validation successful - ID: {self.domain_id}")
                
                # Clean up test link if needed
                if 'idString' in data:
                    try:
                        delete_url = f"{self.base_url}/links/{data['idString']}"
                        self.session.delete(delete_url)
                    except (requests.RequestException, KeyError):
                        pass  # Ignore cleanup errors
                        
            elif response.status_code == 401:
                self.logger.warning(f"Short.io API key is invalid or expired - please check API key in .env file")
                self.domain_id = None
            else:
                self.logger.warning(f"Domain validation failed: {response.status_code} - {response.text}")
                self.domain_id = None
        except Exception as e:
            self.logger.warning(f"Domain validation failed: {e}")
            self.domain_id = None


def test_link_tracker():
    """Test function for LinkTracker functionality"""
    print("Testing LinkTracker...")
    
    # Test Short.io functionality
    import os
    os.environ['USE_SUPABASE_EDGE_FUNCTION'] = 'false'
    tracker_shortio = LinkTracker()
    
    # Test single link creation
    test_url_shortio = "https://www.indeed.com/jobs?q=CDL+driver&l=Dallas%2C+TX"
    short_url_shortio = tracker_shortio.create_short_link(
        original_url=test_url_shortio,
        title="CDL Driver Jobs Dallas",
        tags=["job", "cdl", "dallas", "test"]
    )
    
    print(f"\n--- Short.io Test ---")
    print(f"Original: {test_url_shortio}")
    print(f"Short: {short_url_shortio}")
    assert short_url_shortio.startswith("https://freeworldjobs.short.gy/") or short_url_shortio == test_url_shortio
    
    # Test Supabase Edge Function functionality
    os.environ['USE_SUPABASE_EDGE_FUNCTION'] = 'true'
    tracker_supabase = LinkTracker()
    
    test_url_supabase = "https://www.indeed.com/jobs?q=Software+Engineer&l=Austin%2C+TX"
    test_candidate_id = "test-candidate-123"
    supabase_url = tracker_supabase.create_short_link(
        original_url=test_url_supabase,
        title="Software Engineer Jobs Austin",
        candidate_id=test_candidate_id
    )
    
    print(f"\n--- Supabase Edge Function Test ---")
    print(f"Original: {test_url_supabase}")
    print(f"Supabase Edge Function URL: {supabase_url}")
    expected_supabase_url = f"https://project.supabase.co/functions/v1/click-redirect?target={test_url_supabase}&candidate_id={test_candidate_id}"
    assert supabase_url == expected_supabase_url
    
    # Reset environment variable
    del os.environ['USE_SUPABASE_EDGE_FUNCTION']

    # Original bulk creation and analytics tests (can be adapted or removed if not relevant to new flow)
    # For now, keeping them as is, assuming they run with Short.io if USE_SUPABASE_EDGE_FUNCTION is false
    
    # Test bulk creation
    test_jobs = [
        {
            'url': 'https://www.indeed.com/viewjob?jk=123456',
            'title': 'CDL Driver - Local Routes',
            'tags': ['job', 'cdl', 'local']
        },
        {
            'url': 'https://www.indeed.com/viewjob?jk=789012',
            'title': 'OTR Driver - Excellent Pay',
            'tags': ['job', 'cdl', 'otr']
        }
    ]
    
    bulk_results = tracker_shortio.bulk_create_links(test_jobs)
    print("\nBulk results (Short.io):")
    for original, short in bulk_results.items():
        print(f"  {original} -> {short}")
    
    # Test analytics functionality
    print("\n" + "="*50)
    print("TESTING ANALYTICS FUNCTIONALITY (Short.io)")
    print("="*50)
    
    # Test domain analytics
    print("\n1. Domain Analytics:")
    domain_stats = tracker_shortio.get_domain_analytics()
    if domain_stats:
        print(f"   ✅ Domain analytics retrieved successfully")
        print(f"   📊 Data keys: {list(domain_stats.keys())}")
    else:
        print("   ❌ Failed to get domain analytics")
    
    # Test individual link analytics
    print("\n2. Individual Link Analytics:")
    if short_url_shortio and short_url_shortio != test_url_shortio:
        link_stats = tracker_shortio.get_link_analytics(short_url_shortio)
        if link_stats:
            print(f"   ✅ Link analytics for {short_url_shortio}")
            print(f"   📊 Clicks: {link_stats.get('totalClicks', 0)}")
            print(f"   📊 Data keys: {list(link_stats.keys())}")
        else:
            print(f"   ❌ Failed to get analytics for {short_url_shortio}")
    
    # Test all links analytics
    print("\n3. All Links Analytics:")
    all_links = tracker_shortio.get_all_links_analytics(limit=10)
    if all_links:
        print(f"   ✅ Retrieved analytics for {all_links.get('total_links', 0)} links")
        for link in all_links.get('links', [])[:3]:  # Show first 3
            print(f"   📊 {link.get('title', 'Untitled')}: {link.get('clicks', 0)} clicks")
    else:
        print("   ❌ Failed to get all links analytics")


if __name__ == "__main__":
    test_link_tracker()
