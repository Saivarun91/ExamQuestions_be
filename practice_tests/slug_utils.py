from bson import ObjectId
from django.utils.text import slugify


def _slug_taken(slug, exclude_id=None):
    from practice_tests.models import PracticeTest

    if not slug:
        return True

    existing = PracticeTest.objects(slug=slug).first()
    if not existing:
        return False
    if exclude_id and str(existing.id) == str(exclude_id):
        return False
    return True


def allocate_practice_test_slug(title, course, existing_test=None):
    """
    Return a slug unique across the practice_tests collection.

    Production DBs may still have a legacy unique index on slug alone (slug_1),
    so per-course uniqueness checks are not sufficient.
    """
    base = slugify(title or "") or "practice-test"
    exclude_id = str(existing_test.id) if existing_test else None
    course_tag = str(getattr(course, "id", "") or "")[-8:] or "course"

    candidates = [base]
    if course_tag:
        candidates.append(f"{base}-{course_tag}")

    counter = 1
    while counter <= 500:
        candidates.append(f"{base}-{course_tag}-{counter}")
        counter += 1

    for slug in candidates:
        if not _slug_taken(slug, exclude_id=exclude_id):
            return slug

    return f"{base}-{course_tag}-{ObjectId()}"
