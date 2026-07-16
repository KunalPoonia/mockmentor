<!--
  ⚠️  DRAFT — REWRITE IN YOUR OWN WORDS BEFORE THE MENTOR MEETING.
  Doc 01 requires the authored content to be YOURS. This is a scaffold so the
  DSA pipeline is functional end-to-end; replace the wording below with your
  own understanding of each pattern. Keep the "## Topic" headers so ingestion
  still works.
-->

# Data Structures & Algorithms — Interview Pattern Notes

Conceptual notes on nine common interview patterns. Each section explains what
the pattern is, the cue that tells you to reach for it, a short worked scenario
in words (no code), its typical cost, and the mistakes people make with it.

## Arrays & Two Pointers

**What it is:** A technique that walks two indices through a sequence at the same time so you can compare or combine elements without a nested loop. The two pointers usually move in one of two styles: *opposite ends* converging toward the middle, or *same direction* at different speeds (a "fast/slow" or "read/write" pair).

**When to use it:** When the input is sorted (or can be sorted) and the problem asks you to find a pair, triplet, or partition meeting some condition — "find two numbers that sum to a target," "remove duplicates in place," "move all zeros to the end." The cue is that a brute-force answer would compare every element against every other, and sorting or ordering lets you skip most of those comparisons.

**Example:** To check whether a sorted array contains two numbers summing to a target, start one pointer at the left and one at the right. If their sum is too big, move the right pointer left (shrinking the sum); if too small, move the left pointer right (growing it). Each step rules out a whole set of pairs, so you converge in a single pass instead of comparing every pair.

**Complexity:** Usually O(n) time after an O(n log n) sort, and O(1) extra space — the big win over the O(n²) nested-loop version.

**Watch out for:** The array must actually be sorted for the opposite-ends variant to be valid; forgetting to advance a pointer (or advancing the wrong one) causes an infinite loop or a missed answer. Handle duplicates deliberately when the problem forbids repeated results.

## Sliding Window

**What it is:** A moving range over a *contiguous* run of elements that expands and contracts as you scan, maintaining a running summary (a sum, a count, a frequency map) so you never recompute the whole window from scratch. It is really the same-direction two-pointer idea specialized to "a window with a left and right edge."

**When to use it:** When the problem asks for the best or a valid *contiguous* subarray or substring meeting some condition — "longest substring without repeats," "smallest subarray with sum ≥ K," "longest window with at most K distinct characters." Windows come in two flavours: *fixed size* (slide a window of length k) and *variable size* (grow the right edge, then shrink the left until the window is valid again).

**Example:** For the longest substring without repeating characters, grow the window's right edge one character at a time and track which characters are inside. When a duplicate appears, shrink from the left until the duplicate is gone, then keep going. Record the largest valid window seen. Each character is added once and removed at most once, so the whole scan is linear.

**Complexity:** O(n) time because each element enters and leaves the window at most once; O(k) space for whatever summary the window maintains.

**Watch out for:** The pattern only applies to *contiguous* ranges — if the elements you want can be non-adjacent, a window won't capture them. The classic bug is recomputing the window's summary from scratch on every move (which quietly makes it O(n·k) again) instead of updating it incrementally as the edges move.

## Binary Search

**What it is:** A search that repeatedly halves a range and discards the half that cannot contain the answer, so the search space shrinks exponentially. The deeper idea is that it works on any *monotonic* predicate — a condition that is false, false, …, then true, true — not just on literally sorted arrays.

**When to use it:** When data is sorted, or when the answer lives on a monotonic range you can "guess and check." That includes "search for the smallest/largest value that still satisfies a condition" problems ("binary search on the answer"), like the minimum capacity that finishes a job in time. The cue is that checking a candidate answer is cheap and, once a candidate works, every larger (or smaller) one does too.

**Example:** To find a target in a sorted array, look at the middle element. If it equals the target you're done; if the target is smaller, repeat on the left half; if larger, on the right half. Because each step throws away half of what remains, about twenty steps suffice to search a million items, versus up to a million for a linear scan.

**Complexity:** O(log n) time, O(1) space for the iterative version.

**Watch out for:** Off-by-one errors in the bounds and the mid calculation are the most common source of bugs — be clear about whether the range is inclusive or exclusive and whether you're searching for "equal to" or "first that satisfies." An infinite loop happens if the range doesn't actually shrink each iteration.

## Linked Lists

**What it is:** A chain of nodes where each node holds a value and a reference to the next node (and sometimes the previous), so elements are connected by pointers rather than sitting in one contiguous block of memory.

**When to use it:** When you need cheap insertion or deletion in the middle without shifting other elements, when you don't know the size ahead of time, or when a problem hands you a linked structure to reverse, merge, or find the middle of. The trade-off versus an array is that you lose O(1) random access — reaching the nth node means walking n links.

**Example:** To detect a cycle, run a slow pointer one step at a time and a fast pointer two steps at a time. If the list loops, the fast pointer eventually laps the slow one and they meet inside the loop; if the fast pointer reaches the end, there was no cycle. The same fast/slow trick finds the middle node in one pass (when fast reaches the end, slow is at the middle).

**Complexity:** O(1) insertion/deletion once you hold the right node, but O(n) to *find* a node by position or value; O(1) extra space for the pointer tricks.

**Watch out for:** Losing the rest of the list by reassigning a `next` pointer before saving it, and null-pointer mistakes at the head/tail. A dummy "sentinel" head node often removes messy special-casing when the head itself might change.

## Stacks & Queues

**What it is:** Two ordering disciplines. A stack is last-in-first-out (LIFO), like a pile of plates — you only touch the top. A queue is first-in-first-out (FIFO), like a line at a counter — you add at the back and remove from the front. Both expose just a couple of O(1) operations; the discipline is the point.

**When to use it:** Reach for a stack when the most recent thing must be handled first — matching brackets, undo history, evaluating expressions, or any depth-first exploration (a stack is the explicit form of recursion's call stack). Reach for a queue when things must be handled in arrival order — task scheduling, buffering, or breadth-first exploration level by level.

**Example:** To check balanced parentheses, push each opening bracket onto a stack and, on each closing bracket, pop and verify it matches the expected opener. If a pop finds a mismatch, or the stack isn't empty at the end, the string is unbalanced. The stack naturally remembers the most recent unclosed bracket, which is exactly the one a closer must match.

**Complexity:** O(1) for push/pop and enqueue/dequeue; O(n) space for whatever you're holding.

**Watch out for:** Popping from an empty stack/queue (guard for it), and reaching for the wrong discipline — using a stack where order-of-arrival matters gives reversed results. A queue built naively on top of an array can be O(n) per dequeue unless you use a circular buffer or a deque.

## Recursion & Backtracking

**What it is:** Recursion solves a problem by calling itself on smaller subproblems until a base case stops the descent. Backtracking is recursion that builds a candidate solution one choice at a time and abandons ("backtracks" from) a partial candidate the moment it can't possibly lead to a valid answer — pruning whole branches of the search.

**When to use it:** Recursion fits problems that break into similar smaller problems (tree/graph traversal, divide-and-conquer). Backtracking fits problems that ask you to *enumerate or find* combinations, permutations, or arrangements under constraints — subsets, N-queens, Sudoku, maze paths — where you explore choices and undo them.

**Example:** To generate all subsets of a set, at each element make a choice: include it or not, recursing on the remaining elements. Every leaf of that decision tree is one subset, and the base case (no elements left) records the subset built so far. Backtracking adds a pruning step — e.g. in N-queens, abandon a placement as soon as two queens attack each other, rather than completing a doomed board.

**Complexity:** Often exponential in the worst case (there can be exponentially many combinations), but pruning can cut the explored space dramatically. Watch the recursion depth — it costs stack space proportional to how deep the calls go.

**Watch out for:** A missing or wrong base case causes infinite recursion and a stack overflow. In backtracking, forgetting to *undo* a choice before trying the next one corrupts the shared state and produces wrong results.

## Trees (BFS / DFS)

**What it is:** A hierarchical structure of nodes with a single root and no cycles; each node has children, and every node except the root has exactly one parent. Depth-first search (DFS) goes as deep as possible down one branch before backtracking (naturally expressed with recursion or a stack); breadth-first search (BFS) visits nodes level by level (using a queue).

**When to use it:** Choose DFS for problems about paths from root to leaf, subtree properties, or anything where recursion is natural — its pre/in/post-order variants suit different needs (e.g. in-order traversal of a binary search tree yields sorted values). Choose BFS for problems about the shallowest or nearest result, like the minimum depth of a tree or producing level-order output.

**Example:** To print a binary tree level by level, use a queue: enqueue the root, then repeatedly dequeue a node, record its value, and enqueue its children. Because a queue is first-in-first-out, nodes come out grouped by level. Processing the queue "one level's worth at a time" lets you know where each level ends.

**Complexity:** Both BFS and DFS visit every node once, so O(n) time. Space differs: DFS uses O(h) for the call/stack depth (h = height), while BFS uses O(w) for the queue (w = maximum width of a level) — which matters on very deep versus very wide trees.

**Watch out for:** Null-child checks before recursing/enqueueing, and picking the traversal order that actually matches the question (in-order vs pre-order vs level-order give different sequences). Deep, skewed trees can blow the recursion stack — an explicit stack avoids that.

## Graphs (BFS / DFS + basics)

**What it is:** A set of nodes (vertices) connected by edges, which may be directed or undirected and weighted or unweighted. It generalizes trees: graphs can have cycles, disconnected parts, and multiple paths between two nodes. They're usually represented as an adjacency list (each node stores its neighbours) or an adjacency matrix.

**When to use it:** When entities have arbitrary pairwise relationships — road maps, social networks, task dependencies, state machines. BFS finds the shortest path in an *unweighted* graph; DFS suits cycle detection, connectivity/component counting, and topological ordering of dependencies. If edges have weights, plain BFS no longer gives shortest paths and you move to algorithms like Dijkstra's.

**Example:** To find the fewest hops between two cities on a flight map, run BFS from the start: visit all one-hop cities, then all two-hop cities, and so on. The level at which you first reach the destination is the minimum number of flights, because BFS reaches nearer nodes before farther ones. A *visited* set is essential — without it, cycles send the search into an infinite loop and revisit nodes wastefully.

**Complexity:** O(V + E) time for BFS/DFS with an adjacency list (every vertex and edge examined once); O(V) extra space for the visited set plus the queue or recursion stack.

**Watch out for:** Forgetting the visited set (infinite loops on cycles), and mixing up directed vs undirected edges when building the adjacency list. On disconnected graphs, a single traversal won't reach everything — you must start a fresh traversal from each unvisited node to cover all components.

## Dynamic Programming (intro-level)

**What it is:** A technique that solves a problem by combining answers to *overlapping subproblems* and storing each subproblem's result so it's computed only once. There are two styles: *top-down* (recursion plus memoization — cache results as you go) and *bottom-up* (fill a table from the smallest subproblems upward). It's essentially recursion with the repeated work removed.

**When to use it:** When a problem has *optimal substructure* (the best overall answer is built from best answers to subproblems) **and** those subproblems *repeat*. Typical phrasings: "count the number of ways," "minimum/maximum cost to…," "longest/largest subsequence such that…". The cue that DP beats plain recursion is that a naive recursion would solve the same subproblem many times.

**Example:** Computing the Nth Fibonacci number naively recomputes the same values an exponential number of times. Storing each computed value in a table — or just keeping the last two — turns it into a single linear pass. The same "remember what you've already solved" move powers classics like coin change (fewest coins for an amount) and the longest common subsequence of two strings.

**Complexity:** Usually (number of distinct subproblems) × (work per subproblem). Fibonacci and coin change are O(n) / O(n·coins); two-string problems are often O(n·m). Space is the size of the table, which can sometimes be reduced by keeping only the rows/values you still need.

**Watch out for:** Getting the *state* wrong — you must identify exactly what parameters distinguish one subproblem from another, or the cache keys collide. Distinguish DP from greedy: greedy commits to a locally best choice and never reconsiders, which fails when a worse-looking early choice enables a better overall answer — that's when you need DP.
