# superpowers-executing-plans

Adapted from `obra/superpowers` for Cline.
Use the active Cline superpowers rules to translate any Claude Code specific tool references.

Original skill name: `executing-plans`
Original trigger description: Use when you have a written implementation plan to execute in a separate session with review checkpoints

## Instructions

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Note:** Tell your human partner that Superpowers works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use superpowers:subagent-driven-development instead of this skill.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

## Integration

**Required workflow skills:**
- **superpowers:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting
- **superpowers:writing-plans** - Creates the plan this skill executes
- **superpowers:finishing-a-development-branch** - Complete development after all tasks

## Host Adaptation

When executing a plan in this adapter, treat document reading, testing, and doc backfill as part of the work instead of optional cleanup.

1. Before the first code edit, use the tool's native text-search capability, or whatever retrieval method it judges best, then read the matching repository `README` sections, any relevant module or service `README` sections, the implementation plan, and any referenced spec, design, interface, data-structure, schema, Redis, S3, tech-stack, or operational passages. Keep that reading scoped to the current task, and do not read entire unrelated documents. If the task touches interfaces, data structures, Redis, S3, or stack-specific behavior, read those materials first.
2. If the plan assumes a document exists but it is missing, stale, or contradictory, stop and raise that issue before continuing.
3. After code changes, add or update unit tests for the affected behavior. Do not skip this unless the user has explicitly accepted the gap.
4. If the change crosses service, API, storage, or workflow boundaries and integration testing is feasible in the current repository, run or add integration tests too. If it is not feasible, say why.
5. If the implementation changes documented behavior, contracts, fields, examples, architecture notes, or runbooks, update the relevant documents before claiming completion.
6. In the final handoff, include a clear implementation summary with exact file paths: which files were added, which files were modified, which documents you read, which documents you backfilled, which unit tests ran, which integration tests ran, and how they performed.
7. Report test results with the best available completion signal: exact pass rate when available, otherwise pass/total or pass/fail counts. If a relevant test was not run, mark it `NOT RUN`. If anything failed, mark it clearly with `FAILED` and do not bury it in prose.
8. If a relevant document was not updated yet, say so explicitly and mark it `NOT BACKFILLED` or `BACKFILL REQUIRED` instead of implying it was done.

