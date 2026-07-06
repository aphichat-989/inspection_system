from datetime import date

from django.db import transaction

from .models import InspectionResultType, InspectionRound, InspectionSession, InspectionTest


FOUND_RESULT_NAME = "Found"
NOT_FOUND_RESULT_NAME = "Not Found"
NOT_FOUND_STOP_LIMIT = 4
NOT_FOUND_STOP_REASON = "NOT_FOUND reached 4 occurrences"
AUTO_COMPLETED_MESSAGE = "Inspection completed automatically because NOT_FOUND reached 4 occurrences."


def get_round_result_types():
    found, _ = InspectionResultType.objects.get_or_create(
        name=FOUND_RESULT_NAME,
        defaults={"description": "Defect was detected during the test round."},
    )
    not_found, _ = InspectionResultType.objects.get_or_create(
        name=NOT_FOUND_RESULT_NAME,
        defaults={"description": "Defect was not detected during the test round."},
    )
    return found, not_found


def build_next_session_number():
    today = date.today()
    prefix = today.strftime("TS%Y%m%d")
    existing_count = InspectionSession.objects.filter(session_number__startswith=prefix).count()
    candidate_number = existing_count + 1
    while True:
        session_number = f"{prefix}-{candidate_number:04d}"
        if not InspectionSession.objects.filter(session_number=session_number).exists():
            return session_number
        candidate_number += 1


def test_summary(test):
    found = 0
    not_found = 0
    completed = 0
    last_round = 0
    for round_item in test.rounds.all():
        if round_item.result_type_id:
            completed += 1
            last_round = max(last_round, round_item.round_number)
        result_name = round_item.result_type.name if round_item.result_type else ""
        if result_name == FOUND_RESULT_NAME:
            found += 1
        elif result_name == NOT_FOUND_RESULT_NAME:
            not_found += 1
    decided = found + not_found
    detection_rate = round((found / decided) * 100) if decided else 0
    completed_rounds = test.completed_rounds or last_round or completed
    return {
        "test": test,
        "found": found,
        "not_found": not_found,
        "completed": completed_rounds,
        "total_rounds": test.total_rounds,
        "detection_rate": detection_rate,
        "stop_reason": test.stop_reason,
        "status": test.status,
        "is_finished": test.status == InspectionTest.STATUS_FINISHED,
        "next_round_number": min(completed_rounds + 1, test.total_rounds),
    }


@transaction.atomic
def record_inspection_round(session, test_id, result_value, comment_value=""):
    if result_value not in {"found", "not_found"}:
        return None, "Please select FOUND or NOT_FOUND before submitting."

    found_result, not_found_result = get_round_result_types()
    test = InspectionTest.objects.select_for_update().get(pk=test_id, session=session)
    if test.status == InspectionTest.STATUS_FINISHED:
        return None, "This inspection test is already finished. Additional rounds cannot be recorded."

    completed_rounds = test.rounds.filter(result_type__isnull=False).count()
    next_round_number = max(test.completed_rounds, completed_rounds) + 1
    if next_round_number > test.total_rounds:
        test.completed_rounds = test.total_rounds
        test.status = InspectionTest.STATUS_FINISHED
        test.save(update_fields=["completed_rounds", "status"])
        return None, "All planned rounds are already completed. Additional rounds cannot be recorded."

    result_type = found_result if result_value == "found" else not_found_result
    round_item, created = InspectionRound.objects.get_or_create(
        inspection_test=test,
        round_number=next_round_number,
        defaults={"result_type": result_type, "comment": comment_value},
    )
    if not created and round_item.result_type_id:
        return None, "This round has already been recorded."
    if not created:
        round_item.result_type = result_type
        round_item.comment = comment_value
        round_item.save(update_fields=["result_type", "comment"])

    not_found_count = test.rounds.filter(result_type=not_found_result).count()
    update_fields = ["completed_rounds"]
    test.completed_rounds = next_round_number
    auto_completed = False
    if not_found_count >= NOT_FOUND_STOP_LIMIT:
        test.status = InspectionTest.STATUS_FINISHED
        test.stop_reason = NOT_FOUND_STOP_REASON
        update_fields.extend(["status", "stop_reason"])
        auto_completed = True
    elif next_round_number >= test.total_rounds:
        test.status = InspectionTest.STATUS_FINISHED
        update_fields.append("status")
    test.save(update_fields=update_fields)

    if not session.tests.exclude(status=InspectionTest.STATUS_FINISHED).exists():
        session.status = InspectionSession.STATUS_COMPLETED
        session.save(update_fields=["status"])

    return {"test": test, "round": round_item, "auto_completed": auto_completed}, None
