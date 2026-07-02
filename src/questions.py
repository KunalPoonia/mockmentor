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
SUBJECTS = {
    "os": {
        "name": "Operating Systems",
        "blurb": "Concurrency, Memory, Kernels",
        "icon": "terminal",
        "available": True,
    },
    "ds": {
        "name": "Data Structures",
        "blurb": "Trees, Graphs, Hash Maps",
        "icon": "account_tree",
        "available": False,
    },
    "sd": {
        "name": "System Design",
        "blurb": "Scale, Microservices, DBs",
        "icon": "dns",
        "available": False,
    },
    "algo": {
        "name": "Algorithms",
        "blurb": "DP, Sorting, Search",
        "icon": "code",
        "available": False,
    },
}

# Seed questions per subject. 10 OS questions (2 per OSTEP chapter) line up with
# the "Question N of 10" progress indicator in the UI.
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
}


def get_subjects():
    """Return the subject catalogue (id -> metadata) for the selector UI."""
    return SUBJECTS


def get_questions(subject_id):
    """Return the seed questions for a subject, or [] if it has no corpus yet."""
    return QUESTION_BANK.get(subject_id, [])
