# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**
My initial design included the Owner, Pet, Task, Constraints, and Scheduler classes. The Owner class has a one-to-many relationship with the Pet class. It also has a preference attribute which influences the scheduling process. The Pet class in turn can have many tasks (one-to-many relationship) and holds basic information about tasks and their schedules. The Scheduler uses Owner preferences to create constraints which are applied when placing tasks in appropriate timeslots. It also generates the reasoning for why tasks are scheduled that way.

**b. Design changes**

Yes. The design changed during implementation. Initially the Constraint class was not part of the design. I initially had each constraint as its own class. I found that implementing them separately felt repetitive and made the design a bit cluttered. So I opted to have a single class to keep the design clean, simpler, and focused on the scheduling problem. This structure remained unchanged until the end of the project, but some attributes and methods had to be added or changed, particularly in the Scheduler() class.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**
The scheduler considers the time slot availability, priorities, frequencies, and owner preferences.
A pet's tasks can't conflict with each other or with other pets' tasks if the owner has multiple pets. A regular schedule starts at 9 AM, but a 'Morning preference' starts scheduling at 6 AM for walks. Higher priority and recurring tasks are scheduled first to ensure essential care isn't skipped.

**b. Tradeoffs**
One tradeoff is single-day planning, which makes it impossible to optimize across multiple days. This is reasonable as it allows for simpler and robust logic; daily plans should be good enough for routine pet care.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI for design brainstorming, debugging, refactoring, and code/error explanation.  
It was used to brainstorm possible objects needed for the project. It was heavily used to refactor code in agent mode to increase development speed, avoid repetitive tasks, and automate workflows. (Updating a class/function often requires updating calling files, classes, or objects). It also ran some tests after some of its implementations to make sure that updates worked as intended. I occasionally asked the coding assistant to explain why I was getting an error or how its suggestions worked. This was valuable for keeping track of all the code written in this project.  
To get the most out of the AI tool, I found that using simpler prompts and follow-up prompts (questions and requests) returned better results. I think this allowed the chat session to be focused on what I wanted to accomplish. To further focus my request or prompt, I would attach a files, (code and images), indicate selected code, and start fresh chat sessions. This regularly made the thinking process faster and more accurate. Having chat session allowed to easily back track and continue previous tasks with the AI tool.

**b. Judgment and verification**

When brainstorming ideas for objects for the project, it suggested additional classes which I thought were unnecessary. It suggested classes like TaskType, OwnerPreferences, etc., which were all just attributes for classes that I had in mind. I also rejected overcomplicated suggestions. Logic that seemed too complex for me was also disregarded as my focus was on being able to understand the code generated.

---

## 4. Testing and Verification

**a. What you tested**

The behaviors tested include task addition, sorting/filtering, recurring task generation, scheduling conflict detection, and task completion logic.
I think these behaviors provide the basis for a task scheduler. To track tasks, they need to be successfully registered. Sorting provides convenience for users to track specific task characteristics. Detecting conflicts ensures that two distinct tasks from different pets do not get scheduled at the same time; two tasks can't be completed at the same time. The completion logic ensures that tasks aren't unnecessarily repeated.

**b. Confidence**

I am not very confident that the scheduler works correctly. I believe there are edge cases that i can't think of right now. Some edge cases to test later include preference management and duplicates handling.

---

## 5. Reflection

**a. What went well**

I am satisfied with the UI design and building the app from scratch in about 1 week. While it can still be improved, I think the UI is easy to follow and provides clear direction on the next steps. Users should be able to create tasks, schedule them, and complete them.

**b. What you would improve**

One thing that I would improve is the scheduling logic. While it does a decent job at scheduling without conflict based on priorities and a few preferences, I don't think it is smart enough. Currently it can't schedule similar tasks for different pets at the same time if needed (two dogs can't play, eat, or walk at the same time). There are few available user preferences and users can't register new ones as desired.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
  I've learned the importance of consistently tracking AI-generated code in large-scale projects. I found that the further I went into the project, AI wouldn't always highlight or explain the updates it was implementing. I found myself having to "vibe code" at some point because I had a hard time finding and understanding the changes it implemented without asking for clarification.
