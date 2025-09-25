def clamp(value: int | float, min_value: int | float, max_value: int | float):
  return max(min(value, max_value), min_value)