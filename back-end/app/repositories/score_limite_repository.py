from typing import Optional

import pandas as pd

from app.config import SCORE_LIMITE_CSV
from app.schemas.tables import ScoreLimitRange


def find_range_for_score(score: int) -> Optional[ScoreLimitRange]:
    df = pd.read_csv(SCORE_LIMITE_CSV)
    match = df[(df["score_min"] <= score) & (score <= df["score_max"])]
    return ScoreLimitRange(**match.iloc[0].to_dict()) if not match.empty else None
