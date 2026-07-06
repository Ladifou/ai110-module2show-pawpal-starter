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

    def has_preference(self, keyword: str) -> bool:
        """Check if owner has a preference containing keyword."""
        keyword_lower = keyword.lower()
        return any(keyword_lower in pref.lower() for pref in self.preferences)

    def add_pet(self, pet: 'Pet') -> None:
        """Add a pet to the owner's list of pets (duplicates are not added)."""
        if pet not in self.pets:
            self.pets.append(pet)

    def filter_all_tasks(self, pet_id: Optional[str] = None, completed: Optional[bool] = None,
                         frequency: Optional[str] = None) -> List['Task']:
        """Filter tasks across all pets owned by this owner."""
        all_tasks = []
        for pet in self.pets:
            if pet_id and pet.pet_id != pet_id:
                continue
            all_tasks.extend(pet.filter_tasks(completed=completed, frequency=frequency))
        return all_tasks

    def generate_global_schedule(self, date: datetime) -> Dict:
        """Generate schedules for all pets with global high-priority task scheduling.

        All high-priority tasks across all pets are scheduled first,
        then medium-priority, then low-priority tasks.

        Args:
            date: Date to generate schedules for

        Returns:
            Dict with pet schedules and scheduling summary
        """
        # Collect all pending tasks from all pets with their pet reference
        all_tasks = []
        for pet in self.pets:
            for task in pet.tasks:
                if task.due_date.date() == date.date() and not task.is_completed:
                    all_tasks.append((pet, task))

        # Sort globally by priority (high first) then frequency
        priority_order = {"high": 0, "medium": 1, "low": 2}
        frequency_order = {"daily": 0, "weekly": 1, "occasional": 2}

        all_tasks.sort(key=lambda x: (
            priority_order.get(x[1].priority.lower(), 3),
            frequency_order.get(x[1].default_frequency.lower(), 3)
        ))

        # Schedule tasks in global priority order
        scheduled_info = []
        for pet, task in all_tasks:
            scheduler = Scheduler(scheduler_id=f"scheduler_{pet.pet_id}", pet=pet)
            constraints = scheduler.generate_constraints(pet, self, task)

            available_slot = scheduler.find_available_slot(task, constraints)
            if available_slot:
                end_time = scheduler._calculate_end_time(available_slot, task.default_duration)
                task.update_time_slot(available_slot, end_time)
                scheduled_info.append((pet.name, task.name, task.priority.upper(),
                                      available_slot.strftime('%H:%M'),
                                      end_time.strftime('%H:%M')))

        # Generate individual pet schedules
        pet_schedules = {}
        for pet in self.pets:
            scheduler = Scheduler(scheduler_id=f"scheduler_{pet.pet_id}", pet=pet)
            daily_plan = scheduler.generate_daily_plan(date)
            pet_schedules[pet.pet_id] = {
                "pet_name": pet.name,
                "scheduled_tasks": len(daily_plan['scheduled_tasks']),
                "tasks": daily_plan['scheduled_tasks']
            }

        return {
            "date": date,
            "pet_schedules": pet_schedules,
            "scheduled_info": scheduled_info,
            "total_tasks": len(all_tasks),
            "total_scheduled": len(scheduled_info)
        }


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
        """Filter tasks by completion status and/or frequency."""
        filtered = self.tasks.copy()
        if completed is not None:
            filtered = [t for t in filtered if t.is_completed == completed]
        if frequency is not None:
            filtered = [t for t in filtered if t.default_frequency.lower() == frequency.lower()]
        return filtered


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


@dataclass
class Scheduler:
    scheduler_id: str
    pet: Pet
    tasks: List[Task] = field(default_factory=list)

    def generate_daily_plan(self, date: datetime) -> Dict:
        """Generate a daily schedule plan for the pet based on priority and constraints.
        Only schedules tasks whose due_date matches the requested date."""
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
            # Generate constraints specific to this task
            constraints = self.generate_constraints(self.pet, self.pet.owner, task)
            available_slot = self.find_available_slot(task, constraints)
            if available_slot:
                end_time = self._calculate_end_time(available_slot, task.default_duration)
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
        """Generate a detailed explanation of why a task was scheduled at a particular time."""
        reasons = []

        # Priority-based reasoning
        if task.priority.lower() == "high":
            reasons.append("High priority task scheduled first")
        elif task.priority.lower() == "medium":
            reasons.append("Medium priority task scheduled after high-priority tasks")
        else:
            reasons.append("Low priority task scheduled in available slot")

        # Task type specific reasoning
        if task.task_type == TaskType.MEDICATION:
            reasons.append("Medication must be administered at regular intervals")
        elif task.task_type == TaskType.FEEDING:
            reasons.append("Essential feeding time for pet health")
        elif task.task_type == TaskType.WALK:
            reasons.append("Exercise/walk scheduled for pet activity")
        elif task.task_type == TaskType.GROOMING:
            reasons.append("Grooming session scheduled")
        elif task.task_type == TaskType.ENRICHMENT:
            reasons.append("Enrichment activity for mental stimulation")

        # Owner preference-based reasoning - check actual time constraints
        if start_time.hour >= 6 and start_time.hour < 12:
            if task.task_type == TaskType.WALK and self.pet.owner.has_preference("morning"):
                reasons.append("Scheduled during owner's preferred morning time window (6 AM - 12 PM)")
            elif self.pet.owner.has_preference("morning"):
                reasons.append("Scheduled within morning preference window")

        # Frequency-based reasoning
        if task.default_frequency.lower() == "daily":
            reasons.append("Daily recurring task")
        elif task.default_frequency.lower() == "weekly":
            reasons.append("Weekly recurring task")

        # Conflict avoidance reasoning
        if len(self.pet.owner.pets) > 1:
            reasons.append("Time selected to avoid conflicts with other pets' schedules")

        reason_text = " | ".join(reasons)
        return f"✓ {task.name} scheduled at {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n   {reason_text}"

    def generate_constraints(self, pet: Pet, owner: Owner, task: Optional['Task'] = None) -> List[Constraint]:
        """Generate scheduling constraints from owner preferences (morning -> time window, available -> availability).

        Args:
            pet: Pet being scheduled
            owner: Owner with preferences
            task: Optional task - if provided, only returns constraints applicable to this task
        """
        constraints = []
        constraint_id = 0

        for preference in owner.preferences:
            pref_lower = preference.lower()
            if "morning" in pref_lower:
                # Morning preference applies only to walk tasks
                if task is None or task.task_type == TaskType.WALK:
                    constraints.append(Constraint(
                        f"constraint_{constraint_id}",
                        "time_window",
                        preference,
                        is_hard_constraint=False,
                        priority=2,
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

    def check_owner_conflict(self, task: Task) -> bool:
        """Check if owner is busy with another pet at this task's time (multi-pet conflict).
        Only checks conflicts on the same date as the task."""
        if not task.start_time or not task.end_time:
            return False

        # Get other pets' times only for the same date as this task
        task_date = task.due_date.date()
        owner = self.pet.owner

        for other_pet in owner.pets:
            if other_pet.pet_id == self.pet.pet_id:
                continue
            for other_task in other_pet.tasks:
                # Only check conflicts for tasks on the same date
                if other_task.start_time and other_task.end_time and other_task.due_date.date() == task_date:
                    if not (task.end_time <= other_task.start_time or task.start_time >= other_task.end_time):
                        return True
        return False
    def find_available_slot(self, task: Task, constraints: List[Constraint]) -> Optional[datetime]:
        """Find an available time slot for a task considering ALL pets' schedules.
        Prioritizes slots that satisfy soft constraints (owner preferences) while respecting hard constraints.
        Uses interval-based gap detection, starting at 6 AM for morning-preferred walks, 9 AM for others."""
        base_date = task.due_date if task.due_date else datetime.now()
        duration_minutes = task.default_duration

        # Find all gaps in the schedule that fit the task duration
        gaps = self._find_schedule_gaps(base_date, duration_minutes, task)

        # Score each gap based on constraint satisfaction
        valid_gaps = []
        for gap_start in gaps:
            hard_satisfied, soft_score = self._satisfies_constraints(task, gap_start, constraints)
            if hard_satisfied:
                # Temporarily set times to verify no conflicts
                end_time = self._calculate_end_time(gap_start, duration_minutes)
                task.start_time = gap_start
                task.end_time = end_time

                if not self.check_owner_conflict(task):
                    valid_gaps.append((soft_score, gap_start))

                # Reset for next attempt
                task.start_time = None
                task.end_time = None

        # Sort by soft constraint score (descending) and return best match
        if valid_gaps:
            valid_gaps.sort(key=lambda x: x[0], reverse=True)
            return valid_gaps[0][1]

        return None

    def _find_schedule_gaps(self, base_date: datetime, duration_minutes: int, task: Optional['Task'] = None) -> List[datetime]:
        """Find all available time gaps (at least duration_minutes long) between 6 AM - 5 PM.
        Starts at 6 AM if owner has morning preference for walks, otherwise 9 AM.
        Considers both current pet's scheduled tasks and other pets' tasks on the same date."""
        gaps = []

        # Check if owner has morning preference for walks
        start_hour = 9
        if task and task.task_type == TaskType.WALK and self.pet.owner.has_preference("morning"):
            start_hour = 6

        day_start = base_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
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
        for pet in owner.pets:
            if pet.pet_id == self.pet.pet_id:
                continue
            for task in pet.tasks:
                if task.start_time and task.end_time and task.due_date.date() == plan_date:
                    all_times.append((task.start_time, task.end_time))

        return sorted(all_times, key=lambda x: x[0])

    def _satisfies_constraints(self, task: Task, start_time: datetime, constraints: List[Constraint]) -> tuple:
        """Check if a proposed start time satisfies all constraints for the task.

        Returns:
            (satisfies_hard, soft_score) - whether hard constraints pass and a score for soft constraints (higher is better)
        """
        time_slot = {"start": start_time, "end": self._calculate_end_time(start_time, task.default_duration)}
        soft_score = 0

        for constraint in constraints:
            if constraint.is_hard_constraint:
                if not constraint.validate(task, time_slot):
                    return (False, 0)
            else:
                # Soft constraint - reward if satisfied
                if constraint.validate(task, time_slot):
                    soft_score += constraint.priority

        return (True, soft_score)

    def explain_schedule(self, daily_plan_explanation: str = "") -> str:
        """Generate a detailed human-readable explanation of the daily schedule with reasoning."""
        if not self.pet.tasks:
            return "No tasks scheduled."

        explanation = f"\n{'='*60}\n"
        explanation += f"DAILY SCHEDULE FOR {self.pet.name.upper()}\n"
        explanation += f"{'='*60}\n"

        # Sort by scheduled time (start_time), with unscheduled tasks at the end
        sorted_tasks = sorted(self.pet.tasks, key=lambda t: t.start_time or datetime.max)

        explanation += f"\nTASK DETAILS WITH SCHEDULING RATIONALE:\n"
        explanation += f"{'-'*60}\n"

        scheduled_count = 0
        for task in sorted_tasks:
            if task.start_time and task.end_time:
                scheduled_count += 1
                start_str = task.start_time.strftime("%H:%M")
                end_str = task.end_time.strftime("%H:%M")
                duration = task.default_duration
                task_type = task.task_type.value.upper()
                priority = task.priority.upper()
                frequency = task.default_frequency.upper()

                explanation += f"\n{scheduled_count}. {start_str} - {end_str} | {task.name}\n"
                # Add scheduling rationale
                task_reason = self._generate_task_explanation(task, task.start_time, task.end_time)
                explanation += f"   ├─ Scheduling Rationale:\n"
                for line in task_reason.split('\n')[1:]:  # Skip the time line
                    explanation += f"   │  {line.strip()}\n"

            else:
                explanation += f"\n⚠ {task.name} (UNSCHEDULED - no available slot found)\n"

        explanation += f"\n{'-'*60}\n"
        explanation += f"SCHEDULING SUMMARY:\n"
        explanation += f"{'-'*60}\n"

        if daily_plan_explanation:
            explanation += daily_plan_explanation + "\n"

        explanation += f"Successfully Scheduled: {scheduled_count}\n"
        explanation += f"Unscheduled: {len(self.pet.tasks) - scheduled_count}\n"

        total_duration = sum(t.default_duration for t in self.pet.tasks if t.start_time and t.end_time)
        explanation += f"Total Scheduled Duration: {total_duration} minutes\n"

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
        for pet in owner.pets:
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
