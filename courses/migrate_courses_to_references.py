"""
Migration script to convert existing Course documents to use ReferenceFields
for provider and category instead of StringFields.

This script should be run ONCE after updating the Course model.
Run this script using: python manage.py shell < courses/migrate_courses_to_references.py
"""

from courses.models import Course
from providers.models import Provider
from categories.models import Category

print("🚀 Starting migration: Converting courses to use reference fields...")
print("=" * 60)

# Get all courses
courses = Course.objects.all()
total_courses = courses.count()
print(f"Found {total_courses} courses to migrate")
print("=" * 60)

migrated = 0
skipped = 0
errors = []

for course in courses:
    try:
        needs_save = False
        
        # Check if provider is a string and needs conversion
        provider_value = course._data.get('provider')
        if isinstance(provider_value, str):
            print(f"\n📦 Processing course: {course.title}")
            print(f"   Current provider (string): {provider_value}")
            
            # Try to find the provider
            provider = None
            try:
                # Try by name first
                provider = Provider.objects.get(name=provider_value)
            except Provider.DoesNotExist:
                # Try by slug
                try:
                    from django.utils.text import slugify
                    provider_slug = slugify(provider_value)
                    provider = Provider.objects.get(slug=provider_slug)
                except Provider.DoesNotExist:
                    error_msg = f"Provider '{provider_value}' not found for course '{course.title}'"
                    print(f"   ❌ {error_msg}")
                    errors.append(error_msg)
                    continue
            
            if provider:
                course.provider = provider
                needs_save = True
                print(f"   ✅ Mapped to provider: {provider.name}")
        
        # Check if category is a string and needs conversion
        category_value = course._data.get('category')
        if category_value and isinstance(category_value, str):
            print(f"   Current category (string): {category_value}")
            
            # Try to find the category
            category = None
            try:
                # Try by title first
                category = Category.objects.get(title=category_value)
            except Category.DoesNotExist:
                # Try by slug
                try:
                    from django.utils.text import slugify
                    category_slug = slugify(category_value)
                    category = Category.objects.get(slug=category_slug)
                except Category.DoesNotExist:
                    print(f"   ⚠️  Category '{category_value}' not found, setting to None")
                    category = None
            
            if category:
                course.category = category
                needs_save = True
                print(f"   ✅ Mapped to category: {category.title}")
        
        # Save if changes were made
        if needs_save:
            course.save()
            migrated += 1
            print(f"   💾 Saved course: {course.title}")
        else:
            skipped += 1
            print(f"   ⏭️  Skipped (already migrated): {course.title}")
            
    except Exception as e:
        error_msg = f"Error processing course '{course.title}': {str(e)}"
        print(f"   ❌ {error_msg}")
        errors.append(error_msg)

print("\n" + "=" * 60)
print("🎉 Migration complete!")
print("=" * 60)
print(f"✅ Migrated: {migrated} courses")
print(f"⏭️  Skipped: {skipped} courses")
print(f"❌ Errors: {len(errors)}")

if errors:
    print("\n⚠️  Errors encountered:")
    for error in errors:
        print(f"  - {error}")
    print("\n📝 Please ensure all providers exist in the database before running this migration.")
else:
    print("\n✨ All courses migrated successfully!")

print("\n📝 Next Steps:")
print("  1. Restart Django server")
print("  2. Test the API endpoints")
print("  3. Verify courses are displaying correctly on frontend")

