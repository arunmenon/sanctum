"""sanctum-ref: the lab's reference Sanctum (lab plan §7), configs C1-naive, C1-fair and C2.

Runs as its own process (`python -m sanctum_ref`), serves `sanctum.retrieve` over MCP stdio,
and reaches hubs only through the runner's gateway proxy. Imports only `sanctum_contracts`,
the standard library, `mcp`, `pydantic`, `pyyaml` and `tiktoken`. No LLM, no memory, no
name translation: those arrive with C4 (M4)."""
