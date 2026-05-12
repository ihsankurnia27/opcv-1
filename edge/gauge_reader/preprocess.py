"""Preprocessing: CLAHE lighting normalization, bilateral denoising, background subtraction."""

import cv2
import numpy as np


def to_lab_l_channel(img):
    """Convert BGR to LAB, return L channel (perceptual luminance)."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    return lab[:, :, 0]


def apply_clahe(gray, clip=2.0, tile=8):
    """Apply CLAHE to grayscale image for lighting normalization."""
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tile, tile))
    return clahe.apply(gray)


def bilateral_denoise(img):
    """Edge-preserving bilateral filter on BGR image."""
    return cv2.bilateralFilter(img, 5, 75, 75)


def build_background_model(frames):
    """Median of N frames as background reference. Input: list of grayscale ndarrays."""
    if not frames:
        return None
    stack = np.stack(frames, axis=0)
    return np.median(stack, axis=0).astype(np.uint8)


def subtract_background(gray, ref):
    """Absolute difference with Otsu binarization. Returns binary mask."""
    if ref is None:
        return None
    diff = cv2.absdiff(gray, ref)
    _, binary = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def preprocess(img, clahe=True, denoise=True):
    """Full preprocessing pipeline: BGR → LAB → CLAHE on L → merge back to BGR → bilateral.

    Preserves color channels (a, b) from LAB. Returns BGR image ready for center/needle detection.
    """
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0]
    if clahe:
        l_channel = apply_clahe(l_channel)
    lab[:, :, 0] = l_channel
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    if denoise:
        result = bilateral_denoise(result)
    return result
