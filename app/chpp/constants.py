# TrainingType IDs verified against lucianoq/hattrick (Go CHPP library,
# chpp/type_training_type.go) and confirmed against live data (TrainingType 7
# = Short passes / Подаване). 0 (General) and 1 (Stamina) are deprecated
# in-game and map to "other".
#
# 2  Set Pieces
# 3  Defending
# 4  Scoring
# 5  Winger (Cross)
# 6  Shooting (Scoring + Set Pieces)
# 7  Short Passes
# 8  Playmaking
# 9  Goalkeeping
# 10 Through Passes (passing, defenders + midfielders)
# 11 Defensive Positions
# 12 Wing Attacks

TRAINING_TYPE_TO_SKILL = {
    2: "set_pieces",
    3: "defending",
    4: "scoring",
    5: "winger",
    6: "scoring",
    7: "passing",
    8: "playmaking",
    9: "goalkeeping",
    10: "passing",
    11: "defending",
    12: "winger",
}

# Specialty IDs — still best-effort; verify against the CHPP `translations`
# file before relying on them for anything critical.
SPECIALTIES = {
    0: "none",
    1: "technical",
    2: "quick",
    3: "powerful",
    4: "unpredictable",
    5: "head",
    6: "regainer",
    8: "support",
}
