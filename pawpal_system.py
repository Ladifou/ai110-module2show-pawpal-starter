from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum


class TaskType(Enum):
    WALK = "walk"
    FEEDING = "feeding"
    MEDICATION = "medication"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"


@dataclass
class Owner:
    owner_id: str
    name: str
    email: str
    phone: str
    address: str
    preferences: List[str] = field(default_factory=list)

    def add_preference(self, preference: str) -> None:
        """Add a scheduling preference for the owner."""
        if preference not in self.preferences:
            self.preferences.append(preference)

    def get_preferences(self) -> List[str]:
        """Retrieve a copy of the owner's scheduling preferences."""
        return self.preferences.copy()

    def remove_preference(self, preference: str) -> None:
        """Remove a scheduling preference from the owner."""
        if preference in self.preferences:
            self.preferences.remove(preference)

    def request_daily_plan(self, pet: 'Pet', date: datetime) -> Dict:
        """Request a daily schedule plan for a pet."""
        scheduler = Scheduler(f"scheduler_{pet.pet_id}", pet)
        return scheduler.generate_daily_plan(date)


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
        """Generate a daily schedule plan for the pet based on priority and constraints."""
        constraints = self.generate_constraints(self.pet, self.pet.owner)
        scheduled_tasks = []
        scheduling_reasons = []

        # Sort tasks by priority and frequency
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (
                {"high": 0, "medium": 1, "low": 2}.get(t.priority.lower(), 3),
                {"daily": 0, "weekly": 1, "occasional": 2}.get(t.default_frequency.lower(), 3)
            )
        )

        for task in sorted_tasks:
            available_slot = self.find_available_slot(task, constraints)
            if available_slot:
                duration_minutes = task.get_duration()
                total_minutes = available_slot.minute + duration_minutes

                if total_minutes < 60:
                    end_time = available_slot.replace(minute=total_minutes)
                else:
                    hours_to_add = total_minutes // 60
                    remaining_minutes = total_minutes % 60
                    end_time = available_slot.replace(
                        hour=available_slot.hour + hours_to_add,
                        minute=remaining_minutes
                    )

                task.update_time_slot(available_slot, end_time)
                scheduled_tasks.append(task)

                # Generate explanation for this task
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

    def _generate_task_explanation(self, task: Task, start_time: datetime, end_time: datetime) -> str:
        """Generate a string explaining why a task was scheduled at a particular time."""
        reason = f"✓ {task.name} scheduled at {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

        if task.priority.lower() == "high":
            reason += " (High priority task)"
        elif task.task_type == TaskType.WALK and "morning" in " ".join(self.pet.owner.get_preferences()).lower():
            reason += " (Scheduled during morning preference)"
        elif task.task_type == TaskType.FEEDING:
            reason += " (Essential feeding time)"
        elif task.task_type == TaskType.MEDICATION:
            reason += " (Medication must be administered)"

        return reason

    def generate_constraints(self, pet: Pet, owner: Owner) -> List[Constraint]:
        """Generate scheduling constraints from owner preferences (morning -> time window, available -> availability)."""
        constraints = []

        for preference in owner.get_preferences():
            if "morning" in preference.lower():
                constraints.append(Constraint(
                    f"constraint_{len(constraints)}",
                    "time_window",
                    preference,
                    is_hard_constraint=False,
                    priority=1,
                    affected_times={"start_hour": 6, "end_hour": 12}
                ))
            elif "available" in preference.lower():
                constraints.append(Constraint(
                    f"constraint_{len(constraints)}",
                    "availability",
                    preference,
                    is_hard_constraint=True,
                    priority=2
                ))

        return constraints

    def schedule_tasks(self, task: Task, constraints: List[Constraint]) -> bool:
        """Schedule a task if constraints are satisfied and no time conflicts exist."""
        if not self.validate_constraints(task, constraints):
            return False
        if self.check_time_overlap(task):
            return False
        self.tasks.append(task)
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

        for scheduled_task in self.tasks:
            if scheduled_task.start_time and scheduled_task.end_time:
                if not (task.end_time <= scheduled_task.start_time or
                        task.start_time >= scheduled_task.end_time):
                    return True
        return False

    def find_available_slot(self, task: Task, constraints: List[Constraint]) -> Optional[datetime]:
        """Find an available time slot for a task within business hours (9 AM - 5 PM)."""
        start_hour = 9
        start_minute = 0

        # Find the last scheduled task with an end time
        scheduled_with_times = [t for t in self.tasks if t.end_time]
        if scheduled_with_times:
            last_task = max(scheduled_with_times, key=lambda t: t.end_time)
            if last_task.end_time:
                start_hour = last_task.end_time.hour
                start_minute = last_task.end_time.minute

        # Get current date from the task's due date
        base_date = task.due_date if task.due_date else datetime.now()
        available_slot = base_date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)

        # Check if within business hours (9 AM to 5 PM)
        if available_slot.hour >= 17:
            return None

        return available_slot

    def explain_schedule(self, daily_plan_explanation: str = "") -> str:
        """Generate a detailed human-readable explanation of the daily schedule with statistics."""
        if not self.tasks:
            return "No tasks scheduled."

        explanation = f"\n{'='*60}\n"
        explanation += f"DAILY SCHEDULE FOR {self.pet.name.upper()}\n"
        explanation += f"{'='*60}\n"

        sorted_tasks = sorted(self.tasks, key=lambda t: t.start_time or datetime.min)

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
        explanation += f"Total Tasks: {len(self.tasks)}\n"
        total_duration = sum(t.get_duration() for t in self.tasks)
        explanation += f"Total Duration: {total_duration} minutes\n"
        explanation += f"Schedule Start: {sorted_tasks[0].start_time.strftime('%H:%M') if sorted_tasks else 'N/A'}\n"
        explanation += f"Schedule End: {sorted_tasks[-1].end_time.strftime('%H:%M') if sorted_tasks else 'N/A'}\n"
        explanation += f"{'='*60}\n"

        return explanation
