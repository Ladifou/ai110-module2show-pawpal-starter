import streamlit as st
from datetime import datetime
from pawpal_system import TaskType, Owner, Pet, Constraint, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("👤 Owner & Pets")

if "owners" not in st.session_state:
    st.session_state.owners = {}

if "added_task_ids" not in st.session_state:
    st.session_state.added_task_ids = set()

owner_id = "owner_1"
if owner_id not in st.session_state.owners:
    st.session_state.owners[owner_id] = Owner(owner_id=owner_id, name="Jordan", email="", phone="", address="")

owner = st.session_state.owners[owner_id]
st.write(f"**Owner:** {owner.name}")

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

st.write(f"Preferences: {', '.join(owner.get_preferences()) if owner.get_preferences() else 'None'}")

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
st.write(f"**Pets:** {', '.join([p.name for p in owner.get_pets()]) if owner.get_pets() else 'No pets added yet'}")


st.markdown("### 📋 Tasks")
st.caption("Add tasks for your pet(s). These will be scheduled with multi-pet conflict checking.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

# Select pet for task
if owner.get_pets():
    selected_pet = st.selectbox("Select pet for task", [p.name for p in owner.get_pets()])

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
        frequency = st.selectbox("Frequency", ["daily", "weekly"], index=0)

    if st.button("Add task"):
        st.session_state.tasks.append({
            "pet": selected_pet,
            "title": task_title,
            "duration_minutes": int(duration),
            "priority": priority,
            "type": task_type,
            "frequency": frequency
        })
        st.session_state.added_task_ids.clear()  # Reset tracking when new task is added
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

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.error("Please add at least one task before generating a schedule.")
    elif not owner.get_pets():
        st.error("Please add at least one pet before generating a schedule.")
    else:
        st.success("Schedule generated with multi-pet conflict checking!")

        # Create Task instances only for tasks that haven't been added yet
        for idx, task_data in enumerate(st.session_state.tasks):
            task_key = f"{idx}_{task_data['pet']}_{task_data['title']}_{task_data['type']}_{task_data.get('frequency', 'daily')}"

            # Skip if this task was already added
            if task_key in st.session_state.added_task_ids:
                continue

            pet_name = task_data["pet"]
            pet = next((p for p in owner.get_pets() if p.name == pet_name), None)

            if pet:
                task = Task(
                    task_id=f"task_{idx}",
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
                st.session_state.added_task_ids.add(task_key)  # Mark as added

        # Generate schedules for all pets
        all_schedules = []
        for pet in owner.get_pets():
            if pet.get_task_count() > 0:
                scheduler = Scheduler(scheduler_id=f"scheduler_{pet.pet_id}", pet=pet)
                scheduler.tasks = pet.get_schedule()
                daily_plan = scheduler.generate_daily_plan(datetime.now())
                all_schedules.append((pet, scheduler, daily_plan))

        # Display schedules for all pets
        if all_schedules:
            st.markdown("### 📊 Daily Schedules")

            for pet, scheduler, daily_plan in all_schedules:
                with st.expander(f"🐾 {pet.name}'s Schedule", expanded=True):
                    st.write(scheduler.explain_schedule(daily_plan["explanation"]))

                    st.subheader("Scheduled Tasks")
                    table_data = []
                    for task in daily_plan["scheduled_tasks"]:
                        table_data.append({
                            "Task": task.name,
                            "Start Time": task.start_time.strftime('%H:%M') if task.start_time else 'N/A',
                            "End Time": task.end_time.strftime('%H:%M') if task.end_time else 'N/A',
                            "Duration (min)": task.default_duration,
                            "Priority": task.priority.upper(),
                            "Type": task.task_type.value.upper()
                        })
                    st.table(table_data)

            # Display owner's consolidated schedule
            st.markdown("### 👤 Owner's Consolidated Schedule")
            owner_schedule = scheduler.get_owner_scheduled_times()
            if owner_schedule:
                st.info("⚠️ **Conflict Check:** The system checked all pets' schedules for overlaps.")
                for start, end, pet_name, task_name in owner_schedule:
                    st.write(f"• {start.strftime('%H:%M')} - {end.strftime('%H:%M')} | {pet_name}: {task_name}")
            else:
                st.info("No conflicts detected! All pets' schedules fit within available time.")

            # Task completion and recurring task handling
            st.divider()
            st.markdown("### ✅ Mark Tasks Complete")
            st.caption("Mark tasks as complete to create the next occurrence for recurring tasks.")

            for pet, scheduler, daily_plan in all_schedules:
                st.subheader(f"🐾 {pet.name}")
                for task_idx, task in enumerate(daily_plan["scheduled_tasks"]):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        status = "✓ Completed" if task.is_completed else "⏳ Pending"
                        st.write(f"**{task.name}** ({task.default_frequency.upper()}) - {status}")
                    with col2:
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

            for pet in owner.get_pets():
                if pet.get_task_count() > 0:
                    st.subheader(f"🐾 {pet.name} - All Tasks")

                    all_tasks_data = []
                    for task in pet.get_schedule():
                        all_tasks_data.append({
                            "Task": task.name,
                            "Frequency": task.default_frequency.upper(),
                            "Due Date": task.due_date.strftime('%Y-%m-%d'),
                            "Status": "✓ Complete" if task.is_completed else "⏳ Pending",
                            "Duration (min)": task.default_duration,
                            "Priority": task.priority.upper()
                        })

                    if all_tasks_data:
                        st.table(all_tasks_data)
                    else:
                        st.info("No tasks for this pet.")
        else:
            st.info("No tasks scheduled. Add tasks to pets to generate schedules.")
            
    
    
