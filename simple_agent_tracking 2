#!/usr/bin/env python3
"""
Simple Agent Click Tracking - One Link Per Agent
Much simpler than per-job tracking
"""

class SimpleAgentTracker:
    """One universal tracking link per Free Agent"""
    
    def __init__(self):
        from link_tracker import LinkTracker
        self.tracker = LinkTracker()
    
    def get_agent_click_link(self, agent_uuid: str, agent_name: str, coach_username: str) -> str:
        """
        Get ONE universal click tracking link for this agent
        All apply buttons use the same link - much simpler!
        """
        
        # Create ONE universal tracking URL per agent
        # This redirects through webhook which logs the click + actual job URL
        universal_link = f"https://freeworldjobs.short.gy/{agent_uuid[:8]}-clicks"
        
        # Tags for analytics (same as before)
        tags = [
            f"candidate:{agent_uuid}",
            f"agent:{agent_name.replace(' ', '-')}",
            f"coach:{coach_username}",
            "type:universal_click"
        ]
        
        # Only create the link once per agent (could cache this)
        try:
            tracked_url = self.tracker.create_short_link(
                # Webhook URL that handles the redirect
                "https://yqbdltothngundojuebk.functions.supabase.co/agent-click-redirect",
                title=f"Job Clicks - {agent_name}",
                tags=tags
            )
            return tracked_url
        except:
            # Fallback - direct webhook URL with agent UUID
            return f"https://yqbdltothngundojuebk.functions.supabase.co/agent-click-redirect?agent={agent_uuid}"
    
    def create_job_apply_url(self, agent_uuid: str, job_url: str, universal_click_link: str) -> str:
        """
        Create apply URL that goes through universal tracker
        
        Flow:
        1. User clicks apply button 
        2. Goes to universal_click_link
        3. Webhook logs "agent clicked" 
        4. Webhook redirects to actual job_url
        """
        
        # Encode the actual job URL as a parameter
        import urllib.parse
        encoded_job_url = urllib.parse.quote(job_url)
        
        # Universal link with job URL parameter
        return f"{universal_click_link}?target={encoded_job_url}"

# Example usage
def demo_simple_tracking():
    """Show how simple this would be"""
    
    tracker = SimpleAgentTracker()
    
    # Benjamin gets ONE universal link for ALL jobs
    benjamin_link = tracker.get_agent_click_link(
        "ef78e371-1929-11ef-937f-de2fe15254ef",
        "Benjamin Bechtolsheim", 
        "james.hazelton"
    )
    
    print(f"🔗 Benjamin's Universal Link: {benjamin_link}")
    
    # ALL job apply buttons use the SAME link (with different targets)
    job_urls = [
        "https://indeed.com/job1",
        "https://indeed.com/job2", 
        "https://indeed.com/job3"
    ]
    
    for i, job_url in enumerate(job_urls):
        apply_url = tracker.create_job_apply_url(
            "ef78e371-1929-11ef-937f-de2fe15254ef",
            job_url,
            benjamin_link
        )
        print(f"  Job {i+1} Apply Button: {apply_url}")

if __name__ == "__main__":
    demo_simple_tracking()