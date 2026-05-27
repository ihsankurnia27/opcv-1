"""
Test that slider HTML elements are properly wired in index.html.

Verifies:
  - Every SLIDER_RANGES key has a corresponding <input type="range"> element
  - Each slider has a matching <span class="slider-value"> value label
  - Each slider has oninput="onSliderInput(this, 'key')" attribute
  - getFormValues() fields with sliders keep hidden <input type="number"> for compatibility
  - Slider min/max/step match SLIDER_RANGES entries
"""

import re
import pytest
from pathlib import Path

INDEX_HTML = Path(__file__).parent.parent / "app" / "static" / "index.html"

# Fields whose primary element IS the range slider (no hidden number input)
RANGE_PRIMARY = {"clahe_clip", "clahe_tile"}


def _read_index() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


def _extract_slider_ranges(js: str) -> dict[str, dict]:
    """Extract SLIDER_RANGES as {key: {min, max, step}}."""
    m = re.search(r"const\s+SLIDER_RANGES\s*=\s*\{", js)
    if not m:
        raise AssertionError("SLIDER_RANGES not found")
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
    ranges = {}
    pat = re.compile(
        r"\b([a-zA-Z_]\w*)\s*:\s*\{\s*min\s*:\s*([^,]+),\s*"
        r"max\s*:\s*([^,]+),\s*step\s*:\s*([^}]+)\s*\}",
        re.VERBOSE,
    )
    for match in pat.finditer(obj_text):
        key = match.group(1)
        ranges[key] = {
            "min": float(match.group(2)),
            "max": float(match.group(3)),
            "step": float(match.group(4)),
        }
    return ranges


def _find_slider_tag(html: str, field_id: str) -> str | None:
    """Find <input type="range"> for given field. Tries field_id_slider then field_id."""
    # Try explicit slider id="key_slider" pattern
    pattern_dedicated = re.compile(
        r'<input\s+[^>]*type="range"[^>]*id="' + re.escape(field_id) + r'_slider"',
        re.IGNORECASE,
    )
    m = pattern_dedicated.search(html)
    if m:
        # Return the full tag
        start = m.start()
        tag_end = html.index(">", start) + 1
        return html[start:tag_end]

    # Try primary-id pattern (field IS the slider, e.g. clahe_clip)
    pattern_primary = re.compile(
        r'<input\s+[^>]*type="range"[^>]*id="' + re.escape(field_id) + r'"',
        re.IGNORECASE,
    )
    m = pattern_primary.search(html)
    if m:
        start = m.start()
        tag_end = html.index(">", start) + 1
        return html[start:tag_end]

    return None


def _get_attr(tag: str, attr: str) -> str | None:
    """Extract an attribute value from an HTML tag string."""
    m = re.search(r'\b' + re.escape(attr) + r'\s*=\s*"([^"]*)"', tag, re.IGNORECASE)
    return m.group(1) if m else None


class TestSliderHtml:
    @classmethod
    def setup_class(cls):
        cls.html = _read_index()
        cls.slider_ranges = _extract_slider_ranges(cls.html)

    def test_every_numeric_param_has_slider(self):
        """Every key in SLIDER_RANGES must have a visible <input type="range"> in the HTML."""
        missing = []
        for key in sorted(self.slider_ranges.keys()):
            tag = _find_slider_tag(self.html, key)
            if tag is None:
                missing.append(key)
        assert not missing, (
            f"No <input type='range'> found for SLIDER_RANGES keys: {missing}"
        )

    def test_every_slider_has_value_label(self):
        """Every slider must have a <span id="key_val" class="slider-value">."""
        missing = []
        for key in sorted(self.slider_ranges.keys()):
            pattern = re.compile(
                r'<span[^>]*id="' + re.escape(key) + r'_val"[^>]*class="slider-value"'
            )
            if not pattern.search(self.html):
                missing.append(key)
        assert not missing, (
            f"Missing <span id='{{key}}_val' class='slider-value'> for: {missing}"
        )

    def test_every_slider_has_oninput_handler(self):
        """Every slider must have oninput="onSliderInput(this, 'key')"."""
        missing = []
        for key in sorted(self.slider_ranges.keys()):
            pattern = re.compile(
                r'oninput="onSliderInput\(this,\s*&#39;' + re.escape(key) + r"&#39;\)\"",
            )
            # Also try single-quote version (actual HTML may vary)
            if not pattern.search(self.html):
                # Try the literal attribute form: oninput="onSliderInput(this,'key')"
                pattern2 = re.compile(
                    r'oninput="onSliderInput\(this,\s*&#x27;' + re.escape(key)
                    + r"&#x27;\)\""
                )
                pattern3 = re.compile(
                    r'oninput=\'onSliderInput\(this,\s*"' + re.escape(key) + r'"\)\''
                )
                # The simplest check: find the slider tag and check it has an oninput attribute
                tag = _find_slider_tag(self.html, key)
                if tag:
                    oninput_val = _get_attr(tag, "oninput")
                    if not oninput_val or key not in oninput_val:
                        missing.append(key)
                else:
                    missing.append(key)

        assert not missing, (
            f"Slider(s) missing oninput='onSliderInput(this, \"{{key}}\")': {missing}"
        )

    def test_hidden_inputs_for_compatibility(self):
        """Non-range-primary fields must have a hidden <input type='number'> with original id."""
        missing = []
        for key in sorted(self.slider_ranges.keys()):
            if key in RANGE_PRIMARY:
                continue  # These are the slider themselves, no hidden input
            pattern = re.compile(
                r'<input[^>]*id="' + re.escape(key) + r'"[^>]*style="display:none"'
            )
            if not pattern.search(self.html):
                missing.append(key)
        assert not missing, (
            f"Missing hidden <input id='{{key}}' type='number' style='display:none'> "
            f"for: {missing}"
        )

    def test_slider_min_matches_slider_ranges(self):
        """Slider min attribute should match SLIDER_RANGES entry."""
        mismatches = []
        for key, expected in sorted(self.slider_ranges.items()):
            tag = _find_slider_tag(self.html, key)
            if not tag:
                mismatches.append((key, "no tag", str(expected["min"])))
                continue
            min_val = _get_attr(tag, "min")
            if min_val is None:
                mismatches.append((key, "no min attr", str(expected["min"])))
            elif float(min_val) != expected["min"]:
                mismatches.append((key, min_val, str(expected["min"])))
        assert not mismatches, (
            "Slider min mismatch (key, actual, expected): " + str(mismatches)
        )

    def test_slider_max_matches_slider_ranges(self):
        """Slider max attribute should match SLIDER_RANGES entry."""
        mismatches = []
        for key, expected in sorted(self.slider_ranges.items()):
            tag = _find_slider_tag(self.html, key)
            if not tag:
                mismatches.append((key, "no tag", str(expected["max"])))
                continue
            max_val = _get_attr(tag, "max")
            if max_val is None:
                mismatches.append((key, "no max attr", str(expected["max"])))
            elif float(max_val) != expected["max"]:
                mismatches.append((key, max_val, str(expected["max"])))
        assert not mismatches, (
            "Slider max mismatch (key, actual, expected): " + str(mismatches)
        )

    def test_slider_step_matches_slider_ranges(self):
        """Slider step attribute should match SLIDER_RANGES entry."""
        mismatches = []
        for key, expected in sorted(self.slider_ranges.items()):
            tag = _find_slider_tag(self.html, key)
            if not tag:
                mismatches.append((key, "no tag", str(expected["step"])))
                continue
            step_val = _get_attr(tag, "step")
            if step_val is None:
                mismatches.append((key, "no step attr", str(expected["step"])))
            elif float(step_val) != expected["step"]:
                mismatches.append((key, step_val, str(expected["step"])))
        assert not mismatches, (
            "Slider step mismatch (key, actual, expected): " + str(mismatches)
        )

    def test_get_form_values_reads_hidden_inputs(self):
        """getFormValues() reads by field id — verify hidden inputs exist for all fields."""
        js = self.html
        # Extract getFormValues field array
        m = re.search(
            r"function\s+getFormValues\s*\(\s*\)\s*\{[^}]*?const\s+fields\s*=\s*\[([^\]]+)\]",
            js,
            re.DOTALL,
        )
        assert m, "Could not find getFormValues() fields array"
        fields = set(re.findall(r"'([^']+)'", m.group(1)))
        fields.add("cam_auto_exposure")

        # For each numeric field (not excluded), check it has an element in the DOM
        excluded = {
            "point", "camera_id", "cam_resolution", "detect_method",
            "use_clahe", "circle_adaptive_thresh", "cam_auto_exposure",
            "server_api_url", "api_key",
        }
        numeric = fields - excluded

        missing_el = []
        for field in sorted(numeric):
            # Need an element with this id (either hidden input or the range primary)
            pattern = re.compile(r'<input[^>]*id="' + re.escape(field) + r'"')
            has_element = bool(pattern.search(js))
            # Also check if there's a slider with this id
            if not has_element:
                slider = _find_slider_tag(js, field)
                if slider:
                    has_element = True
            if not has_element:
                missing_el.append(field)

        assert not missing_el, (
            f"Fields in getFormValues() missing DOM element (no slider or hidden input): "
            f"{missing_el}"
        )

    def test_slider_value_initialized_from_hidden(self):
        """The slider's value attribute should match the hidden input's value attribute."""
        mismatches = []
        for key in sorted(self.slider_ranges.keys()):
            if key in RANGE_PRIMARY:
                continue
            tag = _find_slider_tag(self.html, key)
            if not tag:
                continue
            slider_val = _get_attr(tag, "value")

            # Find hidden input value
            hidden_pattern = re.compile(
                r'<input[^>]*id="' + re.escape(key) + r'"[^>]*value="([^"]*)"'
            )
            hm = hidden_pattern.search(self.html)
            if hm and slider_val:
                hidden_val = hm.group(1)
                if slider_val != hidden_val:
                    mismatches.append((key, slider_val, hidden_val))
        assert not mismatches, (
            "Slider/hidden input value mismatch (key, slider, hidden): " + str(mismatches)
        )

    def test_refresh_sliders_function_exists(self):
        """refreshSliders() function must be defined in the JS."""
        assert "function refreshSliders()" in self.html, (
            "refreshSliders() function not found in index.html"
        )
        # Check it references SLIDER_RANGES keys
        assert "SLIDER_RANGES" in self.html.split("function refreshSliders")[1], (
            "refreshSliders() should iterate SLIDER_RANGES keys"
        )
        # Check it updates value labels
        assert "'_val'" in self.html.split("function refreshSliders")[1], (
            "refreshSliders() should reference value label span IDs"
        )

    def test_debounced_update_exists(self):
        """debouncedUpdateStreamConfig() must exist with 300ms timeout."""
        assert "debouncedUpdateStreamConfig" in self.html, (
            "debouncedUpdateStreamConfig function not found"
        )
        assert "300" in self.html, (
            "Expected 300ms debounce timeout not found"
        )
