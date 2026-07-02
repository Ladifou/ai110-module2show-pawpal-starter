import unittest
from datetime import datetime
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


if __name__ == "__main__":
    unittest.main()
