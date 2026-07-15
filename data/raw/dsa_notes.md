<!--
  ⚠️  DRAFT — REWRITE IN YOUR OWN WORDS BEFORE THE MENTOR MEETING.
  Doc 01 requires the authored content to be YOURS. This is a scaffold so the
  DSA pipeline is functional end-to-end; replace the wording below with your
  own understanding of each pattern. Keep the "## Topic" headers and the
  "What it is / When to use it / Example" structure so ingestion still works.
-->

# Data Structures & Algorithms — Interview Pattern Notes

Conceptual notes on nine common interview patterns. Each section explains what
the pattern is, the cue that tells you to reach for it, and a short worked
scenario in words (no code).

## Arrays & Two Pointers

**What it is:** A technique that walks two indices through a sequence at the same time — often one from each end, or one slow and one fast — so you can compare or combine elements without a nested loop.

**When to use it:** When the input is sorted (or can be sorted) and the problem asks you to find a pair, a triplet, or a partition that satisfies some condition, e.g. "find two numbers that sum to a target."

**Example:** To check if a sorted array contains two numbers summing to a target, start one pointer at the left and one at the right. If their sum is too big, move the right pointer left; if too small, move the left pointer right. You converge on the answer in a single pass instead of comparing every pair.

## Sliding Window

**What it is:** A moving range over a contiguous run of elements that expands and contracts as you scan, maintaining a running summary (a sum, a count, a set of characters) so you never recompute the whole window from scratch.

**When to use it:** When the problem asks for the best or a valid *contiguous* subarray or substring meeting some condition — "longest substring without repeats," "smallest subarray with sum ≥ K."

**Example:** For the longest substring without repeating characters, grow the window's right edge one character at a time. When a duplicate appears, shrink from the left until the duplicate is gone. Track the largest window size seen. Each character enters and leaves the window at most once, so it's linear time.

## Binary Search

**What it is:** A search that repeatedly halves a sorted range, discarding the half that cannot contain the answer, so the search space shrinks exponentially.

**When to use it:** When data is sorted, or when the answer lies on a monotonic range you can "guess and check" — including "search for the smallest value that still works" style problems, not just literal lookups.

**Example:** To find a target in a sorted array, look at the middle element. If it equals the target you're done; if the target is smaller, repeat on the left half; if larger, the right half. Twenty steps is enough to search a million items.

## Linked Lists

**What it is:** A chain of nodes where each node points to the next, so elements are connected by references rather than sitting in one contiguous block of memory.

**When to use it:** When you need cheap insertion or deletion in the middle without shifting other elements, or when a problem specifically hands you a linked structure to reverse, detect a cycle in, or merge.

**Example:** To detect a cycle, run a slow pointer one step at a time and a fast pointer two steps at a time. If the list loops, the fast pointer eventually laps the slow one and they meet; if it ends, there was no cycle.

## Stacks & Queues

**What it is:** Two ordering disciplines — a stack is last-in-first-out (like a pile of plates), a queue is first-in-first-out (like a line at a counter).

**When to use it:** Reach for a stack when the most recent thing must be handled first — matching brackets, undo history, depth-first traversal. Reach for a queue when things must be handled in arrival order — scheduling, breadth-first traversal.

**Example:** To check balanced parentheses, push each opening bracket onto a stack and pop when you see a closing one, verifying it matches. If the stack is empty at the end, everything was balanced.

## Recursion & Backtracking

**What it is:** Recursion solves a problem by calling itself on smaller subproblems until a base case stops it. Backtracking is recursion that builds a candidate solution step by step and abandons ("backtracks" from) a path as soon as it can't lead to a valid answer.

**When to use it:** When a problem breaks naturally into similar smaller problems (tree traversals, divide-and-conquer), or when you must explore all combinations/permutations under constraints (subsets, N-queens, maze paths).

**Example:** To generate all subsets of a set, at each element choose to include it or not, recursing on the rest. Every leaf of that decision tree is one subset. The base case — no elements left — records the subset built so far.

## Trees (BFS / DFS)

**What it is:** A hierarchical structure of nodes with a single root and no cycles. Depth-first search (DFS) goes as deep as possible before backtracking; breadth-first search (BFS) visits level by level.

**When to use it:** DFS suits problems about paths from root to leaf, subtree properties, or when recursion is natural. BFS suits problems about the shallowest/nearest result, like the minimum depth of a tree or level-order output.

**Example:** To print a binary tree level by level, use a queue: start with the root, then repeatedly dequeue a node, record its value, and enqueue its children. Because a queue is first-in-first-out, nodes come out in level order.

## Graphs (BFS / DFS + basics)

**What it is:** A set of nodes (vertices) connected by edges, which may be directed or undirected. It generalizes trees — graphs can have cycles and multiple paths between nodes.

**When to use it:** When entities have arbitrary pairwise relationships — networks, maps, dependencies. BFS finds shortest paths in unweighted graphs; DFS suits cycle detection, connectivity, and topological ordering of dependencies.

**Example:** To find the fewest hops between two cities on a flight map, run BFS from the start city, visiting all one-hop cities, then all two-hop cities, and so on. The level at which you first reach the destination is the minimum number of flights. A visited set prevents revisiting and infinite loops.

## Dynamic Programming (intro-level)

**What it is:** A technique that solves a problem by combining answers to overlapping subproblems and storing each subproblem's result so it's computed only once (memoization or a bottom-up table).

**When to use it:** When a problem has optimal substructure (the best overall answer is built from best answers to subproblems) and those subproblems repeat — "count the ways," "minimum cost," "longest/largest such that."

**Example:** Computing the Nth Fibonacci number naively recomputes the same values exponentially many times. Storing each computed value in a table (or keeping just the last two) turns it into a single linear pass — the essence of trading a little memory for a lot of speed.
