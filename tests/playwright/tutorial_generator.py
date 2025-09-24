#!/usr/bin/env python3
"""
Tutorial Generator for FreeWorld Success Coach Portal
Uses Playwright to capture screenshots and workflows for comprehensive documentation
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from playwright.sync_api import sync_playwright, Page, Browser

# Add parent directories for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from conftest import (
    TEST_CONFIG, navigate_to_tab, set_search_parameters,
    check_permission_access, get_batch_form_elements,
    login_as_admin, login_as_coach
)

class TutorialCapture:
    """Automated tutorial generation using Playwright"""

    def __init__(self, output_dir: str = "docs/coach-tutorial"):
        self.output_dir = Path(output_dir)
        self.screenshots_dir = self.output_dir / "screenshots"
        self.workflows_dir = self.output_dir / "workflows"

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

        self.tutorial_data = {
            "generated_at": datetime.now().isoformat(),
            "sections": [],
            "field_definitions": {},
            "workflows": [],
            "troubleshooting": []
        }

    def capture_workflow(self, page: Page, workflow_name: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Capture a complete workflow with screenshots and annotations"""
        print(f"📸 Capturing workflow: {workflow_name}")

        workflow_data = {
            "name": workflow_name,
            "description": f"Step-by-step guide for {workflow_name.lower()}",
            "steps": [],
            "screenshots": [],
            "duration": 0
        }

        start_time = time.time()

        for i, step in enumerate(steps):
            step_start = time.time()
            step_num = i + 1

            print(f"   📋 Step {step_num}: {step.get('description', 'Performing action')}")

            # Take before screenshot if needed
            if step.get('screenshot_before', False):
                screenshot_name = f"{workflow_name.lower().replace(' ', '_')}_step_{step_num}_before.png"
                screenshot_path = self.screenshots_dir / screenshot_name
                page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"      📷 Before screenshot: {screenshot_name}")

            # Execute step action
            try:
                if step['action'] == 'navigate':
                    success = navigate_to_tab(page, step['target'])
                    result = "success" if success else "failed"
                elif step['action'] == 'click':
                    iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
                    element = iframe_locator.locator(step['selector'])
                    element.click()
                    result = "success"
                elif step['action'] == 'fill':
                    iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
                    element = iframe_locator.locator(step['selector'])
                    element.clear()
                    element.fill(step['value'])
                    result = "success"
                elif step['action'] == 'wait':
                    time.sleep(step.get('duration', 2))
                    result = "success"
                elif step['action'] == 'set_parameters':
                    success = set_search_parameters(page, step['parameters'])
                    result = "success" if success else "failed"
                else:
                    result = "skipped"

                # Wait after action
                if step.get('wait_after', True):
                    time.sleep(step.get('wait_duration', 2))

            except Exception as e:
                print(f"      ⚠️ Step failed: {e}")
                result = "error"

            # Take after screenshot
            screenshot_name = f"{workflow_name.lower().replace(' ', '_')}_step_{step_num}.png"
            screenshot_path = self.screenshots_dir / screenshot_name
            page.screenshot(path=str(screenshot_path), full_page=True)

            # Extract current page info for documentation
            try:
                iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
                page_text = iframe_locator.locator('body').text_content(timeout=5000)
                visible_elements = self._extract_visible_elements(iframe_locator)
            except:
                page_text = ""
                visible_elements = []

            step_data = {
                "step_number": step_num,
                "description": step['description'],
                "action": step['action'],
                "result": result,
                "duration": time.time() - step_start,
                "screenshot": screenshot_name,
                "visible_elements": visible_elements,
                "notes": step.get('notes', ''),
                "expected_outcome": step.get('expected_outcome', '')
            }

            workflow_data["steps"].append(step_data)
            workflow_data["screenshots"].append(screenshot_name)

        workflow_data["duration"] = time.time() - start_time
        return workflow_data

    def _extract_visible_elements(self, iframe_locator) -> List[Dict[str, str]]:
        """Extract visible UI elements for documentation"""
        elements = []
        try:
            # Common UI elements to document
            selectors = [
                ('button', 'button'),
                ('input', 'input'),
                ('select', 'select'),
                ('text*="Search"', 'search_field'),
                ('text*="Location"', 'location_field'),
                ('text*="Memory Only"', 'memory_button'),
                ('text*="Fresh Only"', 'fresh_button'),
            ]

            for selector, element_type in selectors:
                try:
                    element = iframe_locator.locator(selector).first
                    if element.is_visible(timeout=1000):
                        text = element.text_content() or element.get_attribute('placeholder') or ''
                        elements.append({
                            "type": element_type,
                            "text": text,
                            "selector": selector
                        })
                except:
                    continue

        except Exception as e:
            print(f"      ⚠️ Element extraction failed: {e}")

        return elements

    def generate_getting_started_guide(self, browser: Browser) -> None:
        """Generate comprehensive getting started guide"""
        print("📚 Generating Getting Started Guide...")

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(self.workflows_dir),
            record_video_size={"width": 1920, "height": 1080}
        )

        page = context.new_page()
        page.set_default_timeout(TEST_CONFIG["timeout"])

        # Login workflow
        login_workflow = self.capture_workflow(page, "Coach Login", [
            {
                "action": "navigate_to_url",
                "target": TEST_CONFIG["base_url"],
                "description": "Navigate to FreeWorld Success Coach Portal",
                "screenshot_before": True,
                "expected_outcome": "Portal login page loads"
            },
            {
                "action": "wait",
                "duration": 5,
                "description": "Wait for page to fully load"
            },
            {
                "action": "fill",
                "selector": 'input[placeholder="username"]',
                "value": TEST_CONFIG["admin_username"],
                "description": "Enter username in login form"
            },
            {
                "action": "fill",
                "selector": 'input[type="password"]',
                "value": TEST_CONFIG["admin_password"],
                "description": "Enter password in login form"
            },
            {
                "action": "click",
                "selector": 'button:has-text("Sign In")',
                "description": "Click Sign In button",
                "expected_outcome": "Successfully logged in, main interface visible"
            },
            {
                "action": "wait",
                "duration": 8,
                "description": "Wait for main interface to load"
            }
        ])

        # Navigation workflow
        navigation_workflow = self.capture_workflow(page, "Interface Navigation", [
            {
                "action": "navigate",
                "target": "🔍 Job Search",
                "description": "Navigate to Job Search tab",
                "expected_outcome": "Job Search interface visible"
            },
            {
                "action": "navigate",
                "target": "👥 Free Agents",
                "description": "Navigate to Free Agents tab",
                "expected_outcome": "Free Agents management interface visible"
            },
            {
                "action": "navigate",
                "target": "📊 Coach Analytics",
                "description": "Navigate to Coach Analytics tab",
                "expected_outcome": "Analytics dashboard visible"
            },
            {
                "action": "navigate",
                "target": "🏢 Companies",
                "description": "Navigate to Companies tab",
                "expected_outcome": "Companies overview visible"
            }
        ])

        # Basic search workflow
        basic_search_workflow = self.capture_workflow(page, "Basic Job Search", [
            {
                "action": "navigate",
                "target": "🔍 Job Search",
                "description": "Navigate to Job Search tab"
            },
            {
                "action": "set_parameters",
                "parameters": {
                    "location": "Houston, TX",
                    "search_terms": "CDL driver",
                    "classifier_type": "CDL Traditional"
                },
                "description": "Set basic search parameters",
                "expected_outcome": "Search form populated with parameters"
            },
            {
                "action": "click",
                "selector": 'button:has-text("💾 Memory Only")',
                "description": "Click Memory Only search",
                "expected_outcome": "Search starts, results appear"
            },
            {
                "action": "wait",
                "duration": 10,
                "description": "Wait for search results"
            }
        ])

        # Store workflows
        self.tutorial_data["workflows"].extend([
            login_workflow, navigation_workflow, basic_search_workflow
        ])

        context.close()

    def generate_field_definitions(self) -> None:
        """Generate comprehensive field definitions"""
        print("📝 Generating Field Definitions...")

        field_definitions = {
            "search_parameters": {
                "location": {
                    "description": "Target geographic location for job search",
                    "type": "text_input",
                    "examples": ["Houston, TX", "Dallas, TX", "Austin, TX"],
                    "tips": "Use city, state format for best results"
                },
                "search_terms": {
                    "description": "Keywords to search for in job postings",
                    "type": "text_input",
                    "examples": ["CDL driver", "truck driver", "warehouse forklift"],
                    "tips": "Use relevant job titles and skills"
                },
                "classifier_type": {
                    "description": "AI classification system to use",
                    "type": "select",
                    "options": ["CDL Traditional", "Career Pathways"],
                    "tips": "CDL Traditional for driving jobs, Career Pathways for warehouse progression"
                }
            },
            "search_modes": {
                "memory_only": {
                    "button": "💾 Memory Only",
                    "description": "Search cached jobs from recent searches (fast, no API cost)",
                    "when_to_use": "Quick results for recently searched locations"
                },
                "indeed_fresh": {
                    "button": "🔍 Indeed Fresh Only",
                    "description": "Search fresh jobs from Indeed API (slower, API cost)",
                    "when_to_use": "Get latest job postings for new locations"
                }
            },
            "job_quantities": {
                "test": {
                    "display": "25 jobs (test)",
                    "description": "Small test search for verification",
                    "cost": "Low"
                },
                "sample": {
                    "display": "100 jobs (sample)",
                    "description": "Standard search size for most use cases",
                    "cost": "Medium"
                },
                "medium": {
                    "display": "500 jobs (medium)",
                    "description": "Comprehensive search for larger markets",
                    "cost": "High"
                },
                "full": {
                    "display": "1000+ jobs (full)",
                    "description": "Maximum search size (admin permission required)",
                    "cost": "Very High"
                }
            },
            "quality_levels": {
                "good": {
                    "description": "High-quality matches meeting all criteria",
                    "color": "Green",
                    "criteria": "Good pay, benefits, clear requirements"
                },
                "so_so": {
                    "description": "Moderate matches with some limitations",
                    "color": "Yellow",
                    "criteria": "Acceptable but may have experience preferences"
                },
                "bad": {
                    "description": "Poor matches not recommended",
                    "color": "Red",
                    "criteria": "Low pay, poor conditions, or misleading"
                }
            }
        }

        self.tutorial_data["field_definitions"] = field_definitions

    def generate_troubleshooting_guide(self) -> None:
        """Generate troubleshooting guide based on common issues"""
        print("🔧 Generating Troubleshooting Guide...")

        troubleshooting = [
            {
                "issue": "Search returns no results",
                "solutions": [
                    "Try a different location nearby (e.g., if Dallas doesn't work, try Houston)",
                    "Use broader search terms (e.g., 'driver' instead of 'CDL Class A driver')",
                    "Switch from Memory Only to Indeed Fresh to get latest postings",
                    "Check if location is spelled correctly"
                ],
                "prevention": "Start with Memory Only search, then use Fresh if needed"
            },
            {
                "issue": "Search takes too long or times out",
                "solutions": [
                    "Use smaller job quantities (25 or 100 jobs instead of 500+)",
                    "Try Memory Only search first",
                    "Check internet connection",
                    "Try searching during off-peak hours"
                ],
                "prevention": "Start with test mode (25 jobs) to verify location works"
            },
            {
                "issue": "Can't access certain tabs or features",
                "solutions": [
                    "Check with admin about your permission levels",
                    "Verify you're logged in with correct account",
                    "Try logging out and back in",
                    "Contact support if permissions should be different"
                ],
                "prevention": "Confirm required permissions with admin before starting"
            },
            {
                "issue": "PDF export not working",
                "solutions": [
                    "Ensure you have jobs in your search results",
                    "Try reducing number of jobs in export",
                    "Check browser popup blockers",
                    "Try different browser if issues persist"
                ],
                "prevention": "Test with small job count first"
            }
        ]

        self.tutorial_data["troubleshooting"] = troubleshooting

    def generate_daily_workflows(self, browser: Browser) -> None:
        """Generate daily workflow guides"""
        print("📅 Generating Daily Workflow Guides...")

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        login_as_admin(page)

        # Daily startup workflow
        daily_startup = self.capture_workflow(page, "Daily Startup Routine", [
            {
                "action": "navigate",
                "target": "📊 Coach Analytics",
                "description": "Check overnight analytics and performance metrics",
                "expected_outcome": "See yesterday's Free Agent engagement numbers"
            },
            {
                "action": "navigate",
                "target": "🗓️ Batches & Scheduling",
                "description": "Review scheduled batch jobs status",
                "expected_outcome": "Verify automated searches completed successfully"
            },
            {
                "action": "navigate",
                "target": "👥 Free Agents",
                "description": "Check for new Free Agent registrations",
                "expected_outcome": "Review any new agents needing job searches"
            }
        ])

        # Agent job search workflow
        agent_search = self.capture_workflow(page, "Agent Job Search Process", [
            {
                "action": "navigate",
                "target": "👥 Free Agents",
                "description": "Select Free Agent needing jobs"
            },
            {
                "action": "navigate",
                "target": "🔍 Job Search",
                "description": "Start job search process"
            },
            {
                "action": "set_parameters",
                "parameters": {
                    "location": "Houston, TX",
                    "search_terms": "CDL driver",
                    "classifier_type": "CDL Traditional"
                },
                "description": "Set parameters based on agent profile"
            },
            {
                "action": "click",
                "selector": 'button:has-text("💾 Memory Only")',
                "description": "Try memory search first for speed"
            }
        ])

        self.tutorial_data["workflows"].extend([daily_startup, agent_search])
        context.close()

    def save_tutorial_documentation(self) -> None:
        """Save all tutorial documentation to files"""
        print("💾 Saving Tutorial Documentation...")

        # Save main tutorial data
        with open(self.output_dir / "tutorial_data.json", 'w') as f:
            json.dump(self.tutorial_data, f, indent=2)

        # Generate markdown files
        self._generate_markdown_files()

        print(f"✅ Tutorial documentation saved to: {self.output_dir}")
        print(f"📸 Screenshots saved to: {self.screenshots_dir}")
        print(f"🎬 Workflows saved to: {self.workflows_dir}")

    def _generate_markdown_files(self) -> None:
        """Generate markdown documentation files"""

        # Main README
        readme_content = f"""# FreeWorld Success Coach Portal - User Guide

Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

## Table of Contents

1. [Getting Started](getting-started/README.md)
2. [Daily Workflows](daily-workflows/README.md)
3. [Features Guide](features-guide/README.md)
4. [Field Definitions](reference/field-definitions.md)
5. [Troubleshooting](troubleshooting/README.md)

## Quick Start

1. **Login**: Use your coach credentials to access the portal
2. **Navigate**: Use the main tabs to access different features
3. **Search Jobs**: Start with Memory Only searches, use Fresh for new locations
4. **Monitor Analytics**: Check Free Agent engagement regularly

## Support

For technical issues or questions about using the portal:
- Check the [Troubleshooting Guide](troubleshooting/README.md)
- Review [Field Definitions](reference/field-definitions.md) for clarification
- Contact your system administrator for permission issues

---
*This guide was automatically generated from live system interactions*
"""

        with open(self.output_dir / "README.md", 'w') as f:
            f.write(readme_content)

        # Field definitions
        field_def_content = self._generate_field_definitions_markdown()
        os.makedirs(self.output_dir / "reference", exist_ok=True)
        with open(self.output_dir / "reference" / "field-definitions.md", 'w') as f:
            f.write(field_def_content)

        # Troubleshooting guide
        troubleshooting_content = self._generate_troubleshooting_markdown()
        os.makedirs(self.output_dir / "troubleshooting", exist_ok=True)
        with open(self.output_dir / "troubleshooting" / "README.md", 'w') as f:
            f.write(troubleshooting_content)

        print("📄 Markdown files generated successfully")

    def _generate_field_definitions_markdown(self) -> str:
        """Generate field definitions markdown"""
        content = "# Field Definitions\n\n"

        for category, fields in self.tutorial_data["field_definitions"].items():
            content += f"## {category.replace('_', ' ').title()}\n\n"

            for field_name, field_info in fields.items():
                content += f"### {field_name.replace('_', ' ').title()}\n\n"
                content += f"**Description**: {field_info['description']}\n\n"

                if 'type' in field_info:
                    content += f"**Type**: {field_info['type']}\n\n"

                if 'examples' in field_info:
                    content += "**Examples**:\n"
                    for example in field_info['examples']:
                        content += f"- {example}\n"
                    content += "\n"

                if 'tips' in field_info:
                    content += f"💡 **Tip**: {field_info['tips']}\n\n"

                content += "---\n\n"

        return content

    def _generate_troubleshooting_markdown(self) -> str:
        """Generate troubleshooting markdown"""
        content = "# Troubleshooting Guide\n\n"

        for issue in self.tutorial_data["troubleshooting"]:
            content += f"## {issue['issue']}\n\n"

            content += "### Solutions\n"
            for solution in issue['solutions']:
                content += f"1. {solution}\n"
            content += "\n"

            if 'prevention' in issue:
                content += f"### Prevention\n{issue['prevention']}\n\n"

            content += "---\n\n"

        return content

def generate_complete_tutorial():
    """Generate complete tutorial documentation"""
    print("🚀 FreeWorld Success Coach Portal - Tutorial Generation")
    print("=" * 60)

    generator = TutorialCapture()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)

        try:
            # Generate all tutorial components
            generator.generate_getting_started_guide(browser)
            generator.generate_daily_workflows(browser)
            generator.generate_field_definitions()
            generator.generate_troubleshooting_guide()

            # Save documentation
            generator.save_tutorial_documentation()

            print("\n🎉 Tutorial generation completed successfully!")
            print(f"📚 Documentation available at: {generator.output_dir}")

        finally:
            browser.close()

if __name__ == "__main__":
    generate_complete_tutorial()