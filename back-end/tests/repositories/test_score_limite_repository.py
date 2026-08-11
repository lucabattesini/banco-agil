from app.repositories import score_limite_repository
from app.schemas.tables import ScoreLimitRange


def test_find_range_for_score_returns_matching_range(tmp_csvs):
    score_range = score_limite_repository.find_range_for_score(750)

    assert isinstance(score_range, ScoreLimitRange)
    assert score_range.limite_maximo == 6000.0


def test_find_range_for_score_returns_none_when_out_of_range(tmp_csvs):
    assert score_limite_repository.find_range_for_score(-1) is None
    assert score_limite_repository.find_range_for_score(1001) is None
