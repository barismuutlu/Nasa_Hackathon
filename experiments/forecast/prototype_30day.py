import numpy as np, pandas as pd, pyarrow.parquet as pq
from sklearn.linear_model import LinearRegression
W, G = 30, 2                      # 30 günlük pencere; girdi penceresi hedeften 2 gün önce biter
LR=(-69.7,-31.9,-65.4,-27.6)
t=pq.read_table('/home/baris-mutlu/Desktop/NASA/data/hotspots_harm.parquet',columns=['latitude','longitude','acq_date','region','weight_harm'],filters=[('region','=','argentina')]).to_pandas()
t['cell_lat']=np.floor(t.latitude)+.5; t['cell_lon']=np.floor(t.longitude)+.5
day0=pd.Timestamp('2003-01-01'); t=t[t.acq_date>=day0]; t['di']=(t.acq_date-day0).dt.days
cells=t[['cell_lat','cell_lon']].drop_duplicates().reset_index(drop=True); cells['ci']=range(len(cells))
cells['lr']=cells.cell_lon.between(LR[0],LR[2])&cells.cell_lat.between(LR[1],LR[3])
t=t.merge(cells); last_full=pd.Timestamp('2026-11-12'); nd=(last_full-day0).days+1
t=t[t.di<nd]
A=np.zeros((len(cells),nd)); np.add.at(A,(t.ci.to_numpy(),t.di.to_numpy()),t.weight_harm.to_numpy())
C=np.concatenate([np.zeros((len(cells),1)),A.cumsum(1)],1)
def ws(s): return C[:,s+W]-C[:,s]
rows=[]
for y in range(2003,2027):
    for m in range(1,13):
        o=(pd.Timestamp(y,m,15)-day0).days
        if o-G-W<0: continue
        nxt=np.log1p(ws(o)) if o+W<=nd else np.full(len(cells),np.nan)
        if o-G>nd: continue
        rows.append(pd.DataFrame({'ci':cells.ci,'year':y,'om':m,'prev':np.log1p(ws(o-G-W)),'next':nxt}))
D=pd.concat(rows,ignore_index=True)
def prep(d,h):
    nn=h.groupby(['ci','om'])['next'].mean().rename('nn'); pn=h.groupby(['ci','om'])['prev'].mean().rename('pn')
    d=d.join(nn,on=['ci','om']).join(pn,on=['ci','om']); d['dev']=d['next']-d.nn; d['pdev']=d.prev-d.pn
    d['rpdev']=d.groupby(['year','om']).pdev.transform('mean'); return d
X=['pdev','rpdev']; se_m=se_n=0; hits=n=0; tots=[]
for Y in range(2015,2026):
    d=prep(D[D.year<=Y],D[D.year<Y]).dropna(subset=X+['nn','dev'])
    tr=d[d.year<Y]; te=d[d.year==Y].copy(); p=LinearRegression().fit(tr[X],tr.dev).predict(te[X])
    se_m+=((te.dev-p)**2).sum(); se_n+=(te.dev**2).sum()
    big=np.abs(p)>0.2; hits+=(np.sign(p[big])==np.sign(te.dev[big])).sum(); n+=big.sum()
    te['pred']=np.expm1(te.nn+p); te['obs']=np.expm1(te['next']); te['norm']=np.expm1(te.nn); te=te.merge(cells[['ci','lr']])
    for sc,mk in [('AR',slice(None)),('LR',te.lr)]:
        tots.append(te[mk] .groupby(['year','om'])[['obs','pred','norm']].sum().assign(scope=sc) if sc=='LR' else te.groupby(['year','om'])[['obs','pred','norm']].sum().assign(scope=sc))
print(f'Geriye dönük test (2 gün boşluk, 30 gün): beceri={1-se_m/se_n:.3f} yön=%{100*hits/n:.1f}')
T=pd.concat(tots); T['err']=np.log1p(T.obs)-np.log1p(T.pred)
# canlı: başlangıç 2026-11-15, girdi 2026-10-14 … 11-12, tüm geçmişle eğit
hist=D[D.next.notna()]; live=D[(D.year==2026)&(D.om==11)]
d=prep(pd.concat([hist,live]).drop_duplicates(['ci','year','om'],keep='last'),hist)
tr=d.dropna(subset=X+['nn','dev']); lv=d[(d.year==2026)&(d.om==11)].copy()
m=LinearRegression().fit(tr[X],tr.dev); lv['pred']=np.expm1(lv.nn+m.predict(lv[X])); lv['norm']=np.expm1(lv.nn); lv=lv.merge(cells)
print('katsayılar:',dict(zip(X,m.coef_.round(3))))
for sc,mk in [('Arjantin',slice(None)),('La Rioja',lv.lr)]:
    s=lv[mk] if sc=='La Rioja' else lv; e=T[T.scope==('LR' if sc=='La Rioja' else 'AR')].err
    p=s.pred.sum(); lo,hi=np.expm1(np.log1p(p)+e.quantile(.1)),np.expm1(np.log1p(p)+e.quantile(.9))
    print(f'  {sc:9s} 15 Kas–14 Ara: beklenen {p:,.0f} (10–90%: {lo:,.0f}–{hi:,.0f}), normal {s.norm.sum():,.0f}, oran {p/s.norm.sum():.2f}, son 30 gün/normal {np.expm1(s.prev).sum()/np.expm1(s.pn).sum():.2f}')

print('\n--- toplam sapması kontrolü (backtest) ---')
# yöntem 1: Σ expm1(log tahmin)  | yöntem 2: oran (Σpred/Σnorm) × aritmetik normal (önceki yılların aynı pencere toplamlarının ort., son 10 yıl)
raw_tot={}
for Y in range(2003,2027):
    pass
Dfull=D.copy(); Dfull['obs']=np.expm1(Dfull['next']); Dfull=Dfull.merge(cells[['ci','lr']])
for sc in ['AR','LR']:
    d=Dfull if sc=='AR' else Dfull[Dfull.lr]
    tot=d.groupby(['year','om']).obs.sum().unstack('om')
    TT=T[T.scope==sc].copy()
    am=[tot.loc[(tot.index<y)&(tot.index>=y-10),om].mean() for y,om in TT.index]
    TT['arith_norm']=am; TT['pred2']=TT.pred/TT.norm*TT.arith_norm
    for c in ['pred','pred2','norm','arith_norm']:
        print(f'  {sc} {c:10s} toplam sapma={100*(TT[c].sum()/TT.obs.sum()-1):+6.1f}%  MAE(log)={np.mean(np.abs(np.log1p(TT[c])-np.log1p(TT.obs))):.3f}')
print('son 30 gün gerçek (14 Eki–12 Kas) Arjantin:', round(np.expm1(lv.prev).sum()), ' La Rioja:', round(np.expm1(lv[lv.lr].prev).sum()))

print('\n--- CANLI (düzeltilmiş): 15 Kas – 14 Ara 2026 ---')
for sc in ['AR','LR']:
    d=Dfull if sc=='AR' else Dfull[Dfull.lr]; s=lv if sc=='AR' else lv[lv.lr]
    tot=d[d.om==11].groupby('year').obs.sum(); an=tot.loc[2016:2025].mean()
    TT=T[T.scope==sc].copy(); am=[]
    for y,om in TT.index:
        tt=d[d.om==om].groupby('year').obs.sum(); am.append(tt.loc[y-10:y-1].mean())
    TT['pred2']=TT.pred/TT.norm*pd.Series(am,index=TT.index); e=np.log1p(TT.obs)-np.log1p(TT.pred2)
    r=s.pred.sum()/s.norm.sum(); p=r*an
    lo,hi=np.expm1(np.log1p(p)+e.quantile(.1)),np.expm1(np.log1p(p)+e.quantile(.9))
    lab='normalin altı' if r<0.67 else ('normalin üstü' if r>1.5 else 'normale yakın')
    print(f'  {"Arjantin" if sc=="AR" else "La Rioja":9s} beklenen {p:,.0f} (10–90%: {lo:,.0f}–{hi:,.0f})  normal(2016–25 ort.) {an:,.0f}  oran {r:.2f} → {lab}')
    print(f'     geçmiş yıllar aynı pencere: min {tot.loc[2016:2025].min():,.0f}  max {tot.loc[2016:2025].max():,.0f}')
