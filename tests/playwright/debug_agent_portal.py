#!/usr/bin/env python3
"""
Debug what happens when navigating to agent portal links
"""
import time
import base64
import json
from playwright.sync_api import sync_playwright

def debug_agent_portals():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=1000)
        page = browser.new_page()

        # Test legacy URL
        legacy_url = "https://fwcareertest.streamlit.app/?agent_config=eyJhZ2VudF91dWlkIjoiNTYxZGU0MzItNWMyNy00NjliLWI2NTItYzk1ODlhMjBiN2M2IiwiYWdlbnRfbmFtZSI6IkRhbGxhcyBUZXN0IExpbmsiLCJsb2NhdGlvbiI6IkRhbGxhcyIsInJvdXRlX2ZpbHRlciI6WyJMb2NhbCIsIk9UUiIsIlVua25vd24iXSwiZmFpcl9jaGFuY2Vfb25seSI6ZmFsc2UsIm1heF9qb2JzIjo1MCwiZXhwZXJpZW5jZV9sZXZlbCI6ImJvdGgiLCJjb2FjaF91c2VybmFtZSI6IkphbWVzIEhhemVsdG9uIn0=&candidate_id=561de432-5c27-469b-b652-c9589a20b7c6"

        print("🔍 Testing legacy agent portal URL...")
        print(f"URL: {legacy_url}")

        # Decode parameters
        agent_config_b64 = "eyJhZ2VudF91dWlkIjoiNTYxZGU0MzItNWMyNy00NjliLWI2NTItYzk1ODlhMjBiN2M2IiwiYWdlbnRfbmFtZSI6IkRhbGxhcyBUZXN0IExpbmsiLCJsb2NhdGlvbiI6IkRhbGxhcyIsInJvdXRlX2ZpbHRlciI6WyJMb2NhbCIsIk9UUiIsIlVua25vd24iXSwiZmFpcl9jaGFuY2Vfb25seSI6ZmFsc2UsIm1heF9qb2JzIjo1MCwiZXhwZXJpZW5jZV9sZXZlbCI6ImJvdGgiLCJjb2FjaF91c2VybmFtZSI6IkphbWVzIEhhemVsdG9uIn0="
        agent_config = json.loads(base64.b64decode(agent_config_b64).decode('utf-8'))
        print(f"Decoded config: {agent_config}")

        page.goto(legacy_url)

        # Check if iframe loads
        try:
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
            iframe_locator.locator('div[data-testid="stApp"]').wait_for(timeout=30000)
            print("✅ Iframe loaded successfully")

            # Save content for inspection
            iframe = page.locator('iframe[title="streamlitApp"]').element_handle()
            iframe_page = iframe.content_frame()
            content = iframe_page.content()

            with open("debug_legacy_portal_content.html", "w") as f:
                f.write(content)
            print("💾 Legacy portal content saved")

            # Look for any text content
            try:
                all_text = iframe_locator.locator('body').text_content()
                print(f"📝 Page text content (first 500 chars): {all_text[:500]}...")

                # Check if it's showing login page instead
                login_indicators = ["Username", "Password", "Sign In", "username", "password"]
                found_login = []
                for indicator in login_indicators:
                    if indicator.lower() in all_text.lower():
                        found_login.append(indicator)

                if found_login:
                    print(f"⚠️ Appears to be showing login page: {found_login}")
                    print("   → Agent portal may require authentication")

                # Look for any agent-related content
                agent_indicators = ["Dallas", "Test Link", "Jobs", "Apply", "agent", "portal"]
                found_agent = []
                for indicator in agent_indicators:
                    if indicator.lower() in all_text.lower():
                        found_agent.append(indicator)

                if found_agent:
                    print(f"✅ Found agent-related content: {found_agent}")
                else:
                    print("❌ No agent-related content found")

            except Exception as e:
                print(f"💥 Error getting text content: {e}")

        except Exception as e:
            print(f"❌ Failed to load iframe: {e}")

        # Test new portal URL
        print(f"\n" + "="*60)
        new_url = "https://fwcareertest.streamlit.app/agent_job_feed?config=eyJhZ2VudF91dWlkIjoiZjdmMDZmYWQtZmMzYi00ZmNjLWJiYWUtOGNiMzVmNDQ5YjcxIiwiYWdlbnRfbmFtZSI6IkphY29iIiwibG9jYXRpb24iOiJJbmxhbmQgRW1waXJlIiwicm91dGVfdHlwZV9maWx0ZXIiOiJib3RoIiwiZmFpcl9jaGFuY2Vfb25seSI6ZmFsc2UsIm1heF9qb2JzIjoiQWxsIiwibWF0Y2hfcXVhbGl0eV9maWx0ZXIiOiJnb29kIGFuZCBzby1zbyIsImNvYWNoX3VzZXJuYW1lIjoiSmFtZXMgSGF6ZWx0b24iLCJzaG93X3ByZXBhcmVkX2ZvciI6dHJ1ZX0="

        print("🔍 Testing new agent portal URL...")
        print(f"URL: {new_url}")

        # Decode parameters
        config_b64 = "eyJhZ2VudF91dWlkIjoiZjdmMDZmYWQtZmMzYi00ZmNjLWJiYWUtOGNiMzVmNDQ5YjcxIiwiYWdlbnRfbmFtZSI6IkphY29iIiwibG9jYXRpb24iOiJJbmxhbmQgRW1waXJlIiwicm91dGVfdHlwZV9maWx0ZXIiOiJib3RoIiwiZmFpcl9jaGFuY2Vfb25seSI6ZmFsc2UsIm1heF9qb2JzIjoiQWxsIiwibWF0Y2hfcXVhbGl0eV9maWx0ZXIiOiJnb29kIGFuZCBzby1zbyIsImNvYWNoX3VzZXJuYW1lIjoiSmFtZXMgSGF6ZWx0b24iLCJzaG93X3ByZXBhcmVkX2ZvciI6dHJ1ZX0="
        config = json.loads(base64.b64decode(config_b64).decode('utf-8'))
        print(f"Decoded config: {config}")

        page.goto(new_url)

        try:
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
            iframe_locator.locator('div[data-testid="stApp"]').wait_for(timeout=30000)
            print("✅ New portal iframe loaded successfully")

            # Save content for inspection
            iframe = page.locator('iframe[title="streamlitApp"]').element_handle()
            iframe_page = iframe.content_frame()
            content = iframe_page.content()

            with open("debug_new_portal_content.html", "w") as f:
                f.write(content)
            print("💾 New portal content saved")

            # Look for any text content
            try:
                all_text = iframe_locator.locator('body').text_content()
                print(f"📝 Page text content (first 500 chars): {all_text[:500]}...")

                # Check for agent-related content
                agent_indicators = ["Jacob", "Inland Empire", "Jobs", "Apply", "agent", "portal", "prepared"]
                found_agent = []
                for indicator in agent_indicators:
                    if indicator.lower() in all_text.lower():
                        found_agent.append(indicator)

                if found_agent:
                    print(f"✅ Found agent-related content: {found_agent}")
                else:
                    print("❌ No agent-related content found")

                # Check if it's showing login page
                login_indicators = ["Username", "Password", "Sign In"]
                found_login = []
                for indicator in login_indicators:
                    if indicator in all_text:
                        found_login.append(indicator)

                if found_login:
                    print(f"⚠️ Appears to be showing login page: {found_login}")

            except Exception as e:
                print(f"💥 Error getting text content: {e}")

        except Exception as e:
            print(f"❌ Failed to load new portal iframe: {e}")

        browser.close()

if __name__ == "__main__":
    debug_agent_portals()