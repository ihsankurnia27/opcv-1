def angle_to_value(angle_deg, min_angle, max_angle, min_value, max_value):
    """Map needle angle to gauge value with wrap-around support.

    Returns value clamped to [min_value, max_value].
    """
    new_range = max_value - min_value
    if min_angle <= max_angle:
        denom = max_angle - min_angle
        if denom == 0:
            return min_value
        value = ((angle_deg - min_angle) * new_range) / denom + min_value
    else:
        denom = (360 - min_angle) + max_angle
        if denom == 0:
            return min_value
        if angle_deg >= min_angle:
            numer = angle_deg - min_angle
        else:
            numer = (360 - min_angle) + angle_deg
        value = (numer * new_range) / denom + min_value
    return max(min_value, min(max_value, value))
