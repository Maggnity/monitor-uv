import pytest

from app.domain.uv_scale import classify


@pytest.mark.parametrize(
    "uv,key",
    [
        (0, "low"),
        (2.4, "low"),
        (2.5, "moderate"),
        (5.49, "moderate"),
        (5.5, "high"),
        (7.49, "high"),
        (7.5, "very_high"),
        (10.49, "very_high"),
        (10.5, "extreme"),
        (14, "extreme"),
    ],
)
def test_classify_boundaries(uv, key):
    assert classify(uv).key == key


def test_classify_copy():
    level = classify(9)
    assert level.label == "Muito alto"
    assert level.recommendation == "Evite sol entre 10h e 16h"


def test_classify_negative_raises():
    with pytest.raises(ValueError):
        classify(-0.1)
