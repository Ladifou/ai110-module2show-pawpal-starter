from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Set
from enum import Enum


class TaskType(Enum):
    WALK = "walk"
    FEEDING = "feeding"
    MEDICATION = "medication"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"


# Precomputed mappings to avoid recreation in lambdas
PRIORITY_MAP = {"high": 0, "medium": 1, "low": 2}
FREQUENCY_MAP = {"daily": 0, "weekly": 1, "occasional": 2}


@dataclass
class Owner:
    owner_id: str
    name: str
    email: str
    phone: str
    address: str
    preferences: List[str] = field(default_factory=list)
    pets: List['Pet'] = field(default_factory=list)
    _preference_cache: Set[str] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self):
        self._preference_cache = {p.lower() for p in self.preferences}

    def add_preference(self, preference: str) -> None:
        """Add a scheduling preference for the owner."""
        normalized = preference.lower()
        if normalized not in self._preference_cache:
            self.preferences.append(preference)
            self._preference_cache.add(normalized)

    def get_preferences(self) -> List[str]:
        """Retrieve a copy of the owner's scheduling preferences."""
        return self.preferences.copy()

    def has_preference(self, keyword: str) -> bool:
        """O(1) lookup: check if owner has a preference containing keyword."""
        return keyword.lower() in self._preference_cache

    def remove_preference(self, preference: str) -> None:
        """Remove a scheduling preference from the owner."""
        if preference in self.preferences:
            self.preferences.remove(preference)

    def add_pet(self, pet: 'Pet') -> None:
        """Add a pet to the owner's list of pets (duplicates are not added)."""
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet: 'Pet') -> None:
        """Remove a pet from the owner's list of pets."""
        if pet in self.pets:
            self.pets.remove(pet)

    def get_pets(self) -> List['Pet']:
        """Return a copy of all pets owned by this owner."""
        return self.pets.copy()

    def request_daily_plan(self, pet: 'Pet', date: datetime) -> Dict:
        """Request a daily schedule plan for a pet."""
        scheduler = Scheduler(f"scheduler_{pet.pet_id}", pet)
        return scheduler.generate_daily_plan(date)

    def filter_all_tasks(self, pet_id: Optional[str] = None, completed: Optional[bool] = None,
                         frequency: Optional[str] = None) -> List['Task']:
        """Filter tasks across all pets owned by this owner.

        Args:
            pet_id: Filter by specific pet ID. If None, return tasks from all pets.
            completed: If True, return only completed tasks. If False, return only pending. If None, return all.
            frequency: Filter by frequency ("daily", "weekly", etc.). If None, return all frequencies.

        Returns:
            List of tasks matching the filter criteria, organized by pet.
        """
        all_tasks = []

        for pet in self.pets:
            if pet_id and pet.pet_id != pet_id:
                continue
            all_tasks.extend(pet.filter_tasks(completed=completed, frequency=frequency))

        return all_tasks

    def get_all_pending_tasks(self) -> List['Task']:
        """Get all pending tasks across all owned pets."""
        return self.filter_all_tasks(completed=False)

    def get_all_completed_tasks(self) -> List['Task']:
        """Get all completed tasks across all owned pets."""
        return self.filter_all_tasks(completed=True)


@dataclass
class Pet:
    pet_id: str
    name: str
    pet_type: str
    breed: str
    age: int
    owner: Owner
    tasks: List['Task'] = field(default_factory=list)

    def update_info(self, data: dict) -> None:
        """Update pet attributes from a dictionary (tasks cannot be modified)."""
        for key, value in data.items():
            if hasattr(self, key) and key != "tasks":
                setattr(self, key, value)

    def add_task(self, task: 'Task') -> None:
        """Add a task to the pet's schedule (duplicates are not added)."""
        if task not in self.tasks:
            self.tasks.append(task)

    def get_schedule(self) -> List['Task']:
        """Retrieve a copy of all tasks scheduled for this pet."""
        return self.tasks.copy()

    def get_task_count(self) -> int:
        """Return the total number of tasks scheduled for this pet."""
        return len(self.tasks)

    def mark_task_complete(self, task: 'Task') -> Optional['Task']:
        """Mark a task as complete and create next occurrence if recurring."""
        if task not in self.tasks:
            return None

        task.mark_complete()
        next_task = task.create_next_occurrence()
        if next_task:
            self.add_task(next_task)
            return next_task
        return None

    def filter_tasks(self, completed: Optional[bool] = None, frequency: Optional[str] = None) -> List['Task']:
        """Filter tasks by completion status and/or frequency.

        Args:
            completed: If True, return only completed tasks. If False, return only pending tasks. If None, return all.
            frequency: Filter by frequency ("daily", "weekly", etc.). If None, return all frequencies.

        Returns:
            List of tasks matching the filter criteria.
        """
        filtered = self.tasks.copy()

        if completed is not None:
            filtered = [t for t in filtered if t.is_completed == completed]

        if frequency is not None:
            filtered = [t for t in filtered if t.default_frequency.lower() == frequency.lower()]

        return filtered

    def get_pending_tasks(self) -> List['Task']:
        """Get all pending (incomplete) tasks for this pet."""
        return self.filter_tasks(completed=False)

    def get_completed_tasks(self) -> List['Task']:
        """Get all completed tasks for this pet."""
        return self.filter_tasks(completed=True)

    def get_daily_tasks(self) -> List['Task']:
        """Get all daily recurring tasks for this pet."""
        return self.filter_tasks(frequency="daily")

    def get_weekly_tasks(self) -> List['Task']:
        """Get all weekly recurring tasks for this pet."""
        return self.filter_tasks(frequency="weekly")


@dataclass
class Constraint:
    constraint_id: str
    constraint_type: str
    description: str
    is_hard_constraint: bool = False
    priority: int = 0
    affected_times: Dict = field(default_factory=dict)

    def validate(self, task: 'Task', time_slot: dict) -> bool:
        """Validate that a task's time slot satisfies this constraint."""
        if self.constraint_type == "time_window":
            start_hour = self.affected_times.get("start_hour", 0)
            end_hour = self.affected_times.get("end_hour", 23)
            task_start = time_slot.get("start")
            if task_start:
                return start_hour <= task_start.hour < end_hour
            return True
        return True

    def check_conflict(self, time_slot: dict) -> bool:
        """Check if a time slot conflicts with this constraint."""
        if self.constraint_type == "unavailable_time":
            excluded_start = self.affected_times.get("start")
            excluded_end = self.affected_times.get("end")
            task_start = time_slot.get("start")
            task_end = time_slot.get("end")
            if excluded_start and excluded_end and task_start and task_end:
                return not (task_end <= excluded_start or task_start >= excluded_end)
        return False

    def get_satisfaction_score(self, task: 'Task') -> float:
        """Return a satisfaction score (0.0-1.0) for how well a task meets this preference."""
        if self.constraint_type == "preference":
            return 1.0 if self.priority > 0 else 0.5
        return 0.0


@dataclass
class Task:
    task_id: str
    name: str
    description: str
    task_type: TaskType
    default_duration: int
    default_frequency: str
    default_priority: str
    pet: Pet
    due_date: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    priority: str = field(default="")
    is_completed: bool = False
    constraints: List[Constraint] = field(default_factory=list)

    def __post_init__(self):
        if not self.priority:
            self.priority = self.default_priority

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def create_next_occurrence(self) -> Optional['Task']:
        """Create the next occurrence of this task if it's recurring (daily/weekly)."""
        from datetime import timedelta

        if self.default_frequency.lower() == "daily":
            next_due_date = self.due_date + timedelta(days=1)
        elif self.default_frequency.lower() == "weekly":
            next_due_date = self.due_date + timedelta(weeks=1)
        else:
            return None

        next_task = Task(
            task_id=f"{self.task_id}_next",
            name=self.name,
            description=self.description,
            task_type=self.task_type,
            default_duration=self.default_duration,
            default_frequency=self.default_frequency,
            default_priority=self.default_priority,
            pet=self.pet,
            due_date=next_due_date,
            priority=self.priority
        )

        for constraint in self.constraints:
            next_task.add_constraint(constraint)

        return next_task

    def update_time_slot(self, start_time: datetime, end_time: datetime) -> None:
        """Update the scheduled start and end times for this task."""
        self.start_time = start_time
        self.end_time = end_time

    def get_time_slot(self) -> dict:
        """Return a dictionary with the task's start, end, and duration info."""
        return {
            "start": self.start_time,
            "end": self.end_time,
            "duration_minutes": self.default_duration
        }

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a scheduling constraint to this task (duplicates are not added)."""
        if constraint not in self.constraints:
            self.constraints.append(constraint)

    def get_constraints(self) -> List[Constraint]:
        """Return a copy of all constraints associated with this task."""
        return self.constraints.copy()

    def get_duration(self) -> int:
        """Return the default duration of this task in minutes."""
        return self.default_duration

    def get_frequency(self) -> str:
        """Return the frequency at which this task should be performed."""
        return self.default_frequency


@dataclass
class Scheduler:
    scheduler_id: str
    pet: Pet
    tasks: List[Task] = field(default_factory=list)

    def generate_daily_plan(self, date: datetime) -> Dict:
        """Generate a daily schedule plan for the pet based on priority and constraints.
        Only schedules tasks whose due_date matches the requested date."""
        constraints = self.generate_constraints(self.pet, self.pet.owner)
        scheduled_tasks = []
        scheduling_reasons = []

        # Sort tasks once using precomputed mappings - avoid lambda dict recreation
        sorted_tasks = self._get_sorted_tasks()

        # Filter tasks to only those due on the requested date and not already completed
        plan_date = date.date()
        tasks_for_today = [t for t in sorted_tasks if t.due_date.date() == plan_date and not t.is_completed]

        # Clear previous times for tasks being rescheduled (fresh schedule generation)
        for task in tasks_for_today:
            task.start_time = None
            task.end_time = None

        for task in tasks_for_today:
            available_slot = self.find_available_slot(task, constraints)
            if available_slot:
                end_time = self._calculate_end_time(available_slot, task.get_duration())
                task.update_time_slot(available_slot, end_time)
                scheduled_tasks.append(task)

                reason = self._generate_task_explanation(task, available_slot, end_time)
                scheduling_reasons.append(reason)
            else:
                scheduling_reasons.append(f"⚠ Could not find available slot for {task.name}")

        return {
            "date": date,
            "pet": self.pet,
            "scheduled_tasks": scheduled_tasks,
            "explanation": "\n".join(scheduling_reasons)
        }

    def _get_sorted_tasks(self) -> List[Task]:
        """Sort tasks by priority and frequency using precomputed mappings."""
        return sorted(
            self.pet.tasks,
            key=lambda t: (
                PRIORITY_MAP.get(t.priority.lower(), 3),
                FREQUENCY_MAP.get(t.default_frequency.lower(), 3)
            )
        )

    def _calculate_end_time(self, start_time: datetime, duration_minutes: int) -> datetime:
        """Calculate end time given start time and duration."""
        return start_time + timedelta(minutes=duration_minutes)

    def _generate_task_explanation(self, task: Task, start_time: datetime, end_time: datetime) -> str:
        """Generate a string explaining why a task was scheduled at a particular time."""
        reason = f"✓ {task.name} scheduled at {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

        if task.priority.lower() == "high":
            reason += " (High priority task)"
        elif task.task_type == TaskType.WALK and self.pet.owner.has_preference("morning"):
            reason += " (Scheduled during morning preference)"
        elif task.task_type == TaskType.FEEDING:
            reason += " (Essential feeding time)"
        elif task.task_type == TaskType.MEDICATION:
            reason += " (Medication must be administered)"

        return reason

    def generate_constraints(self, pet: Pet, owner: Owner) -> List[Constraint]:
        """Generate scheduling constraints from owner preferences (morning -> time window, available -> availability)."""
        constraints = []
        constraint_id = 0

        for preference in owner.get_preferences():
            pref_lower = preference.lower()
            if "morning" in pref_lower:
                constraints.append(Constraint(
                    f"constraint_{constraint_id}",
                    "time_window",
                    preference,
                    is_hard_constraint=False,
                    priority=1,
                    affected_times={"start_hour": 6, "end_hour": 12}
                ))
                constraint_id += 1
            elif "available" in pref_lower:
                constraints.append(Constraint(
                    f"constraint_{constraint_id}",
                    "availability",
                    preference,
                    is_hard_constraint=True,
                    priority=2
                ))
                constraint_id += 1

        return constraints

    def schedule_tasks(self, task: Task, constraints: List[Constraint]) -> bool:
        """Schedule a task if constraints are satisfied and no time conflicts exist."""
        if not self.validate_constraints(task, constraints):
            return False
        if self.check_time_overlap(task):
            return False
        self.pet.add_task(task)
        return True

    def validate_constraints(self, task: Task, constraints: List[Constraint]) -> bool:
        """Validate that a task satisfies all hard constraints."""
        time_slot = task.get_time_slot()
        for constraint in constraints:
            if constraint.is_hard_constraint:
                if not constraint.validate(task, time_slot):
                    return False
        return True

    def check_time_overlap(self, task: Task) -> bool:
        """Check if a task's time slot overlaps with any scheduled tasks."""
        if not task.start_time or not task.end_time:
            return False

        for scheduled_task in self.pet.tasks:
            if scheduled_task.start_time and scheduled_task.end_time:
                if not (task.end_time <= scheduled_task.start_time or
                        task.start_time >= scheduled_task.end_time):
                    return True
        return False

    def check_owner_conflict(self, task: Task) -> bool:
        """Check if owner is busy with another pet at this task's time (multi-pet conflict).
        Only checks conflicts on the same date as the task."""
        if not task.start_time or not task.end_time:
            return False

        # Get other pets' times only for the same date as this task
        task_date = task.due_date.date()
        owner = self.pet.owner

        for other_pet in owner.get_pets():
            if other_pet.pet_id == self.pet.pet_id:
                continue
            for other_task in other_pet.tasks:
                # Only check conflicts for tasks on the same date
                if other_task.start_time and other_task.end_time and other_task.due_date.date() == task_date:
                    if not (task.end_time <= other_task.start_time or task.start_time >= other_task.end_time):
                        return True
        return False


    def get_owner_scheduled_times(self) -> List[tuple]:
        """Get all scheduled time slots for all pets owned by this owner (excluding current pet)."""
        all_times = []
        for pet in self.pet.owner.get_pets():
            if pet.pet_id == self.pet.pet_id:
                continue
            for task in pet.tasks:
                if task.start_time and task.end_time:
                    all_times.append((task.start_time, task.end_time, pet.name, task.name))
        return sorted(all_times, key=lambda x: x[0])

    def mark_task_complete_and_schedule_next(self, task: Task) -> Optional[Task]:
        """Mark a task as complete and create the next occurrence if it's recurring."""
        task.mark_complete()

        next_task = task.create_next_occurrence()
        if next_task:
            self.pet.add_task(next_task)
            return next_task
        return None

    def find_available_slot(self, task: Task, constraints: List[Constraint]) -> Optional[datetime]:
        """Find an available time slot for a task considering ALL pets' schedules.
        Uses interval-based gap detection to try multiple slots (9 AM - 5 PM)."""
        base_date = task.due_date if task.due_date else datetime.now()
        duration_minutes = task.default_duration

        # Find all gaps in the schedule that fit the task duration
        gaps = self._find_schedule_gaps(base_date, duration_minutes)

        # Try each gap to find one that satisfies constraints
        for gap_start in gaps:
            if self._satisfies_constraints(task, gap_start, constraints):
                # Temporarily set times to verify no conflicts
                end_time = self._calculate_end_time(gap_start, duration_minutes)
                task.start_time = gap_start
                task.end_time = end_time

                if not self.check_owner_conflict(task):
                    return gap_start

                # Reset and try next gap
                task.start_time = None
                task.end_time = None

        return None

    def _find_schedule_gaps(self, base_date: datetime, duration_minutes: int) -> List[datetime]:
        """Find all available time gaps (at least duration_minutes long) between 9 AM - 5 PM.
        Considers both current pet's scheduled tasks and other pets' tasks on the same date."""
        gaps = []

        day_start = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
        day_end = base_date.replace(hour=17, minute=0, second=0, microsecond=0)

        # Get ALL scheduled times for the requested date only (current pet + other pets)
        all_scheduled = self._get_all_scheduled_times(base_date)

        if not all_scheduled:
            # Entire day is free
            return [day_start]

        # Try slots at 30-minute intervals starting from day_start
        current = day_start
        duration_delta = timedelta(minutes=duration_minutes)

        while current + duration_delta <= day_end:
            # Check if this slot conflicts with any scheduled task on this date
            slot_end = current + duration_delta
            has_conflict = False

            for scheduled_start, scheduled_end in all_scheduled:
                # Check for overlap using interval logic
                if not (slot_end <= scheduled_start or current >= scheduled_end):
                    has_conflict = True
                    # Jump to end of this scheduled task
                    current = scheduled_end
                    break

            if not has_conflict:
                gaps.append(current)
                current += timedelta(minutes=30)  # Move to next 30-min slot
            # If conflict, current is already updated to jump past it

        return gaps

    def _get_all_scheduled_times(self, target_date: datetime) -> List[tuple]:
        """Get all scheduled time slots for a specific date across current pet AND other pets."""
        all_times = []
        owner = self.pet.owner
        plan_date = target_date.date()

        # Add current pet's scheduled tasks for the target date
        for task in self.pet.tasks:
            if task.start_time and task.end_time and task.due_date.date() == plan_date:
                all_times.append((task.start_time, task.end_time))

        # Add other pets' scheduled tasks for the target date
        for pet in owner.get_pets():
            if pet.pet_id == self.pet.pet_id:
                continue
            for task in pet.tasks:
                if task.start_time and task.end_time and task.due_date.date() == plan_date:
                    all_times.append((task.start_time, task.end_time))

        return sorted(all_times, key=lambda x: x[0])

    def _satisfies_constraints(self, task: Task, start_time: datetime, constraints: List[Constraint]) -> bool:
        """Check if a proposed start time satisfies all constraints for the task."""
        time_slot = {"start": start_time, "end": self._calculate_end_time(start_time, task.default_duration)}

        for constraint in constraints:
            if constraint.is_hard_constraint and not constraint.validate(task, time_slot):
                return False
        return True

    def explain_schedule(self, daily_plan_explanation: str = "") -> str:
        """Generate a detailed human-readable explanation of the daily schedule with statistics."""
        if not self.pet.tasks:
            return "No tasks scheduled."

        explanation = f"\n{'='*60}\n"
        explanation += f"DAILY SCHEDULE FOR {self.pet.name.upper()}\n"
        explanation += f"{'='*60}\n"

        # Sort by scheduled time (start_time), with unscheduled tasks at the end
        sorted_tasks = sorted(self.pet.tasks, key=lambda t: t.start_time or datetime.max)

        explanation += f"\nTASK DETAILS:\n"
        explanation += f"{'-'*60}\n"

        for idx, task in enumerate(sorted_tasks, 1):
            if task.start_time and task.end_time:
                start_str = task.start_time.strftime("%H:%M")
                end_str = task.end_time.strftime("%H:%M")
                duration = task.get_duration()
                task_type = task.task_type.value.upper()
                priority = task.priority.upper()

                explanation += f"\n{idx}. {start_str} - {end_str} | {task.name}\n"
                explanation += f"   ├─ Type: {task_type}\n"
                explanation += f"   ├─ Duration: {duration} minutes\n"
                explanation += f"   ├─ Priority: {priority}\n"
                explanation += f"   └─ Description: {task.description}\n"

        explanation += f"\n{'-'*60}\n"
        explanation += f"SCHEDULING SUMMARY:\n"
        explanation += f"{'-'*60}\n"

        if daily_plan_explanation:
            explanation += daily_plan_explanation + "\n"

        explanation += f"\n{'-'*60}\n"
        explanation += f"STATISTICS:\n"
        explanation += f"{'-'*60}\n"
        explanation += f"Total Tasks: {len(self.pet.tasks)}\n"
        total_duration = sum(t.get_duration() for t in self.pet.tasks)
        explanation += f"Total Duration: {total_duration} minutes\n"

        # Get first and last tasks with scheduled times
        scheduled_tasks_with_times = [t for t in sorted_tasks if t.start_time and t.end_time]
        if scheduled_tasks_with_times:
            explanation += f"Schedule Start: {scheduled_tasks_with_times[0].start_time.strftime('%H:%M')}\n"
            explanation += f"Schedule End: {scheduled_tasks_with_times[-1].end_time.strftime('%H:%M')}\n"
        else:
            explanation += f"Schedule Start: N/A\n"
            explanation += f"Schedule End: N/A\n"

        explanation += f"{'='*60}\n"

        return explanation

    def filter_scheduled_tasks(self, completed: Optional[bool] = None, frequency: Optional[str] = None,
                               scheduled_only: bool = False) -> List['Task']:
        """Filter the current pet's tasks with advanced options.

        Args:
            completed: If True, return only completed tasks. If False, return only pending. If None, return all.
            frequency: Filter by frequency ("daily", "weekly", etc.). If None, return all frequencies.
            scheduled_only: If True, only return tasks with start_time and end_time set.

        Returns:
            Filtered list of tasks.
        """
        filtered = self.pet.filter_tasks(completed=completed, frequency=frequency)

        if scheduled_only:
            filtered = [t for t in filtered if t.start_time and t.end_time]

        return filtered

    def get_unscheduled_tasks(self) -> List['Task']:
        """Get all tasks that haven't been scheduled (no start/end time)."""
        return [t for t in self.pet.tasks if not t.start_time or not t.end_time]

    def get_failed_to_schedule(self) -> List['Task']:
        """Get pending tasks that couldn't be scheduled."""
        return [t for t in self.pet.tasks if not t.is_completed and (not t.start_time or not t.end_time)]

    def detect_conflicts(self, target_date: Optional[datetime] = None) -> List[tuple]:
        """Detect conflicts between tasks on the same date across all pets owned by the owner.

        Args:
            target_date: Date to check for conflicts. If None, checks all scheduled dates.

        Returns:
            List of conflict tuples (pet1_name, task1_name, time1, pet2_name, task2_name, time2)
        """
        conflicts = []
        owner = self.pet.owner

        # Get all tasks with times to check
        all_tasks_with_times = []
        for pet in owner.get_pets():
            for task in pet.tasks:
                if task.start_time and task.end_time:
                    if target_date is None or task.due_date.date() == target_date.date():
                        all_tasks_with_times.append((pet, task))

        # Check for overlaps
        for i, (pet1, task1) in enumerate(all_tasks_with_times):
            for pet2, task2 in all_tasks_with_times[i+1:]:
                # Check if tasks are on the same date and overlap in time
                if task1.due_date.date() == task2.due_date.date():
                    # Check for time overlap
                    if not (task1.end_time <= task2.start_time or task1.start_time >= task2.end_time):
                        conflicts.append((
                            pet1.name,
                            task1.name,
                            f"{task1.start_time.strftime('%H:%M')}-{task1.end_time.strftime('%H:%M')}",
                            pet2.name,
                            task2.name,
                            f"{task2.start_time.strftime('%H:%M')}-{task2.end_time.strftime('%H:%M')}"
                        ))

        return conflicts
