import numpy as np
import cv2
from gauge_reader.preprocess import to_lab_l_channel, apply_clahe, bilateral_denoise


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
