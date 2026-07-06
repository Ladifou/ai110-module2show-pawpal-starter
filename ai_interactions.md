# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked Claude to help me implement an improved scheduling logic based on priorities and owner preferences.

**What did the agent do?**

It edited the Scheduler() class in pawpal_system.py file then ran several Bash commands.

- it ran commands to verify syntax correctness from the updates
- created a testing file to test the priority scheduling, identified errors and fixed them.
- Deleted the temporary testing file then provided an explanation of the changes implemented + tests results.

**What did you have to verify or fix manually?**

In my app, the clicking the generate schedule button caused a rerun of the app (streamlit) causing some filtering/sorting features to fail. I initially asked Claude why it was happening, it responded that it couldn't find any error in the code. I had to mention the streamlit rerun resetting sorting selections before it was able to correct the bug. Another issue that i encountered was it inconsistency to update dependent files such as main.py and app.py.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

|                       | Option A | Option B |
| --------------------- | -------- | -------- |
| **Model / tool used** |          |          |
| **Prompt**            |          |          |
| **Response summary**  |          |          |
| **What was useful**   |          |          |
| **Problems noticed**  |          |          |
| **Decision**          |          |          |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
