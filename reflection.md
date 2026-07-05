# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**
My initial design included the Owner, Pet, Task, Constraints, and Scheduler classes. The Owner class which has a 1 to many relation with pet class. It also has a preference attribute which influences the scheduling process. The pet class in turn can have many tasks (1 to many relationship) and holds basic information tasks and their schedules. Scheduler uses Owner preferences to create constraints which are applied when placing tasks in appropriate timeslots. It also generate the reasoning for why tasks are scheduled that way.

**b. Design changes**

Yes. The design changed during implementation. Initially the Constraint class was not part of the design. I initially had each constraints as their own classes. I found that implementing them separately felt repetative and made the design a bit cluttered. So i opted to have a single class to keep the design clean, simpler and focused on the scheduling problem.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**
The scheduler considers the time slots availabilities, priorities, frequencies, and owner preferences.
A pet's tasks can't conflict with each other including other pets if owner has multiple pets. A regular schedule starts at 9 AM but a 'Morning preferences' starts scheduling at 6AM. Higher priority and recurring tasks are scheduled first to esnsure essential care isn't skippe.

**b. Tradeoffs**
One tradeoff is the single day planning which makes it impossible to optimize across multiple days. This is reasonable as it allows to implement simpler logic; daily plans should be good enough for routine pet care.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
