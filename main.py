from datetime import datetime
from pawpal_system import Owner, Pet, Task, TaskType, Scheduler


def visualize_priority_scheduling(pets, title="PRIORITY-BASED SCHEDULING VISUALIZATION"):
    """Visualize how tasks are scheduled by priority level."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    # Collect all tasks with their priorities
    all_tasks = []
    for pet in pets:
        for task in pet.tasks:
            all_tasks.append({
                'pet': pet.name,
                'task': task.name,
                'priority': task.default_priority.upper(),
                'duration': task.default_duration,
                'start_time': task.start_time,
                'end_time': task.end_time,
                'type': task.task_type.value
            })

    if not all_tasks:
        print("No tasks to visualize.")
        return

    # Priority order mapping
    priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}

    # Sort tasks by priority
    sorted_tasks = sorted(all_tasks, key=lambda x: priority_order.get(x['priority'], 3))

    print("\nSCHEDULING QUEUE - by priority order:\n")
    print(f"{'Order':<8} {'Priority':<10} {'Pet':<12} {'Task':<20} {'Duration':<8} {'Scheduled':<10}")
    print("-" * 80)

    for idx, task in enumerate(sorted_tasks, 1):
        scheduled_status = "YES" if task['start_time'] else "NO"
        print(f"{idx:<8} {task['priority']:<10} {task['pet']:<12} {task['task']:<20} {task['duration']:>2} min  {scheduled_status:<10}")

    # Timeline visualization
    print("\n\nDAILY SCHEDULE TIMELINE:\n")

    # Group tasks by pet
    tasks_by_pet = {}
    for task in sorted_tasks:
        if task['pet'] not in tasks_by_pet:
            tasks_by_pet[task['pet']] = []
        tasks_by_pet[task['pet']].append(task)

    for pet_name, tasks in tasks_by_pet.items():
        print(f"\n{pet_name}'s Schedule:")
        print("---" + "-" * 70)

        for task in tasks:
            priority = task['priority']
            priority_tag = {'HIGH': 'HIGH  ', 'MEDIUM': 'MED   ', 'LOW': 'LOW   '}[priority]

            if task['start_time'] and task['end_time']:
                start = task['start_time'].strftime('%H:%M')
                end = task['end_time'].strftime('%H:%M')
                time_slot = f"{start}-{end}"
                status = "SCHEDULED"

                print(f"  {priority_tag} {time_slot}  {task['task']:<20} Duration: {task['duration']:>2} min  {status}")
            else:
                status = "UNSCHEDULED (no time slot)"
                print(f"  {priority_tag} ----------  {task['task']:<20} Duration: {task['duration']:>2} min  {status}")

        print("---" + "-" * 70)

    # Priority scheduling explanation
    print("\n\nSCHEDULING ALGORITHM IN ACTION:\n")
    print("Step 1: Collect all tasks")
    print(f"  Total tasks collected: {len(all_tasks)}")

    high_priority = [t for t in all_tasks if t['priority'] == 'HIGH']
    medium_priority = [t for t in all_tasks if t['priority'] == 'MEDIUM']
    low_priority = [t for t in all_tasks if t['priority'] == 'LOW']

    print(f"\nStep 2: Sort by priority level")
    print(f"  HIGH priority tasks:   {len(high_priority)} task(s)")
    print(f"  MEDIUM priority tasks: {len(medium_priority)} task(s)")
    print(f"  LOW priority tasks:    {len(low_priority)} task(s)")

    scheduled = [t for t in all_tasks if t['start_time']]
    unscheduled = [t for t in all_tasks if not t['start_time']]

    print(f"\nStep 3: Attempt to schedule tasks (highest priority first)")
    print(f"  Successfully scheduled: {len(scheduled)} tasks")
    print(f"  Could not schedule:     {len(unscheduled)} tasks")

    if unscheduled:
        print(f"\n  Unscheduled tasks (no available time slots found):")
        for task in unscheduled:
            print(f"    - {task['pet']}: {task['task']} ({task['priority']} priority)")

    # Priority impact visualization
    print("\n\nPRIORITY IMPACT ANALYSIS:\n")
    for priority_level in ['HIGH', 'MEDIUM', 'LOW']:
        tasks_at_level = [t for t in all_tasks if t['priority'] == priority_level]
        scheduled_at_level = [t for t in tasks_at_level if t['start_time']]

        if tasks_at_level:
            success_rate = (len(scheduled_at_level) / len(tasks_at_level)) * 100
            bar_filled = int(success_rate / 10)
            bar_empty = 10 - bar_filled
            visual_bar = "=" * bar_filled + " " * bar_empty

            print(f"{priority_level:8} {visual_bar}  {success_rate:5.0f}% ({len(scheduled_at_level)}/{len(tasks_at_level)} scheduled)")

    print("\n" + "=" * 80)


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
    print(f"\n[OK] Owner created: {owner.name}")

    # Add owner preferences
    owner.add_preference("prefer morning walks")
    owner.add_preference("grooming last")
    owner.add_preference("only available 9-5")
    print(f"[OK] Owner preferences added: {len(owner.preferences)} preferences")

    # Create Pet 1: Max (Dog)
    max_pet = Pet(
        pet_id="pet_001",
        name="Max",
        pet_type="Dog",
        breed="Golden Retriever",
        age=3,
        owner=owner
    )
    owner.add_pet(max_pet)
    print(f"\n[OK] Pet created: {max_pet.name} ({max_pet.pet_type})")

    # Create Pet 2: Luna (Cat)
    luna_pet = Pet(
        pet_id="pet_002",
        name="Luna",
        pet_type="Cat",
        breed="Siamese",
        age=2,
        owner=owner
    )
    owner.add_pet(luna_pet)
    print(f"[OK] Pet created: {luna_pet.name} ({luna_pet.pet_type})")

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
    print(f"[OK] Task created: {task1.name} ({task1.default_duration} mins)")

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
    print(f"[OK] Task created: {task2.name} ({task2.default_duration} mins)")

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
    print(f"[OK] Task created: {task3.name} ({task3.default_duration} mins)")

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
    print(f"[OK] Task created: {task4.name} ({task4.default_duration} mins)")

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
    print(f"[OK] Task created: {task5.name} ({task5.default_duration} mins)")

    # Create scheduler for Max and schedule tasks
    print(f"\n--- Scheduling tasks for {max_pet.name} ---")
    scheduler_max = Scheduler(
        scheduler_id="scheduler_001",
        pet=max_pet
    )

    # Add tasks to pet
    tasks_max = [task1, task2, task3]
    for task in tasks_max:
        max_pet.add_task(task)

    # Generate daily plan for Max
    daily_plan_max = scheduler_max.generate_daily_plan(today)
    print(f"\nMax's schedule: {len(daily_plan_max['scheduled_tasks'])} tasks scheduled")

    # Create scheduler for Luna and schedule tasks
    print(f"\n--- Scheduling tasks for {luna_pet.name} ---")
    scheduler_luna = Scheduler(
        scheduler_id="scheduler_002",
        pet=luna_pet
    )

    # Add tasks to pet
    tasks_luna = [task4, task5]
    for task in tasks_luna:
        luna_pet.add_task(task)

    # Generate daily plan for Luna
    daily_plan_luna = scheduler_luna.generate_daily_plan(today)
    print(f"Luna's schedule: {len(daily_plan_luna['scheduled_tasks'])} tasks scheduled")

    # Visualize priority-based scheduling
    visualize_priority_scheduling([max_pet, luna_pet])

    # Display detailed schedule explanations
    print("\n" + "=" * 60)
    print("DETAILED SCHEDULE EXPLANATIONS")
    print("=" * 60)

    print("\n--- Scheduling Rationale for Max ---")
    print(scheduler_max.explain_schedule(daily_plan_max['explanation']))

    print("\n--- Scheduling Rationale for Luna ---")
    print(scheduler_luna.explain_schedule(daily_plan_luna['explanation']))

    # Check for task conflicts
    print("\n" + "=" * 60)
    print("CONFLICT DETECTION")
    print("=" * 60)

    conflicts = scheduler_max.detect_conflicts(today)
    if conflicts:
        print(f"\nWARNING: Found {len(conflicts)} task conflict(s)!")
        for pet1_name, task1_name, time1, pet2_name, task2_name, time2 in conflicts:
            print(f"\n  WARNING: Owner cannot be in two places at once!")
            print(f"    {pet1_name}: {task1_name} at {time1}")
            print(f"    {pet2_name}: {task2_name} at {time2}")
    else:
        print("\nOK: No task conflicts detected. Owner can attend all scheduled tasks.")

    # Print summary
    print("\n" + "=" * 60)
    print("SYSTEM OVERVIEW")
    print("=" * 60)

    print(f"\nOwner Information:")
    print(f"  Name: {owner.name}")
    print(f"  Email: {owner.email}")
    print(f"  Phone: {owner.phone}")
    print(f"  Address: {owner.address}")

    print(f"\nOwner Preferences ({len(owner.preferences)}):")
    for pref in owner.preferences:
        print(f"  • {pref}")

    print(f"\nPets ({len(owner.pets)}):")
    for pet in owner.pets:
        print(f"  • {pet.name} ({pet.pet_type}) - {pet.breed}, Age: {pet.age}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
