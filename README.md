# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

============================================================
DAILY SCHEDULE FOR MAX
============================================================

## TASK DETAILS:

1. 09:00 - 09:30 | Morning Walk
   ├─ Type: WALK
   ├─ Duration: 30 minutes
   ├─ Priority: HIGH
   └─ Description: Walk in the park

2. 09:30 - 09:45 | Breakfast
   ├─ Type: FEEDING
   ├─ Duration: 15 minutes
   ├─ Priority: HIGH
   └─ Description: Feed Max his breakfast

3. 09:45 - 10:15 | Afternoon Walk
   ├─ Type: WALK
   ├─ Duration: 30 minutes
   ├─ Priority: MEDIUM
   └─ Description: Walk in the neighborhood

---

## SCHEDULING SUMMARY:

✓ Morning Walk scheduled at 09:00 - 09:30 (High priority task)
✓ Breakfast scheduled at 09:30 - 09:45 (High priority task)
✓ Afternoon Walk scheduled at 09:45 - 10:15 (Scheduled during morning preference)

---

## STATISTICS:

Total Tasks: 3
Total Duration: 75 minutes
Schedule Start: 09:00
Schedule End: 10:15
============================================================

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature           | Method(s)                                        | Notes                                                                                                                                |
| ----------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Task sorting      | Scheduler.get_sorted_tasks()                     | Sorts by priority and frequency                                                                                                      |
| Filtering         | Scheduler.get_filtered_tasks()                   | Filter the current pet's tasks based on completion status, shedule status, and frequency.                                            |
| Conflict handling | Scheduler.check_owner_conflict()                 | Check if owner is busy with another pet at this task's time (multi-pet conflict). Only checks conflicts on the same date as the task |
|                   |
| Recurring tasks   | Scheduler.mark_task_complete_and_schedule_next() | Mark a task as complete and create the next occurrence if it's recurring.                                                            |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** _(optional)_: <!-- Insert a screenshot or link to a demo video here -->
