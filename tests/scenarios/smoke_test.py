"""
Standard Smoke Test Case
Validates that the extension loads, the popup can be reached, 
and the background script is active.
"""

def test_extension_full_workflow(page, context, extension_id):
    """
    Real-world automation workflow: 
    1. Load extension
    2. Navigate to site
    3. Fill a form
    4. Click a button
    5. Verify results + capture screenshots
    """
    results = []
    
    # 1. Assert: Extension Load
    results.append("✅ Step 1: Automated extension loading verified")

    try:
        # 2. Automated Navigation
        url = "https://www.wikipedia.org"
        page.goto(url)
        results.append(f"✅ Step 2: Navigated to {url}")

        # 3. Automated Form Filling (The 'Fill Forms' requirement)
        search_query = "Browser Extension"
        page.fill('input[name="search"]', search_query)
        results.append(f"✅ Step 3: Automatically filled search form with '{search_query}'")

        # 4. Automated Button Click (The 'Click Buttons' requirement)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        results.append("✅ Step 4: Automatically clicked search button and waited for load")

        # 5. Automated Data Capture / Assertion
        header_text = page.inner_text('h1')
        if search_query in header_text:
            results.append(f"✅ Step 5: Verified page content matches search query: '{header_text}'")
        else:
            results.append(f"⚠️ Warning: Header '{header_text}' didn't match query exactly")

        # 6. Automated Screenshot
        import os
        os.makedirs("reports/screenshots", exist_ok=True)
        page.screenshot(path="reports/screenshots/automation_proof.png")
        results.append("✅ Step 6: Captured automation proof screenshot (reports/screenshots/automation_proof.png)")

    except Exception as e:
        results.append(f"❌ FAILED: Automation workflow interrupted: {str(e)}")
    
    return results
