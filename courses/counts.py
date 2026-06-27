def sync_course_counts(course, *, save=True):
    """Update stored course counters after write operations."""
    if not course:
        return None

    from practice_tests.models import PracticeTest
    from questions.models import Question

    practice_test_count = PracticeTest.objects(course=course).count()
    question_count = Question.objects(course=course).count()

    course.practice_exams = practice_test_count
    course.questions = question_count

    if save:
        course.save()

    return course
