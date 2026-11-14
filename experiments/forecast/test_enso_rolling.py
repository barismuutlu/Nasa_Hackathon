import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/baris-mutlu/Desktop/NASA/pipeline'); import forecast as F
from sklearn.linear_model import LinearRegression
last=F.last_complete_month(); P=F.build_panel(last); P=P[P.period<=last].copy()
P['ly']=np.log1p(P.n_harm); P=P.sort_values(['cell_lat','cell_lon','period']).reset_index(drop=True)
E=pd.read_csv('/home/baris-mutlu/Desktop/NASA/data/deploy/enso_index.csv'); E=E[E.n_days>=25]
E['period']=pd.PeriodIndex.from_fields(year=E.year,month=E.month,freq='M')
def enso_feature(Y):
    # anomali tabanı: sadece Y'den önceki yıllar (2003+); 3 aylık ortalama t-1'de biter
    base=E[(E.year>=2003)&(E.year<Y)].groupby('month').ts_c.mean()
    a=(E.set_index('period').ts_c - E.set_index('period').month.map(base)).sort_index()
    return a.rolling(3).mean()
def run(variant):
    se_m=se_n=0.0; hits=n=0; yearly=[]
    for Y in range(2015,2026):
        hist=P[P.year<Y]
        norm=hist.groupby(['cell_lat','cell_lon','month']).ly.mean().rename('norm')
        d=P[P.year<=Y].merge(norm.reset_index(),how='left'); d['dev']=d.ly-d.norm
        d['rdev']=d.groupby('period').dev.transform('mean'); d=d.sort_values(['cell_lat','cell_lon','period'])
        g=d.groupby(['cell_lat','cell_lon']); d['dev1']=g.dev.shift(1); d['rdev1']=g.rdev.shift(1)
        X=['dev1','rdev1']
        if variant in 'AB':
            en=enso_feature(Y); d['enso']=(d.period-1).map(en).astype(float); X=X+['enso']
        if variant=='B':
            d['enso_warm']=d.enso*d.month.isin([10,11,12,1,2,3]); X=X+['enso_warm']
        d=d.dropna(subset=X+['dev','norm']); tr=d[d.year<Y]; te=d[d.year==Y]
        m=LinearRegression().fit(tr[X],tr.dev); p=m.predict(te[X])
        sm=((te.dev-p)**2).sum(); sn=(te.dev**2).sum(); se_m+=sm; se_n+=sn; yearly.append(round(1-sm/sn,2))
        big=np.abs(p)>0.2; hits+=(np.sign(p[big])==np.sign(te.dev[big])).sum(); n+=big.sum()
    return 1-se_m/se_n, hits/n, n, yearly, dict(zip(X,np.round(m.coef_,3)))
for lab,v in [('Bahtiyar (sadece FIRMS)','-'),('A: + El Niño (NASA)','A'),('B: + El Niño × sıcak mevsim','B')]:
    s,h,n,yr,co=run(v); print(f'{lab:30s} beceri={s:.3f} yön=%{100*h:.1f} n={n}\n   yıllık beceri 2015-25: {yr}\n   katsayılar (son yıl): {co}')

print('\n--- ufuk testi (h ay ileri; bilgi t-h ve öncesi) ---')
def run_h(h, use_enso):
    se_m=se_n=0.0; hits=n=0
    for Y in range(2015,2026):
        hist=P[P.year<Y]
        norm=hist.groupby(['cell_lat','cell_lon','month']).ly.mean().rename('norm')
        d=P[P.year<=Y].merge(norm.reset_index(),how='left'); d['dev']=d.ly-d.norm
        d['rdev']=d.groupby('period').dev.transform('mean'); d=d.sort_values(['cell_lat','cell_lon','period'])
        g=d.groupby(['cell_lat','cell_lon']); d['devh']=g.dev.shift(h); d['rdevh']=g.rdev.shift(h)
        X=['devh','rdevh']
        if use_enso:
            en=enso_feature(Y); d['enso']=(d.period-h).map(en).astype(float); X=X+['enso']
        d=d.dropna(subset=X+['dev','norm']); tr=d[d.year<Y]; te=d[d.year==Y]
        p=LinearRegression().fit(tr[X],tr.dev).predict(te[X])
        se_m+=((te.dev-p)**2).sum(); se_n+=(te.dev**2).sum()
        big=np.abs(p)>0.2; hits+=(np.sign(p[big])==np.sign(te.dev[big])).sum(); n+=big.sum()
    return 1-se_m/se_n, (hits/n if n else float('nan'))
for h in [1,2,3,4,6]:
    s0,h0=run_h(h,False); s1,h1=run_h(h,True)
    print(f'  {h} ay: sadece FIRMS beceri={s0:.3f} yön=%{100*h0:.0f}  |  + El Niño beceri={s1:.3f} yön=%{100*h1:.0f}  |  fark {s1-s0:+.3f}')
