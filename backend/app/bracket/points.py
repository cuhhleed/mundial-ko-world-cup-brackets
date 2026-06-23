from dataclasses import dataclass


@dataclass(frozen=True)
class SlotPointValues:
    correct_winner: int
    correct_score: int
    correct_pk_score: int


POINTS: dict[str, SlotPointValues] = {
    "R32":   SlotPointValues(correct_winner=2,  correct_score=0,  correct_pk_score=0),
    "R16":   SlotPointValues(correct_winner=4,  correct_score=0,  correct_pk_score=0),
    "QF":    SlotPointValues(correct_winner=8,  correct_score=0,  correct_pk_score=0),
    "SF":    SlotPointValues(correct_winner=16, correct_score=16, correct_pk_score=40),
    "FINAL": SlotPointValues(correct_winner=32, correct_score=32, correct_pk_score=40),
    "TP":    SlotPointValues(correct_winner=10, correct_score=0,  correct_pk_score=0),
}
