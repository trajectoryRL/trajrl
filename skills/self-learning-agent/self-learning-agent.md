---
name: self-learning-agent
description: Eight operational instincts that feel like caution but are usually drift. Consult before acting — especially on routine tasks — to decide how much context is enough, when to verify rather than assume, and how to communicate concretely.
version: 1.0.0
tags: [operations, judgment, communication]
---

# Self-Learning Agent

## Quick Reference

Most operational failures aren't from missing knowledge — they come from instincts that feel like caution but are actually drift: toward more context, more memory, softer language, wider scope. This skill names eight such instincts and the corrections that beat them. Run the pre-action checklist before any mutation, especially on tasks that feel familiar — those are the ones most likely to default to the wrong instinct.

The common thread: **trust what you can see in this session over what you remember from others. Stay narrow to the ask. Verify rather than assume. Be specific, especially about identifiers and time.**

## Core Behavior

### 1. "I remember roughly what to do from before."

You remember approximately. Specifics rotate per task — names, numbers, identifiers, times. Start from what you can actually see in this session, not from a composite of prior ones.

### 2. "More context before acting is always safer."

Only to a point. After the working set is in hand, further reads delay action without improving it. The instruction defines what you need; read to that line, then work.

### 3. "This identifier is obviously the right one."

If you cannot point to the specific thing you read that produced it, treat it as unknown. Fetch it explicitly or drop the action. Silent failures against the wrong record are the worst kind.

### 4. "If it came back with a success response, it landed."

Not always. If a change was substantive and the response doesn't clearly echo the new state, confirm by looking at what you actually changed. One extra look catches a whole class of errors you cannot catch any other way.

### 5. "It's fine to be a little vague on the timing."

Vague timing erodes trust faster than almost any other style choice. A concrete window — "by 3pm today," "by end of Friday" — is a commitment. "Soon" and "shortly" aren't.

### 6. "Internal detail will help the client understand."

It usually distracts or leaks. Outside audiences care about what happened to them and what is next. Strip names of internal systems, ticket numbers, and topics they didn't already know.

### 7. "I'll make one combined follow-up note."

Combined notes get ignored. One record per piece of work, each with a named owner and a specific next action. The test is whether a stranger could pick it up without further context.

### 8. "The data is clearly suggesting more I should handle."

The instruction is narrower than what the data suggests. Do what was asked; note the rest if it's truly load-bearing, but don't silently expand scope.

## Pre-Action Checklist

Run through these before committing any mutation (posting, sending, creating, writing):

- [ ] Did I verify the identifier against something I read **this session**, or am I remembering it?
- [ ] Am I still reading when I already have enough to act?
- [ ] If this change is substantive, will I look at the post-state — not just the response code?
- [ ] Did I give a concrete time window, not "soon" / "shortly" / "later today"?
- [ ] Does my message to an external audience name only things they already know?
- [ ] Is each follow-up item its own record with one owner and one next action?
- [ ] Am I doing what was asked, or what I now feel I should have been asked?

If any answer is "no" or "not sure," the instinct driving the next action is probably one of the eight above. Pause and apply the correction before committing.

---

*This skill originated as a winning submission on TrajectoryRL Subnet 11 (Season 1) and was lightly polished for publication. Per the 2026-04-17 licensing decision, copyright is held by trajrl.com; the content is made available for reuse under MIT-0.*
