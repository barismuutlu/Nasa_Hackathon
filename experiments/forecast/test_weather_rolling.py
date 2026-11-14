# Bahtiyar protokolü (1 ay ileri, yıllık kayan başlangıç 2015-2025, log1p, taban = normal) — hava ekli/eksiz aynı kodla
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/baris-mutlu/Desktop/NASA/pipeline'); import forecast as F
from sklearn.linear_model import LinearRegression
last=F.last_complete_month(); P=F.build_panel(last); P=P[P.period<=last].copy()
P['ly']=np.log1p(P.n_harm)
w=pd.read_parquet('/home/baris-mutlu/Desktop/NASA/data/weather_power.parquet'); w=w[w.n_days>=25]
P=P.merge(w[['cell_lat','cell_lon','year','month','prec_mm','tmax_c','rh_pct']],how='left')
P=P.sort_values(['cell_lat','cell_lon','period']).reset_index(drop=True)
def run(use_w):
    se_m=se_n=0.0; hits=n=0
    for Y in range(2015,2026):
        hist=P[P.year<Y]
        norm=hist.groupby(['cell_lat','cell_lon','month']).ly.mean().rename('norm')
        d=P[P.year<=Y].merge(norm.reset_index(),how='left')
        d['dev']=d.ly-d.norm
        d['rdev']=d.groupby('period').dev.transform('mean')
        if use_w:
            wn=hist.groupby(['cell_lat','cell_lon','month'])[['prec_mm','tmax_c','rh_pct']].mean().add_suffix('_n').reset_index()
            d=d.merge(wn,how='left')
            for c in ['prec_mm','tmax_c','rh_pct']: d[c+'_a']=d[c]-d[c+'_n']
        d=d.sort_values(['cell_lat','cell_lon','period'])
        g=d.groupby(['cell_lat','cell_lon'])
        X=['dev1','rdev1']+(['prec1','prec3','tmax1','rh1'] if use_w else [])
        d['dev1']=g.dev.shift(1); d['rdev1']=g.rdev.shift(1)
        if use_w:
            d['prec1']=g.prec_mm_a.shift(1); d['prec3']=g.prec_mm_a.transform(lambda x:x.shift(1).rolling(3).sum())
            d['tmax1']=g.tmax_c_a.shift(1); d['rh1']=g.rh_pct_a.shift(1)
        d=d.dropna(subset=X+['dev','norm'])
        tr=d[d.year<Y]; te=d[d.year==Y]
        m=LinearRegression().fit(tr[X],tr.dev); p=m.predict(te[X])
        se_m+=((te.dev-p)**2).sum(); se_n+=(te.dev**2).sum()
        big=np.abs(p)>0.2; hits+=(np.sign(p[big])==np.sign(te.dev[big])).sum(); n+=big.sum()
    return 1-se_m/se_n, hits/n, n
for lab,uw in [('Bahtiyar modeli (sadece FIRMS)',False),('+ NASA POWER hava',True)]:
    s,h,n=run(uw); print(f'{lab:32s} beceri={s:.3f}  yön isabeti=%{100*h:.1f} (n={n})')
