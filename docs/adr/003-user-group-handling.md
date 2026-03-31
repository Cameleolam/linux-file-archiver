# 003 - Linux User & Group Handling

## Context
The script archives files for members of a specified Linux group. Linux group membership
has subtleties that affect which users we discover and process.

## Questions & Answers

### Q: grp.getgrnam only returns secondary group members. What about primary?
**A: Handle both.** `grp.getgrnam("testarchive").gr_mem` returns users who have
"testarchive" as a SECONDARY group (listed in `/etc/group`). Users who have it as
their PRIMARY group (the `gid` field in `/etc/passwd`) are NOT in `gr_mem`.

To find all members:
1. Get group GID: `grp.getgrnam(group_name).gr_gid`
2. Get secondary members: `grp.getgrnam(group_name).gr_mem`
3. Iterate all users: `pwd.getpwall()`, find those with matching `pw_gid`
4. Merge both lists, deduplicate

This is a common Linux gotcha. Implementing it shows systems knowledge.

### Q: User exists in /etc/passwd but home directory doesn't exist on disk?
**A: Skip with warning.** `pwd.getpwnam("alice").pw_dir` returns `/home/alice`
but `Path("/home/alice").exists()` returns False. This happens when a user was
created with `--no-create-home`, or home was manually deleted.

Get home path from pwd, check it exists on disk, if not log WARNING and skip user.
Separate the two failure modes in logging:
- "User 'alice' not found in system" (pwd.getpwnam raises KeyError)
- "User 'alice' home directory /home/alice does not exist" (Path.exists() is False)

### Q: Should the script require root?
**A: No.** Reading other users' homes typically needs root. But the script should
work for non-root too (archiving your own files from your own group).
Handle PermissionError gracefully per file: log the error, skip the file, continue.

For production deployment, recommend a dedicated service account with read access
to target home directories. Document in README, don't enforce in code.

### Q: User deleted from group between group lookup and file access?
**A: Handle gracefully.** Race condition: we resolve the group, get ["alice", "bob"],
then alice is deleted before we process her. `pwd.getpwnam("alice")` raises KeyError.
Catch it, log WARNING, skip to next user.

## Decision

### Group Member Resolution
```
1. grp.getgrnam(group_name) → get GID + secondary members
2. pwd.getpwall() → find users with matching primary GID
3. Merge + deduplicate
4. For each user: pwd.getpwnam(username) → get home directory
5. Verify home exists on disk
6. Skip with appropriate log message if any step fails
```

### Error Handling Per User
| Situation | Action | Log Level |
|-----------|--------|-----------|
| Group not found | Exit 1 | ERROR |
| Group empty (no members) | Exit 0 | INFO |
| User not found (KeyError) | Skip user | WARNING |
| Home dir doesn't exist | Skip user | WARNING |
| Home dir empty | Skip user (0 files) | INFO |
| Permission denied on home | Skip user | WARNING |

### Root vs Non-Root
- No root check in code
- PermissionError handled per-file, not per-user
- README documents: "Run as root or as a user with read access to target homes"