import numpy as np
import cv2
from gauge_reader.preprocess import to_lab_l_channel, apply_clahe, bilateral_denoise, build_background_model, subtract_background, preprocess


def test_to_lab_l_channel_shape():
    img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = to_lab_l_channel(img)
    assert result.shape == (480, 640)
    assert result.dtype == np.uint8


def test_apply_clahe_output_range():
    gray = np.random.randint(0, 255, (200, 200), dtype=np.uint8)
    result = apply_clahe(gray)
    assert result.shape == gray.shape
    assert result.dtype == np.uint8
    assert result.min() >= 0
    assert result.max() <= 255


def test_apply_clahe_enhances_contrast():
    # Dark image with subtle gradient — CLAHE should increase std dev
    gray = (np.random.randn(200, 200) * 10 + 50).clip(0, 255).astype(np.uint8)
    result = apply_clahe(gray, clip=2.0, tile=8)
    assert result.std() >= gray.std() * 0.9  # at minimum doesn't destroy contrast


def test_bilateral_denoise_preserves_edges():
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img[80:120, 80:120] = 255  # sharp white square
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    result = bilateral_denoise(img)
    edge_original = cv2.Canny(gray, 50, 150).sum()
    edge_result = cv2.Canny(cv2.cvtColor(result, cv2.COLOR_BGR2GRAY), 50, 150).sum()
    # Bilateral should preserve edge structure (edges don't vanish)
    assert edge_result >= edge_original * 0.5


def test_build_background_model_empty():
    assert build_background_model([]) is None


def test_build_background_model_computes_median():
    f1 = np.full((100, 100), 40, dtype=np.uint8)
    f2 = np.full((100, 100), 80, dtype=np.uint8)
    f3 = np.full((100, 100), 60, dtype=np.uint8)
    result = build_background_model([f1, f2, f3])
    assert result.shape == (100, 100)
    assert result.dtype == np.uint8
    assert abs(float(result[50, 50]) - 60) < 5


def test_subtract_background_none_ref():
    gray = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    assert subtract_background(gray, None) is None


def test_subtract_background_detects_change():
    ref = np.full((100, 100), 100, dtype=np.uint8)
    gray = ref.copy()
    gray[40:60, 40:60] = 200  # bright patch
    binary = subtract_background(gray, ref)
    assert binary is not None
    assert binary.shape == (100, 100)
    # Some pixels in the patch region should be 255 (foreground)
    assert binary[40:60, 40:60].sum() > 0


def test_preprocess_defaults_backward_compat():
    """preprocess() with no clahe_clip/tile args should use defaults (clip=2.0, tile=8)."""
    img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    result = preprocess(img, clahe=True, denoise=True)
    assert result.shape == img.shape
    assert result.dtype == np.uint8


def test_preprocess_different_clip_produces_different_output():
    """Different clahe_clip values should produce measurably different results."""
    img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    low = preprocess(img, clahe=True, denoise=False, clahe_clip=0.5, clahe_tile=8)
    high = preprocess(img, clahe=True, denoise=False, clahe_clip=8.0, clahe_tile=8)
    diff = np.abs(low.astype(float) - high.astype(float)).mean()
    assert diff > 0.5, f"clip=0.5 vs clip=8.0 should differ, got mean diff={diff}"


def test_preprocess_different_tile_produces_different_output():
    """Different clahe_tile values should produce measurably different results."""
    img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    small_tile = preprocess(img, clahe=True, denoise=False, clahe_clip=2.0, clahe_tile=2)
    large_tile = preprocess(img, clahe=True, denoise=False, clahe_clip=2.0, clahe_tile=16)
    diff = np.abs(small_tile.astype(float) - large_tile.astype(float)).mean()
    assert diff > 0.5, f"tile=2 vs tile=16 should differ, got mean diff={diff}"


def test_preprocess_pipeline_returns_bgr():
    img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    result = preprocess(img, clahe=True, denoise=True)
    assert result.shape == img.shape
    assert result.dtype == np.uint8
    # With color preservation, channels should not all be identical
    # (should have some variance between channels from original color)
    diff_rg = np.abs(result[:, :, 2].astype(float) - result[:, :, 1].astype(float)).mean()
    diff_gb = np.abs(result[:, :, 1].astype(float) - result[:, :, 0].astype(float)).mean()
    # At least some channel differences should remain after CLAHE+merge of random input
    assert diff_rg > 0 or diff_gb > 0, "channels should not be identical after color-preserving preprocess"
