# Shipping harness fixture

One synthetic CodeHub artifact, one public task and separate evaluator-side gold. This is a checked-in, inference-free example of the reusable bundle contract. It has one direct-hub arm and a zero inference ceiling; it does not configure a Sanctum runtime or prove answer quality.

The `private/` directory contains synthetic fixture gold, not credentials. The controller keeps it outside the agent workspace. Engineers can read it to understand scoring.

Start with the [offline tutorial](../../../docs/lab/quickstart.md). Use fresh ignored output directories for attempts. Do not edit an already-dispatched bundle to change its pins; copy it to a new experiment first.
