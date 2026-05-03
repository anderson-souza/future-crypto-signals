import pytest

from src.exceptions import InsufficientDataError
from src.indicators.models import VolumeResult
from src.indicators.volume import calculate_volume_filter
from tests.conftest import make_candles


def make_candles_with_volumes(volumes: list[float]) -> list:
    candles = make_candles(len(volumes))
    return [c.model_copy(update={"volume": v}) for c, v in zip(candles, volumes)]


def test_returns_volume_result():
    candles = make_candles(21)
    result = calculate_volume_filter(candles, period=20)
    assert isinstance(result, VolumeResult)


def test_rvol_is_one_when_current_equals_average():
    # 20 candles with vol=100, current=100 → rvol=1.0
    volumes = [100.0] * 21
    candles = make_candles_with_volumes(volumes)
    result = calculate_volume_filter(candles, period=20)
    assert abs(result.rvol - 1.0) < 1e-9
    assert result.is_sufficient is True


def test_is_sufficient_false_when_rvol_below_threshold():
    # prev 20 avg = 100, current = 40 → rvol = 0.4 < 0.5
    volumes = [100.0] * 20 + [40.0]
    candles = make_candles_with_volumes(volumes)
    result = calculate_volume_filter(candles, period=20, min_rvol=0.5)
    assert abs(result.rvol - 0.4) < 1e-9
    assert result.is_sufficient is False


def test_is_sufficient_true_when_rvol_above_threshold():
    # prev 20 avg = 100, current = 80 → rvol = 0.8 > 0.5
    volumes = [100.0] * 20 + [80.0]
    candles = make_candles_with_volumes(volumes)
    result = calculate_volume_filter(candles, period=20, min_rvol=0.5)
    assert abs(result.rvol - 0.8) < 1e-9
    assert result.is_sufficient is True


def test_boundary_inclusive_at_min_rvol():
    # prev 20 avg = 100, current = 50 → rvol = 0.5 == min_rvol → is_sufficient=True
    volumes = [100.0] * 20 + [50.0]
    candles = make_candles_with_volumes(volumes)
    result = calculate_volume_filter(candles, period=20, min_rvol=0.5)
    assert abs(result.rvol - 0.5) < 1e-9
    assert result.is_sufficient is True


def test_insufficient_data_raises():
    candles = make_candles(20)  # need 21 for period=20
    with pytest.raises(InsufficientDataError):
        calculate_volume_filter(candles, period=20)


def test_period_zero_raises():
    candles = make_candles(21)
    with pytest.raises(ValueError, match="period must be positive"):
        calculate_volume_filter(candles, period=0)


def test_period_negative_raises():
    candles = make_candles(21)
    with pytest.raises(ValueError, match="period must be positive"):
        calculate_volume_filter(candles, period=-1)


def test_min_rvol_negative_raises():
    candles = make_candles(21)
    with pytest.raises(ValueError, match="min_rvol cannot be negative"):
        calculate_volume_filter(candles, period=20, min_rvol=-0.1)


def test_min_rvol_zero_always_sufficient():
    # filter disabled — any volume passes
    volumes = [100.0] * 20 + [0.001]
    candles = make_candles_with_volumes(volumes)
    result = calculate_volume_filter(candles, period=20, min_rvol=0.0)
    assert result.is_sufficient is True


def test_min_rvol_above_one_works():
    # require above-average volume — current = 100, avg = 80 → rvol = 1.25 >= 1.2
    volumes = [80.0] * 20 + [100.0]
    candles = make_candles_with_volumes(volumes)
    result = calculate_volume_filter(candles, period=20, min_rvol=1.2)
    assert result.is_sufficient is True


def test_zero_average_volume_raises():
    volumes = [0.0] * 20 + [100.0]
    candles = make_candles_with_volumes(volumes)
    with pytest.raises(ValueError, match="average volume is non-positive"):
        calculate_volume_filter(candles, period=20)


def test_negative_average_volume_raises():
    volumes = [-10.0] * 20 + [100.0]
    candles = make_candles_with_volumes(volumes)
    with pytest.raises(ValueError, match="average volume is non-positive"):
        calculate_volume_filter(candles, period=20)


def test_rvol_excludes_current_candle_from_average():
    # prev 20 avg = 100; if current were included, avg would shift
    # current = 200 → rvol should be 200/100 = 2.0, not 200/109.52...
    volumes = [100.0] * 20 + [200.0]
    candles = make_candles_with_volumes(volumes)
    result = calculate_volume_filter(candles, period=20)
    assert abs(result.rvol - 2.0) < 1e-9
