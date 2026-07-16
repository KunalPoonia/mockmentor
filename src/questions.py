"""
Question bank - seed interview questions, organised by subject -> topic.

Each subject offers a list of TOPICS; each topic has a difficulty and a small
set of conceptual seed questions. The UI shows the topic list (with difficulty)
after a subject is picked, so the user chooses what to practise. Once a session
is running, the model's follow-up questions drive it adaptively from there.

Kept in one place so the web server (server.py) and any other front end draw
from the same source. All questions are conceptual (not code-writing) so the
local model can grade them reliably, and each is answerable from the subject's
indexed corpus.
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

# Difficulty labels used in the topic picker.
BEGINNER = "Beginner"
INTERMEDIATE = "Intermediate"
ADVANCED = "Advanced"

# Topics per subject: an ordered list of {id, name, difficulty, questions}.
# OS topics all map to content inside the 5 indexed OSTEP chapters, so grading
# stays grounded. DSA topics map 1:1 to the 9 pattern notes.
TOPICS = {
    "os": [
        {
            "id": "fundamentals",
            "name": "OS Fundamentals & Virtualization",
            "difficulty": BEGINNER,
            "questions": [
                "What is an operating system and what problem does virtualization solve?",
                "What does it mean for the OS to be a 'resource manager'?",
                "What does it mean to 'virtualize' a physical resource like the CPU or memory?",
            ],
        },
        {
            "id": "scheduling",
            "name": "CPU Scheduling",
            "difficulty": INTERMEDIATE,
            "questions": [
                "What is the Shortest Job First scheduling policy and what problem does it have?",
                "How does round robin scheduling improve response time?",
                "What is the difference between turnaround time and response time?",
                "Why can a FIFO scheduler lead to the convoy effect?",
            ],
        },
        {
            "id": "address_spaces",
            "name": "Address Spaces & Virtual Memory",
            "difficulty": INTERMEDIATE,
            "questions": [
                "What is a virtual address space and why does the OS give each process one?",
                "What are the three goals of virtual memory?",
                "How does the OS give each process the illusion of its own private memory?",
            ],
        },
        {
            "id": "concurrency",
            "name": "Threads & Concurrency",
            "difficulty": INTERMEDIATE,
            "questions": [
                "What is a thread, and how does it differ from a process?",
                "Why do we need mutual exclusion when multiple threads share data?",
                "What problem do threads introduce that single-threaded programs don't have?",
            ],
        },
        {
            "id": "synchronization",
            "name": "Race Conditions & Critical Sections",
            "difficulty": ADVANCED,
            "questions": [
                "What is a race condition and why does it happen?",
                "What is a critical section and how do we protect it?",
                "Why can incrementing a shared counter from two threads produce the wrong result?",
            ],
        },
        {
            "id": "deadlocks",
            "name": "Deadlocks",
            "difficulty": ADVANCED,
            "questions": [
                "What is a deadlock, and what conditions cause it?",
                "What are the four conditions that must all hold for a deadlock to occur?",
                "How can circular wait be prevented?",
            ],
        },
    ],
    "dsa": [
        {
            "id": "arrays_two_pointers",
            "name": "Arrays & Two Pointers",
            "difficulty": BEGINNER,
            "questions": [
                "When would you use the two-pointer technique instead of a nested loop?",
                "How do two pointers let you find a pair in a sorted array in one pass?",
            ],
        },
        {
            "id": "sliding_window",
            "name": "Sliding Window",
            "difficulty": INTERMEDIATE,
            "questions": [
                "When would you use a sliding window instead of a nested loop?",
                "How does a sliding window stay linear time instead of quadratic?",
            ],
        },
        {
            "id": "binary_search",
            "name": "Binary Search",
            "difficulty": BEGINNER,
            "questions": [
                "What kind of problems can binary search solve beyond a literal lookup?",
                "Why does binary search require the data to be sorted?",
            ],
        },
        {
            "id": "linked_lists",
            "name": "Linked Lists",
            "difficulty": BEGINNER,
            "questions": [
                "How can you detect a cycle in a linked list, and why does it work?",
                "When is a linked list a better choice than an array?",
            ],
        },
        {
            "id": "stacks_queues",
            "name": "Stacks & Queues",
            "difficulty": BEGINNER,
            "questions": [
                "When would you use a stack versus a queue?",
                "How would you use a stack to check balanced parentheses?",
            ],
        },
        {
            "id": "recursion_backtracking",
            "name": "Recursion & Backtracking",
            "difficulty": INTERMEDIATE,
            "questions": [
                "Why does recursion need a base case, and what happens if you omit one?",
                "What is backtracking, and when is it the right approach?",
            ],
        },
        {
            "id": "trees",
            "name": "Trees (BFS / DFS)",
            "difficulty": INTERMEDIATE,
            "questions": [
                "When would you traverse a tree with BFS versus DFS?",
                "How would you print a binary tree level by level?",
            ],
        },
        {
            "id": "graphs",
            "name": "Graphs (BFS / DFS + basics)",
            "difficulty": ADVANCED,
            "questions": [
                "When would you model a problem as a graph rather than a tree?",
                "How does BFS find the shortest path in an unweighted graph?",
            ],
        },
        {
            "id": "dynamic_programming",
            "name": "Dynamic Programming",
            "difficulty": ADVANCED,
            "questions": [
                "What makes dynamic programming efficient compared to plain recursion?",
                "What does it mean for a problem to have 'overlapping subproblems'?",
            ],
        },
    ],
}


def get_subjects():
    """Return the subject catalogue (id -> metadata) for the selector UI."""
    return SUBJECTS


def get_topics(subject_id):
    """Return the topic list for a subject as lightweight dicts
    {id, name, difficulty, count} - no question text, just enough for the
    topic-picker screen."""
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "difficulty": t["difficulty"],
            "count": len(t["questions"]),
        }
        for t in TOPICS.get(subject_id, [])
    ]


def get_questions(subject_id, topic_id=None):
    """Return seed questions for a subject, optionally filtered to one topic.

    - topic_id given  -> that topic's questions (or [] if the topic is unknown).
    - topic_id omitted -> every question for the subject, flattened (back-compat).
    """
    topics = TOPICS.get(subject_id, [])
    if topic_id is not None:
        for t in topics:
            if t["id"] == topic_id:
                return list(t["questions"])
        return []
    flat = []
    for t in topics:
        flat.extend(t["questions"])
    return flat
