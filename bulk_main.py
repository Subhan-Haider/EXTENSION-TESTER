import argparse
from pathlib import Path

from bulk_runner import run_bulk_tests, normalize_browsers
from report_generator import generate_reports
from summary import print_summary


def main():
    parser = argparse.ArgumentParser(description="Bulk browser extension tester")
    parser.add_argument("--folder", required=True, help="Root folder containing extensions")
    parser.add_argument(
        "--browsers",
        nargs="+",
        default=["all"],
        choices=["chrome", "edge", "firefox", "opera", "all"],
        help="Browsers to test (default: all)",
    )
    parser.add_argument(
        "--report-dir",
        default=str(Path("reports")),
        help="Directory to write reports (JSON/HTML/CSV)",
    )
    parser.add_argument(
        "--runtime",
        action="store_true",
        help="Run runtime browser tests (Playwright required)",
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        default=["https://www.google.com", "https://www.github.com"],
        help="Test URLs for runtime mode",
    )
    args = parser.parse_args()

    report = run_bulk_tests(
        args.folder,
        args.browsers,
        report_path=None,
        run_runtime=args.runtime,
        test_urls=args.urls,
        screenshot_dir=args.report_dir,
    )
    browsers = normalize_browsers(args.browsers)
    print_summary(report, browsers)
    outputs = generate_reports(report, args.report_dir)
    print(f"\nReports saved to: {outputs['html']}, {outputs['json']}, {outputs['csv']}")


if __name__ == "__main__":
    main()
