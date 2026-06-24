---
name: dev-journal
description: Set up and maintain a structured development journal in docs/ that tracks bugs with solutions, architectural decisions, AI session records, learnings, and future improvements. Use this skill when asked to "set up dev journal", "track our decisions", "log a bug fix", "document our session", "record learnings", "log improvements", or "initialize journal system". Configures both CLAUDE.md and AGENTS.md to maintain journal awareness across different AI coding tools.
---

# Development Journal

## Table of Contents

- [Overview](#overview)
- [When to Use This Skill](#when-to-use-this-skill)
- [Core Capabilities](#core-capabilities)
    - [1. Initial Setup - Create Journal Infrastructure](#1-initial-setup---create-memory-infrastructure)
    - [2. Configure CLAUDE.md - Journal-Aware Behavior](#2-configure-claudemd---memory-aware-behavior)
    - [3. Configure AGENTS.md - Multi-Tool Support](#3-configure-agentsmd---multi-tool-support)
    - [4. Searching Journal Files](#4-searching-memory-files)
    - [5. Updating Journal Files](#5-updating-memory-files)
    - [6. Journal File Maintenance](#6-memory-file-maintenance)
- [Templates and References](#templates-and-references)
- [Example Workflows](#example-workflows)
- [Integration with Other Skills](#integration-with-other-skills)
- [Success Criteria](#success-criteria)

## Overview

Maintain a development journal for projects by establishing a structured record-keeping system in `docs/`. This skill sets up an organized folder structure (briefing, building, fixing, planning) with five key journal files (decisions, sessions, learnings, bugs, improvements) and configures CLAUDE.md and AGENTS.md to automatically reference and maintain them. The result is a project that remembers past decisions, solutions to problems, important learning moments, and improvement ideas across coding sessions and across different AI tools.

## When to Use This Skill

Invoke this skill when:

- Starting a new project that will accumulate knowledge over time
- The project already has recurring bugs or decisions that should be documented
- The user asks to "set up dev journal", "initialize journal", or "track our decisions"
- The user wants to log a bug fix, architectural decision, AI session summary, learning, or improvement idea
- Encountering a problem that feels familiar ("didn't we solve this before?")
- Before proposing an architectural change (check existing decisions first)
- After completing a productive AI coding session that should be documented
- When discovering new concepts or techniques worth remembering
- When identifying future enhancements or feature ideas
- Working on projects with multiple developers or AI tools (Claude Code, Cursor, etc.)

## Core Capabilities

### 1. Initial Setup - Create Journal Infrastructure

When invoked for the first time in a project, create the following structure:

```

docs/

&#x20;   ├── 00\_briefing/           # Project briefing and context

&#x20;   ├── 01\_building/           # Active development records

&#x20;   │   ├── decisions.md       # Architectural Decision Records

&#x20;   │   ├── learnings.md       # New concepts and knowledge gained

&#x20;   │   └── sessions.md        # AI session summaries and reflections

&#x20;   ├── 02\_fixing/             # Bug tracking and solutions

&#x20;   │   └── bugs.md            # Bug log with solutions

&#x20;   └── 03\_planning/           # Future work and improvements

&#x20;       └── improvements.md    # Future enhancements and ideas

```

**Directory naming rationale:** Using numbered prefixes (00_, 01_, etc.) creates a natural workflow order: brief → build → fix → plan. The `docs/` location makes it look like standard engineering organization, not AI-specific tooling. This increases adoption and maintenance by human developers.

**Initial file content:** Use the following templates for each file:

#### bugs.md Template
```markdown

\# Bug Log



Track bugs with dates, solutions, and prevention notes. Search this file before debugging familiar-looking issues.



\## Format



\### YYYY-MM-DD - Brief Bug Description

\- \*\*Issue\*\*: What went wrong

\- \*\*Root Cause\*\*: Why it happened

\- \*\*Solution\*\*: How it was fixed

\- \*\*Prevention\*\*: How to avoid it in the future



\---



<!-- Add new entries below this line, newest first -->

```

#### decisions.md Template
```markdown

\# Architectural Decision Records



Document architectural choices with context, alternatives considered, and trade-offs. Check this file before proposing changes that might conflict with past decisions.



\## Format



\### ADR-XXX: Decision Title (YYYY-MM-DD)



\*\*Context:\*\*

\- Why the decision was needed

\- What problem it solves



\*\*Decision:\*\*

\- What was chosen



\*\*Alternatives Considered:\*\*

\- Option 1 -> Why rejected

\- Option 2 -> Why rejected



\*\*Consequences:\*\*

\- Benefits

\- Trade-offs



\---



<!-- Add new entries below this line, newest first -->

```

#### sessions.md Template
```markdown

\# AI Session Records



Track AI-assisted development sessions with summaries, successes, challenges, and friction points. Review this before similar sessions to learn from past experiences.



\## Format



\### YYYY-MM-DD - Session Title



\*\*What We Worked On:\*\*

\- Main objectives and tasks completed

\- Features implemented or problems solved



\*\*What Went Well:\*\*

\- Successful approaches and techniques

\- Effective collaboration patterns

\- Quick wins



\*\*What Could We Do Better:\*\*

\- Areas for improvement

\- Misunderstandings or miscommunications

\- Process inefficiencies



\*\*Friction Points:\*\*

\- Technical blockers encountered

\- Communication challenges

\- Tool or workflow limitations



\*\*Key Takeaways:\*\*

\- Lessons learned for future sessions

\- Best practices identified



\---



<!-- Add new entries below this line, newest first -->

```

#### learnings.md Template
```markdown

\# Learnings



Document new concepts, techniques, and knowledge gained. Reference this file to build on past learning and find resources for deeper understanding.



\## Format



\### YYYY-MM-DD - Learning Title



\*\*What Was New:\*\*

\- Core concept or technique learned

\- Context of when it came up



\*\*Key Points:\*\*

\- Important details to remember

\- How it works or why it matters



\*\*Sources:\*\*

\- Documentation links

\- Articles or tutorials referenced

\- Code examples or repositories



\*\*Where to Learn More:\*\*

\- Advanced resources

\- Related topics to explore

\- Practice exercises or projects



\*\*Applied In:\*\*

\- Where/how this was used in practice (optional)



\---



<!-- Add new entries below this line, newest first -->

```

#### improvements.md Template
```markdown

\# Improvements



Track future enhancements and feature ideas. Review this file during planning sessions to prioritize next steps.



\## Format



\### YYYY-MM-DD - Improvement Title



\*\*Description:\*\*

\- What the improvement would do

\- Problem it would solve or value it would add



\*\*Motivation:\*\*

\- Why this would be beneficial

\- Use cases or scenarios



\*\*Potential Approach:\*\*

\- Initial thoughts on implementation

\- Technologies or patterns to consider



\*\*Priority:\*\*

\- \[ ] High - Critical improvement

\- \[ ] Medium - Nice to have

\- \[ ] Low - Future consideration



\*\*Dependencies:\*\*

\- Prerequisites or related work needed

\- Blockers or considerations



\*\*Status:\*\*

\- \[ ] Proposed

\- \[ ] In Progress

\- \[ ] Completed

\- \[ ] Deferred



\---



<!-- Add new entries below this line, newest first -->

```

### 2. Configure CLAUDE.md - Journal-Aware Behavior

Add or update the following section in the project's `CLAUDE.md` file:

```markdown

\## Development Journal System



This project maintains a development journal in `docs/` for consistency across sessions.



\### Journal Files



\- \*\*01\_building/decisions.md\*\* - Architectural Decision Records with context and trade-offs

\- \*\*01\_building/sessions.md\*\* - AI session summaries with successes and friction points

\- \*\*01\_building/learnings.md\*\* - New concepts, techniques, and knowledge with sources

\- \*\*02\_fixing/bugs.md\*\* - Bug log with dates, solutions, and prevention notes

\- \*\*03\_planning/improvements.md\*\* - Future enhancements and feature ideas



\### Journal-Aware Protocols



\*\*Before proposing architectural changes:\*\*

\- Check `docs/01\_building/decisions.md` for existing decisions

\- Verify the proposed approach doesn't conflict with past choices

\- If it does conflict, acknowledge the existing decision and explain why a change is warranted



\*\*When encountering errors or bugs:\*\*

\- Search `docs/02\_fixing/bugs.md` for similar issues

\- Apply known solutions if found

\- Document new bugs and solutions when resolved



\*\*After completing AI coding sessions:\*\*

\- Log session summary in `docs/01\_building/sessions.md`

\- Include what worked well, friction points, and key takeaways

\- Note patterns for future sessions



\*\*When learning new concepts or techniques:\*\*

\- Document in `docs/01\_building/learnings.md` with sources and key points

\- Include links to documentation and resources for deeper learning

\- Note how the concept was applied in practice



\*\*When identifying future improvements:\*\*

\- Log ideas in `docs/03\_planning/improvements.md` with motivation and approach

\- Include priority level and dependencies

\- Update status as work progresses



\*\*When user requests journal updates:\*\*

\- Update the appropriate journal file (decisions, sessions, learnings, bugs, or improvements)

\- Follow the established format and style (bullet lists, dates, concise entries)



\### Style Guidelines for Journal Files



\- \*\*Prefer bullet lists over tables\*\* for simplicity and ease of editing

\- \*\*Keep entries concise\*\* (1-3 lines for descriptions)

\- \*\*Always include dates\*\* for temporal context

\- \*\*Include URLs\*\* for tickets, documentation, monitoring dashboards, learning resources

\- \*\*Manual cleanup\*\* of old entries is expected (not automated)

```

### 3. Configure AGENTS.md - Multi-Tool Support

If the project has an `AGENTS.md` file (used for agent workflows or multi-tool projects), add the same journal protocols. This ensures consistency whether using Claude Code, Cursor, GitHub Copilot, or other AI tools.

**If AGENTS.md exists:** Add the same "Development Journal System" section as above.

**If AGENTS.md doesn't exist:** Ask the user if they want to create it. Many projects use multiple AI tools and benefit from shared journal protocols.

### 4. Searching Journal Files

When encountering problems or making decisions, proactively search journal files:

**Search bugs.md:**
```bash

\# Look for similar errors

grep -i "connection refused" docs/02\_fixing/bugs.md



\# Find bugs by date range

grep "2025-01" docs/02\_fixing/bugs.md

```

**Search decisions.md:**
```bash

\# Check for decisions about a technology

grep -i "database" docs/01\_building/decisions.md



\# Find all ADRs

grep "^### ADR-" docs/01\_building/decisions.md

```

**Search sessions.md:**
```bash

\# Find sessions on a specific topic

grep -i "authentication" docs/01\_building/sessions.md



\# Look for friction points

grep -i "friction" docs/01\_building/sessions.md

```

**Search learnings.md:**
```bash

\# Find learning on a topic

grep -i "react hooks" docs/01\_building/learnings.md



\# Find all learning resources

grep "Sources:" docs/01\_building/learnings.md

```

**Search improvements.md:**
```bash

\# Find high priority improvements

grep -A 5 "High" docs/03\_planning/improvements.md



\# Find improvements by status

grep "In Progress" docs/03\_planning/improvements.md

```

**Use Grep tool for more complex searches:**
- Search across all journal files: `Grep(pattern="oauth", path="docs/")`
- Context-aware search: `Grep(pattern="bug", path="docs/02\_fixing/bugs.md", -A=3, -B=3)`

### 5. Updating Journal Files

When the user requests updates or when documenting resolved issues, update the appropriate journal file:

**Adding a bug entry:**
```markdown

\### YYYY-MM-DD - Brief Bug Description

\- \*\*Issue\*\*: What went wrong

\- \*\*Root Cause\*\*: Why it happened

\- \*\*Solution\*\*: How it was fixed

\- \*\*Prevention\*\*: How to avoid it in the future

```

**Adding a decision:**
```markdown

\### ADR-XXX: Decision Title (YYYY-MM-DD)



\*\*Context:\*\*

\- Why the decision was needed

\- What problem it solves



\*\*Decision:\*\*

\- What was chosen



\*\*Alternatives Considered:\*\*

\- Option 1 -> Why rejected

\- Option 2 -> Why rejected



\*\*Consequences:\*\*

\- Benefits

\- Trade-offs

```

**Adding a session record:**
```markdown

\### YYYY-MM-DD - Session Title



\*\*What We Worked On:\*\*

\- Main objectives and tasks completed



\*\*What Went Well:\*\*

\- Successful approaches and techniques



\*\*What Could We Do Better:\*\*

\- Areas for improvement



\*\*Friction Points:\*\*

\- Technical blockers encountered



\*\*Key Takeaways:\*\*

\- Lessons learned for future sessions

```

**Adding a learning:**
```markdown

\### YYYY-MM-DD - Learning Title



\*\*What Was New:\*\*

\- Core concept or technique learned



\*\*Key Points:\*\*

\- Important details to remember



\*\*Sources:\*\*

\- Documentation links

\- Articles or tutorials referenced



\*\*Where to Learn More:\*\*

\- Advanced resources

\- Related topics to explore



\*\*Applied In:\*\*

\- Where/how this was used in practice

```

**Adding an improvement:**
```markdown

\### YYYY-MM-DD - Improvement Title



\*\*Description:\*\*

\- What the improvement would do



\*\*Motivation:\*\*

\- Why this would be beneficial



\*\*Potential Approach:\*\*

\- Initial thoughts on implementation



\*\*Priority:\*\*

\- \[ ] High/Medium/Low



\*\*Dependencies:\*\*

\- Prerequisites or related work needed



\*\*Status:\*\*

\- \[ ] Proposed/In Progress/Completed/Deferred

```

### 6. Journal File Maintenance

**Periodically clean old entries:**
- User is responsible for manual cleanup (no automation)
- Remove very old bug entries (6+ months) that are no longer relevant
- Archive completed session records and learnings (6+ months old)
- Mark improvements as Completed or Deferred and archive old ones
- Keep all decisions (they're lightweight and provide historical context)

**Conflict resolution:**
- If proposing something that conflicts with decisions.md, explain why revisiting the decision is warranted
- Update the decision entry if the choice changes
- Add date of revision to show evolution

## Templates and References

All templates are included directly in this skill file under the "Initial Setup" section. When creating initial memory files, copy the relevant template to `docs/` and customize for the project.

## Example Workflows

### Scenario 1: Encountering a Familiar Bug

```

User: "I'm getting a 'connection refused' error from the database"

\-> Search docs/02\_fixing/bugs.md for "connection"

\-> Find previous solution: "Use AlloyDB Auth Proxy on port 5432"

\-> Apply known fix

```

### Scenario 2: Proposing an Architectural Change

```

Internal: "User might benefit from using SQLAlchemy for migrations"

\-> Check docs/01\_building/decisions.md

\-> Find ADR-002: Already decided to use Alembic

\-> Use Alembic instead, maintaining consistency

```

### Scenario 3: User Requests Session Documentation

```

User: "Document what we worked on today"

\-> Read docs/01\_building/sessions.md

\-> Add new entry with date, session title, what was accomplished

\-> Include friction points and key takeaways

\-> Confirm addition to user

```

### Scenario 4: Recording New Learning

```

User: "Add what we learned about React Server Components to our learnings"

\-> Read docs/01\_building/learnings.md

\-> Add new entry with concept, key points, sources, and resources

\-> Confirm addition to user

```

### Scenario 5: Logging Future Improvement

```

User: "We should add dark mode support eventually"

\-> Read docs/03\_planning/improvements.md

\-> Add new entry with description, motivation, priority

\-> Set status to Proposed

\-> Confirm addition to user

```

## Tips for Effective Journal Management

1. **Be proactive**: Check journal files before proposing solutions
2. **Be concise**: Keep entries brief (1-3 lines for descriptions)
3. **Be dated**: Always include dates for temporal context
4. **Be linked**: Include URLs to tickets, docs, monitoring dashboards, learning resources
5. **Be selective**: Focus on recurring or instructive issues, not every bug
6. **Be reflective**: After sessions, take time to document what worked and what didn't
7. **Be forward-thinking**: Capture improvement ideas when they arise, even if not implementing immediately
8. **Follow the workflow**: Brief (00) → Build (01) → Fix (02) → Plan (03)

## Integration with Other Skills

The dev-journal skill complements other skills:

- **requirements-documenter**: Requirements → Decisions (ADRs reference requirements)
- **root-cause-debugger**: Bug diagnosis → Bug log (document solutions after fixes)
- **code-quality-reviewer**: Quality issues → Decisions (document quality standards)
- **docs-sync-editor**: Code changes → Learnings (document new patterns discovered)

When using these skills together, consider updating journal files as a follow-up action.

## Success Criteria

This skill is successfully deployed when:

- `docs/` directory exists with organized folder structure (00_briefing, 01_building, 02_fixing, 03_planning)
- All five journal files are in their proper locations
- CLAUDE.md includes "Development Journal System" section with protocols
- AGENTS.md includes the same protocols (if file exists or user requested)
- Journal files follow template format and style guidelines
- AI assistant checks journal files before proposing changes
- User can easily request journal updates ("add this to learnings", "log this session")
- Journal files look like standard engineering documentation, not AI artifacts
- Sessions are regularly documented with reflections and takeaways
- Learning moments are captured with sources for future reference
- Future improvements are tracked with priority and status
- The workflow (brief → build → fix → plan) is clear and intuitive
