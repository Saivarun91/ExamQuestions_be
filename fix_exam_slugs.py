import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from courses.models import Course
from django.utils.text import slugify

def fix_slugs():
    """Fix all exam slugs to be clean single-segment slugs"""
    courses = Course.objects.all()
    
    print(f"Found {courses.count()} courses")
    
    for course in courses:
        old_slug = course.slug
        
        # Generate clean slug from title
        new_slug = slugify(course.title)
        
        if old_slug != new_slug:
            print(f"Updating: {course.title}")
            print(f"  Old slug: {old_slug}")
            print(f"  New slug: {new_slug}")
            
            course.slug = new_slug
            course.save()
    
    print("\n✅ All slugs fixed!")
    
    # Show all courses with their new slugs
    print("\n📋 Current courses:")
    for course in Course.objects.all():
        print(f"  - {course.title}: /exam-details/{course.slug}")

if __name__ == "__main__":
    fix_slugs()


