# Fama-French on combined pct=0.25 book and legs

Model: FF3 + Momentum + ST_Reversal, daily factors, HAC standard errors. Alpha annualized x252. Pair = current #1 survivor (sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7), mechanism A, pct=0.25.

## Recent window

### combined momentum

```
Fama-French 3-Factor + Momentum + ST_Reversal Regression
=================================================================
  Daily Alpha:    -0.0200%
  Annualized (x252): -5.05%
  Alpha t-stat:     -1.057
  Alpha p-value:    0.2903

  R-squared:  0.1882
  Adj R-squared: 0.1797
  Observations: 487 days

  Loadings (HAC standard errors):
  Factor             Beta   t-stat  p-value
  ------------ ---------- -------- --------
  const           -0.0002   -1.057   0.2903
  Mkt-RF           0.1929    2.402   0.0163
  SMB             -0.1256   -1.855   0.0635
  HML             -0.0426   -0.984   0.3251
  Mom             -0.0519   -0.920   0.3575
  ST_Rev           0.1164    1.982   0.0474
```

### leg A sp500-12m cross1m noscreen

```
Fama-French 3-Factor + Momentum + ST_Reversal Regression
=================================================================
  Daily Alpha:    +0.0063%
  Annualized (x252): +1.60%
  Alpha t-stat:     0.209
  Alpha p-value:    0.8342

  R-squared:  0.0957
  Adj R-squared: 0.0863
  Observations: 487 days

  Loadings (HAC standard errors):
  Factor             Beta   t-stat  p-value
  ------------ ---------- -------- --------
  const            0.0001    0.209   0.8342
  Mkt-RF           0.2018    2.709   0.0068
  SMB             -0.0373   -0.521   0.6026
  HML              0.0092    0.176   0.8603
  Mom             -0.0477   -0.857   0.3913
  ST_Rev           0.1035    1.496   0.1346
```

### leg B sp500-2m cross3m bd7

```
Fama-French 3-Factor + Momentum + ST_Reversal Regression
=================================================================
  Daily Alpha:    -0.0776%
  Annualized (x252): -19.57%
  Alpha t-stat:     -1.587
  Alpha p-value:    0.1126

  R-squared:  0.3077
  Adj R-squared: 0.2931
  Observations: 244 days

  Loadings (HAC standard errors):
  Factor             Beta   t-stat  p-value
  ------------ ---------- -------- --------
  const           -0.0008   -1.587   0.1126
  Mkt-RF           0.3096    3.013   0.0026
  SMB             -0.3451   -3.609   0.0003
  HML             -0.1380   -1.648   0.0993
  Mom             -0.0755   -0.794   0.4270
  ST_Rev           0.2888    3.204   0.0014
```

## Historical window

### combined momentum

```
Fama-French 3-Factor + Momentum + ST_Reversal Regression
=================================================================
  Daily Alpha:    +0.0227%
  Annualized (x252): +5.71%
  Alpha t-stat:     1.790
  Alpha p-value:    0.0735

  R-squared:  0.0283
  Adj R-squared: 0.0244
  Observations: 1255 days

  Loadings (HAC standard errors):
  Factor             Beta   t-stat  p-value
  ------------ ---------- -------- --------
  const            0.0002    1.790   0.0735
  Mkt-RF           0.0400    1.255   0.2093
  SMB             -0.0592   -1.326   0.1848
  HML             -0.0364   -1.442   0.1494
  Mom              0.0144    0.568   0.5702
  ST_Rev           0.0839    2.230   0.0258
```

### leg A sp500-12m cross1m noscreen

```
Fama-French 3-Factor + Momentum + ST_Reversal Regression
=================================================================
  Daily Alpha:    +0.0013%
  Annualized (x252): +0.32%
  Alpha t-stat:     0.089
  Alpha p-value:    0.9289

  R-squared:  0.0383
  Adj R-squared: 0.0345
  Observations: 1250 days

  Loadings (HAC standard errors):
  Factor             Beta   t-stat  p-value
  ------------ ---------- -------- --------
  const            0.0000    0.089   0.9289
  Mkt-RF           0.0625    3.200   0.0014
  SMB             -0.0486   -1.416   0.1567
  HML             -0.0065   -0.179   0.8580
  Mom              0.0005    0.019   0.9849
  ST_Rev           0.1164    2.945   0.0032
```

### leg B sp500-2m cross3m bd7

```
Fama-French 3-Factor + Momentum + ST_Reversal Regression
=================================================================
  Daily Alpha:    +0.0440%
  Annualized (x252): +11.08%
  Alpha t-stat:     1.614
  Alpha p-value:    0.1066

  R-squared:  0.0268
  Adj R-squared: 0.0203
  Observations: 755 days

  Loadings (HAC standard errors):
  Factor             Beta   t-stat  p-value
  ------------ ---------- -------- --------
  const            0.0004    1.614   0.1066
  Mkt-RF           0.0382    0.664   0.5065
  SMB             -0.1036   -1.212   0.2256
  HML             -0.0940   -1.881   0.0600
  Mom              0.0390    0.748   0.4542
  ST_Rev           0.1049    1.455   0.1455
```

