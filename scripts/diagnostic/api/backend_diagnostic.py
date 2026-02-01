#!/usr/bin/env python3
"""
Backend Diagnostic Tool - API and System Health Checker

This script diagnoses backend issues by:
1. Checking all API endpoints for errors
2. Verifying database connectivity
3. Testing authentication flows
4. Checking service dependencies (Redis, PostgreSQL)

Usage:
    python tests/diagnostic/api/backend_diagnostic.py [--verbose] [--full]

Exit codes:
    0 - All checks passed
    1 - Errors found
    2 - Configuration error
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class BackendDiagnostic:
    """Diagnoses backend API and system issues."""

    API_ENDPOINTS = {
        # Client API (port 6080)
        "client_health": {"url": "http://localhost:6080/api/health", "method": "GET"},
        "client_menu": {"url": "http://localhost:6080/api/menu", "method": "GET"},
        "client_tables": {"url": "http://localhost:6080/api/tables", "method": "GET"},
        "client_business": {"url": "http://localhost:6080/api/business-info", "method": "GET"},
        # Employee API (port 6081)
        "employee_health": {"url": "http://localhost:6081/api/health", "method": "GET"},
        "employee_public_stats": {"url": "http://localhost:6081/api/stats/public", "method": "GET"},
    }

    SCOPED_ENDPOINTS = {
        "waiter_orders": {
            "url": "http://localhost:6081/waiter/api/orders",
            "method": "GET",
            "auth_required": True,
            "scope": "waiter",
        },
        "waiter_tables": {
            "url": "http://localhost:6081/waiter/api/table-assignments/my-tables",
            "method": "GET",
            "auth_required": True,
            "scope": "waiter",
        },
        "chef_orders": {
            "url": "http://localhost:6081/chef/api/orders/pending",
            "method": "GET",
            "auth_required": True,
            "scope": "chef",
        },
        "cashier_sessions": {
            "url": "http://localhost:6081/cashier/api/sessions/pending",
            "method": "GET",
            "auth_required": True,
            "scope": "cashier",
        },
    }

    AUTH_ENDPOINTS = {
        "waiter_login": {
            "url": "http://localhost:6081/waiter/api/login",
            "method": "POST",
            "body": {"email": "juan.mesero@cafeteria.test", "password": "ChangeMe!123"},
        },
        "chef_login": {
            "url": "http://localhost:6081/chef/api/login",
            "method": "POST",
            "body": {"email": "carlos.chef@cafeteria.test", "password": "ChangeMe!123"},
        },
        "cashier_login": {
            "url": "http://localhost:6081/cashier/api/login",
            "method": "POST",
            "body": {"email": "pedro.cajero@cafeteria.test", "password": "ChangeMe!123"},
        },
    }

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.passed = []
        self.auth_tokens = {}

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

    def check_endpoint(
        self,
        name: str,
        url: str,
        method: str = "GET",
        body: Optional[dict] = None,
        headers: Optional[dict] = None,
        auth_required: bool = False,
        scope: str = "",
    ) -> tuple[bool, Optional[dict]]:
        """Check a single API endpoint."""
        self.log(f"Checking: {name} ({method} {url})", "INFO")

        import requests

        try:
            req_headers = {"Content-Type": "application/json"}
            if headers:
                req_headers.update(headers)

            # Add auth token if available for this scope
            if auth_required and scope in self.auth_tokens:
                req_headers["Authorization"] = f"Bearer {self.auth_tokens[scope]}"

            if method == "GET":
                response = requests.get(url, headers=req_headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=body, headers=req_headers, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=body, headers=req_headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=req_headers, timeout=10)
            else:
                self.errors.append(f"{name}: Unsupported HTTP method {method}")
                return False, None

            # Check response
            if response.status_code in [200, 201]:
                self.passed.append(f"{name}: HTTP {response.status_code}")
                self.log(f"Status: {response.status_code}", "PASS")

                try:
                    data = response.json()
                    return True, data
                except json.JSONDecodeError:
                    return True, None

            elif response.status_code == 401:
                if auth_required:
                    self.warnings.append(f"{name}: Authentication required (401)")
                    self.log("Authentication required", "WARNING")
                else:
                    self.errors.append(f"{name}: Unauthorized (401)")
                    self.log("Unauthorized", "ERROR")
                return False, None

            elif response.status_code == 403:
                self.errors.append(f"{name}: Forbidden (403) - Check permissions")
                self.log("Forbidden", "ERROR")
                return False, None

            elif response.status_code == 404:
                self.warnings.append(f"{name}: Not Found (404) - Endpoint may not exist")
                self.log("Not found", "WARNING")
                return False, None

            elif response.status_code >= 500:
                self.errors.append(f"{name}: Server Error ({response.status_code})")
                self.log(f"Server error: {response.status_code}", "ERROR")
                return False, None

            else:
                self.warnings.append(f"{name}: Unexpected status ({response.status_code})")
                self.log(f"Unexpected status: {response.status_code}", "WARNING")
                return False, None

        except requests.exceptions.ConnectionError:
            self.errors.append(f"{name}: Connection error - service may be down")
            self.log(f"Cannot connect to {url}", "ERROR")
            return False, None

        except requests.exceptions.Timeout:
            self.errors.append(f"{name}: Request timeout")
            self.log("Request timed out", "ERROR")
            return False, None

        except Exception as e:
            self.errors.append(f"{name}: {str(e)}")
            self.log(f"Error: {str(e)}", "ERROR")
            return False, None

    def check_docker_services(self) -> bool:
        """Check if required Docker services are running."""
        self.log("\nChecking Docker services...", "INFO")

        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            if result.returncode != 0:
                self.errors.append("Docker: Failed to list containers")
                self.log("Docker command failed", "ERROR")
                return False

            # Parse container statuses
            containers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        container = json.loads(line)
                        containers.append(container)
                    except json.JSONDecodeError:
                        pass

            # Check for required services
            required_services = [
                "pronto-client",
                "pronto-employee",
                "pronto-postgres",
                "pronto-redis",
            ]
            running_services = [c.get("Names", []) for c in containers]

            all_running = True
            for service in required_services:
                service_running = any(service in name for name in running_services)
                if service_running:
                    self.passed.append(f"Docker: {service} running")
                else:
                    self.errors.append(f"Docker: {service} NOT running")
                    all_running = False

            return all_running

        except subprocess.TimeoutExpired:
            self.errors.append("Docker: Command timeout")
            return False
        except FileNotFoundError:
            self.warnings.append("Docker: Not installed or not accessible")
            return True  # Skip Docker checks if not available

    def check_database(self) -> bool:
        """Check database connectivity."""
        self.log("\nChecking database connection...", "INFO")

        try:
            import psycopg2

            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="pronto",
                user="pronto",
                password="pronto",
                connect_timeout=5,
            )

            cursor = conn.cursor()

            # Check if tables exist
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
            """
            )
            table_count = cursor.fetchone()[0]

            if table_count > 0:
                self.passed.append(f"Database: {table_count} tables found")
                self.log(f"{table_count} tables found", "PASS")
            else:
                self.warnings.append("Database: No tables found")
                self.log("No tables found", "WARNING")

            # Check specific critical tables
            critical_tables = ["pronto_orders", "pronto_menu_items", "pronto_employees"]
            for table in critical_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                self.passed.append(f"Table {table}: {count} rows")

            cursor.close()
            conn.close()

            return True

        except ImportError:
            self.warnings.append("Database: psycopg2 not available for direct check")
            return True
        except psycopg2.OperationalError as e:
            self.errors.append(f"Database: Connection failed - {str(e)}")
            self.log(f"Database connection failed: {e}", "ERROR")
            return False
        except Exception as e:
            self.errors.append(f"Database: {str(e)}")
            return False

    def check_redis(self) -> bool:
        """Check Redis connectivity."""
        self.log("\nChecking Redis connection...", "INFO")

        try:
            import redis

            r = redis.Redis(host="localhost", port=6379, decode_responses=True, socket_timeout=5)

            # Test connection
            if r.ping():
                self.passed.append("Redis: Connection successful")
                self.log("Redis ping successful", "PASS")

                # Check key count
                key_count = len(r.keys("*"))
                self.passed.append(f"Redis: {key_count} keys in database")
                return True
            else:
                self.errors.append("Redis: Ping failed")
                return False

        except ImportError:
            self.warnings.append("Redis: redis-py not available for direct check")
            return True
        except redis.ConnectionError as e:
            self.errors.append(f"Redis: Connection failed - {str(e)}")
            self.log(f"Redis connection failed: {e}", "ERROR")
            return False

    def check_disk_space(self) -> bool:
        """Check disk space for Docker volumes."""
        self.log("\nChecking disk space...", "INFO")

        try:
            import shutil

            total, used, free = shutil.disk_usage("/")

            free_gb = free / (1024**3)

            if free_gb < 5:
                self.warnings.append(f"Disk space: Low ({free_gb:.1f}GB free)")
                self.log(f"Low disk space: {free_gb:.1f}GB", "WARNING")
            elif free_gb < 2:
                self.errors.append(f"Disk space: Critical ({free_gb:.1f}GB free)")
                self.log(f"Critical disk space: {free_gb:.1f}GB", "ERROR")
                return False
            else:
                self.passed.append(f"Disk space: OK ({free_gb:.1f}GB free)")
                self.log(f"Disk space OK: {free_gb:.1f}GB free", "PASS")

            return True

        except Exception as e:
            self.warnings.append(f"Disk space: Could not check - {str(e)}")
            return True

    def run_full_diagnostic(self, full: bool = False) -> dict:
        """Run the complete backend diagnostic."""
        print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}BACKEND DIAGNOSTIC TOOL{Colors.RESET}")
        print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")

        results = {
            "timestamp": datetime.now().isoformat(),
            "checks_performed": 0,
            "errors": [],
            "warnings": [],
            "passed": [],
            "overall_status": "UNKNOWN",
        }

        # System checks (always run)
        print(f"{Colors.BOLD}--- SYSTEM CHECKS ---{Colors.RESET}")
        self.check_docker_services()
        self.check_disk_space()

        if full:
            # Database and Redis
            print(f"\n{Colors.BOLD}--- DATABASE CHECKS ---{Colors.RESET}")
            self.check_database()
            self.check_redis()

        # API checks
        print(f"\n{Colors.BOLD}--- API ENDPOINT CHECKS ---{Colors.RESET}")

        # Public endpoints
        for name, info in self.API_ENDPOINTS.items():
            results["checks_performed"] += 1
            self.check_endpoint(
                name,
                info["url"],
                info["method"],
            )

        # Auth endpoints (to get tokens)
        print(f"\n{Colors.BOLD}--- AUTHENTICATION CHECKS ---{Colors.RESET}")

        for name, info in self.AUTH_ENDPOINTS.items():
            results["checks_performed"] += 1
            success, data = self.check_endpoint(
                name,
                info["url"],
                info["method"],
                body=info.get("body"),
            )

            # Extract scope from name (waiter_login -> waiter)
            scope = name.replace("_login", "")
            if success and data and data.get("access_token"):
                self.auth_tokens[scope] = data["access_token"]
                self.passed.append(f"Auth: {scope} login successful")

        # Scoped endpoints (with auth)
        if self.auth_tokens:
            print(f"\n{Colors.BOLD}--- SCOPED ENDPOINT CHECKS ---{Colors.RESET}")

            for name, info in self.SCOPED_ENDPOINTS.items():
                results["checks_performed"] += 1
                self.check_endpoint(
                    name,
                    info["url"],
                    info["method"],
                    auth_required=info.get("auth_required", False),
                    scope=info.get("scope", ""),
                )

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
        print(f"Checks Performed: {results['checks_performed']}")

        return results

    def save_results(self, results: dict, filepath: Optional[str] = None):
        """Save diagnostic results to a JSON file."""
        if filepath is None:
            filepath = (
                f"tests/diagnostic/api/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

        self.log(f"Results saved to {filepath}", "INFO")


def main():
    parser = argparse.ArgumentParser(
        description="Backend Diagnostic Tool - Check API, Database, and Services"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    parser.add_argument(
        "--full", "-f", action="store_true", help="Run full diagnostic including DB checks"
    )
    parser.add_argument("--output", "-o", help="Output file for JSON results")
    parser.add_argument("--quick", action="store_true", help="Quick check - only API endpoints")

    args = parser.parse_args()

    diagnostic = BackendDiagnostic(verbose=args.verbose)

    if args.quick:
        results = diagnostic.run_full_diagnostic(full=False)
    else:
        results = diagnostic.run_full_diagnostic(full=args.full)
        diagnostic.save_results(results, args.output)

    # Exit with appropriate code
    if diagnostic.errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
