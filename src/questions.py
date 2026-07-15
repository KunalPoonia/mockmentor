"""
Question bank - the seed interview questions that kick off a session.

Kept in one place so both the Streamlit app (app.py) and the web server
(server.py) draw from the same list. Once a session is running, the model's
follow-up questions drive it adaptively; these are just the starting points.

Only "Operating Systems" has a built corpus right now (the OSTEP chapters in
ChromaDB). The other subjects are declared so the UI can show them as
"coming soon" without pretending they work.
"""

# Subjects the UI can offer. `available` gates whether a session can start.
# OS (OSTEP) and DSA (self-authored notes) both have a built corpus in ChromaDB;
# System Design is declared but not yet indexed.
SUBJECTS = {
    "os": {
        "name": "Operating Systems",
        "blurb": "Concurrency, Memory, Kernels",
        "icon": "terminal",
        "available": True,
    },
    "dsa": {
        "name": "Data Structures & Algorithms",
        "blurb": "Arrays, Trees, Graphs, DP",
        "icon": "account_tree",
        "available": True,
    },
    "sd": {
        "name": "System Design",
        "blurb": "Scale, Microservices, DBs",
        "icon": "dns",
        "available": False,
    },
}

# Seed questions per subject. Conceptual (not code-writing) so the local model
# can grade them reliably. OS: 10 (2 per OSTEP chapter). DSA: ~2 per topic
# across the 9 patterns in dsa_notes.md.
QUESTION_BANK = {
    "os": [
        "What is an operating system and what problem does virtualization solve?",
        "What does it mean for the OS to be a 'resource manager'?",
        "What is the Shortest Job First scheduling policy and what problem does it have?",
        "How does round robin scheduling improve response time?",
        "What is a virtual address space and why does the OS give each process one?",
        "What are the three goals of virtual memory?",
        "What is a race condition and why does it happen?",
        "What is a critical section and how do we protect it?",
        "What is a deadlock, and what conditions cause it?",
        "How can circular wait be prevented?",
    ],
    "dsa": [
        "When would you use the two-pointer technique instead of a nested loop?",
        "When would you use a sliding window instead of a nested loop?",
        "What kind of problems can binary search solve beyond a literal lookup?",
        "Why does binary search require the data to be sorted?",
        "How can you detect a cycle in a linked list, and why does it work?",
        "When is a linked list a better choice than an array?",
        "When would you use a stack versus a queue?",
        "Why does recursion need a base case, and what happens if you omit one?",
        "What is backtracking, and when is it the right approach?",
        "What's the difference between BFS and DFS, and when would you pick one over the other?",
        "When would you model a problem as a graph rather than a tree?",
        "What makes dynamic programming efficient compared to plain recursion?",
    ],
}


def get_subjects():
    """Return the subject catalogue (id -> metadata) for the selector UI."""
    return SUBJECTS


def get_questions(subject_id):
    """Return the seed questions for a subject, or [] if it has no corpus yet."""
    return QUESTION_BANK.get(subject_id, [])
