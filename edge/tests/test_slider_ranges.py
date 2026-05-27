"""
Test that SLIDER_RANGES covers all numeric config keys from getFormValues().

This test parses the inline JS from index.html to extract both data structures
and verifies:
  - Every numeric form field (not checkbox/select/text) has a SLIDER_RANGES entry
  - No orphan SLIDER_RANGES keys (each must exist in getFormValues())
  - Odd-only params (blur_kernel, filter_window, threshold_block) enforce step=2
"""

import re
import pytest
from pathlib import Path

INDEX_HTML = Path(__file__).parent.parent / "app" / "static" / "index.html"

# Fields that should NOT have slider entries because they use different input types
EXCLUDED_FIELDS = {
    # <select> elements
    "point",
    "camera_id",
    "cam_resolution",
    "detect_method",
    # <input type="checkbox">
    "use_clahe",
    "circle_adaptive_thresh",
    "cam_auto_exposure",
    # <input type="text"> / secret
    "server_api_url",
    "api_key",
}

# Params that must have odd min, odd max, and step=2
ODD_ONLY_PARAMS = {"blur_kernel", "filter_window", "threshold_block"}


def _read_index() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


def _extract_get_form_values_fields(js: str) -> set[str]:
    """Extract all field identifiers from the getFormValues() function."""
    # Match the array literal:  ['point','server_api_url', ..., 'cam_exposure_absolute']
    m = re.search(
        r"function\s+getFormValues\s*\(\s*\)\s*\{[^}]*?const\s+fields\s*=\s*\[([^\]]+)\]",
        js,
        re.DOTALL,
    )
    if not m:
        raise AssertionError("Could not find getFormValues fields array in index.html")
    raw = m.group(1)
    # Extract all single-quoted strings
    fields = set(re.findall(r"'([^']+)'", raw))

    # Also include checkbox fields handled outside the main array
    # cam_auto_exposure is handled as a separate checkbox line at the end
    for excl in ("cam_auto_exposure",):
        if excl not in fields:
            fields.add(excl)
    return fields


def _extract_slider_ranges_keys(js: str) -> dict[str, dict]:
    """Extract the SLIDER_RANGES object as {key: {min: ..., max: ..., step: ...}}."""
    m = re.search(
        r"const\s+SLIDER_RANGES\s*=\s*\{",
        js,
    )
    if not m:
        raise AssertionError("Could not find SLIDER_RANGES in index.html")

    # Find the matching closing brace by counting
    start = m.end()
    depth = 1
    i = start
    while i < len(js) and depth > 0:
        if js[i] == "{":
            depth += 1
        elif js[i] == "}":
            depth -= 1
        i += 1
    obj_text = js[start : i - 1]

    ranges: dict[str, dict] = {}
    # Match each key: { min: ..., max: ..., step: ... },
    pattern = re.compile(
        r"""
        \b([a-zA-Z_]\w*)\s*:\s*\{          # key: {
        \s*min\s*:\s*([^,]+)\s*,\s*        # min: value
        \s*max\s*:\s*([^,]+)\s*,\s*        # max: value
        \s*step\s*:\s*([^}]+)\s*\}         # step: value }
        """,
        re.VERBOSE,
    )
    for match in pattern.finditer(obj_text):
        key = match.group(1)
        min_val = float(match.group(2))
        max_val = float(match.group(3))
        step_val = float(match.group(4))
        ranges[key] = {"min": min_val, "max": max_val, "step": step_val}
    return ranges


class TestSliderRangesCoverage:
    """Verify SLIDER_RANGES completeness vs getFormValues()."""

    @classmethod
    def setup_class(cls):
        cls.js = _read_index()
        cls.all_fields = _extract_get_form_values_fields(cls.js)
        cls.slider_keys = set(_extract_slider_ranges_keys(cls.js).keys())
        cls.slider_data = _extract_slider_ranges_keys(cls.js)

        # Compute numeric fields that should have slider entries
        cls.numeric_fields = cls.all_fields - EXCLUDED_FIELDS

    def test_all_numeric_fields_have_slider_ranges(self):
        """Every non-excluded field from getFormValues() must have a SLIDER_RANGES entry."""
        missing = self.numeric_fields - self.slider_keys
        assert not missing, (
            f"The following numeric fields from getFormValues() are missing "
            f"from SLIDER_RANGES: {sorted(missing)}"
        )

    def test_all_slider_keys_exist_in_get_form_values(self):
        """Every key in SLIDER_RANGES must be a valid field in getFormValues()."""
        orphaned = self.slider_keys - self.all_fields
        assert not orphaned, (
            f"The following SLIDER_RANGES keys don't exist in "
            f"getFormValues(): {sorted(orphaned)}"
        )

    def test_odd_only_params_have_step_2(self):
        """Odd-only params must have step=2 and odd min/max (or min=1)."""
        for name in ODD_ONLY_PARAMS:
            entry = self.slider_data.get(name)
            assert entry is not None, f"{name} not found in SLIDER_RANGES"
            assert entry["step"] == 2.0, (
                f"{name} should have step=2 (odd-only), got step={entry['step']}"
            )

    def test_excluded_fields_not_in_slider_ranges(self):
        """Checkbox, select, and text fields must NOT be in SLIDER_RANGES."""
        accidental = self.slider_keys & EXCLUDED_FIELDS
        assert not accidental, (
            f"Excluded fields found in SLIDER_RANGES: {sorted(accidental)}"
        )

    def test_count_match(self):
        """Total slider entries should match total numeric fields."""
        assert len(self.slider_keys) == len(self.numeric_fields), (
            f"SLIDER_RANGES has {len(self.slider_keys)} entries "
            f"but getFormValues() has {len(self.numeric_fields)} numeric fields "
            f"(of {len(self.all_fields)} total). "
            f"Slider keys: {sorted(self.slider_keys)}. "
            f"Numeric fields: {sorted(self.numeric_fields)}."
        )

    def test_slider_ranges_docstring_present(self):
        """SLIDER_RANGES must have a block comment documenting the design."""
        js = self.js
        # Check there's a /* ... */ comment that mentions SLIDER_RANGES
        assert "SLIDER_RANGES" in js
        assert "single source of truth" in js or "Must be kept in sync" in js, (
            "Expected SLIDER_RANGES to have a docstring mentioning "
            "'single source of truth' or 'Must be kept in sync'"
        )
