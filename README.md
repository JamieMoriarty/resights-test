# Assumptions in the solution

## Handling loops in ownership structure.

For reference below, say the company in focus is X.

1. Loops do **not** contribute to ownership shares (i.e., they have weight 0). In other words, suppose A owns 50% of B, and B owns 20% of X, AND B owns 10% of A. Then A owns 50% \* 20% of X, the fact that B owns a bit of itself via A does **not** add anything to its ownership share of X.
2. Different paths from A to X **do** contribute to ownership shares. E.g., if A owns 50% in both B and C, who both own 10% in X, then A owns 2 \* (50% \* 10%) in X.

# Running & output

Data inputs for the script are JSON files matching the format of the provided examples. To input them, change line 4 in the script to match the OS path for the file.

The script outputs 2 files (in the output folder): isOwnedBy.json and owned.json. These represents the companies that the company in focus **is owned by**, and the companies which the company in focus **owns**, respectively.
