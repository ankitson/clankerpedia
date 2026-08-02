import runpy
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "td-reschedule-overdue"


class TdRescheduleOverdueTest(unittest.TestCase):
    def setUp(self):
        self.module = runpy.run_path(str(SCRIPT))
        self.globals = self.module["advance_one"].__globals__

    def recurring_task(self, *, rule, due_date, task_id="task-1"):
        return {
            "id": task_id,
            "content": "Regression fixture",
            "due": {
                "date": due_date,
                "string": rule,
                "isRecurring": True,
            },
        }

    def advance_with_server_state(self, task, after_due):
        calls = []

        def fake_run_td(*args):
            calls.append(args)
            return ""

        def fake_fetch_task(task_id):
            self.assertEqual(task_id, task["id"])
            return {
                **task,
                "due": after_due,
            }

        with patch.dict(
            self.globals,
            {
                "run_td": fake_run_td,
                "fetch_task": fake_fetch_task,
                "reminder_fingerprint": lambda _task_id: (("relative", 30),),
            },
        ):
            outcome = self.module["advance_one"](
                task,
                "Tester",
                False,
                date(2026, 8, 2),
            )

        return outcome, calls

    def test_daily_overdue_tasks_reschedule_to_today_regardless_of_clock_time(self):
        cases = [
            ("every day at 9am", "09:00:00"),
            ("every day at 4pm", "16:00:00"),
            ("every day at 7pm", "19:00:00"),
        ]

        for rule, clock in cases:
            with self.subTest(rule=rule):
                task = self.recurring_task(
                    rule=rule,
                    due_date=f"2026-08-01T{clock}",
                )
                after_due = {
                    "date": f"2026-08-02T{clock}",
                    "string": rule,
                    "isRecurring": True,
                }

                outcome, calls = self.advance_with_server_state(task, after_due)

                self.assertEqual(outcome.status, "advanced")
                self.assertEqual(outcome.now_due, f"2026-08-02T{clock}")
                self.assertEqual(
                    calls,
                    [
                        (
                            "task",
                            "reschedule",
                            "id:task-1",
                            f"2026-08-02T{clock}",
                        )
                    ],
                )

    def test_daily_rule_spellings_and_anchor_use_same_day_reschedule(self):
        rules = [
            "every day at 4pm",
            "everyday at 4pm",
            "daily at 4pm",
            "every day at 4pm starting 2026-01-01",
        ]

        for rule in rules:
            with self.subTest(rule=rule):
                task = self.recurring_task(
                    rule=rule,
                    due_date="2026-08-01T16:00:00",
                )
                after_due = {
                    "date": "2026-08-02T16:00:00",
                    "string": rule,
                    "isRecurring": True,
                }

                outcome, calls = self.advance_with_server_state(task, after_due)

                self.assertEqual(outcome.status, "advanced")
                self.assertEqual(calls[0][0:2], ("task", "reschedule"))
                self.assertNotIn("update", calls[0])

    def test_all_day_daily_task_remains_all_day_on_today(self):
        task = self.recurring_task(
            rule="every day",
            due_date="2026-08-01",
        )
        after_due = {
            "date": "2026-08-02",
            "string": "every day",
            "isRecurring": True,
        }

        outcome, calls = self.advance_with_server_state(task, after_due)

        self.assertEqual(outcome.status, "advanced")
        self.assertEqual(
            calls,
            [("task", "reschedule", "id:task-1", "2026-08-02")],
        )

    def test_non_daily_overdue_task_still_uses_recurrence_advance(self):
        rule = "every saturday at 4pm"
        task = self.recurring_task(
            rule=rule,
            due_date="2026-08-01T16:00:00",
        )
        after_due = {
            "date": "2026-08-08T16:00:00",
            "string": rule,
            "isRecurring": True,
        }

        outcome, calls = self.advance_with_server_state(task, after_due)

        self.assertEqual(outcome.status, "advanced")
        self.assertEqual(
            calls,
            [
                (
                    "task",
                    "update",
                    "id:task-1",
                    "--due",
                    rule,
                )
            ],
        )

    def test_daily_dry_run_shows_same_day_target_without_mutating(self):
        task = self.recurring_task(
            rule="every day at 4pm",
            due_date="2026-08-01T16:00:00",
        )

        with patch.dict(
            self.globals,
            {"run_td": lambda *_args: self.fail("dry run mutated Todoist")},
        ):
            outcome = self.module["advance_one"](
                task,
                "Tester",
                True,
                date(2026, 8, 2),
            )

        self.assertEqual(outcome.status, "would-advance")
        self.assertEqual(outcome.now_due, "2026-08-02T16:00:00")


if __name__ == "__main__":
    unittest.main()
