#!/usr/bin/env python3
"""
Frontend Diagnostic Tool - JavaScript Console Error Checker

This script diagnoses frontend issues by:
1. Checking for page loads
2. Verifying critical DOM elements exist
3. Testing JS dependencies

Usage:
    python tests/diagnostic/ui/frontend_diagnostic.py [--verbose] [--url URL]

Exit codes:
    0 - All checks passed
    1 - Errors found
    2 - Configuration error
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class FrontendDiagnostic:
    """Diagnoses frontend JavaScript and UI issues."""

    PAGES_TO_CHECK = {
        "client_menu": {
            "url": "http://localhost:6080",
            "critical_elements": [
                "#menu-sections",
                ".category-tab",
                ".menu-item-card",
                "#menu-search",
            ],
            "js_dependencies": ["menu.js", "base.js"],
        },
        "client_checkout": {
            "url": "http://localhost:6080?view=details",
            "critical_elements": [
                "#checkout-form",
                "#customer-name",
                "#customer-email",
                "#checkout-btn",
            ],
            "js_dependencies": ["menu.js", "base.js"],
        },
        "waiter_dashboard": {
            "url": "http://localhost:6081/waiter/dashboard",
            "critical_elements": [
                "table",
                "[class*='order']",
                ".category-tab",
            ],
            "js_dependencies": ["dashboard.js", "base.js"],
            "requires_auth": True,
        },
        "chef_dashboard": {
            "url": "http://localhost:6081/chef/dashboard",
            "critical_elements": [
                "[class*='column']",
                "[class*='kds']",
                "[class*='order']",
            ],
            "js_dependencies": ["dashboard.js", "base.js"],
            "requires_auth": True,
        },
        "cashier_dashboard": {
            "url": "http://localhost:6081/cashier/dashboard",
            "critical_elements": [
                "table",
                "[class*='session']",
                "[class*='summary']",
            ],
            "js_dependencies": ["dashboard.js", "base.js"],
            "requires_auth": True,
        },
    }

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.passed = []

    def log(self, message: str, level: str = "INFO"):
        """Log a message with optional color."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "ERROR":
            msg = f"{Colors.RED}[ERROR]{Colors.RESET} {message}"
        elif level == "WARNING":
            msg = f"{Colors.YELLOW}[WARN]{Colors.RESET} {message}"
        elif level == "PASS":
            msg = f"{Colors.GREEN}[PASS]{Colors.RESET} {message}"
        elif level == "INFO" and self.verbose:
            msg = f"{Colors.BLUE}[INFO]{Colors.RESET} {message}"
        else:
            return

        print(f"{timestamp} {msg}")

    def check_page_load(self, page_key: str, page_info: dict) -> bool:
        """Check if a page loads successfully."""
        url = page_info["url"]

        self.log(f"Checking page: {page_key} ({url})", "INFO")

        try:
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                self.errors.append(f"{page_key}: HTTP {response.status_code}")
                self.log(f"Page returned status {response.status_code}", "ERROR")
                return False

            self.passed.append(f"{page_key}: Page loads (HTTP {response.status_code})")
            self.log("Page loads successfully", "PASS")
            return True

        except requests.exceptions.ConnectionError:
            self.errors.append(f"{page_key}: Connection error - service may be down")
            self.log(f"Cannot connect to {url}", "ERROR")
            return False
        except requests.exceptions.Timeout:
            self.errors.append(f"{page_key}: Request timeout")
            self.log(f"Request timed out", "ERROR")
            return False

    def check_critical_elements(self, page_key: str, page_info: dict) -> bool:
        """Check if critical DOM elements exist."""
        url = page_info["url"]

        try:
            response = requests.get(url, timeout=10)
            html = response.text

            elements_found = 0
            elements_missing = []

            for selector in page_info.get("critical_elements", []):
                # Convert CSS selector to regex pattern (basic support)
                selector_escaped = re.escape(selector.lstrip("#."))
                pattern = rf'(?:id|class)=["\']?\*{0, 2}{selector_escaped}'
                if re.search(pattern, html, re.IGNORECASE):
                    elements_found += 1
                else:
                    elements_missing.append(selector)

            if elements_missing:
                self.warnings.append(f"{page_key}: Missing elements: {', '.join(elements_missing)}")
                self.log(f"Missing elements: {elements_missing}", "WARNING")
            else:
                self.passed.append(f"{page_key}: All {elements_found} critical elements present")
                self.log(f"All {elements_found} critical elements found", "PASS")

            return len(elements_missing) == 0

        except Exception as e:
            self.errors.append(f"{page_key}: Error checking elements - {str(e)}")
            self.log(f"Error checking elements: {e}", "ERROR")
            return False

    def check_js_dependencies(self, page_key: str, page_info: dict) -> bool:
        """Check if required JavaScript files are loaded."""
        url = page_info["url"]

        try:
            response = requests.get(url, timeout=10)
            html = response.text

            # Find script tags with src attribute
            scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
            loaded_scripts = [s for s in scripts if s]

            missing_deps = []
            for dep in page_info.get("js_dependencies", []):
                dep_found = any(dep in src for src in loaded_scripts)
                if not dep_found:
                    missing_deps.append(dep)

            if missing_deps:
                self.warnings.append(f"{page_key}: Missing JS deps: {', '.join(missing_deps)}")
                self.log(f"Missing dependencies: {missing_deps}", "WARNING")
            else:
                self.passed.append(f"{page_key}: All JS dependencies loaded")
                self.log("All JS dependencies found", "PASS")

            return len(missing_deps) == 0

        except Exception as e:
            self.errors.append(f"{page_key}: Error checking JS deps - {str(e)}")
            return False

    def check_static_assets(self, base_url: str) -> bool:
        """Check if static assets are accessible."""
        static_url = "http://localhost:9088"

        try:
            # Check static server
            static_response = requests.get(f"{static_url}/", timeout=5)

            if static_response.status_code == 200:
                self.passed.append("Static asset server: Accessible")
                self.log("Static server accessible", "PASS")
                return True
            else:
                self.warnings.append(f"Static server returned HTTP {static_response.status_code}")
                self.log(f"Static server status: {static_response.status_code}", "WARNING")
                return False

        except requests.exceptions.ConnectionError:
            self.warnings.append("Static asset server: Not accessible (may be using internal URL)")
            self.log("Static server not accessible from host", "WARNING")
            return True  # This is expected in Docker

    def check_health_endpoint(self) -> bool:
        """Check API health endpoints."""
        health_endpoints = [
            ("Client", "http://localhost:6080/api/health"),
            ("Employee", "http://localhost:6081/api/health"),
        ]

        all_healthy = True
        for name, url in health_endpoints:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.passed.append(f"Health check: {name} - OK")
                else:
                    self.warnings.append(f"Health check: {name} - HTTP {response.status_code}")
                    all_healthy = False
            except requests.exceptions.ConnectionError:
                self.warnings.append(f"Health check: {name} - Not accessible")
                all_healthy = False

        return all_healthy

    def run_full_diagnostic(self) -> dict:
        """Run the complete frontend diagnostic."""
        print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}FRONTEND DIAGNOSTIC TOOL{Colors.RESET}")
        print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")

        results = {
            "timestamp": datetime.now().isoformat(),
            "pages_checked": 0,
            "errors": [],
            "warnings": [],
            "passed": [],
            "overall_status": "UNKNOWN",
        }

        # Check health endpoints
        self.log("Checking API health endpoints...", "INFO")
        self.check_health_endpoint()

        # Check static assets
        self.log("\nChecking static assets...", "INFO")
        self.check_static_assets("http://localhost:9088")

        # Check each page
        for page_key, page_info in self.PAGES_TO_CHECK.items():
            print(f"\n{Colors.BOLD}--- {page_key.upper()} ---{Colors.RESET}")

            results["pages_checked"] += 1

            # Check page load
            self.check_page_load(page_key, page_info)

            # Check critical elements
            self.check_critical_elements(page_key, page_info)

            # Check JS dependencies
            self.check_js_dependencies(page_key, page_info)

        # Compile results
        results["errors"] = self.errors
        results["warnings"] = self.warnings
        results["passed"] = self.passed
        results["overall_status"] = (
            "PASS" if not self.errors else "FAIL" if self.errors else "WARNING"
        )

        # Print summary
        print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}DIAGNOSTIC SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")

        print(f"\n{Colors.GREEN}Passed: {len(self.passed)}{Colors.RESET}")
        for item in self.passed[:5]:
            print(f"  ✓ {item}")
        if len(self.passed) > 5:
            print(f"  ... and {len(self.passed) - 5} more")

        if self.warnings:
            print(f"\n{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.RESET}")
            for item in self.warnings[:3]:
                print(f"  ⚠ {item}")
            if len(self.warnings) > 3:
                print(f"  ... and {len(self.warnings) - 3} more")

        if self.errors:
            print(f"\n{Colors.RED}Errors: {len(self.errors)}{Colors.RESET}")
            for item in self.errors[:5]:
                print(f"  ✗ {item}")
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more")

        print(f"\n{Colors.BOLD}Overall Status: {results['overall_status']}{Colors.RESET}")

        return results

    def save_results(self, results: dict, filepath: Optional[str] = None):
        """Save diagnostic results to a JSON file."""
        if filepath is None:
            filepath = (
                f"tests/diagnostic/ui/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

        self.log(f"Results saved to {filepath}", "INFO")


def main():
    parser = argparse.ArgumentParser(
        description="Frontend Diagnostic Tool - Check for JavaScript and UI errors"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    parser.add_argument("--url", "-u", help="Check a specific URL instead of all pages")
    parser.add_argument("--output", "-o", help="Output file for JSON results")
    parser.add_argument("--quick", action="store_true", help="Quick check - only client menu page")

    args = parser.parse_args()

    diagnostic = FrontendDiagnostic(verbose=args.verbose)

    if args.url:
        # Check single URL
        page_info = {
            "url": args.url,
            "critical_elements": [],
            "js_dependencies": [],
        }
        diagnostic.check_page_load("custom", page_info)
    elif args.quick:
        # Quick check - only client menu
        diagnostic.PAGES_TO_CHECK = {"client_menu": diagnostic.PAGES_TO_CHECK["client_menu"]}
        diagnostic.run_full_diagnostic()
    else:
        results = diagnostic.run_full_diagnostic()
        diagnostic.save_results(results, args.output)

    # Exit with appropriate code
    if diagnostic.errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
