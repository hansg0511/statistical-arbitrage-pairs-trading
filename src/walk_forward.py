import pandas as pd
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Tuple

class FoldBuilder:
    """
    Constructs overlapping or sequential date windows for walk-forward 
    validation, including selection, optimization, and test periods.
    """
    def __init__(self, start: str, end: str, sel_len: int, opt_len: int, test_len: int, slide: int):
        self.start = pd.to_datetime(start)
        self.end = pd.to_datetime(end)
        self.sel_length = sel_len
        self.opt_length = opt_len
        self.test_length = test_len
        self.slide = slide
        self.folds = self._make_folds()

    def _make_folds(self) -> List[Tuple]:
        folds = []
        curr_sel_start = self.start
        
        while True:
            # Selection Window
            sel_end = curr_sel_start + relativedelta(months=self.sel_length) - timedelta(days=1)
            
            # Optimization Window (starts immediately after selection)
            opt_start = sel_end + timedelta(days=1)
            opt_end = opt_start + relativedelta(months=self.opt_length) - timedelta(days=1)
            
            # Test Window (starts immediately after optimization)
            test_start = opt_end + timedelta(days=1)
            test_end = test_start + relativedelta(months=self.test_length) - timedelta(days=1)
            
            # Stop if the test window exceeds available data
            if test_end > self.end:
                break
                
            folds.append((
                curr_sel_start.date(), sel_end.date(),
                opt_start.date(), opt_end.date(),
                test_start.date(), test_end.date()
            ))
            
            # Slide the window forward
            curr_sel_start = curr_sel_start + relativedelta(months=self.slide)
            
        return folds

    def __iter__(self):
        return iter(self.folds)

    def get_fold(self, index: int):
        if 0 <= index < len(self.folds):
            return self.folds[index]
        return None
