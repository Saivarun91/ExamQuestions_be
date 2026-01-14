# exams/signals.py
from mongoengine import signals
from datetime import datetime
from .models import Question
from practice_tests.models import PracticeTest


def update_question_count(sender, document, **kwargs):
    """Auto-update the total number of questions in the related PracticeTest."""
    if not document.category:
        return

    test = document.category  # Reference to PracticeTest document

    try:
        # ✅ Recalculate total questions linked to this test
        count = Question.objects(category=test).count()
        
        # ✅ Safely update the test record
        test.update(set__questions=count, set__updated_at=datetime.utcnow())
    except Exception as e:
        print(f"[Signal Error] Failed to update question count: {e}")


# ✅ Connect signals
signals.post_save.connect(update_question_count, sender=Question)
signals.post_delete.connect(update_question_count, sender=Question)
