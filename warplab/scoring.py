def score_candidate(speedup: float, cv: float, valid: bool, compile_ok: bool) -> float:
    if not compile_ok or not valid:
        return float("-inf")
    # Base formula: J = speedup - 0.25 * cv
    return speedup - 0.25 * cv
