# Product Description — NT Scout & Trainer Coordination Platform

Working name: **HT Scout Bridge**

---

## 1. The problem

In Hattrick, national-team scouts find talented young players eligible for their country.
Those players need to be trained by someone with the right trainer, the right assistants,
the right training type, spare capacity in the trained positions, and enough cash to buy.

Today the matching happens by brute force: a scout finds a talent, then sends HT-mails to
manager after manager until someone with money and a free slot answers. Most messages are
wasted. Good talents are lost to the deadline while the scout is still searching. Two
scouts unknowingly pitch different players to the same trainer. Nobody has a current
picture of who can actually absorb a player right now.

**The product replaces a broadcast search with a targeted query.** Instead of writing to
forty managers, the scout filters a live registry and writes to three.

---

## 2. Users and roles

| Role | Scope |
|---|---|
| Head coach (селекционер) | Full visibility. Sets scouting priorities and squad needs. |
| Assistant coach | Full visibility except administrative settings. |
| Master scout | Full visibility of players and trainer capacity. Assigns scouts. |
| Position scout | Sees player database and *capacity signals* — not exact figures. |
| Trainer (трениращ) | Manages their own connection, declarations and commitments. Sees their own data and any player offered to them. |

Roles do not have to be assigned entirely by hand: `teamdetails` returns
`NationalTeams` → `NationalTeamStaffType`, which identifies a user's official position in a
national team. Use it to seed head-coach and assistant-coach roles, and to verify that
whoever claims to run the NT actually does.

**Privacy is a retention issue, not a checkbox.** A trainer who grants OAuth and then
discovers that thirty scouts can see their exact bank balance will revoke it and tell
others. Position scouts should see banded capacity ("can afford a top-tier talent",
"slot available on request"), not raw numbers. Exact figures are visible to the head
coach and master scout only.

---

## 3. Core concept: fact vs. intention

The registry has two kinds of data and they must never be conflated.

**Facts — read automatically via CHPP OAuth, never typed by anyone:**
- The trainer's squad with exact skill values
- Current training type, intensity, stamina share
- Trainer level, assistant coaches, other staff
- Cash balance and next week's expected cash (`economy` v1.4 — confirmed available for
  teams managed by the authorising user). `ExpectedCash` is usually the more relevant
  figure: it answers "what will this trainer have next week", which is what matters
  against a transfer deadline.
- Whether the trainer is a bot, and when they last logged in (`teamdetails`) — filters out
  managers who will never reply
- Which positions are currently occupied by which players

**Intentions — declared by the trainer, cannot be derived:**
- How many slots they are *willing to free* and at what quality threshold. A trainer with
  eight foreigners in the trained positions does not have zero free slots — they have
  eight conditional ones. Computed occupancy would report the exact opposite of the truth.
- Which specific players they would move on, and expected sale price
- Timing: immediately, after the current cycle, or after a player reaches a given age
- Whether a purchase is conditional on a sale completing first. "Has 3M" and "has 3M once
  the foreigner sells" are different situations under a transfer deadline.

The API's role for intentions is **contradiction detection and form prefill**, not source
of truth. Show declared alongside actual; flag divergence (three slots declared free, squad
unchanged for two months, no sales). Usually this means a forgotten declaration, not a lie.

**Declarations expire.** Every declaration carries a validity window (suggested: 4 weeks).
On expiry it greys out and drops out of scout search results until the trainer confirms
with one click. Prompt for renewal right after the weekly training update, when the trainer
is logging in anyway. Without expiry the registry rots into exactly the stale information
the product exists to eliminate.

---

## 4. Feature set

### P0 — the minimum that solves the problem

1. **Trainer onboarding via OAuth.** One-click connect, explicit screen showing exactly
   what will be read and who can see it.
2. **Capacity registry.** Per trainer: training type, trainer/assistant level, squad
   occupancy, budget band, declared free slots with conditions and expiry.
3. **Scout query.** Filter by training type, trainer quality, budget band, slot
   availability, timing. Returns a ranked shortlist.
4. **Targeted outreach.** For each match, a prefilled compose link
   (`hattrick.org/MyHattrick/Inbox/?actionType=newMail&userid=<ID>`) plus a generated,
   player-specific message draft. **Sending is always manual and always one message at a
   time.** No bulk send — it is both impossible via the API and a game-rules violation.
5. **Player registry.** Scouts post player IDs with estimated value, market status, and
   notes. Public data auto-populates from `playerdetails`.

### P1 — the things that make it stick

6. **On-plan verification.** After each training update, recompute every tracked player
   against their target and raise a flag when they drift. This replaces the manual
   spreadsheet review entirely.
7. **Swap analysis.** When a scout offers a player to a trainer who would have to free a
   slot, compute both sides: current occupant reaches target at age X, candidate at age Y.
   Turns a subjective "sure, I'll drop him" into a comparison.
8. **Claim / reservation.** Mark a player as being handled by a given scout so two scouts
   don't pitch the same trainer.
9. **Reverse market.** Trainers post standing wants ("slot for playmaking, up to 2M, under
   18"). Scouts search those. Inverts the flow and removes blind outreach in both directions.

### P2

10. **Trainer reliability score.** `trainingevents` holds the real history — show
    objectively whether a trainer trained what they committed to. Only possible with OAuth,
    and not something Hattrick Portal offers. Strongest differentiator.
11. **Alerts** via Discord/Telegram: tracked player listed for transfer, approaching age
    threshold, declaration about to expire, NT eligibility window.
12. **Squad-need view.** Head coach defines the target squad profile; the system reports
    gaps against the current tracked pool.

---

## 5. Key flows

**Scout finds a talent on the market**
Scout submits player ID → public data auto-fills → scout adds estimated value and target
profile → system returns ranked trainers with capacity → scout picks 2-3 → generated drafts
→ scout sends manually → scout marks a claim.

**Trainer frees a slot**
Trainer opens declaration form (prefilled with actual squad) → marks which player they
would move and under what condition → sets expiry → becomes visible to scout queries.

**Weekly health check**
After training update → recompute all tracked players → flag drift → notify the responsible
scout with a ready message draft for the owner.

---

## 6. Non-goals

- **No automated messaging.** Ever. Not batched, not queued, not "one click sends five".
- **No transfer market crawling.** Market discovery is scout-initiated.
- **No scraping of hattrick.org or of Hattrick Portal.**
- **Not a replacement for Hattrick Portal Tracker.** Portal already holds the scouting
  database. The differentiator here is the trainer-capacity marketplace. Talk to `_Duke_`
  (userId 1148126) before duplicating anything.
- **No storage of Hattrick passwords.** OAuth only.

---

## 7. Non-functional

- English UI mandatory (CHPP requirement). Bulgarian as a second locale.
- Country-agnostic data model — a Bulgarian-only tool is at the edge of the approval bar;
  a tool any NT can use is comfortably above it.
- Refresh no more than once per day per object; sequential CHPP requests only.
- Trainers can revoke access at any time; on revocation, retained derived data must be
  purged or anonymised.

---

## 8. Open questions

1. ~~Does an economy/cash endpoint exist?~~ **Resolved** — `economy` v1.4 gives `Cash` and
   `ExpectedCash` for teams managed by the authorising user. Budget is a fact, not a
   declaration. (The *willingness to spend it* still is a declaration.)
2. Do we implement the Schum training formula in-house, or negotiate access with Portal?
3. How do we handle a trainer who is in the registry but does not want OAuth — a
   declaration-only tier with a visible "unverified" marker?
4. What is the arbitration rule when two scouts claim the same player?
5. Does the head coach get a veto on placements, or is it advisory?

---

## 9. First implementation step

Do not start with code. The CHPP application, including the English function list, must be
submitted and approved before development begins. The function list drafted from §4 P0 is
the document that determines whether the project proceeds.
