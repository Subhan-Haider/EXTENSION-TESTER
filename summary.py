from typing import Dict, List


def print_summary(report: Dict, browsers: List[str]) -> None:
    print("\n===== TEST SUMMARY =====")
    if not report.get("extensions"):
        print("No extensions found.")
        return

    name_width = max(len(name) for name in report["extensions"].keys())
    name_width = max(name_width, 9)

    header = f"{'Extension':{name_width}}"
    for browser in browsers:
        header += f"  {browser:8}"
    print(header)
    print("-" * len(header))

    for ext_name, data in report["extensions"].items():
        line = f"{ext_name:{name_width}}"
        for browser in browsers:
            result = data["browsers"].get(browser, {})
            status = "PASS" if result.get("valid") else "FAIL"
            line += f"  {status:8}"
        print(line)
