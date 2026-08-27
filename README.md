# HT Scout Bridge

Coordination platform for national-team scouts and trainers (Bulgaria men's NT
and U21, but country-agnostic by design). Replaces broadcast HT-mail searches
with a targeted query: scouts see which trainers have money and slots; trainers
see which players the scouts plan to bring to market and can raise a hand.

Product spec: [PRODUCT.md](PRODUCT.md) · CHPP constraints: [CHPP_TECHNICAL.md](CHPP_TECHNICAL.md)

---

## ⚠️ CHPP approval comes first

Hattrick's rules require the CHPP application to be **approved before
development runs against their API**, and running an unapproved app can cost
you your team. This codebase is built to respect that:

- **`CHPP_MOCK=1` is the default.** Every CHPP call is served from local XML
  fixtures (`app/chpp/fixtures/`); nothing ever contacts hattrick.org.
- The real OAuth 1.0a client (`app/chpp/client.py`) activates only when
  `CHPP_MOCK=0` **and** consumer keys are configured — i.e. after approval.
- Read-only: no write scopes are requested, no messaging, no market crawling.

Do not flip the switch before the CHPP application (function list drafted from
PRODUCT.md §4 P0) is approved.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# open http://localhost:8000 — pick a demo persona on the login page
```

Tests: `pytest`

### Demo personas (mock mode)

| HT user | Role | What to look at |
|---|---|---|
| GenchoHC (101) | Head coach | exact finances, admin/roles |
| MitkoMaster (103) | Master scout | full registry |
| SashoScout (104) | Position scout | budget **bands only**, players, claims |
| BorkoTrainer (201) | Trainer | playmaking, 12.4M, immediate slot |
| ZharkoTrainer (202) | Trainer | winger, slot conditional on a sale |
| TishoTrainer (203) | Trainer | expired declaration → renew flow |

## What is implemented (P0 + core flows)

- **Trainer onboarding** — OAuth connect (real endpoints wired; mock in dev),
  read-only; revoke purges synced data (PRODUCT.md §7).
- **Capacity registry** (`/trainers`) — training type, coach level, squad
  occupancy, budget (exact for head coach/assistant/master scout, **banded**
  for position scouts), declared slots, last login; bots/stale hidden by default.
- **Slot declarations** — intentions, never derived: skill, quality threshold,
  timing, conditional-on-sale, expected sale price; **expire after 28 days**
  and drop out of scout queries until renewed with one click.
- **Player registry** (`/players`) — scout submits a Hattrick player ID,
  public data auto-fills via `playerdetails`; scout adds estimate, market plan,
  notes.
- **Scout query / matching** — per player, trainers ranked with visible
  reasons (training match, declared slot, budget vs estimate, activity).
- **Targeted outreach** — prefilled HT-mail compose link + player-specific
  draft (EN/BG). Sending is always manual, one at a time.
- **Market pipeline** (`/market`) — trainers see planned/listed players and
  express interest; the handling scout accepts or declines. This replaces the
  forum thread where this information used to get lost.
- **Claims** — one scout per player, visible to everyone.
- **Fetch discipline** — max one refresh per object per 24h, sequential
  requests, error 59 treated as "not authorised yet".
- **i18n** — English (CHPP-mandatory) + Bulgarian, switchable in the top bar.

Not yet implemented (P1/P2): on-plan verification after training updates,
swap analysis, reverse market (standing wants), reliability score, alerts,
squad-need view.

## Before production (real CHPP), verify:

1. **Numeric ID mappings** in `app/chpp/constants.py` (training types,
   specialties) against the CHPP `translations` file — they are community-
   sourced best effort.
2. **XML element paths** in `app/chpp/parse.py` against real responses
   (esp. `teamdetails` NationalTeams block and `training` trainer level).
3. ~~Currency~~ — done: CHPP money (SEK) is converted to the league's local
   currency via `worlddetails` CurrencyRate at sync time, and the currency
   name is displayed. Known limitation: a trainer or player owner in a league
   with a different currency than the scouts' shows amounts in *their* league
   currency. Debugging aid: `scripts/chpp_probe.py` saves the raw XML files
   for your team under `debug_xml/`.
4. `NationalTeamStaffType` role-seeding codes in `app/routers/auth.py`.

## Layout

```
app/
  chpp/        client (OAuth + mock), parsers, fixtures, constants
  services/    capacity bands, trainer ranking, outreach drafts, sync discipline
  routers/     auth, dashboard, scout, trainer, admin
  templates/   Jinja2 UI (EN/BG via app/i18n.py)
  models.py    facts vs intentions data model
  seed.py      demo data mirroring the fixtures
tests/         parsers, matching/capacity logic, i18n coverage, e2e smoke
```
