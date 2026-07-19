import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
from itertools import combinations
from typing import Dict, List, Optional
from src.signal import estimate_ar1

class PairSelector:
    """
    Handles cointegration testing and pair selection logic across 
    different price spaces (Raw and Log).
    """
    def __init__(self, pvalue_threshold: float = 0.05):
        self.pvalue_threshold = pvalue_threshold

    @staticmethod
    def analyze_pair(stock1: pd.Series, stock2: pd.Series) -> Dict[str, float]:
        """
        Perform a comprehensive cointegration analysis on a pair of stocks.
        Returns metrics for both raw and log-price spaces.
        """
        combined = pd.concat([stock1, stock2], axis=1).dropna()
        if len(combined) < 20:
            return {
                'cointegration_pvalue': 1.0,
                'correlation': 0.0,
                'half_life': np.nan,
                'hedge_ratio': np.nan,
                'phi': np.nan,
                'sigma_eq': np.nan,
                'cointegration_pvalue_log': 1.0,
                'correlation_log': 0.0,
                'half_life_log': np.nan,
                'hedge_ratio_log': np.nan,
                'phi_log': np.nan,
                'sigma_eq_log': np.nan
            }
        
        s1, s2 = combined.iloc[:, 0], combined.iloc[:, 1]
        
        # --- RAW SPACE ANALYSIS ---
        _, pvalue, _ = coint(s1, s2)
        correlation = s1.corr(s2)
        model = sm.OLS(s2, sm.add_constant(s1)).fit()
        ar1_res = estimate_ar1(model.resid)

        # --- LOG SPACE ANALYSIS ---
        s1_log, s2_log = np.log(s1), np.log(s2)
        _, pvalue_log, _ = coint(s1_log, s2_log)
        correlation_log = s1_log.corr(s2_log)
        model_log = sm.OLS(s2_log, sm.add_constant(s1_log)).fit()
        ar1_res_log = estimate_ar1(model_log.resid)
    
        return {
            'cointegration_pvalue': pvalue,
            'correlation': correlation,
            'half_life': ar1_res['half_life'],
            'hedge_ratio': model.params[1],
            'intercept': model.params[0],
            'phi': ar1_res['phi'],
            'sigma_eq': ar1_res['sigma_eq'],
            'cointegration_pvalue_log': pvalue_log,
            'correlation_log': correlation_log,
            'half_life_log': ar1_res_log['half_life'],
            'hedge_ratio_log': model_log.params[1],
            'intercept_log': model_log.params[0],
            'phi_log': ar1_res_log['phi'],
            'sigma_eq_log': ar1_res_log['sigma_eq']
        }
        
    def select_pairs(self, master_df: pd.DataFrame, sector_map: Dict[str, List[str]], start: str, end: str, same_sector_only: bool = True, return_divergence_threshold: Optional[float] = None) -> pd.DataFrame:
        """
        Analyze pairs and return cointegrated pairs.
        When same_sector_only=True, restricts pairs to within the same sector.
        When same_sector_only=False, considers all possible pairs across all sectors.
        When return_divergence_threshold is set, skips pairs whose cumulative stock returns
        over the selection window differ by more than the threshold.

        Populates self._stats dict after each call:
            total_combinations, divergence_skipped, coint_tested, coint_passed
        """
        self._stats = {'total_combinations': 0, 'divergence_skipped': 0, 'coint_tested': 0, 'coint_passed': 0}
        all_results = []
        
        # Handle MultiIndex or standard DataFrame
        if isinstance(master_df.columns, pd.MultiIndex):
            close_prices = master_df['Close']
        else:
            close_prices = master_df

        if same_sector_only:
            # Original behavior: iterate through sectors to maintain homogeneity
            sector_iter = sector_map.items()
        else:
            # Cross-sector: treat all tickers as one group with a placeholder sector
            all_tickers = sorted([t for t in set().union(*sector_map.values()) if t in close_prices.columns])
            if len(all_tickers) < 2:
                return pd.DataFrame()
            sector_iter = [('Cross-Sector', all_tickers)]
            
        # Iterate through sectors (or the single cross-sector group)
        for sector, tickers in sector_iter:
            # Only use tickers available in the dataframe and SORT ALPHABETICALLY
            # to match the combination order in the original Analysis.py
            available_tickers = sorted([t for t in tickers if t in close_prices.columns])
            if len(available_tickers) < 2:
                continue
                
            sector_data = close_prices.loc[start:end, available_tickers]
            sector_results = []
    
            for ticker1, ticker2 in combinations(sector_data.columns, 2):
                self._stats['total_combinations'] += 1
                # Return divergence pre-filter: skip pairs with divergent cumulative returns
                if return_divergence_threshold is not None:
                    c1, c2 = sector_data[ticker1], sector_data[ticker2]
                    r1 = c1.iloc[-1] / c1.iloc[0] - 1
                    r2 = c2.iloc[-1] / c2.iloc[0] - 1
                    if abs(r1 - r2) > return_divergence_threshold:
                        self._stats['divergence_skipped'] += 1
                        continue
                self._stats['coint_tested'] += 1
                try:
                    result = self.analyze_pair(sector_data[ticker1], sector_data[ticker2])
                    sector_results.append({
                        'pair': f'{ticker1}-{ticker2}',
                        'sector': sector,
                        **result,
                        'period': f'{start} to {end}'
                    })
                except Exception as e:
                    print(f"Error analyzing pair {ticker1}-{ticker2} in {sector}: {str(e)}")
            
            if sector_results:
                sector_df = pd.DataFrame(sector_results)
                # 1. Apply Analysis.py legacy filter (Raw P < 0.05 and Raw Half-Life > 0)
                mask = (sector_df['cointegration_pvalue'] < self.pvalue_threshold) & (sector_df['half_life'] > 0)
                filtered_sector = sector_df[mask].sort_values('cointegration_pvalue', ascending=True)
                all_results.append(filtered_sector)
        
        if not all_results:
            self._stats['coint_passed'] = 0
            return pd.DataFrame()

        df = pd.concat(all_results)
        
        # 2. Apply run_oos_walkforward.py Strategy Filter (Log P < 0.05)
        # Note: Analysis.py results are already filtered for Raw P < 0.05
        df = df[df['cointegration_pvalue_log'] < self.pvalue_threshold]
        
        self._stats['coint_passed'] = len(df)
        
        # 3. Final Rank by Log Space significance as per strategy parameters
        return df.sort_values('cointegration_pvalue_log', ascending=True)

    def revalidate_pairs(self, pairs_list: List[str], master_df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
        """
        Re-analyze a specific list of pairs over a new date range.
        Used to verify if cointegration still holds before entering a test period.
        """
        results = []
        
        if isinstance(master_df.columns, pd.MultiIndex):
            close_prices = master_df['Close']
        else:
            close_prices = master_df
            
        close_prices = close_prices.loc[start:end]
    
        for pair_str in pairs_list:
            try:
                parts = pair_str.split('-')
                if len(parts) != 2: continue
                ticker1, ticker2 = parts
                
                if ticker1 not in close_prices.columns or ticker2 not in close_prices.columns:
                    continue
                    
                result = self.analyze_pair(close_prices[ticker1], close_prices[ticker2])
                results.append({
                    'pair': pair_str,
                    **result,
                    'period': f'{start} to {end} (Revalidation)'
                })
            except Exception as e:
                print(f"Error revalidating pair {pair_str}: {str(e)}")
        
        return pd.DataFrame(results)
