import numpy as np

def check_hr_stability(current_hr: float, anchor_hr: float, threshold: float) -> bool:
    """
    Checks if the current hedge ratio has drifted too far from the anchor value.
    Returns True if the drift is within the threshold, False otherwise.
    """
    if anchor_hr == 0:
        return True
    
    drift = abs(current_hr - anchor_hr) / abs(anchor_hr)
    return drift <= threshold

def calculate_locked_zscore(s1_val: float, s2_val: float, 
                             alpha_entry: float, beta_entry: float, 
                             mu_entry: float, sigma_entry: float, 
                             log_space: bool = True) -> float:
    """
    Calculates a Z-score using parameters 'locked' at trade entry.
    Prevents the signal from absorbing the spread's drift during a trade.
    """
    if log_space:
        s1_val, s2_val = np.log(s1_val), np.log(s2_val)
        
    resid = s2_val - (alpha_entry + beta_entry * s1_val)
    z = (resid - mu_entry) / (sigma_entry + 1e-10)
    return z
