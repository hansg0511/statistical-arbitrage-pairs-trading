# Centralized project constants

# ---------------------------------------------------------------------------
# Core mega-cap universe (67 stocks across 8 GICS sectors)
# ---------------------------------------------------------------------------
SECTOR_MAP_CORE = {
    'Tech': ['AAPL', 'MSFT', 'CRM', 'ADBE', 'TXN', 'NVDA', 'INTC', 'CSCO', 'ORCL', 'AVGO'],
    'Financials': ['JPM', 'V', 'MA', 'BAC', 'GS', 'MS', 'AXP', 'PYPL'],
    'CommServices': ['GOOGL', 'META', 'NFLX', 'VZ', 'DIS', 'CMCSA', 'TMUS', 'T'],
    'Staples': ['PG', 'KO', 'PEP', 'WMT', 'COST', 'MDLZ', 'CL', 'MO'],
    'Discretionary': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'SBUX', 'TJX'],
    'Healthcare': ['JNJ', 'UNH', 'LLY', 'ABT', 'DHR', 'TMO', 'PFE', 'MRK', 'AMGN', 'GILD'],
    'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX'],
    'Industrials': ['GE', 'HON', 'UPS', 'UNP', 'CAT', 'BA', 'LMT', 'RTX']
}
TICKERS_CORE = [t for sector in SECTOR_MAP_CORE.values() for t in sector]

# ---------------------------------------------------------------------------
# Full S&P 500 universe (503 stocks across all 11 GICS sectors)
# ---------------------------------------------------------------------------
SECTOR_MAP_SP500 = {
    'Tech': ['AAPL', 'ACN', 'ADBE', 'ADI', 'ADSK', 'AKAM', 'AMAT', 'AMD', 'ANET', 'APH', 'APP', 'AVGO', 'CDNS', 'CDW', 'CIEN', 'COHR', 'CRM', 'CRWD', 'CSCO', 'CTSH', 'DDOG', 'DELL', 'FFIV', 'FICO', 'FLEX', 'FSLR', 'FTNT', 'GDDY', 'GEN', 'GLW', 'HPE', 'HPQ', 'IBM', 'INTC', 'INTU', 'IT', 'JBL', 'KEYS', 'KLAC', 'LITE', 'LRCX', 'MCHP', 'MPWR', 'MRVL', 'MSFT', 'MSI', 'MU', 'NOW', 'NTAP', 'NVDA', 'NXPI', 'ON', 'ORCL', 'PANW', 'PLTR', 'PTC', 'Q', 'QCOM', 'ROP', 'SMCI', 'SNDK', 'SNPS', 'STX', 'SWKS', 'TDY', 'TEL', 'TER', 'TRMB', 'TXN', 'TYL', 'VRSN', 'WDAY', 'WDC', 'ZBRA'],
    'Financials': ['ACGL', 'AFL', 'AIG', 'AIZ', 'AJG', 'ALL', 'AMP', 'AON', 'APO', 'ARES', 'AXP', 'BAC', 'BEN', 'BLK', 'BNY', 'BRK.B', 'BRO', 'BX', 'C', 'CB', 'CBOE', 'CFG', 'CINF', 'CME', 'COF', 'COIN', 'CPAY', 'EG', 'ERIE', 'FDS', 'FIS', 'FISV', 'FITB', 'GL', 'GPN', 'GS', 'HBAN', 'HIG', 'HOOD', 'IBKR', 'ICE', 'IVZ', 'JKHY', 'JPM', 'KEY', 'KKR', 'L', 'MA', 'MCO', 'MET', 'MRSH', 'MS', 'MSCI', 'MTB', 'NDAQ', 'NTRS', 'PFG', 'PGR', 'PNC', 'PRU', 'PYPL', 'RF', 'RJF', 'SCHW', 'SPGI', 'STT', 'SYF', 'TFC', 'TROW', 'TRV', 'USB', 'V', 'WFC', 'WRB', 'WTW', 'XYZ'],
    'CommServices': ['CHTR', 'CMCSA', 'DIS', 'EA', 'ECHO', 'FOX', 'FOXA', 'GOOG', 'GOOGL', 'LYV', 'META', 'NFLX', 'NWS', 'NWSA', 'OMC', 'PSKY', 'T', 'TKO', 'TMUS', 'TTD', 'TTWO', 'VZ', 'WBD'],
    'Staples': ['ADM', 'BF.B', 'BG', 'CASY', 'CHD', 'CL', 'CLX', 'COST', 'DG', 'DLTR', 'EL', 'GIS', 'HRL', 'HSY', 'KDP', 'KHC', 'KMB', 'KO', 'KR', 'KVUE', 'MDLZ', 'MKC', 'MNST', 'MO', 'PEP', 'PG', 'PM', 'SJM', 'STZ', 'SYY', 'TAP', 'TGT', 'TSN', 'WMT'],
    'Discretionary': ['ABNB', 'AMZN', 'APTV', 'AZO', 'BBY', 'BKNG', 'CCL', 'CMG', 'CVNA', 'DASH', 'DECK', 'DHI', 'DPZ', 'DRI', 'EBAY', 'EXPE', 'F', 'GM', 'GPC', 'GRMN', 'HAS', 'HD', 'HLT', 'LEN', 'LOW', 'LULU', 'LVS', 'MAR', 'MCD', 'MGM', 'NCLH', 'NKE', 'NVR', 'ORLY', 'PHM', 'RCL', 'RL', 'ROST', 'SBUX', 'TJX', 'TPR', 'TSCO', 'TSLA', 'ULTA', 'WSM', 'WYNN', 'YUM'],
    'Healthcare': ['A', 'ABBV', 'ABT', 'ALGN', 'AMGN', 'BAX', 'BDX', 'BIIB', 'BMY', 'BSX', 'CAH', 'CI', 'CNC', 'COO', 'COR', 'CRL', 'CVS', 'DGX', 'DHR', 'DVA', 'DXCM', 'ELV', 'EW', 'GEHC', 'GILD', 'HCA', 'HSIC', 'HUM', 'IDXX', 'INCY', 'IQV', 'ISRG', 'JNJ', 'LH', 'LLY', 'MCK', 'MDT', 'MRK', 'MRNA', 'MTD', 'PFE', 'PODD', 'REGN', 'RMD', 'RVTY', 'SOLV', 'STE', 'SYK', 'TECH', 'TMO', 'UHS', 'UNH', 'VEEV', 'VRTX', 'VTRS', 'WAT', 'WST', 'ZBH', 'ZTS'],
    'Energy': ['APA', 'BKR', 'COP', 'CVX', 'DVN', 'EOG', 'EQT', 'EXE', 'FANG', 'HAL', 'KMI', 'MPC', 'OKE', 'OXY', 'PSX', 'SLB', 'TPL', 'TRGP', 'VLO', 'WMB', 'XOM'],
    'Industrials': ['ADP', 'ALLE', 'AME', 'AOS', 'AXON', 'BA', 'BLDR', 'BR', 'CARR', 'CAT', 'CHRW', 'CMI', 'CPRT', 'CSX', 'CTAS', 'DAL', 'DE', 'DOV', 'EFX', 'EME', 'EMR', 'ETN', 'EXPD', 'FAST', 'FDX', 'FDXF', 'FIX', 'FTV', 'GD', 'GE', 'GEV', 'GNRC', 'GWW', 'HII', 'HON', 'HONA', 'HUBB', 'HWM', 'IEX', 'IR', 'ITW', 'J', 'JBHT', 'JCI', 'LDOS', 'LHX', 'LII', 'LMT', 'LUV', 'MAS', 'MMM', 'NDSN', 'NOC', 'NSC', 'ODFL', 'OTIS', 'PAYX', 'PCAR', 'PH', 'PNR', 'PWR', 'ROK', 'ROL', 'RSG', 'RTX', 'SNA', 'SWK', 'TDG', 'TT', 'TXT', 'UAL', 'UBER', 'UNP', 'UPS', 'URI', 'VLTO', 'VRSK', 'VRT', 'WAB', 'WM', 'XYL'],
    'Materials': ['ALB', 'AMCR', 'APD', 'AVY', 'BALL', 'CF', 'CRH', 'CTVA', 'DD', 'DOW', 'ECL', 'FCX', 'IFF', 'IP', 'LIN', 'LYB', 'MLM', 'MOS', 'NEM', 'NUE', 'PKG', 'PPG', 'SHW', 'STLD', 'SW', 'VMC'],
    'RealEstate': ['AMT', 'ARE', 'AVB', 'BXP', 'CBRE', 'CCI', 'CPT', 'CSGP', 'DLR', 'DOC', 'EQIX', 'EQR', 'ESS', 'EXR', 'FRT', 'HST', 'INVH', 'IRM', 'KIM', 'MAA', 'O', 'PLD', 'PSA', 'REG', 'SBAC', 'SPG', 'UDR', 'VICI', 'VTR', 'WELL', 'WY'],
    'Utilities': ['AEE', 'AEP', 'AES', 'ATO', 'AWK', 'CEG', 'CMS', 'CNP', 'D', 'DTE', 'DUK', 'ED', 'EIX', 'ES', 'ETR', 'EVRG', 'EXC', 'FE', 'LNT', 'NEE', 'NI', 'NRG', 'PCG', 'PEG', 'PNW', 'PPL', 'SO', 'SRE', 'VST', 'WEC', 'XEL'],
}
TICKERS_SP500 = [t for sector in SECTOR_MAP_SP500.values() for t in sector]

# ---------------------------------------------------------------------------
# Active universe selection — change this to switch between universes
# ---------------------------------------------------------------------------
UNIVERSE = 'sp500'  # 'core' | 'sp500'

if UNIVERSE == 'sp500':
    SECTOR_MAP = SECTOR_MAP_SP500
    TICKERS = TICKERS_SP500
else:
    SECTOR_MAP = SECTOR_MAP_CORE
    TICKERS = TICKERS_CORE
