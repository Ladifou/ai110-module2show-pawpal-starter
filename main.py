from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Task, TaskType, Constraint, Scheduler


def main():
    print("=" * 60)
    print("PAWPAL - Pet Care Scheduling System")
    print("=" * 60)

    # Create an Owner
    owner = Owner(
        owner_id="owner_001",
        name="Sarah Johnson",
        email="sarah@example.com",
        phone="555-0123",
        address="123 Main St, Springfield"
    )
    print(f"\n✓ Owner created: {owner.name}")

    # Add owner preferences
    owner.add_preference("prefer morning walks")
    owner.add_preference("grooming last")
    owner.add_preference("only available 9-5")
    print(f"✓ Owner preferences: {owner.get_preferences()}")

    # Create Pet 1: Max (Dog)
    max_pet = Pet(
        pet_id="pet_001",
        name="Max",
        pet_type="Dog",
        breed="Golden Retriever",
        age=3,
        owner=owner
    )
    print(f"\n✓ Pet created: {max_pet.name} ({max_pet.pet_type})")

    # Create Pet 2: Luna (Cat)
    luna_pet = Pet(
        pet_id="pet_002",
        name="Luna",
        pet_type="Cat",
        breed="Siamese",
        age=2,
        owner=owner
    )
    print(f"✓ Pet created: {luna_pet.name} ({luna_pet.pet_type})")

    # Get today's date for task scheduling
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Create tasks for Max
    print(f"\n--- Creating tasks for {max_pet.name} ---")

    task1 = Task(
        task_id="task_001",
        name="Morning Walk",
        description="Walk in the park",
        task_type=TaskType.WALK,
        default_duration=30,
        default_frequency="daily",
        default_priority="high",
        pet=max_pet,
        due_date=today
    )
    print(f"✓ Task created: {task1.name} ({task1.get_duration()} mins)")

    task2 = Task(
        task_id="task_002",
        name="Breakfast",
        description="Feed Max his breakfast",
        task_type=TaskType.FEEDING,
        default_duration=15,
        default_frequency="daily",
        default_priority="high",
        pet=max_pet,
        due_date=today
    )
    print(f"✓ Task created: {task2.name} ({task2.get_duration()} mins)")

    task3 = Task(
        task_id="task_003",
        name="Afternoon Walk",
        description="Walk in the neighborhood",
        task_type=TaskType.WALK,
        default_duration=30,
        default_frequency="daily",
        default_priority="medium",
        pet=max_pet,
        due_date=today
    )
    print(f"✓ Task created: {task3.name} ({task3.get_duration()} mins)")

    # Create tasks for Luna
    print(f"\n--- Creating tasks for {luna_pet.name} ---")

    task4 = Task(
        task_id="task_004",
        name="Feeding",
        description="Feed Luna her meal",
        task_type=TaskType.FEEDING,
        default_duration=10,
        default_frequency="daily",
        default_priority="high",
        pet=luna_pet,
        due_date=today
    )
    print(f"✓ Task created: {task4.name} ({task4.get_duration()} mins)")

    task5 = Task(
        task_id="task_005",
        name="Playtime",
        description="Interactive play with toys",
        task_type=TaskType.ENRICHMENT,
        default_duration=20,
        default_frequency="daily",
        default_priority="medium",
        pet=luna_pet,
        due_date=today
    )
    print(f"✓ Task created: {task5.name} ({task5.get_duration()} mins)")

    # Create scheduler for Max and schedule tasks
    print(f"\n--- Scheduling tasks for {max_pet.name} ---")
    scheduler_max = Scheduler(
        scheduler_id="scheduler_001",
        pet=max_pet
    )

    # Add tasks to scheduler
    tasks_max = [task1, task2, task3]
    for task in tasks_max:
        scheduler_max.tasks.append(task)

    # Generate daily plan for Max
    daily_plan_max = scheduler_max.generate_daily_plan(today)
    print(f"\n{scheduler_max.explain_schedule(daily_plan_max['explanation'])}")

    # Create scheduler for Luna and schedule tasks
    print(f"\n--- Scheduling tasks for {luna_pet.name} ---")
    scheduler_luna = Scheduler(
        scheduler_id="scheduler_002",
        pet=luna_pet
    )

    # Add tasks to scheduler
    tasks_luna = [task4, task5]
    for task in tasks_luna:
        scheduler_luna.tasks.append(task)

    # Generate daily plan for Luna
    daily_plan_luna = scheduler_luna.generate_daily_plan(today)
    print(f"\n{scheduler_luna.explain_schedule(daily_plan_luna['explanation'])}")

    # Print summary
    print("\n" + "=" * 60)
    print("DAILY SCHEDULE SUMMARY")
    print("=" * 60)
    print(f"Owner: {owner.name}")
    print(f"Date: {today.strftime('%B %d, %Y')}")
    print(f"\nOwner Preferences:")
    for pref in owner.get_preferences():
        print(f"  • {pref}")

    print(f"\n{max_pet.name}'s Schedule:")
    print(f"  Total tasks: {len(scheduler_max.tasks)}")
    print(f"  Total duration: {sum(t.get_duration() for t in scheduler_max.tasks)} minutes")

    print(f"\n{luna_pet.name}'s Schedule:")
    print(f"  Total tasks: {len(scheduler_luna.tasks)}")
    print(f"  Total duration: {sum(t.get_duration() for t in scheduler_luna.tasks)} minutes")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
