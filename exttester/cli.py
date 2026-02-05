import click
from pathlib import Path

from .validator import ExtensionValidator, validate_all_extensions, BrowserType
from .bulk_runner import run_bulk_tests, normalize_browsers
from .report_generator import generate_reports, ReportGenerator
from .summary import print_summary
from .extension_tester import ExtensionTester
from .api_checker import APICompatibilityChecker
from .gui import main as run_gui
from .pipeline import TestingPipeline, PipelineReporter
from .store_checker import StoreComplianceChecker
from .runtime_tester import run_runtime_tests


@click.group()
def cli():
    """Browser Extension Tester - Validate and test browser extensions"""
    pass


@cli.command()
def gui():
    """Launch the graphical user interface"""
    click.echo("Launching Browser Extension Tester GUI...")
    run_gui()


@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--browser', type=click.Choice(['chrome', 'firefox', 'edge', 'opera', 'all'], case_sensitive=False), 
              default='all', help='Browser to test for (default: all)')
def test(path, browser):
    """Test a single extension folder"""
    ext_path = Path(path)

    if browser.lower() == 'all':
        browsers = [BrowserType.CHROME, BrowserType.FIREFOX, BrowserType.EDGE, BrowserType.OPERA]
    else:
        browser_map = {
            'chrome': BrowserType.CHROME,
            'firefox': BrowserType.FIREFOX,
            'edge': BrowserType.EDGE,
            'opera': BrowserType.OPERA
        }
        browsers = [browser_map[browser.lower()]]

    click.echo(f"\n{'='*70}")
    click.echo(f"Testing Extension: {ext_path.name}")
    click.echo(f"Browsers: {', '.join(browsers)}")
    click.echo(f"{'='*70}\n")

    for target_browser in browsers:
        click.secho(f"\n[*] Testing for {target_browser}:", bold=True)
        validator = ExtensionValidator(target_browser)
        is_valid, errors, warnings = validator.validate_extension(str(ext_path), target_browser)
        compatible = validator.detected_browsers

        if is_valid:
            click.secho("[OK] Status: VALID", fg='green', bold=True)
        else:
            click.secho("[FAIL] Status: INVALID", fg='red', bold=True)

        if compatible:
            click.secho(f"     Compatible with: {', '.join(compatible)}", fg='cyan')

        if errors:
            click.secho(f"\n     Errors ({len(errors)}):", fg='red', bold=True)
            for i, error in enumerate(errors, 1):
                click.echo(f"       {i}. {error}")

        if warnings:
            click.secho(f"\n     Warnings ({len(warnings)}):", fg='yellow', bold=True)
            for i, warning in enumerate(warnings, 1):
                click.echo(f"       {i}. {warning}")

        if not errors and not warnings:
            click.secho("\n     [OK] No issues found!", fg='green')

    click.echo(f"\n{'='*70}\n")


@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--browser', type=click.Choice(['chrome', 'firefox', 'edge', 'opera', 'all'], case_sensitive=False),
              default='all', help='Browser to test for (default: all)')
def test_all(path, browser):
    """Test all extensions in a directory"""
    dir_path = Path(path)

    if browser.lower() == 'all':
        browsers = [BrowserType.CHROME, BrowserType.FIREFOX, BrowserType.EDGE, BrowserType.OPERA]
    else:
        browser_map = {
            'chrome': BrowserType.CHROME,
            'firefox': BrowserType.FIREFOX,
            'edge': BrowserType.EDGE,
            'opera': BrowserType.OPERA
        }
        browsers = [browser_map[browser.lower()]]

    click.echo(f"\n{'='*70}")
    click.echo(f"Testing All Extensions in: {dir_path}")
    click.echo(f"Browsers: {', '.join(browsers)}")
    click.echo(f"{'='*70}\n")

    results = validate_all_extensions(str(dir_path))

    if not results:
        click.secho("No extensions found in directory.", fg='yellow')
        return

    total = len(results)
    valid = sum(1 for _, (is_valid, _, _) in results.items() if is_valid)
    total_errors = sum(len(errors) for _, (_, errors, _) in results.items())
    total_warnings = sum(len(warnings) for _, (_, _, warnings) in results.items())

    click.secho(f"\nTotal Extensions: {total}", bold=True)
    click.secho(f"Valid Extensions: {valid}", fg='green')
    click.secho(f"Total Errors: {total_errors}", fg='red')
    click.secho(f"Total Warnings: {total_warnings}", fg='yellow')

    click.echo(f"\n{'-'*70}\n")
    for ext_name in sorted(results.keys()):
        is_valid, errors, warnings = results[ext_name]

        if is_valid:
            click.secho(f"[OK] {ext_name}", fg='green', bold=True)
        else:
            click.secho(f"[FAIL] {ext_name}", fg='red', bold=True)

        if errors:
            for error in errors:
                click.secho(f"      [FAIL] {error}", fg='red')

        if warnings:
            for warning in warnings:
                click.secho(f"      [WARN] {warning}", fg='yellow')

        if not errors and not warnings:
            click.echo("      No issues found")

        click.echo()

    click.echo(f"{'='*70}\n")


def _run_bulk(path, browsers, report_dir, runtime, urls):
    selected = list(browsers)
    browsers = normalize_browsers(selected)
    click.echo(f"\n{'='*70}")
    click.echo(f"Bulk Testing Extensions Under: {Path(path)}")
    click.echo(f"Browsers: {', '.join(browsers)}")
    click.echo(f"Report directory: {report_dir}")
    click.echo(f"{'='*70}\n")

    report_data = run_bulk_tests(
        path,
        selected,
        report_path=None,
        run_runtime=runtime,
        test_urls=list(urls),
        screenshot_dir=report_dir,
    )
    print_summary(report_data, browsers)
    outputs = generate_reports(report_data, report_dir)
    click.echo(f"\nReports saved to:")
    click.echo(f"  HTML: {outputs['html']}")
    click.echo(f"  JSON: {outputs['json']}")
    click.echo(f"  CSV:  {outputs['csv']}")
    if outputs.get("pdf"):
        click.echo(f"  PDF:  {outputs['pdf']}")


@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--browser', 'browsers', multiple=True,
              type=click.Choice(['chrome', 'firefox', 'edge', 'opera', 'all'], case_sensitive=False),
              default=('all',), help='Browsers to test (default: all)')
@click.option('--report-dir', default='reports', show_default=True,
              help='Directory to write reports (JSON/HTML/CSV/PDF)')
@click.option('--runtime', is_flag=True, help='Run runtime browser tests (Playwright required)')
@click.option('--urls', multiple=True, default=('https://www.google.com', 'https://www.github.com'),
              show_default=True, help='Test URLs for runtime mode')
def bulk(path, browsers, report_dir, runtime, urls):
    """Bulk test all extensions under a root folder"""
    _run_bulk(path, browsers, report_dir, runtime, urls)


@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--browser', 'browsers', multiple=True,
              type=click.Choice(['chrome', 'firefox', 'edge', 'opera', 'all'], case_sensitive=False),
              default=('all',), help='Browsers to test (default: all)')
@click.option('--report-dir', default='reports', show_default=True,
              help='Directory to write reports (JSON/HTML/CSV/PDF)')
def scan(path, browsers, report_dir):
    """Scan a folder of extensions and generate reports"""
    _run_bulk(path, browsers, report_dir, False, ())


@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--browser', 'browsers', multiple=True,
              type=click.Choice(['chrome', 'firefox', 'edge', 'opera', 'all'], case_sensitive=False),
              default=('all',), help='Browsers to test (default: all)')
@click.option('--report-dir', default='reports', show_default=True,
              help='Directory to write reports (JSON/HTML/CSV/PDF)')
def report(path, browsers, report_dir):
    """Run a scan and generate reports (alias of scan)"""
    _run_bulk(path, browsers, report_dir, False, ())


@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--browser', multiple=True,
              type=click.Choice(['chrome', 'edge', 'firefox'], case_sensitive=False),
              default=('chrome',), help='Browsers to test (default: chrome)')
@click.option('--url', 'urls', multiple=True,
              default=('https://www.google.com', 'https://www.github.com'),
              show_default=True, help='Test URLs')
def runtime_test(path, browser, urls):
    """Run runtime browser tests (Playwright)"""
    ext_path = Path(path)
    click.echo(f"\n{'='*70}")
    click.echo(f"Runtime Testing: {ext_path.name}")
    click.echo(f"Browsers: {', '.join(browser)}")
    click.echo(f"URLs: {', '.join(urls)}")
    click.echo(f"{'='*70}\n")

    results = run_runtime_tests(str(ext_path), list(browser), list(urls))
    if results.get("error"):
        click.secho(f"[FAIL] {results.get('error')}", fg='red')
        return

    for b, data in results.items():
        if isinstance(data, dict) and data.get('skipped'):
            click.secho(f"{b}: {data.get('skipped')}", fg='yellow')
            continue
        click.secho(f"\n{b}:", bold=True)
        for t in data.get('timings', []) or []:
            click.echo(f"  {t.get('url')}: {t.get('load_ms')} ms")
        if data.get('console_errors'):
            click.secho("  Console Errors:", fg='red')
            for e in data['console_errors']:
                click.echo(f"    {e}")
        else:
            click.echo("  No console errors.")


@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--format', type=click.Choice(['html', 'json', 'csv', 'markdown'], case_sensitive=False),
              default='html', help='Report format (default: html)')
def advanced_test(path, format):
    """Run advanced extension tests (popup, content scripts, background, APIs)"""
    ext_path = Path(path)

    click.echo(f"\n{'='*70}")
    click.echo(f"Advanced Testing: {ext_path.name}")
    click.echo(f"{'='*70}\n")

    tester = ExtensionTester(str(ext_path))
    test_results = tester.run_all_tests()

    click.secho("Extension Component Tests:", bold=True)

    test_details = {}
    for test_name, (passed, issues) in test_results.items():
        status = "PASS" if passed else "FAIL"
        color = 'green' if passed else 'red'
        click.secho(f"  {test_name.upper()}: {status}", fg=color)

        if issues:
            for issue in issues:
                click.echo(f"    {issue}")

        test_details[test_name] = {
            'status': 'PASS' if passed else 'FAIL',
            'message': f"Component: {test_name}",
            'errors': [i for i in issues if i.startswith('[FAIL]') or 'Error' in i],
            'warnings': [i for i in issues if i.startswith('[WARN]') or 'Warn' in i]
        }

    click.secho("\nAPI Compatibility Check:", bold=True)

    api_checker = APICompatibilityChecker(str(ext_path))
    api_issues = api_checker.check_api_usage()

    if api_issues:
        for issue in api_issues:
            click.echo(f"  {issue}")
    else:
        click.secho("  [OK] No API compatibility issues found", fg='green')

    test_details['api_compatibility'] = {
        'status': 'PASS' if not api_issues else 'FAIL',
        'message': 'API Compatibility Check',
        'errors': [i for i in api_issues if 'FAIL' in i],
        'warnings': [i for i in api_issues if 'WARN' in i]
    }

    click.secho(f"\nGenerating {format.upper()} Report...", bold=True)

    report_gen = ReportGenerator(test_details, str(ext_path))

    if format.lower() == 'html':
        report_path = report_gen.generate_html_report()
    elif format.lower() == 'json':
        report_path = report_gen.generate_json_report()
    elif format.lower() == 'csv':
        report_path = report_gen.generate_csv_report()
    else:
        report_path = report_gen.generate_markdown_report()

    click.secho(f"  [OK] Report saved to: {report_path}", fg='green')
    click.echo(f"\n{'='*70}\n")


@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--browser', type=click.Choice(['chrome', 'firefox', 'edge', 'opera', 'all'], case_sensitive=False),
              default='all', help='Check compatibility for browser')
def check_apis(path, browser):
    """Check for API compatibility issues"""
    ext_path = Path(path)

    if browser.lower() == 'all':
        browsers = [BrowserType.CHROME, BrowserType.FIREFOX, BrowserType.EDGE, BrowserType.OPERA]
    else:
        browser_map = {
            'chrome': BrowserType.CHROME,
            'firefox': BrowserType.FIREFOX,
            'edge': BrowserType.EDGE,
            'opera': BrowserType.OPERA
        }
        browsers = [browser_map[browser.lower()]]

    click.echo(f"\n{'='*70}")
    click.echo(f"API Compatibility Check: {ext_path.name}")
    click.echo(f"Browsers: {', '.join(browsers)}")
    click.echo(f"{'='*70}\n")

    api_checker = APICompatibilityChecker(str(ext_path))
    report = api_checker.generate_compatibility_report(browsers)

    for browser_name, issues in report.items():
        if issues:
            click.secho(f"\n{browser_name.upper()}:", bold=True, fg='yellow')
            for issue in issues:
                click.echo(f"  {issue}")
        else:
            click.secho(f"\n{browser_name.upper()}: [OK] No issues", bold=True, fg='green')

    click.echo(f"\n{'='*70}\n")


@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--store', type=click.Choice(['chrome', 'edge', 'firefox', 'all'], case_sensitive=False),
              default='all', help='Store to check (default: all)')
def store_check(path, store):
    """Check store compliance and privacy policy readiness"""
    ext_path = Path(path)
    checker = StoreComplianceChecker(str(ext_path))
    report = checker.check_all()

    stores = ['chrome', 'edge', 'firefox'] if store.lower() == 'all' else [store.lower()]

    click.echo(f"\n{'='*70}")
    click.echo(f"Store Compliance Check: {ext_path.name}")
    click.echo(f"Stores: {', '.join([s.upper() for s in stores])}")
    click.echo(f"{'='*70}\n")

    for store_name in stores:
        store_data = report.get(store_name, {})
        score = store_data.get('score', 0)
        errors = store_data.get('errors', [])
        warnings = store_data.get('warnings', [])

        score_label = f"{store_name.upper()} Store Readiness: {score}%"
        color = 'green' if score >= 85 else 'yellow' if score >= 70 else 'red'
        click.secho(score_label, fg=color, bold=True)

        if errors:
            click.secho("  Errors:", fg='red', bold=True)
            for err in errors:
                click.echo(f"    - {err}")
        if warnings:
            click.secho("  Warnings:", fg='yellow', bold=True)
            for warn in warnings:
                click.echo(f"    - {warn}")
        if not errors and not warnings:
            click.secho("  [OK] No issues found", fg='green')

        click.echo("")

    privacy = report.get('privacy', {})
    privacy_warnings = privacy.get('warnings', [])
    data_indicators = privacy.get('data_indicators', [])

    click.secho("Privacy Policy Scan:", bold=True)
    if data_indicators:
        click.echo(f"  Data indicators: {len(data_indicators)}")
        for indicator in data_indicators[:10]:
            click.echo(f"    - {indicator}")
        if len(data_indicators) > 10:
            click.echo(f"    - ... +{len(data_indicators) - 10} more")
    else:
        click.echo("  Data indicators: none")

    policy_file = privacy.get('policy_file')
    policy_url = privacy.get('policy_url')
    if policy_file:
        click.echo(f"  Policy file: {policy_file}")
    if policy_url:
        click.echo(f"  Policy URL: {policy_url}")

    if privacy_warnings:
        click.secho("  Warnings:", fg='yellow', bold=True)
        for warn in privacy_warnings:
            click.echo(f"    - {warn}")
    else:
        click.secho("  [OK] Privacy policy check passed", fg='green')

    click.echo(f"\n{'='*70}\n")


@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--browser', type=click.Choice(['chrome', 'firefox', 'edge', 'opera', 'all'], case_sensitive=False),
              default='all', help='Browsers to test (default: all)')
@click.option('--format', type=click.Choice(['text', 'json', 'html'], case_sensitive=False),
              default='text', help='Output format (default: text)')
def pipeline(path, browser, format):
    """Run complete 6-stage testing pipeline"""
    ext_path = Path(path)

    browser_list = ['chrome', 'firefox', 'edge'] if browser.lower() == 'all' else [browser.lower()]

    click.secho("\n" + "="*70, bold=True)
    click.secho("BROWSER EXTENSION TESTING PIPELINE", bold=True, fg='cyan')
    click.secho("="*70, bold=True)

    click.echo(f"\nExtension: {ext_path.name}")
    click.echo(f"Path: {ext_path}")
    click.echo(f"Browsers: {', '.join([b.upper() for b in browser_list])}")
    click.echo(f"Output: {format.upper()}")

    click.secho("\nTesting Stages:", bold=True)
    click.echo("  1) Static File Checks")
    click.echo("  2) Manifest Validation")
    click.echo("  3) Lint & Syntax Check")
    click.echo("  4) Browser Load Test")
    click.echo("  5) Runtime Behavior Test")
    click.echo("  6) Compatibility Analysis")

    click.secho("\nRunning tests...\n", bold=True)

    pipeline_runner = TestingPipeline(str(ext_path), browser_list)
    results = pipeline_runner.run()

    click.echo(PipelineReporter.get_summary(results))

    errors_found = False
    for stage in results['stages']:
        if isinstance(stage, dict) and stage.get('errors'):
            if not errors_found:
                click.secho("\nERRORS FOUND:\n", bold=True, fg='red')
                errors_found = True

            stage_name = stage.get('name', f"Stage {stage.get('stage_num')}")
            click.secho(f"  {stage_name}:", fg='red')

            for error in stage['errors']:
                click.echo(f"    - {error}")

    if format.lower() == 'json':
        import json
        report_file = ext_path / 'pipeline_results.json'
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        click.secho(f"\n[OK] Results saved to: {report_file}", fg='green', bold=True)

    exit_code = 0 if results['summary']['success'] else 1
    return exit_code


if __name__ == '__main__':
    cli()
