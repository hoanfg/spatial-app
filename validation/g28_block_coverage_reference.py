import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.stats import rankdata
from numpy.random import default_rng
import json
# Independent vectorized replay of fixed nonoverlapping block resampling.
# It uses the production block partition and percentile convention, not a production import.
N=20; B=200; R=120; rho=.6; truth=6/np.pi*np.arcsin(rho/2)
rng=default_rng(271128); x,y=np.indices((N,N));x=x.ravel();y=y.ravel()
blocks={}
for k in [1,2,4,5,10]:
    keys=(x//k)*1000003+y//k
    _,inv=np.unique(keys,return_inverse=True)
    blocks[k]=np.array([np.flatnonzero(inv==i) for i in range(inv.max()+1)])
out=[]
for sigma in [0,1,2]:
  res={k:[] for k in blocks if len(blocks[k])>=5}
  for rep in range(R):
    a=rng.normal(size=(N,N)); e=rng.normal(size=(N,N))
    if sigma:
      a=gaussian_filter(a,sigma,mode='wrap'); e=gaussian_filter(e,sigma,mode='wrap')
    a=a.ravel(); e=e.ravel(); b=rho*a+np.sqrt(1-rho*rho)*e
    for k in res:
      m=blocks[k]; idx=m[rng.integers(0,len(m),size=(B,len(m)))].reshape(B,-1)
      ra=rankdata(a[idx],axis=1); rb=rankdata(b[idx],axis=1)
      ra-=ra.mean(1,keepdims=True); rb-=rb.mean(1,keepdims=True)
      rr=(ra*rb).sum(1)/np.sqrt((ra*ra).sum(1)*(rb*rb).sum(1))
      lo,hi=np.percentile(rr,[2.5,97.5]);res[k].append([float(lo),float(hi)])
  for k,intervals in res.items():
    v=np.array(intervals); hit=int(((v[:,0]<=truth)&(truth<=v[:,1])).sum());out.append(dict(sigma=sigma,block=k,blocks=len(blocks[k]),hits=hit,reps=R,coverage=hit/R,mean_width=float(np.mean(v[:,1]-v[:,0]))))
print(json.dumps(dict(seed=271128,n_side=N,replicates=R,resamples=B,latent_pearson=rho,true_spearman=truth,rows=out,excluded_block10_count=len(blocks[10])),indent=2))
