from bson import ObjectId


def _practice_test_question_count(practice_test, exam_q_by_pt=None):
    """Questions for one practice test: actual exam questions, else configured count."""
    if practice_test is None:
        return 0

    pt_id = str(getattr(practice_test, "id", "") or "")
    if exam_q_by_pt is not None and pt_id:
        actual = int(exam_q_by_pt.get(pt_id, 0) or 0)
        if actual > 0:
            return actual

    try:
        from exams.models import Question as ExamQuestion

        actual = ExamQuestion.objects(category=practice_test).count()
        if actual > 0:
            return actual
    except Exception:
        pass

    return int(getattr(practice_test, "questions", 0) or 0)


def _exam_question_counts_by_practice_test(practice_test_ids):
    """Return {practice_test_id_str: question_count} in one aggregation."""
    if not practice_test_ids:
        return {}

    try:
        from exams.models import Question as ExamQuestion
    except Exception:
        return {}

    oids = []
    for pt_id in practice_test_ids:
        if ObjectId.is_valid(str(pt_id)):
            oids.append(ObjectId(str(pt_id)))

    if not oids:
        return {}

    counts = {}
    for row in ExamQuestion._get_collection().aggregate(
        [
            {"$match": {"category": {"$in": oids}}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        ]
    ):
        counts[str(row["_id"])] = int(row.get("count") or 0)
    return counts


def sync_course_counts(course, *, save=True):
    """Update stored course counters after write operations."""
    if not course:
        return None

    from practice_tests.models import PracticeTest
    from questions.models import Question as CourseQuestion

    practice_tests = list(PracticeTest.objects(course=course))
    practice_test_count = len(practice_tests)
    exam_q_by_pt = _exam_question_counts_by_practice_test(
        [pt.id for pt in practice_tests]
    )

    practice_questions = sum(
        _practice_test_question_count(pt, exam_q_by_pt) for pt in practice_tests
    )
    course_questions = CourseQuestion.objects(course=course).count()
    question_count = max(course_questions, practice_questions)

    course.practice_exams = practice_test_count
    course.questions = question_count

    if save:
        course.save()

    return course


def refresh_course_counts_for_practice_test(practice_test):
    """Update practice-test question count and parent course counters."""
    if not practice_test:
        return None

    course = getattr(practice_test, "course", None)
    try:
        from exams.models import Question as ExamQuestion

        actual = ExamQuestion.objects(category=practice_test).count()
        if actual > 0:
            practice_test.questions = actual
            practice_test.save()
    except Exception:
        pass

    if course:
        sync_course_counts(course)
    return course


def bulk_course_practice_stats(course_ids):
    """
    Live practice-test counts for listing pages.
    Returns {course_id_str: {"practice_exams": int, "questions": int}}.
    """
    oids = [ObjectId(str(cid)) for cid in course_ids if ObjectId.is_valid(str(cid))]
    if not oids:
        return {}

    from practice_tests.models import PracticeTest

    stats = {str(oid): {"practice_exams": 0, "questions": 0} for oid in oids}
    tests_by_course = {str(oid): [] for oid in oids}
    all_pt_ids = []

    for doc in PracticeTest._get_collection().find(
        {"course": {"$in": oids}},
        {"course": 1, "questions": 1},
    ):
        course_id = str(doc.get("course"))
        if course_id not in stats:
            continue
        pt_id = doc.get("_id")
        all_pt_ids.append(pt_id)
        tests_by_course[course_id].append(
            {
                "id": pt_id,
                "questions": int(doc.get("questions") or 0),
            }
        )

    exam_q_by_pt = _exam_question_counts_by_practice_test(all_pt_ids)

    for course_id, tests in tests_by_course.items():
        practice_exams = len(tests)
        questions = 0
        for test in tests:
            pt_id = str(test["id"])
            actual = int(exam_q_by_pt.get(pt_id, 0) or 0)
            questions += actual if actual > 0 else int(test.get("questions") or 0)
        stats[course_id] = {
            "practice_exams": practice_exams,
            "questions": questions,
        }

    return stats


def resolve_public_course_counts(
    course_id, stored_practice_exams=0, stored_questions=0, live_stats=None
):
    """Prefer live stats when stored counters are missing or lower."""
    live = (live_stats or {}).get(str(course_id)) or {}
    practice_exams = int(live.get("practice_exams") or 0)
    questions = int(live.get("questions") or 0)

    stored_practice_exams = int(stored_practice_exams or 0)
    stored_questions = int(stored_questions or 0)

    return {
        "practice_exams": max(stored_practice_exams, practice_exams),
        "questions": max(stored_questions, questions),
    }
