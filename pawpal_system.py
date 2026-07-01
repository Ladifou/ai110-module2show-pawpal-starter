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
        pass

    def get_preferences(self) -> List[str]:
        pass

    def remove_preference(self, preference: str) -> None:
        pass

    def request_daily_plan(self, pet: 'Pet', date: datetime) -> Dict:
        pass


@dataclass
class Pet:
    pet_id: str
    name: str
    pet_type: str
    breed: str
    age: int
    owner: Owner

    def update_info(self, data: dict) -> None:
        pass

    def get_schedule(self) -> List['Task']:
        pass


@dataclass
class Constraint:
    constraint_id: str
    constraint_type: str
    description: str
    is_hard_constraint: bool = False
    priority: int = 0
    affected_times: Dict = field(default_factory=dict)

    def validate(self, task: 'Task', time_slot: dict) -> bool:
        pass

    def check_conflict(self, time_slot: dict) -> bool:
        pass

    def get_satisfaction_score(self, task: 'Task') -> float:
        pass


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
        pass

    def update_time_slot(self, start_time: datetime, end_time: datetime) -> None:
        pass

    def get_time_slot(self) -> dict:
        pass

    def add_constraint(self, constraint: Constraint) -> None:
        pass

    def get_constraints(self) -> List[Constraint]:
        pass

    def get_duration(self) -> int:
        pass

    def get_frequency(self) -> str:
        pass


@dataclass
class Scheduler:
    scheduler_id: str
    pet: Pet
    owner: Owner
    tasks: List[Task] = field(default_factory=list)

    def generate_daily_plan(self, date: datetime) -> Dict:
        pass

    def generate_constraints(self, pet: Pet, owner: Owner) -> List[Constraint]:
        pass

    def schedule_tasks(self, task: Task, constraints: List[Constraint]) -> bool:
        pass

    def validate_constraints(self, task: Task, constraints: List[Constraint]) -> bool:
        pass

    def check_time_overlap(self, task: Task) -> bool:
        pass

    def find_available_slot(self, task: Task, constraints: List[Constraint]) -> Optional[datetime]:
        pass

    def explain_schedule(self) -> str:
        pass
