from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import (
    DefectType,
    InspectionRound,
    InspectionSession,
    InspectionTest,
    Inspector,
    ProductionLine,
    TestCondition,
)
from .views import NOT_FOUND_STOP_REASON


class InspectionWorkflowTests(TestCase):
    def setUp(self):
        self.line = ProductionLine.objects.create(name="Line A")
        self.condition = TestCondition.objects.create(name="Normal Light")
        self.inspector = Inspector.objects.create(name="Inspector A")
        self.defect = DefectType.objects.create(name="Scratch")

    def create_session_with_test(self, total_rounds=30):
        session = InspectionSession.objects.create(
            session_number="TS20260703-0001",
            inspection_date=date(2026, 7, 3),
            line=self.line,
            test_condition=self.condition,
            inspector=self.inspector,
            status=InspectionSession.STATUS_IN_PROGRESS,
        )
        test = InspectionTest.objects.create(
            session=session,
            defect_type=self.defect,
            test_name=str(self.defect.pk),
            total_rounds=total_rounds,
        )
        return session, test

    def test_create_session_does_not_precreate_rounds(self):
        response = self.client.post(
            reverse("inspection:create"),
            {
                "inspection_date": "2026-07-03",
                "line": self.line.pk,
                "test_condition": self.condition.pk,
                "inspector": self.inspector.pk,
                "overall_comment": "",
                "defects": [self.defect.pk],
                f"rounds_{self.defect.pk}": "30",
            },
        )

        self.assertEqual(response.status_code, 302)
        test = InspectionTest.objects.get(defect_type=self.defect)
        self.assertEqual(test.total_rounds, 30)
        self.assertEqual(test.rounds.count(), 0)

    def test_detail_displays_only_current_round_without_creating_database_rows(self):
        session, test = self.create_session_with_test(total_rounds=30)

        response = self.client.get(reverse("inspection:detail", kwargs={"pk": session.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Current Round")
        self.assertContains(response, "1 / 30")
        self.assertNotContains(response, "Round 30")
        self.assertContains(response, "FOUND")
        self.assertContains(response, "NOT_FOUND")
        self.assertContains(response, "Note")
        self.assertContains(response, "Save")
        self.assertEqual(test.rounds.count(), 0)

    def test_saving_round_creates_one_record_and_advances_current_round(self):
        session, test = self.create_session_with_test(total_rounds=30)
        url = reverse("inspection:detail", kwargs={"pk": session.pk})

        response = self.client.post(
            url,
            {
                "action": "save",
                "current_index": "0",
                "current_test_id": str(test.pk),
                "result": "found",
                "comment": "ok",
            },
        )

        self.assertEqual(response.status_code, 302)
        test.refresh_from_db()
        self.assertEqual(test.completed_rounds, 1)
        self.assertEqual(test.rounds.count(), 1)
        round_item = test.rounds.get()
        self.assertEqual(round_item.round_number, 1)
        self.assertEqual(round_item.comment, "ok")

        response = self.client.get(url)
        self.assertContains(response, "2 / 30")
        self.assertEqual(test.rounds.count(), 1)

        response = self.client.get(f"{url}?summary=1")
        self.assertContains(response, "ประวัติรอบทดสอบ")
        self.assertContains(response, "Round 1")
        self.assertContains(response, "1 / 30")
        self.assertContains(response, "ok")

    def test_save_requires_result(self):
        session, test = self.create_session_with_test(total_rounds=30)
        response = self.client.post(
            reverse("inspection:detail", kwargs={"pk": session.pk}),
            {
                "action": "save",
                "current_index": "0",
                "current_test_id": str(test.pk),
                "comment": "missing result",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(test.rounds.count(), 0)

    def test_not_found_four_finishes_test_and_rejects_extra_rounds(self):
        session, test = self.create_session_with_test(total_rounds=30)
        url = reverse("inspection:detail", kwargs={"pk": session.pk})

        for index in range(4):
            response = self.client.post(
                url,
                {
                    "action": "save",
                    "current_index": "0",
                    "current_test_id": str(test.pk),
                    "result": "not_found",
                    "comment": "",
                },
            )
            self.assertEqual(response.status_code, 302)
            if index == 3:
                self.assertIn("summary=1", response["Location"])

        test.refresh_from_db()
        self.assertEqual(test.status, InspectionTest.STATUS_FINISHED)
        self.assertEqual(test.stop_reason, NOT_FOUND_STOP_REASON)
        self.assertEqual(test.completed_rounds, 4)
        self.assertEqual(test.rounds.count(), 4)

        response = self.client.post(
            url,
            {
                "action": "save",
                "current_index": "0",
                "current_test_id": str(test.pk),
                "result": "found",
                "comment": "manual extra request",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("already finished", response.content.decode())
        self.assertEqual(InspectionRound.objects.filter(inspection_test=test).count(), 4)

    def test_completing_planned_rounds_finishes_test_and_shows_summary(self):
        session, test = self.create_session_with_test(total_rounds=2)
        url = reverse("inspection:detail", kwargs={"pk": session.pk})

        for index in range(2):
            response = self.client.post(
                url,
                {
                    "action": "save",
                    "current_index": "0",
                    "current_test_id": str(test.pk),
                    "result": "found",
                    "comment": "",
                },
            )
            self.assertEqual(response.status_code, 302)
            if index == 1:
                self.assertIn("summary=1", response["Location"])

        test.refresh_from_db()
        session.refresh_from_db()
        self.assertEqual(test.status, InspectionTest.STATUS_FINISHED)
        self.assertEqual(test.completed_rounds, 2)
        self.assertEqual(test.rounds.count(), 2)
        self.assertEqual(session.status, InspectionSession.STATUS_COMPLETED)