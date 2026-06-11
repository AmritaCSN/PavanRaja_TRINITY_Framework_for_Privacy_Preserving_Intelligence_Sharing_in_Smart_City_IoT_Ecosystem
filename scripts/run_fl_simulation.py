#!/usr/bin/env python3.10
"""TRINITY Phase 3 — FL Simulation (FedAvg + FedProx) — 50 rounds"""
import argparse,copy,json,logging,time,sys
from pathlib import Path
import numpy as np
import torch, torch.nn as nn
from torch.optim import Adam
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s — %(message)s')
log=logging.getLogger('TRINITY.sim')
DEVICE=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
SITES=['site-1','site-2','site-3']
sys.path.insert(0,str(Path(__file__).parent))
from model import get_model,FedProxLoss
from data_loader import TonIoTDataManager

def compute_metrics(model,loader,device):
    model.eval(); ap,al=[],[]
    with torch.no_grad():
        for X,y in loader:
            X,y=X.to(device),y.to(device)
            ap.append(torch.argmax(model(X),1).cpu()); al.append(y.cpu())
    p=torch.cat(ap).numpy(); l=torch.cat(al).numpy()
    tp=((p==1)&(l==1)).sum(); fp=((p==1)&(l==0)).sum()
    fn=((p==0)&(l==1)).sum(); tn=((p==0)&(l==0)).sum()
    acc=(tp+tn)/(tp+fp+fn+tn+1e-8); pre=tp/(tp+fp+1e-8)
    rec=tp/(tp+fn+1e-8); f1=2*pre*rec/(pre+rec+1e-8)
    model.train()
    return {'accuracy':round(float(acc),4),'precision':round(float(pre),4),
            'recall':round(float(rec),4),'f1':round(float(f1),4)}

def fedavg_agg(gm,lms,counts):
    total=sum(counts); gs=gm.state_dict()
    for k in gs:
        gs[k]=sum(lms[i].state_dict()[k].float()*(counts[i]/total) for i in range(len(lms)))
    gm.load_state_dict(gs); return gm

def local_train(model,loader,algo,gp,epochs=5,lr=1e-3,mu=0.01,dev=DEVICE):
    model.train(); opt=Adam(model.parameters(),lr=lr)
    ce=nn.CrossEntropyLoss(); tl=tc=tp_=0; n=0; t0=time.time()
    fp_loss=FedProxLoss(mu) if algo=='fedprox' else None
    for _ in range(epochs):
        for X,y in loader:
            X,y=X.to(dev),y.to(dev); opt.zero_grad()
            logits=model(X)
            if algo=='fedprox' and gp:
                loss,ce_,prox_=fp_loss(logits,y,list(model.parameters()),gp)
                tp_+=prox_.item(); tc+=ce_.item()
            else:
                loss=ce(logits,y); tc+=loss.item()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            opt.step(); tl+=loss.item(); n+=1
    return {'train_loss':round(tl/max(n,1),6),'ce_loss':round(tc/max(n,1),6),
            'prox_loss':round(tp_/max(n,1),6),'latency_s':round(time.time()-t0,3)}

def run_sim(algo,n_rounds,data_root,results_dir,log_dir):
    log.info("="*50+f"\nTRINITY FL | algo={algo.upper()} rounds={n_rounds} device={DEVICE}\n"+"="*50)
    dms={s:TonIoTDataManager(s,data_root) for s in SITES}
    nf=dms['site-1'].n_features
    gm=get_model(nf).to(DEVICE)
    log.info(f"ThreatDetectorMLP | features={nf} params={gm.count_parameters():,}")
    slogs=[]; clogs={s:[] for s in SITES}
    for rnd in range(1,n_rounds+1):
        t0=time.time(); log.info(f"Round {rnd}/{n_rounds}")
        lms=[]; counts=[]
        for site in SITES:
            lm=copy.deepcopy(gm)
            gp=[p.clone().detach().to(DEVICE) for p in gm.parameters()] if algo=='fedprox' else None
            stats=local_train(lm,dms[site].get_train_loader(),algo,gp,dev=DEVICE)
            vm=compute_metrics(lm,dms[site].get_val_loader(),DEVICE)
            clogs[site].append({'round':rnd,'client_id':site,'algo':algo,
                'accuracy':vm['accuracy'],'f1':vm['f1'],
                'train_loss':stats['train_loss'],'ce_loss':stats['ce_loss'],
                'prox_loss':stats['prox_loss'],'latency_seconds':stats['latency_s'],
                'epsilon_spent':None})
            log.info(f"  {site} acc={vm['accuracy']:.4f} f1={vm['f1']:.4f} loss={stats['train_loss']:.4f}")
            lms.append(lm); counts.append(dms[site].n_train)
        gm=fedavg_agg(gm,lms,counts)
        gm_=compute_metrics(gm,dms['site-1'].get_test_loader(),DEVICE)
        lat=round(time.time()-t0,3)
        slogs.append({'round':rnd,'global_accuracy':gm_['accuracy'],'global_f1':gm_['f1'],
            'global_precision':gm_['precision'],'global_recall':gm_['recall'],
            'latency_seconds':lat,'algo':algo,'model_hash':None,'blockchain_tx_id':None})
        log.info(f"  GLOBAL acc={gm_['accuracy']:.4f} f1={gm_['f1']:.4f} time={lat}s")
    Path(log_dir).mkdir(exist_ok=True); Path(results_dir).mkdir(exist_ok=True)
    json.dump(slogs,open(f'{log_dir}/server_{algo}_rounds.json','w'),indent=2)
    for s in SITES: json.dump(clogs[s],open(f'{log_dir}/{s}_{algo}_rounds.json','w'),indent=2)
    final=slogs[-1]
    res={'algo':algo,'n_rounds':n_rounds,'final_accuracy':final['global_accuracy'],
         'final_f1':final['global_f1'],'final_precision':final['global_precision'],
         'final_recall':final['global_recall'],
         'avg_latency_s':round(np.mean([s['latency_seconds'] for s in slogs]),3),
         'privacy_mode':'none','epsilon':None}
    json.dump(res,open(f'{results_dir}/{algo}_results.json','w'),indent=2)
    log.info(f"DONE {algo.upper()} | acc={final['global_accuracy']:.4f} f1={final['global_f1']:.4f}")
    return res

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--algo',choices=['fedavg','fedprox','both'],default='both')
    p.add_argument('--rounds',type=int,default=50)
    p.add_argument('--data_root',default='data/processed')
    p.add_argument('--results_dir',default='results')
    p.add_argument('--log_dir',default='logs')
    args=p.parse_args()
    algos=['fedavg','fedprox'] if args.algo=='both' else [args.algo]
    all_r={}
    for algo in algos:
        all_r[algo]=run_sim(algo,args.rounds,args.data_root,args.results_dir,args.log_dir)
    print("\n"+"="*55+"\nTRINITY Phase 3 Results\n"+"="*55)
    print(f"{'Algo':<12}{'Accuracy':<12}{'F1':<10}{'Latency/round'}")
    print("-"*55)
    for algo,r in all_r.items():
        print(f"{algo.upper():<12}{r['final_accuracy']:<12.4f}{r['final_f1']:<10.4f}{r['avg_latency_s']:.3f}s")

if __name__=='__main__': main()
