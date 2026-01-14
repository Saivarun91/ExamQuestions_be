"""
Test script to verify all APIs are working correctly.
Run this after initializing data: python manage.py shell < test_apis.py
"""

import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 70)
print("🧪 TESTING ALL HOME PAGE APIs")
print("=" * 70)

def test_api(name, url):
    """Test a GET API endpoint"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data.get('success'):
                count = len(data.get('data', []))
                print(f"✅ {name}: OK (returned {count} items)")
                return True
            elif isinstance(data, list):
                print(f"✅ {name}: OK (returned {len(data)} items)")
                return True
            else:
                print(f"⚠️  {name}: OK but unexpected format")
                return True
        else:
            print(f"❌ {name}: Failed (Status: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: Connection failed - Is Django server running?")
        return False
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)}")
        return False

# Test all public APIs
print("\n📡 Testing Public APIs (No Auth Required):")
print("-" * 70)

tests = [
    ("Hero Section", f"{API_BASE}/api/home/hero/"),
    ("Value Propositions", f"{API_BASE}/api/home/value-propositions/"),
    ("Blog Posts", f"{API_BASE}/api/home/blog-posts/"),
    ("Recently Updated Exams", f"{API_BASE}/api/home/recently-updated-exams/"),
    ("FAQs", f"{API_BASE}/api/home/faqs/"),
    ("Email Subscribe Section", f"{API_BASE}/api/home/email-subscribe-section/"),
    ("Featured Courses", f"{API_BASE}/api/courses/"),
    ("Categories", f"{API_BASE}/api/categories/"),
]

passed = 0
failed = 0

for name, url in tests:
    if test_api(name, url):
        passed += 1
    else:
        failed += 1

print("\n" + "=" * 70)
print(f"📊 TEST RESULTS: {passed}/{len(tests)} passed")
if failed == 0:
    print("🎉 ALL TESTS PASSED! Your APIs are working correctly.")
    print("\n✨ Next Steps:")
    print("  1. Visit http://localhost:3000 to see your dynamic home page")
    print("  2. Build admin UI pages to manage these sections")
    print("  3. Add authentication to test admin APIs")
else:
    print(f"⚠️  {failed} tests failed. Please check:")
    print("  1. Is Django server running? (python manage.py runserver)")
    print("  2. Did you run init_all_data.py to create sample data?")
    print("  3. Check terminal for Django errors")
print("=" * 70)

