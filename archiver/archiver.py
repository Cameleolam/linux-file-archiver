"""Core archival logic.

Resolves group members, walks home directories, moves files to archive
preserving the original directory structure.

Design principle: functions are pure where possible (take inputs, return results).
Side effects (file moves, logging) are explicit and contained.
"""