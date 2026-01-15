#!/usr/bin/env python3
"""
Comprehensive QA Test Runner for JobPilot AI Backend.
Runs all test suites and generates quality score report.
"""
import subprocess
import sys
import time
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

# Fix Windows Unicode encoding issues
def _safe_console():
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        # Never crash the runner because of console encoding
        pass

_safe_console()


class QATestRunner:
    """Comprehensive QA test runner with scoring."""
    
    def __init__(self):
        self.results = {
            "total_score": 0,
            "max_score": 100,
            "test_results": {},
            "coverage": 0,
            "start_time": time.time(),
            "end_time": None
        }
        
        self.test_suites = {
            "config": {"weight": 5, "description": "Test Configuration & Environment"},
            "auth": {"weight": 15, "description": "Authentication & Authorization"},
            "security": {"weight": 15, "description": "Security & Input Validation"},
            "resume": {"weight": 10, "description": "Resume Upload & Processing"},
            "ai_features": {"weight": 25, "description": "AI Extensions (Resume/Interview/Skills)"},
            "jobs_matching": {"weight": 15, "description": "Job Search & Matching"},
            "notifications": {"weight": 5, "description": "Notifications & Email"},
            "performance": {"weight": 10, "description": "Performance & Load Testing"},
            "e2e": {"weight": 0, "description": "End-to-End Workflow Tests"}
        }
    
    def run_command(self, command: List[str], timeout: int = 300) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            print(f"Running: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(__file__).parent
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)
    
    def discover_test_files(self, pattern: str) -> List[str]:
        """Discover test files matching pattern using glob (Windows-safe)."""
        from pathlib import Path
        import glob
        
        test_dir = Path(__file__).parent / "tests"
        discovered = []
        
        # Split multiple patterns
        patterns = pattern.split()
        for pat in patterns:
            # Remove 'tests/' prefix if present since we're already in test_dir
            if pat.startswith("tests/"):
                pat = pat[6:]
            
            # Convert pattern to absolute path for glob
            full_pattern = str(test_dir / pat)
            matches = glob.glob(full_pattern)
            
            # Also try without wildcard for exact matches
            if not matches and '*' not in pat:
                exact_path = test_dir / pat
                if exact_path.exists():
                    matches = [str(exact_path)]
            
            discovered.extend(matches)
        
        # Remove duplicates and return relative paths
        unique_files = list(set(discovered))
        return [str(Path(f).relative_to(Path(__file__).parent)) for f in unique_files if Path(f).exists()]
    
    def run_test_suite(self, suite_name: str, test_patterns: str) -> Dict:
        """Run a specific test suite and return results."""
        print(f"\n{'='*60}")
        print(f"Running {suite_name} Tests")
        print(f"{'='*60}")
        
        # Set test environment
        env = os.environ.copy()
        env.update({
            "ENVIRONMENT": "test",
            "DATABASE_URL": "sqlite+aiosqlite:///./test_jobpilot.db",
            "JWT_SECRET": "test-secret-key-for-qa-testing",
            "EMAIL_ENABLED": "false",
            "REDIS_URL": "redis://localhost:6379/1",
            "LOG_LEVEL": "ERROR"
        })
        
        # Discover actual test files (Windows-safe)
        test_files = self.discover_test_files(test_patterns)
        
        if not test_files:
            print(f"No test files found for {suite_name} (pattern: {test_patterns})")
            return {
                "suite": suite_name,
                "description": self.test_suites[suite_name]["description"],
                "weight": self.test_suites[suite_name]["weight"],
                "score": 0,
                "max_score": self.test_suites[suite_name]["weight"],
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "skipped": 0,
                "total": 0,
                "success_rate": 0,
                "duration": 0,
                "exit_code": 0,
                "stdout": "",
                "stderr": f"No test files found for pattern: {test_patterns}"
            }
        
        print(f"Discovered {len(test_files)} test file(s): {', '.join(test_files)}")
        
        # Run pytest with coverage
        cmd = [
            sys.executable, "-m", "pytest"
        ] + test_files + [
            "-v",
            "--tb=short",
            "--timeout=300",
            f"--cov=app",
            "--cov-report=term-missing",
            "--cov-report=json:coverage.json",
            "--json-report",
            f"--json-report-file={suite_name}_report.json"
        ]
        
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command(cmd)
        duration = time.time() - start_time
        
        # Parse results
        passed = stdout.count(" PASSED")
        failed = stdout.count(" FAILED")
        errors = stdout.count(" ERROR")
        skipped = stdout.count(" SKIPPED")
        
        # Calculate score
        total_tests = passed + failed + errors
        if total_tests > 0:
            success_rate = passed / total_tests
            suite_score = int(success_rate * self.test_suites[suite_name]["weight"])
        else:
            success_rate = 0
            suite_score = 0
        
        result = {
            "suite": suite_name,
            "description": self.test_suites[suite_name]["description"],
            "weight": self.test_suites[suite_name]["weight"],
            "score": suite_score,
            "max_score": self.test_suites[suite_name]["weight"],
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "total": total_tests,
            "success_rate": success_rate,
            "duration": duration,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr
        }
        
        # Print summary
        status = "PASSED" if exit_code == 0 else "FAILED"
        print(f"\n{status} {suite_name}: {suite_score}/{self.test_suites[suite_name]['weight']} points")
        print(f"   Tests: {passed} passed, {failed} failed, {errors} errors, {skipped} skipped")
        print(f"   Duration: {duration:.2f}s")
        
        return result
    
    def run_all_tests(self, quick: bool = False) -> Dict:
        """Run all test suites."""
        print("Starting Comprehensive QA Test Suite")
        print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test suite configurations
        test_configs = [
            ("config", "test_config.py"),
            ("auth", "test_auth.py test_auth_comprehensive.py"),
            ("security", "test_security.py"),
            ("resume", "test_resume_comprehensive.py"),
            ("ai_features", "test_*ai*.py test_*interview*.py test_*skill*.py"),
            ("jobs_matching", "test_job_sources_comprehensive.py test_matcher.py test_apply_kit.py"),
            ("notifications", "test_notifications.py test_tracker_notifications.py"),
        ]
        
        if not quick:
            test_configs.append(("performance", "test_performance.py"))
        
        # Run each test suite
        for suite_name, pattern in test_configs:
            if suite_name in self.test_suites:
                result = self.run_test_suite(suite_name, pattern)
                self.results["test_results"][suite_name] = result
                self.results["total_score"] += result["score"]
        
        # Run E2E tests if not quick mode
        if not quick:
            print(f"\n{'='*60}")
            print("[E2E] Running End-to-End Tests")
            print(f"{'='*60}")
            
            e2e_result = self.run_test_suite("e2e", "test_e2e_workflow.py")
            
            # E2E failures MUST reduce score
            if e2e_result["exit_code"] != 0 or e2e_result["failed"] > 0:
                print(f"[CRITICAL] E2E tests failed: {e2e_result['failed']} failures")
                # Deduct 10 points for E2E failure
                self.results["total_score"] = max(0, self.results["total_score"] - 10)
                self.results["e2e_status"] = "FAILED"
            else:
                print("[SUCCESS] E2E tests passed!")
                self.results["e2e_status"] = "PASSED"
        
        # Get final coverage
        self.get_coverage_report()
        
        self.results["end_time"] = time.time()
        return self.results
    
    def get_coverage_report(self):
        """Get code coverage report."""
        try:
            if os.path.exists("coverage.json"):
                with open("coverage.json", "r") as f:
                    coverage_data = json.load(f)
                    self.results["coverage"] = coverage_data.get("totals", {}).get("percent_covered", 0)
        except Exception as e:
            print(f"⚠️ Could not read coverage report: {e}")
            self.results["coverage"] = 0
    
    def generate_report(self) -> str:
        """Generate comprehensive QA report."""
        total_duration = self.results["end_time"] - self.results["start_time"]
        
        report = f"""
# 🎯 JobPilot AI Backend - QA Test Report

**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Duration**: {total_duration:.2f} seconds
**Total Score**: {self.results['total_score']}/{self.results['max_score']} ({self.results['total_score']/self.results['max_score']*100:.1f}%)
**Code Coverage**: {self.results['coverage']:.1f}%

## 📊 Test Suite Results

| Suite | Score | Max | Success Rate | Tests | Duration |
|-------|-------|-----|--------------|-------|----------|
"""
        
        for suite_name, result in self.results["test_results"].items():
            status = "✅" if result["exit_code"] == 0 else "❌"
            report += f"| {status} {result['description']} | {result['score']} | {result['max_score']} | {result['success_rate']:.1%} | {result['total']} | {result['duration']:.1f}s |\n"
        
        # Quality assessment
        score_pct = self.results['total_score'] / self.results['max_score'] * 100
        
        report += f"""

## Quality Assessment

"""
        
        if score_pct >= 90:
            report += "**[EXCELLENT]** - Production Ready!"
        elif score_pct >= 80:
            report += "**[GOOD]** - Minor improvements needed"
        elif score_pct >= 70:
            report += "**[ACCEPTABLE]** - Some issues to address"
        elif score_pct >= 60:
            report += "**[NEEDS WORK]** - Significant improvements required"
        else:
            report += "**[CRITICAL]** - Major issues must be fixed"
        
        report += f"""

### Quality Metrics
- **Test Coverage**: {self.results['coverage']:.1f}% (Target: 80%+)
- **Test Success Rate**: {self.calculate_overall_success_rate():.1%}
- **Performance**: {'✅ Passed' if self.check_performance_passed() else '❌ Failed'}
- **Security**: {'✅ Passed' if self.check_security_passed() else '❌ Failed'}

### Recommendations
"""
        
        recommendations = self.generate_recommendations()
        for rec in recommendations:
            report += f"- {rec}\n"
        
        # Detailed results
        report += "\n## 📋 Detailed Results\n\n"
        
        for suite_name, result in self.results["test_results"].items():
            if result["failed"] > 0 or result["errors"] > 0:
                report += f"### ❌ {result['description']} Issues\n"
                report += f"- Failed: {result['failed']}\n"
                report += f"- Errors: {result['errors']}\n"
                if result["stderr"]:
                    report += f"- Error Details: {result['stderr'][:500]}...\n"
                report += "\n"
        
        return report
    
    def calculate_overall_success_rate(self) -> float:
        """Calculate overall test success rate."""
        total_tests = sum(r["total"] for r in self.results["test_results"].values())
        total_passed = sum(r["passed"] for r in self.results["test_results"].values())
        
        if total_tests > 0:
            return total_passed / total_tests
        return 0.0
    
    def check_performance_passed(self) -> bool:
        """Check if performance tests passed."""
        perf_result = self.results["test_results"].get("performance")
        return perf_result and perf_result["exit_code"] == 0
    
    def check_security_passed(self) -> bool:
        """Check if security tests passed."""
        sec_result = self.results["test_results"].get("security")
        return sec_result and sec_result["exit_code"] == 0
    
    def generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        if self.results["coverage"] < 80:
            recommendations.append(f"Increase test coverage from {self.results['coverage']:.1f}% to 80%+")
        
        for suite_name, result in self.results["test_results"].items():
            if result["success_rate"] < 0.9:
                recommendations.append(f"Fix failing tests in {result['description']} ({result['failed']} failed)")
        
        if not self.check_performance_passed():
            recommendations.append("Address performance test failures - check response times and resource usage")
        
        if not self.check_security_passed():
            recommendations.append("Fix security vulnerabilities identified in security tests")
        
        if self.results["total_score"] < 80:
            recommendations.append("Overall score below 80% - prioritize fixing critical test failures")
        
        if not recommendations:
            recommendations.append("Excellent work! All tests passing. Consider adding more edge case tests.")
        
        return recommendations
    
    def save_report(self, filename: str = "qa_report.md"):
        """Save the QA report to file."""
        report = self.generate_report()
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"QA Report saved to: {filename}")
        return filename


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run comprehensive QA tests for JobPilot AI Backend")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only (skip performance tests)")
    parser.add_argument("--suite", type=str, help="Run specific test suite only")
    parser.add_argument("--report", type=str, default="qa_report.md", help="Report output filename")
    
    args = parser.parse_args()
    
    runner = QATestRunner()
    
    if args.suite:
        # Run specific suite
        if args.suite in runner.test_suites:
            # Get the configured pattern for this suite
            test_configs = {
                "config": "test_config.py",
                "auth": "test_auth.py test_auth_comprehensive.py",
                "security": "test_security.py",
                "resume": "test_resume_comprehensive.py",
                "ai_features": "test_*ai*.py test_*interview*.py test_*skill*.py",
                "jobs_matching": "test_job_sources_comprehensive.py test_matcher.py test_apply_kit.py",
                "notifications": "test_notifications.py test_tracker_notifications.py",
                "performance": "test_performance.py",
                "e2e": "test_e2e_workflow.py"
            }
            
            pattern = test_configs.get(args.suite, f"tests/test_{args.suite}*.py")
            result = runner.run_test_suite(args.suite, pattern)
            print(f"\nSuite Result: {result['score']}/{result['max_score']} points")
        else:
            print(f"❌ Unknown test suite: {args.suite}")
            print(f"Available suites: {', '.join(runner.test_suites.keys())}")
            sys.exit(1)
    else:
        # Run all tests
        results = runner.run_all_tests(quick=args.quick)
        
        # Generate and save report
        report_file = runner.save_report(args.report)
        
        # Print summary
        print(f"\n{'='*60}")
        print("FINAL QA RESULTS")
        print(f"{'='*60}")
        print(f"Total Score: {results['total_score']}/{results['max_score']} ({results['total_score']/results['max_score']*100:.1f}%)")
        print(f"Coverage: {results['coverage']:.1f}%")
        print(f"Duration: {results['end_time'] - results['start_time']:.2f}s")
        print(f"Report: {report_file}")
        
        # Exit with appropriate code
        if results['total_score'] >= 80:
            print("QA PASSED - Ready for production!")
            sys.exit(0)
        else:
            print("QA FAILED - Improvements needed")
            sys.exit(1)


if __name__ == "__main__":
    main()