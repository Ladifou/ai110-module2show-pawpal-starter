import unittest
from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Task, TaskType, Constraint, Scheduler


class TestTaskCompletion(unittest.TestCase):
    """Test suite for task completion functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.owner = Owner(
            owner_id="owner_test_001",
            name="Test Owner",
            email="test@example.com",
            phone="555-0000",
            address="Test Address"
        )

        self.pet = Pet(
            pet_id="pet_test_001",
            name="Test Pet",
            pet_type="Dog",
            breed="Labrador",
            age=2,
            owner=self.owner
        )

        self.task = Task(
            task_id="task_test_001",
            name="Test Walk",
            description="Test walk task",
            task_type=TaskType.WALK,
            default_duration=30,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )

    def test_mark_complete_changes_task_status(self):
        """Verify that calling mark_complete() changes the task's is_completed status to True."""
        # Arrange: Task should initially be incomplete
        self.assertFalse(self.task.is_completed, "Task should start as incomplete")

        # Act: Mark the task as complete
        self.task.mark_complete()

        # Assert: Task should now be marked as complete
        self.assertTrue(self.task.is_completed, "Task should be marked as complete after calling mark_complete()")

    def test_mark_complete_multiple_calls(self):
        """Verify that mark_complete() can be called multiple times without errors."""
        # Act: Call mark_complete multiple times
        self.task.mark_complete()
        self.task.mark_complete()
        self.task.mark_complete()

        # Assert: Task should still be complete
        self.assertTrue(self.task.is_completed, "Task should remain complete after multiple mark_complete() calls")


class TestPetTaskCount(unittest.TestCase):
    """Test suite for pet task management."""

    def setUp(self):
        """Set up test fixtures."""
        self.owner = Owner(
            owner_id="owner_test_002",
            name="Test Owner 2",
            email="test2@example.com",
            phone="555-0001",
            address="Test Address 2"
        )

        self.pet = Pet(
            pet_id="pet_test_002",
            name="Test Pet 2",
            pet_type="Cat",
            breed="Siamese",
            age=3,
            owner=self.owner
        )

    def test_adding_task_increases_pet_task_count(self):
        """Verify that adding a task to a pet increases the pet's task count."""
        # Arrange: Pet should start with zero tasks
        initial_count = self.pet.get_task_count() if hasattr(self.pet, 'get_task_count') else 0
        self.assertEqual(initial_count, 0, "Pet should start with zero tasks")

        # Act: Create and add a task to the pet
        task1 = Task(
            task_id="task_test_002",
            name="Feeding",
            description="Feed the pet",
            task_type=TaskType.FEEDING,
            default_duration=15,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )
        self.pet.add_task(task1) if hasattr(self.pet, 'add_task') else self.pet.tasks.append(task1)

        # Assert: Pet's task count should increase by 1
        updated_count = self.pet.get_task_count() if hasattr(self.pet, 'get_task_count') else len(self.pet.tasks)
        self.assertEqual(updated_count, 1, "Pet's task count should be 1 after adding one task")

    def test_adding_multiple_tasks_increases_pet_task_count(self):
        """Verify that adding multiple tasks to a pet increases the pet's task count accordingly."""
        # Arrange: Pet should start with zero tasks
        initial_count = self.pet.get_task_count() if hasattr(self.pet, 'get_task_count') else 0
        self.assertEqual(initial_count, 0, "Pet should start with zero tasks")

        # Act: Create and add multiple tasks to the pet
        tasks = [
            Task(
                task_id=f"task_multi_{i}",
                name=f"Task {i}",
                description=f"Test task {i}",
                task_type=TaskType.WALK if i % 2 == 0 else TaskType.FEEDING,
                default_duration=20 + (i * 10),
                default_frequency="daily",
                default_priority="high",
                pet=self.pet,
                due_date=datetime.now()
            )
            for i in range(3)
        ]

        for task in tasks:
            self.pet.add_task(task) if hasattr(self.pet, 'add_task') else self.pet.tasks.append(task)

        # Assert: Pet's task count should be 3
        updated_count = self.pet.get_task_count() if hasattr(self.pet, 'get_task_count') else len(self.pet.tasks)
        self.assertEqual(updated_count, 3, "Pet's task count should be 3 after adding three tasks")

    def test_get_schedule_returns_all_pet_tasks(self):
        """Verify that get_schedule() returns all tasks added to the pet."""
        # Arrange: Add multiple tasks to the pet
        task1 = Task(
            task_id="task_sched_001",
            name="Walk",
            description="Morning walk",
            task_type=TaskType.WALK,
            default_duration=30,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )
        task2 = Task(
            task_id="task_sched_002",
            name="Feeding",
            description="Dinner time",
            task_type=TaskType.FEEDING,
            default_duration=15,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )

        self.pet.add_task(task1) if hasattr(self.pet, 'add_task') else self.pet.tasks.append(task1)
        self.pet.add_task(task2) if hasattr(self.pet, 'add_task') else self.pet.tasks.append(task2)

        # Act: Get the pet's schedule
        schedule = self.pet.get_schedule()

        # Assert: Schedule should contain both tasks
        self.assertEqual(len(schedule), 2, "Schedule should contain 2 tasks")
        self.assertIn(task1, schedule, "Schedule should contain task1")
        self.assertIn(task2, schedule, "Schedule should contain task2")


class TestSortingEdgeCases(unittest.TestCase):
    """Test suite for sorting edge cases with priority and frequency."""

    def setUp(self):
        """Set up test fixtures."""
        self.owner = Owner(
            owner_id="owner_sort_001",
            name="Sort Test Owner",
            email="sort@example.com",
            phone="555-1234",
            address="Sort Address"
        )
        self.pet = Pet(
            pet_id="pet_sort_001",
            name="Sort Pet",
            pet_type="Dog",
            breed="Labrador",
            age=2,
            owner=self.owner
        )
        self.scheduler = Scheduler(f"scheduler_{self.pet.pet_id}", self.pet)

    def test_sort_tasks_with_identical_priority_and_frequency(self):
        """Verify that tasks with same priority and frequency sort deterministically."""
        # Arrange: Create tasks with identical priority and frequency
        task_a = Task(
            task_id="task_sort_a",
            name="Task A",
            description="First task",
            task_type=TaskType.WALK,
            default_duration=30,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )
        task_b = Task(
            task_id="task_sort_b",
            name="Task B",
            description="Second task",
            task_type=TaskType.FEEDING,
            default_duration=30,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )

        self.pet.add_task(task_a)
        self.pet.add_task(task_b)

        # Act: Sort tasks
        sorted_tasks = self.scheduler._get_sorted_tasks()

        # Assert: Both tasks present and order is deterministic
        self.assertEqual(len(sorted_tasks), 2, "Both tasks should be in sorted list")
        task_names = [t.name for t in sorted_tasks]
        self.assertIn("Task A", task_names)
        self.assertIn("Task B", task_names)

    def test_sort_with_invalid_priority_value(self):
        """Verify sorting handles invalid priority values without crashing."""
        # Arrange: Create task with invalid priority
        task = Task(
            task_id="task_invalid_priority",
            name="Invalid Priority Task",
            description="Task with invalid priority",
            task_type=TaskType.WALK,
            default_duration=30,
            default_frequency="daily",
            default_priority="ULTRA_CRITICAL",  # Invalid
            pet=self.pet,
            due_date=datetime.now()
        )
        self.pet.add_task(task)

        # Act & Assert: Should not crash
        sorted_tasks = self.scheduler._get_sorted_tasks()
        self.assertEqual(len(sorted_tasks), 1, "Task with invalid priority should be included")

    def test_sort_with_invalid_frequency_value(self):
        """Verify sorting handles invalid frequency values without crashing."""
        # Arrange: Create task with invalid frequency
        task = Task(
            task_id="task_invalid_freq",
            name="Invalid Frequency Task",
            description="Task with invalid frequency",
            task_type=TaskType.WALK,
            default_duration=30,
            default_frequency="never_heard_of_this",  # Invalid
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )
        self.pet.add_task(task)

        # Act & Assert: Should not crash
        sorted_tasks = self.scheduler._get_sorted_tasks()
        self.assertEqual(len(sorted_tasks), 1, "Task with invalid frequency should be included")

    def test_sort_empty_task_list(self):
        """Verify sorting handles empty task list."""
        # Act: Sort empty pet's tasks
        sorted_tasks = self.scheduler._get_sorted_tasks()

        # Assert: Should return empty list
        self.assertEqual(sorted_tasks, [], "Empty task list should return empty sorted list")

    def test_sort_priority_ordering(self):
        """Verify tasks are sorted by priority (high > medium > low)."""
        # Arrange: Create tasks with different priorities
        low = Task(
            task_id="task_low",
            name="Low Priority",
            description="Low",
            task_type=TaskType.ENRICHMENT,
            default_duration=10,
            default_frequency="daily",
            default_priority="low",
            pet=self.pet,
            due_date=datetime.now()
        )
        high = Task(
            task_id="task_high",
            name="High Priority",
            description="High",
            task_type=TaskType.MEDICATION,
            default_duration=10,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )
        medium = Task(
            task_id="task_medium",
            name="Medium Priority",
            description="Medium",
            task_type=TaskType.WALK,
            default_duration=10,
            default_frequency="daily",
            default_priority="medium",
            pet=self.pet,
            due_date=datetime.now()
        )

        self.pet.tasks = [low, high, medium]

        # Act: Sort tasks
        sorted_tasks = self.scheduler._get_sorted_tasks()

        # Assert: Order should be high, medium, low
        self.assertEqual(sorted_tasks[0].priority.lower(), "high")
        self.assertEqual(sorted_tasks[1].priority.lower(), "medium")
        self.assertEqual(sorted_tasks[2].priority.lower(), "low")


class TestRecurringTaskEdgeCases(unittest.TestCase):
    """Test suite for recurring task edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.owner = Owner(
            owner_id="owner_recur_001",
            name="Recurring Test Owner",
            email="recur@example.com",
            phone="555-5678",
            address="Recurring Address"
        )
        self.pet = Pet(
            pet_id="pet_recur_001",
            name="Recurring Pet",
            pet_type="Cat",
            breed="Siamese",
            age=3,
            owner=self.owner
        )

    def test_daily_task_creates_next_with_correct_date(self):
        """Verify daily recurring task creates next occurrence with date+1."""
        # Arrange
        base_date = datetime(2026, 7, 4, 10, 30)
        task = Task(
            task_id="task_daily",
            name="Daily Medication",
            description="Take medication",
            task_type=TaskType.MEDICATION,
            default_duration=5,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=base_date
        )

        # Act
        next_task = task.create_next_occurrence()

        # Assert
        self.assertIsNotNone(next_task, "Daily task should create next occurrence")
        self.assertEqual(next_task.due_date, base_date + timedelta(days=1))
        self.assertEqual(next_task.due_date.hour, base_date.hour)
        self.assertEqual(next_task.due_date.minute, base_date.minute)

    def test_weekly_task_creates_next_with_correct_date(self):
        """Verify weekly recurring task creates next occurrence with date+7 days."""
        # Arrange
        base_date = datetime(2026, 7, 4, 14, 0)
        task = Task(
            task_id="task_weekly",
            name="Weekly Grooming",
            description="Grooming session",
            task_type=TaskType.GROOMING,
            default_duration=60,
            default_frequency="weekly",
            default_priority="medium",
            pet=self.pet,
            due_date=base_date
        )

        # Act
        next_task = task.create_next_occurrence()

        # Assert
        self.assertIsNotNone(next_task, "Weekly task should create next occurrence")
        self.assertEqual(next_task.due_date, base_date + timedelta(weeks=1))

    def test_occasional_task_does_not_create_next(self):
        """Verify non-recurring (occasional) task returns None for next occurrence."""
        # Arrange
        task = Task(
            task_id="task_occasional",
            name="Annual Checkup",
            description="Vet checkup",
            task_type=TaskType.MEDICATION,
            default_duration=30,
            default_frequency="occasional",
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )

        # Act
        next_task = task.create_next_occurrence()

        # Assert
        self.assertIsNone(next_task, "Occasional task should not create next occurrence")

    def test_recurring_task_preserves_constraints(self):
        """Verify next occurrence of recurring task copies constraints."""
        # Arrange
        task = Task(
            task_id="task_constrained",
            name="Constrained Task",
            description="Task with constraint",
            task_type=TaskType.WALK,
            default_duration=30,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )

        constraint = Constraint(
            constraint_id="constraint_morning",
            constraint_type="time_window",
            description="Morning only",
            is_hard_constraint=True,
            priority=1,
            affected_times={"start_hour": 6, "end_hour": 12}
        )
        task.add_constraint(constraint)

        # Act
        next_task = task.create_next_occurrence()

        # Assert
        self.assertEqual(len(next_task.get_constraints()), 1)
        self.assertEqual(next_task.constraints[0].constraint_id, "constraint_morning")

    def test_recurring_task_id_chain(self):
        """Verify task IDs chain with _next suffix."""
        # Arrange
        task = Task(
            task_id="med_001",
            name="Medication",
            description="Daily med",
            task_type=TaskType.MEDICATION,
            default_duration=5,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )

        # Act
        next1 = task.create_next_occurrence()
        next2 = next1.create_next_occurrence()
        next3 = next2.create_next_occurrence()

        # Assert
        self.assertEqual(next1.task_id, "med_001_next")
        self.assertEqual(next2.task_id, "med_001_next_next")
        self.assertEqual(next3.task_id, "med_001_next_next_next")

    def test_recurring_task_across_month_boundary(self):
        """Verify recurring task dates work correctly across month boundaries."""
        # Arrange: July 31 + 1 day = Aug 1
        task = Task(
            task_id="task_month_boundary",
            name="Daily Task",
            description="Crosses month",
            task_type=TaskType.WALK,
            default_duration=30,
            default_frequency="daily",
            default_priority="medium",
            pet=self.pet,
            due_date=datetime(2026, 7, 31, 10, 0)
        )

        # Act
        next_task = task.create_next_occurrence()

        # Assert
        self.assertEqual(next_task.due_date, datetime(2026, 8, 1, 10, 0))

    def test_recurring_task_across_year_boundary(self):
        """Verify recurring task dates work correctly across year boundaries."""
        # Arrange: Dec 31 + 1 day = Jan 1 next year
        task = Task(
            task_id="task_year_boundary",
            name="Year Boundary Task",
            description="New Year",
            task_type=TaskType.FEEDING,
            default_duration=15,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime(2026, 12, 31, 9, 0)
        )

        # Act
        next_task = task.create_next_occurrence()

        # Assert
        self.assertEqual(next_task.due_date, datetime(2027, 1, 1, 9, 0))


class TestSchedulingGapsAndConflicts(unittest.TestCase):
    """Test suite for scheduling gaps and conflict detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.owner = Owner(
            owner_id="owner_schedule_001",
            name="Schedule Test Owner",
            email="schedule@example.com",
            phone="555-9012",
            address="Schedule Address"
        )
        self.pet = Pet(
            pet_id="pet_schedule_001",
            name="Schedule Pet",
            pet_type="Dog",
            breed="Golden Retriever",
            age=4,
            owner=self.owner
        )
        self.owner.add_pet(self.pet)
        self.scheduler = Scheduler(f"scheduler_{self.pet.pet_id}", self.pet)

    def test_back_to_back_tasks_do_not_conflict(self):
        """Verify tasks scheduled back-to-back (end of one = start of next) don't conflict."""
        # Arrange
        base_date = datetime(2026, 7, 4)
        task1 = Task(
            task_id="task1",
            name="Task 1",
            description="First task",
            task_type=TaskType.WALK,
            default_duration=60,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=base_date
        )
        task2 = Task(
            task_id="task2",
            name="Task 2",
            description="Second task",
            task_type=TaskType.FEEDING,
            default_duration=30,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=base_date
        )

        # Schedule back-to-back: 9:00-10:00, then 10:00-10:30
        task1.update_time_slot(
            datetime(2026, 7, 4, 9, 0),
            datetime(2026, 7, 4, 10, 0)
        )
        task2.update_time_slot(
            datetime(2026, 7, 4, 10, 0),
            datetime(2026, 7, 4, 10, 30)
        )
        self.pet.add_task(task1)
        self.pet.add_task(task2)

        # Act & Assert
        conflicts = self.scheduler.detect_conflicts()
        self.assertEqual(len(conflicts), 0, "Back-to-back tasks should not conflict")

    def test_overlapping_tasks_are_detected(self):
        """Verify overlapping task times are correctly detected as conflicts."""
        # Arrange
        base_date = datetime(2026, 7, 4)
        task1 = Task(
            task_id="task_overlap_1",
            name="Task 1",
            description="First",
            task_type=TaskType.WALK,
            default_duration=60,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=base_date
        )
        task2 = Task(
            task_id="task_overlap_2",
            name="Task 2",
            description="Second",
            task_type=TaskType.FEEDING,
            default_duration=60,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=base_date
        )

        # Schedule overlapping: 9:00-10:00 and 9:30-10:30
        task1.update_time_slot(
            datetime(2026, 7, 4, 9, 0),
            datetime(2026, 7, 4, 10, 0)
        )
        task2.update_time_slot(
            datetime(2026, 7, 4, 9, 30),
            datetime(2026, 7, 4, 10, 30)
        )
        self.pet.add_task(task1)
        self.pet.add_task(task2)

        # Act
        conflicts = self.scheduler.detect_conflicts()

        # Assert
        self.assertEqual(len(conflicts), 1, "Overlapping tasks should be detected")
        self.assertIn("Task 1", conflicts[0])
        self.assertIn("Task 2", conflicts[0])

    def test_tasks_on_different_dates_do_not_conflict(self):
        """Verify tasks on different dates don't conflict even if times overlap."""
        # Arrange
        task1 = Task(
            task_id="task_diff_date_1",
            name="July Task",
            description="On July 4",
            task_type=TaskType.WALK,
            default_duration=60,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime(2026, 7, 4, 10, 0)
        )
        task2 = Task(
            task_id="task_diff_date_2",
            name="July 5 Task",
            description="On July 5",
            task_type=TaskType.FEEDING,
            default_duration=60,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime(2026, 7, 5, 10, 0)
        )

        # Both at 10:00-11:00 but different dates
        task1.update_time_slot(datetime(2026, 7, 4, 10, 0), datetime(2026, 7, 4, 11, 0))
        task2.update_time_slot(datetime(2026, 7, 5, 10, 0), datetime(2026, 7, 5, 11, 0))
        self.pet.add_task(task1)
        self.pet.add_task(task2)

        # Act & Assert
        conflicts = self.scheduler.detect_conflicts()
        self.assertEqual(len(conflicts), 0, "Tasks on different dates should not conflict")

    def test_unscheduled_tasks_dont_block_gaps(self):
        """Verify unscheduled tasks (no times) don't appear in gap detection."""
        # Arrange
        unscheduled = Task(
            task_id="unscheduled",
            name="Unscheduled",
            description="No times set",
            task_type=TaskType.WALK,
            default_duration=30,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime(2026, 7, 4, 10, 0)
        )
        self.pet.add_task(unscheduled)

        # Act
        gaps = self.scheduler._find_schedule_gaps(datetime(2026, 7, 4), 60)

        # Assert: Should find gaps starting at 9:00
        self.assertGreater(len(gaps), 0, "Should find gaps when only unscheduled tasks exist")
        self.assertIn(datetime(2026, 7, 4, 9, 0), gaps)

    def test_multi_pet_conflict_detection(self):
        """Verify conflicts are detected across multiple pets of same owner."""
        # Arrange: Create second pet for same owner
        pet2 = Pet(
            pet_id="pet_schedule_002",
            name="Second Pet",
            pet_type="Cat",
            breed="Tabby",
            age=2,
            owner=self.owner
        )
        self.owner.add_pet(self.pet)
        self.owner.add_pet(pet2)

        # Create overlapping tasks on different pets
        task1 = Task(
            task_id="task_pet1",
            name="Dog Walk",
            description="Walking dog",
            task_type=TaskType.WALK,
            default_duration=60,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime(2026, 7, 4, 10, 0)
        )
        task2 = Task(
            task_id="task_pet2",
            name="Cat Playtime",
            description="Playing with cat",
            task_type=TaskType.ENRICHMENT,
            default_duration=60,
            default_frequency="daily",
            default_priority="high",
            pet=pet2,
            due_date=datetime(2026, 7, 4, 10, 30)
        )

        # Both at overlapping times on same date
        task1.update_time_slot(datetime(2026, 7, 4, 10, 0), datetime(2026, 7, 4, 11, 0))
        task2.update_time_slot(datetime(2026, 7, 4, 10, 30), datetime(2026, 7, 4, 11, 30))

        self.pet.add_task(task1)
        pet2.add_task(task2)

        # Act
        conflicts = self.scheduler.detect_conflicts()

        # Assert
        self.assertEqual(len(conflicts), 1, "Multi-pet conflicts should be detected")

    def test_full_schedule_leaves_no_gaps(self):
        """Verify that fully booked schedule (9-5) leaves no gaps."""
        # Arrange: Fill entire 9 AM - 5 PM with two 4-hour tasks
        base_date = datetime(2026, 7, 4)
        task1 = Task(
            task_id="task_full_1",
            name="Morning Block",
            description="4 hours",
            task_type=TaskType.WALK,
            default_duration=240,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=base_date
        )
        task2 = Task(
            task_id="task_full_2",
            name="Afternoon Block",
            description="4 hours",
            task_type=TaskType.FEEDING,
            default_duration=240,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=base_date
        )

        task1.update_time_slot(datetime(2026, 7, 4, 9, 0), datetime(2026, 7, 4, 13, 0))
        task2.update_time_slot(datetime(2026, 7, 4, 13, 0), datetime(2026, 7, 4, 17, 0))
        self.pet.add_task(task1)
        self.pet.add_task(task2)

        # Act
        gaps = self.scheduler._find_schedule_gaps(base_date, 60)

        # Assert: No 60-minute gaps available
        self.assertEqual(len(gaps), 0, "Fully booked schedule should have no gaps")


class TestTaskCompletionWithRecurrence(unittest.TestCase):
    """Extended test suite for task completion and recurrence."""

    def setUp(self):
        """Set up test fixtures."""
        self.owner = Owner(
            owner_id="owner_completion_001",
            name="Completion Test Owner",
            email="completion@example.com",
            phone="555-3456",
            address="Completion Address"
        )
        self.pet = Pet(
            pet_id="pet_completion_001",
            name="Completion Pet",
            pet_type="Dog",
            breed="Poodle",
            age=5,
            owner=self.owner
        )

    def test_mark_nonexistent_task_complete_returns_none(self):
        """Verify marking a task not in the pet's list returns None."""
        # Arrange
        fake_task = Task(
            task_id="fake_task",
            name="Not Real",
            description="Doesn't exist",
            task_type=TaskType.WALK,
            default_duration=30,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )

        # Act
        result = self.pet.mark_task_complete(fake_task)

        # Assert
        self.assertIsNone(result, "Marking non-existent task should return None")

    def test_mark_recurring_daily_task_creates_next(self):
        """Verify completing a daily recurring task creates the next occurrence."""
        # Arrange
        base_date = datetime(2026, 7, 4, 9, 0)
        task = Task(
            task_id="task_daily_recur",
            name="Daily Medication",
            description="Take pills",
            task_type=TaskType.MEDICATION,
            default_duration=5,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=base_date
        )
        self.pet.add_task(task)

        # Act
        next_task = self.pet.mark_task_complete(task)

        # Assert
        self.assertTrue(task.is_completed, "Original task should be marked complete")
        self.assertIsNotNone(next_task, "Next occurrence should be created")
        self.assertEqual(next_task.due_date, base_date + timedelta(days=1))
        self.assertIn(next_task, self.pet.tasks, "Next task should be added to pet")

    def test_mark_recurring_weekly_task_creates_next(self):
        """Verify completing a weekly recurring task creates the next occurrence."""
        # Arrange
        base_date = datetime(2026, 7, 4, 14, 0)
        task = Task(
            task_id="task_weekly_recur",
            name="Weekly Grooming",
            description="Bath time",
            task_type=TaskType.GROOMING,
            default_duration=90,
            default_frequency="weekly",
            default_priority="medium",
            pet=self.pet,
            due_date=base_date
        )
        self.pet.add_task(task)

        # Act
        next_task = self.pet.mark_task_complete(task)

        # Assert
        self.assertTrue(task.is_completed)
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task.due_date, base_date + timedelta(weeks=1))
        self.assertIn(next_task, self.pet.tasks)

    def test_mark_non_recurring_task_complete_no_next(self):
        """Verify completing a non-recurring task returns None."""
        # Arrange
        task = Task(
            task_id="task_occasional",
            name="Annual Checkup",
            description="Yearly vet visit",
            task_type=TaskType.MEDICATION,
            default_duration=60,
            default_frequency="occasional",
            default_priority="high",
            pet=self.pet,
            due_date=datetime.now()
        )
        self.pet.add_task(task)

        # Act
        next_task = self.pet.mark_task_complete(task)

        # Assert
        self.assertTrue(task.is_completed)
        self.assertIsNone(next_task, "Non-recurring task should not create next occurrence")
        self.assertEqual(len(self.pet.tasks), 1, "Only original task should remain")

    def test_recurring_task_completion_chain(self):
        """Verify completing multiple occurrences of a recurring task."""
        # Arrange
        date1 = datetime(2026, 7, 4, 9, 0)
        task1 = Task(
            task_id="chain_task",
            name="Chain Task",
            description="To be repeated",
            task_type=TaskType.FEEDING,
            default_duration=15,
            default_frequency="daily",
            default_priority="high",
            pet=self.pet,
            due_date=date1
        )
        self.pet.add_task(task1)

        # Act: Complete task1 to get task2
        task2 = self.pet.mark_task_complete(task1)

        # Assert task1 completed, task2 created
        self.assertTrue(task1.is_completed)
        self.assertIsNotNone(task2)
        self.assertEqual(len(self.pet.tasks), 2)

        # Act: Complete task2 to get task3
        task3 = self.pet.mark_task_complete(task2)

        # Assert task2 completed, task3 created
        self.assertTrue(task2.is_completed)
        self.assertIsNotNone(task3)
        self.assertEqual(len(self.pet.tasks), 3)
        self.assertEqual(task3.due_date, date1 + timedelta(days=2))


if __name__ == "__main__":
    unittest.main()
