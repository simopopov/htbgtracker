# CHPP Technical Reference — NT Scouting & Training Coordination Tool

Verified against the official CHPP documentation at
`https://www.hattrick.org/Community/CHPP/NewDocs/` on 2026-08-03 (login required).
Per-file pages: `File.aspx?name=<file>`. OAuth guide: `/Community/CHPP/oauth/`.

---

## 0. Read this before writing any code

The documentation states plainly: as a CHPP developer you may ONLY access the documented
interfaces. Developing products that work with any other part of the site is strictly
forbidden, and violation may cost you your team.

For this project that means:

- **No scraping of `hattrick.org`** — not player pages, not transfer search, not the mail form.
- **No browser automation of the Hattrick UI**, for reading or writing.
- Scraping third-party sites (e.g. Hattrick Portal) is outside Hattrick's rules but governed
  by those sites' own terms — get permission or don't.

Second rule that shapes architecture: if you supply Hattrick-related data to other
developers, they must also be CHPP-approved. CHPP-to-CHPP exchange is permitted; the
providing side decides.

---

## 1. Approval process — BEFORE development

1. Apply for CHPP status with a description of intended functions.
2. Hattrick approves the program **and each function separately**.
3. Only then begin development.
4. After development, choose which approved functions to publish.

Requirements:

- **General interest.** Applications for small groups (a federation, a circle of friends)
  are rejected. Minimum bar: usefulness to at least one country. An NT scouting/training
  coordination platform clears this; building it country-agnostic clears it comfortably.
- **English** description, function list, and language support.
- Developing before approval, or running an unapproved application, can lead to a ban.

---

## 2. Authentication — OAuth 1.0a

```
Request Token     https://chpp.hattrick.org/oauth/request_token.ashx
Authorize         https://chpp.hattrick.org/oauth/authorize.aspx
Authenticate      https://chpp.hattrick.org/oauth/authenticate.aspx
Access Token      https://chpp.hattrick.org/oauth/access_token.ashx
Check Token       https://chpp.hattrick.org/oauth/check_token.ashx
Invalidate Token  https://chpp.hattrick.org/oauth/invalidate_token.ashx
Protected resource https://chpp.hattrick.org/chppxml.ashx?file=<name>&version=<v>
```

- Standard OAuth Core 1.0a — any compliant client library works.
- **GET** for all requests. **HMAC-SHA1** signatures.
- Always supply `oauth_callback`; use `oauth_callback=oob` if the product cannot receive one.
- `ConsumerKey` / `ConsumerSecret` come from the OAuth page for your product.
- Hattrick provides an OAuth Signature Test page for debugging signing.

### Scopes (CHPP 2.0)

Read access needs no scope. Write commands require explicit scopes, requested at authorize
time as `&scope=a,b`:

| Scope | Grants |
|---|---|
| `manage_challenges` | Friendly challenges |
| `set_matchorder` | Match orders |
| `manage_youthplayers` | Youth player management |
| `set_training` | Change training settings |
| `place_bid` | Bid on transfers |

**This project needs no write scopes.** Requesting them would make onboarding scarier for
trainers with zero benefit. Read-only is the right posture — the app never touches anyone's
team, it only observes and reports.

Never store user logins or security codes. OAuth tokens only.

---

## 3. Response envelope

Every XML response opens with `HattrickData`:

| Element | Meaning |
|---|---|
| `FileName` | The file the request was sent to |
| `Version` | Delivered version of the XML output |
| `UserID` | Logged-on user's UserID (not TeamID) |
| `FetchedDate` | DateTime of the fetch |

---

## 4. Error codes (complete)

| Code | Meaning |
|---|---|
| -1 | No information |
| 0 | Not logged in |
| 1 | Access denied |
| 2 | File not specified |
| 3 | File not supported |
| 4 | POST not supported |
| 5 | Must use POST for this action |
| 6 | Only for Supporters |
| 7 | Not supported version |
| 10 | Invalid parameter |
| 50 | Unknown TeamID |
| 51 | Unknown MatchID |
| 52 | Unknown ActionType |
| 53 | MatchID not subscribed to |
| 54 | Unknown YouthTeamID |
| 55 | Unknown YouthPlayerID |
| 56 | Unknown PlayerID |
| 57 | Unknown LeagueID |
| 58 | Unknown LeagueLevelUnitID |
| **59** | **Request only allowed for teams owned by the requesting user** |
| 60 | Unknown TournamentId |
| 61 | Unknown LadderId |
| 62 | Youth player is now a senior — `SeniorPlayerID` is returned |
| 63 | Missing required parameters |
| 64 | The player has become a coach |
| 70 | Challenge failed |
| 71 | Bid failed |
| 80 | Banned from international friendly |
| 81 | Banned from transfers |
| 90 | Hattrick down for maintenance |
| 91 | Youth academy down for maintenance |
| 92 | Transfer market down for maintenance |
| 93 | HTOIntegrated platform down for maintenance |
| 99 | Other undefined error |
| anything else | Internal .NET error — report with the code |

**Code 59 is a normal branch, not an exception.** It fires whenever the app asks for
owner-scoped data on a team the authorising user does not own. Handle it as "not authorised
by this trainer yet".

Codes 62 and 64 matter for a scouting registry: tracked youth players graduate, and players
become coaches. Both need migration handling rather than a dropped record.

---

## 5. Endpoints used by this project

### `playerdetails` — v3.2

The most important constraint in the entire project.

- **`PlayerSkills` is visible to the owner only.** The single exception is `StaminaSkill`,
  exposed from v1.7 onwards.
- `PlayerCategoryID` and `OwnerNotes` are owner-only.
- Public for any player: age (years + days), next birthday, TSI, specialty, salary, owning
  team (id/name/league), whether abroad, mother club and `MotherClubBonus`, transfer status /
  asking price / deadline / highest bid, matches, goals, assists, `Caps`, `CapsU20`,
  warnings, injury status.

Consequence: a scout submitting a player ID gets useful public data immediately. Exact skills
require the owner's OAuth grant. There is no workaround and none is needed.

### `players` — v2.8

- `actionType`: `view` (default) | `viewOldies` | `viewOldCoaches`
- `orderBy` (default `PlayerNumber`), `teamID` (default: logged-on user's)
- Full skills only for the authorising user's own team.

### `training` — v2.2

- `actionType`: `view` (default) | `stats` | `setTraining`
- `view` returns training info for the **logged-in user's team only**
- `stats` shows training-type distribution per league or globally — **requires Supporter**
- `setTraining` requires the `set_training` scope — not used by this project
- `teamId` must refer to a senior team managed by the requesting user

### `economy` — v1.4

- `teamId` must refer to a senior team **managed by the requesting user**
- Returns `Cash` (current) and `ExpectedCash` (budgeted for next week), plus sponsors/
  supporters income detail

`ExpectedCash` is the more useful field for the capacity registry: it answers "what will this
trainer have next week", which is what matters against a transfer deadline.

### `trainingevents` — v1.3

- Only parameter: `playerID`
- Returns the player's skill-up history
- `TrainingEvents` carries an `Available` attribute — **false while the player is in a match**;
  retry rather than treat as empty

This is the backbone of the trainer-reliability score: it shows what a player actually
trained, historically, rather than what someone claims.

### `teamdetails` — v3.9

- `teamID` **or** `userID` (equivalent results; ownerless teams need `teamID`, users without
  a team need `userID`); optional `includeFlags`, `includeDomesticFlags`, `includeSupporters`
- Public data: `Loginname`, `SignupDate`, `LastLoginDate`, `SupporterTier`,
  `HasManagerLicense`, team name, `FoundedDate`, `IsDeactivated`, league / country / region,
  `Trainer` (PlayerID of the coach), `PowerRating`, `LeagueLevelUnit` + `LeagueLevel`,
  `Fanclub`, `BotStatus` (`IsBot`, `BotSince`), `TeamRank`, `YouthTeamID`, `TrophyList`
- `Name` may be the literal string `HIDDEN` if the user hides it — handle it
- **`NationalTeams` → `NationalTeamStaffType`** identifies a user's official role in a
  national team

Two direct product uses: `NationalTeamStaffType` can seed the role model instead of manual
assignment, and `LastLoginDate` + `IsBot` filter out trainers who will never answer a message.
`LeagueID` is how you determine a manager's country without guessing from their username.

### `nationalplayers` — v1.5

- `actionType`: `view` (default, regular or U-20 squad) | `SupporterStats`

### `transfersearch` — v1.1

- Parameters include `ageMin`, `ageMax`, `ageDaysMin` (default 0), `ageDaysMax` (default 111),
  plus skill/price/type filters
- **Not meant to be fetched by bots — only on a manual user request.** Never scheduled,
  never crawled. Market discovery is scout-initiated by design.

### Other files worth knowing

`managercompendium`, `stafflist`, `currentbids`, `transfersteam`, `transfersplayer`,
`playerevents`, `search`, `worlddetails`, `leaguedetails`, `leaguefixtures`, `leaguelevels`,
`avatars`, `achievements`, `hofplayers`, `matches`, `matchdetails`, `matchlineup`,
`matchesarchive`, `matchorders`, `live`, `cupmatches`, `arenadetails`, `fans`, `club`,
`alliances`, `alliancedetails`, `bookmarks`, `challenges`, `supporters`, `regiondetails`,
`nationalteams`, `nationalteamdetails`, `nationalteammatches`, `worldcup`, `worldlanguages`,
`translations`, `staffavatars`, `ladderlist`, `ladderdetails`, `tournamentlist`,
`tournamentdetails`, `tournamentfixtures`, `tournamentleaguetables`, `youthplayerlist`,
`youthplayerdetails`, `youthteamdetails`, `youthleaguedetails`, `youthleaguefixtures`,
`youthavatars`.

Note: older community sources claim there is no youth API. That is out of date — the youth
files exist and were updated in February 2026.

---

## 6. What the API does NOT provide

Three absences the product must design around. None has a workaround.

1. **No messaging endpoint.** There is no file for HT-mail in the 57-file catalogue. Mail is
   composed and sent by the user in the Hattrick UI. The app's output is a targeted shortlist
   plus prefilled compose links:
   `https://www.hattrick.org/MyHattrick/Inbox/?actionType=newMail&userid=<ID>`
   This URL resolves the recipient username automatically (verified). Sending is always
   manual, one message at a time. Bulk or templated messaging is a game-rules violation
   independent of the API.

2. **No automated transfer market monitoring.** See `transfersearch` above.

3. **No access to other managers' training or skills.** `training` and `economy` are scoped
   to teams managed by the authorising user; `playerdetails` skills are owner-only. A
   trainer's real setup is knowable only if they authorise the app.

---

## 7. Fetch discipline

- One XML request at a time per session — no parallelism. Logout at end of session.
- `transfersearch`: only in direct response to a user action. Never scheduled.
- `translations`: cache, refresh roughly weekly — do not fetch every session.
- Refresh no more than once per day per object. Hattrick Portal uses exactly this policy
  (objects max once/day, players daily, matches at least weekly) — a safe precedent.
- Training-dependent recomputation belongs after the weekly training update in the relevant
  league, not nightly for everyone.
- `User-Agent` must contain the application name and version.

---

## 8. Domain constants

- A Hattrick year is **112 days** (16 weeks x 7). Age arithmetic:
  `totalDays = years * 112 + days`.
- Skill denomination scale (index / English / Bulgarian):

  | # | English | Bulgarian |
  |---|---|---|
  | 1 | disastrous | бедствено |
  | 2 | wretched | ужасно |
  | 3 | poor | лошо |
  | 4 | weak | слабо |
  | 5 | inadequate | посредствено |
  | 6 | passable | задоволително |
  | 7 | solid | стабилно |
  | 8 | excellent | отлично |
  | 9 | formidable | прекрасно |
  | 10 | outstanding | изключително |
  | 11 | brilliant | брилянтно |
  | 12 | magnificent | великолепно |
  | 13 | world class | световна класа |
  | 14 | supernatural | свръхестествено |
  | 15 | titanic | титанично |
  | 16 | extra-terrestrial | извънземно |
  | 17 | mythical | митично |
  | 18 | magical | вълшебно |
  | 19 | utopian | легендарно |
  | 20 | divine | божествено |

- Specialty labels as rendered by Hattrick Portal (Bulgarian): `Сила` = Powerful,
  `Непредвидим` = Unpredictable, `Игра с глава` = Head specialist, `Бърз` = Quick,
  `Техничен` = Technical. Do not match on "Силен" — the label is "Сила".
  **Map from the numeric specialty ID in `playerdetails`, never from localised strings.**
- Use `translations` for denominations rather than hardcoding the table above, so the app
  works in every language without a code change.

---

## 9. Training projection

Hattrick Portal exposes a training-plan calculator taking all inputs via query string and
returning per-level milestones with the age at which each level is reached:

`https://hattrickportal.online/Utils/PlayerTrainingPlan.aspx?age=&days=&coach=&assistants=&intensity=&stamina=&goalkeeping=&defending=&playmaking=&winger=&passing=&scoring=&setpieces=&staminaskill=`

Goals (target level per skill, stamina goal) are ASP.NET form fields, not query parameters,
so driving it requires a POST carrying the page viewstate.

**This is a third-party site — do not build a dependency on it without permission.** Contact
`_Duke_` (Hattrick userId 1148126), author of Hattrick Portal (CHPP ApplicationIds 4545 and
4678). The correct long-term approach is implementing the Schum training formula in-house
from CHPP data.

---

## 10. Libraries

- Python: `pychpp` — `https://github.com/PiGo86/pychpp`. Instantiate with consumer
  key/secret and access token; `chpp.team(id).players()` etc.
- PHP: `PHT`
- Go: `lucianoq/hattrick`
