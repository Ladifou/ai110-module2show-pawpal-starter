import streamlit as st
from datetime import datetime
from pawpal_system import TaskType, Owner, Pet, Constraint, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")


st.divider()

st.subheader("👤 Owner & Pets")

if "owners" not in st.session_state:
    st.session_state.owners = {}

if "added_task_ids" not in st.session_state:
    st.session_state.added_task_ids = set()

owner_id = "owner_1"
if owner_id not in st.session_state.owners:
    st.session_state.owners[owner_id] = Owner(owner_id=owner_id, name="", email="", phone="", address="")

owner = st.session_state.owners[owner_id]

# Owner information inputs
st.markdown("#### Owner Information")
col1, col2, col3, col4 = st.columns(4)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.email = st.text_input("Email", value=owner.email)
with col3:
    owner.phone = st.text_input("Phone", value=owner.phone)
with col4:
    owner.address = st.text_input("Address", value=owner.address)

# Owner preferences
st.markdown("#### Owner Preferences")
col1, col2 = st.columns(2)
with col1:
    if st.checkbox("Prefer morning walks (6 AM - 12 PM)"):
        if "morning" not in owner.preferences:
            owner.add_preference("morning")
with col2:
    if st.checkbox("Limited availability"):
        if "limited_availability" not in owner.preferences:
            owner.add_preference("limited_availability")

st.write(f"Preferences: {', '.join(owner.preferences) if owner.preferences else 'None'}")

# Pet management
st.markdown("#### Pets")
if "pet_counter" not in st.session_state:
    st.session_state.pet_counter = 1

col1, col2, col3, col4 = st.columns(4)
with col1:
    pet_name = st.text_input("Pet name", value=f"Pet{st.session_state.pet_counter}")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    breed = st.text_input("Breed", value="Mixed")
with col4:
    age = st.number_input("Age", min_value=0, max_value=30, value=3)

if st.button("Add pet"):
    st.session_state.pet_counter += 1
    pet_id = f"pet_{st.session_state.pet_counter}"
    if "pets" not in st.session_state:
        st.session_state.pets = {}

    new_pet = Pet(
        pet_id=pet_id,
        name=pet_name,
        pet_type=species,
        breed=breed,
        age=age,
        owner=owner
    )
    st.session_state.pets[pet_id] = new_pet
    owner.add_pet(new_pet)
    
    st.success(f"Added {pet_name}!")

st.divider()
st.write(f"**Pets:** {', '.join([p.name for p in owner.pets]) if owner.pets else 'No pets added yet'}")


st.markdown("### 📋 Tasks")
st.caption("Add tasks for your pet(s). These will be scheduled with multi-pet conflict checking.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

# Select pet for task
if owner.pets:
    selected_pet = st.selectbox("Select pet for task", [p.name for p in owner.pets])

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        task_title = st.text_input("Task title", value="Walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        task_type = st.selectbox("Type", ["walk", "feeding", "medication", "enrichment", "grooming"])
    with col5:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "once"], index=0)


    if st.button("Add task"):
        st.session_state.tasks.append({
            "pet": selected_pet,
            "title": task_title,
            "duration_minutes": int(duration),
            "priority": priority,
            "type": task_type,
            "frequency": frequency
        })
        st.success(f"Added task for {selected_pet}")

    if st.session_state.tasks:
        st.write("**Current tasks:**")
        st.table(st.session_state.tasks)
    else:
        st.info("No tasks yet. Add one above.")
else:
    st.warning("Add at least one pet before creating tasks.")

st.divider()

st.subheader("📅 Generate Multi-Pet Schedule")
st.caption("Generates optimized schedules for all pets with conflict checking.")

if "all_schedules" not in st.session_state:
    st.session_state.all_schedules = None

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.error("Please add at least one task before generating a schedule.")
    elif not owner.pets:
        st.error("Please add at least one pet before generating a schedule.")
    else:
        # Create Task instances only for tasks that haven't been added yet
        for idx, task_data in enumerate(st.session_state.tasks):
            pet_name = task_data["pet"]
            pet = next((p for p in owner.pets if p.name == pet_name), None)

            if pet:
                # Check if this task already exists on the pet (by name, type, frequency)
                task_exists = any(
                    t.name == task_data["title"] and
                    t.task_type.value == task_data["type"] and
                    t.default_frequency == task_data.get("frequency", "daily")
                    for t in pet.tasks
                )

                if not task_exists:
                    task = Task(
                        task_id=f"task_{pet.pet_id}_{len(pet.tasks)}",
                        name=task_data["title"],
                        description=f"{task_data['title']} for {pet_name}",
                        task_type=TaskType[task_data["type"].upper()],
                        default_duration=task_data["duration_minutes"],
                        default_frequency=task_data.get("frequency", "daily"),
                        default_priority=task_data["priority"],
                        pet=pet,
                        due_date=datetime.now()
                    )
                    pet.add_task(task)

        # Generate schedules using global priority scheduling
        global_result = owner.generate_global_schedule(datetime.now())

        # Convert result to format expected by display code
        all_schedules = []
        for pet_id, schedule_info in global_result['pet_schedules'].items():
            pet = next((p for p in owner.pets if p.pet_id == pet_id), None)
            if pet and schedule_info['scheduled_tasks'] > 0:
                scheduler = Scheduler(scheduler_id=f"scheduler_{pet_id}", pet=pet)
                # Create a daily_plan-like structure for compatibility
                daily_plan = {
                    "date": datetime.now(),
                    "pet": pet,
                    "scheduled_tasks": schedule_info['tasks'],
                    "explanation": f"{schedule_info['scheduled_tasks']} tasks scheduled for {schedule_info['pet_name']}"
                }
                all_schedules.append((pet, scheduler, daily_plan))

        st.session_state.all_schedules = all_schedules
        st.session_state.global_result = global_result
        st.success("Schedule generated with global HIGH-priority task optimization!")

# Display schedules if they exist
if st.session_state.all_schedules:
    all_schedules = st.session_state.all_schedules

    # Display global scheduling summary
    if 'global_result' in st.session_state:
        result = st.session_state.global_result
        st.markdown("### 🎯 Global Priority Scheduling Summary")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tasks", result['total_tasks'])
        with col2:
            st.metric("Successfully Scheduled", result['total_scheduled'])
        with col3:
            st.metric("Success Rate", f"{int(result['total_scheduled']/result['total_tasks']*100)}%" if result['total_tasks'] > 0 else "N/A")

        st.caption("Scheduling Order: HIGH priority tasks first, then MEDIUM, then LOW")

        # Show scheduling order
        if result['scheduled_info']:
            st.markdown("#### Tasks Scheduled by Priority Order:")
            schedule_df_data = []
            for pet_name, task_name, priority, start_time, end_time in result['scheduled_info']:
                schedule_df_data.append({
                    "Pet": pet_name,
                    "Task": task_name,
                    "Priority": priority,
                    "Start Time": start_time,
                    "End Time": end_time
                })
            if schedule_df_data:
                st.table(schedule_df_data)

    if all_schedules:
        st.markdown("### 📊 Daily Schedules")

        # Display conflict detection
        st.markdown("### 👤 Multi-Pet Conflict Check")
        scheduler = all_schedules[0][1] if all_schedules else None
        conflicts = scheduler.detect_conflicts() if scheduler else []
        if conflicts:
            st.error("⚠️ **Conflicts Detected:** The following tasks overlap across pets:")
            for pet1_name, task1_name, time1, pet2_name, task2_name, time2 in conflicts:
                st.write(f"• {pet1_name}'s {task1_name} ({time1}) conflicts with {pet2_name}'s {task2_name} ({time2})")
        else:
            st.success("✓ No conflicts detected! All pets' schedules are compatible.")

        # Task completion and recurring task handling
        st.divider()
        st.markdown("### ✅ Mark Tasks Complete")
        st.caption("Mark tasks as complete to create the next occurrence for recurring tasks.")

        for pet, scheduler, daily_plan in all_schedules:
            st.subheader(f"🐾 {pet.name}")
            for task_idx, task in enumerate(daily_plan["scheduled_tasks"]):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    status = "✓ Completed" if task.is_completed else "⏳ Pending"
                    st.write(f"**{task.name}** ({task.default_frequency.upper()}) - {status}")
                with col2:
                    if task.start_time and task.end_time:
                        time_str = f"{task.start_time.strftime('%H:%M')} - {task.end_time.strftime('%H:%M')}"
                        st.write(f"⏰ {time_str}")
                    else:
                        st.write("⏰ Unscheduled")
                with col3:
                    if not task.is_completed:
                        def mark_complete_callback(p=pet, t=task):
                            next_task = p.mark_task_complete(t)
                            if "completion_messages" not in st.session_state:
                                st.session_state.completion_messages = []
                            if next_task:
                                msg = f"✓ {t.name} marked complete! Next {t.default_frequency} occurrence created for {next_task.due_date.strftime('%Y-%m-%d')}"
                            else:
                                msg = f"✓ {t.name} marked complete (non-recurring)"
                            st.session_state.completion_messages.append(msg)

                        st.button(f"Mark Complete", key=f"complete_{pet.pet_id}_{task_idx}", on_click=mark_complete_callback)

        # Display completion messages
        if "completion_messages" in st.session_state and st.session_state.completion_messages:
            st.success("\n".join(st.session_state.completion_messages))
            st.session_state.completion_messages = []

        # Show all tasks (including completed and upcoming)
        st.divider()
        st.markdown("### 📜 All Tasks (Including Recurring Occurrences)")

        # Sorting options (applies to all pets)
        col1, col2 = st.columns([1, 3])
        with col1:
            sort_by = st.selectbox(
                "Sort by",
                ["Default", "Time", "Priority"],
                key="sort_all_pets"
            )

        # Collect all tasks from all pets
        all_tasks_with_pets = []
        for pet in owner.pets:
            for task in pet.tasks:
                all_tasks_with_pets.append((pet, task))

        if all_tasks_with_pets:
            st.subheader("📋 All Tasks - All Pets")

            # Sort tasks based on selection
            if sort_by == "Time":
                all_tasks_with_pets = sorted(
                    all_tasks_with_pets,
                    key=lambda x: (x[1].start_time is None, x[1].start_time or datetime.min)
                )
            elif sort_by == "Priority":
                priority_order = {"high": 0, "medium": 1, "low": 2}
                all_tasks_with_pets = sorted(
                    all_tasks_with_pets,
                    key=lambda x: priority_order.get(x[1].default_priority.lower(), 3)
                )

            # Create table header
            header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8 = st.columns([1.2, 1.5, 1.5, 1.2, 1.2, 1, 1, 0.8])
            with header_col1:
                st.write("**Pet**")
            with header_col2:
                st.write("**Task**")
            with header_col3:
                st.write("**Time**")
            with header_col4:
                st.write("**Due Date**")
            with header_col5:
                st.write("**Status**")
            with header_col6:
                st.write("**Duration**")
            with header_col7:
                st.write("**Priority**")
            with header_col8:
                st.write("**Action**")

            st.divider()

            # Create table rows
            for task_idx, (pet, task) in enumerate(all_tasks_with_pets):
                if task.start_time and task.end_time:
                    time_slot = f"{task.start_time.strftime('%H:%M')} - {task.end_time.strftime('%H:%M')}"
                else:
                    time_slot = "—"

                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.2, 1.5, 1.5, 1.2, 1.2, 1, 1, 0.8])
                with col1:
                    st.write(pet.name)
                with col2:
                    st.write(task.name)
                with col3:
                    st.write(time_slot)
                with col4:
                    st.write(task.due_date.strftime('%Y-%m-%d'))
                with col5:
                    status = "✓ Complete" if task.is_completed else "⏳ Pending"
                    st.write(status)
                with col6:
                    st.write(f"{task.default_duration}m")
                with col7:
                    st.write(task.priority.upper())
                with col8:
                    if task.is_completed:
                        st.write("✓")
                    elif not task.start_time or not task.end_time:
                        st.button("✓", key=f"mark_{pet.pet_id}_{task_idx}", disabled=True, help="Schedule task first")
                    else:
                        def mark_complete_callback(p=pet, t=task):
                            next_task = p.mark_task_complete(t)
                            if "completion_messages" not in st.session_state:
                                st.session_state.completion_messages = []
                            if next_task:
                                msg = f"✓ {t.name} marked complete! Next {t.default_frequency} occurrence created for {next_task.due_date.strftime('%Y-%m-%d')}"
                            else:
                                msg = f"✓ {t.name} marked complete (non-recurring)"
                            st.session_state.completion_messages.append(msg)

                        st.button("✓", key=f"mark_{pet.pet_id}_{task_idx}", on_click=mark_complete_callback, help="Mark as complete")

            # Display scheduling explanations
            st.divider()
            st.markdown("### 📝 Scheduling Rationale")
            st.caption("Detailed explanations of why each task was scheduled at its specific time")

            for pet, scheduler, daily_plan in all_schedules:
                with st.expander(f"🐾 {pet.name} - Scheduling Details"):
                    explanation = scheduler.explain_schedule(daily_plan['explanation'])
                    st.text(explanation)
        else:
            st.info("No tasks to display.")
    else:
        st.info("No tasks scheduled. Add tasks to pets to generate schedules.")
            
    
    
