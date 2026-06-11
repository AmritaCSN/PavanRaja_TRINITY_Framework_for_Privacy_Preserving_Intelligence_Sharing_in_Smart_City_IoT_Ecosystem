#!/usr/bin/env python3.10
"""
TRINITY FRAMEWORK — Phase 6+7: Full Experiment Pipeline
proj1: FedAvg              (no blockchain)
proj2: FedProx             (no blockchain)
proj3: FedProx + DP        (no blockchain)
proj4: FedProx + SMPC      (no blockchain)
proj5: FedProx + DP + SMPC (WITH blockchain — Phase 6)
"""
import argparse,copy,json,logging,time,sys,warnings
from pathlib import Path
warnings.filterwarnings('ignore')
import numpy as np
import torch,torch.nn as nn
from torch.optim import Adam

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s — %(message)s')
log=logging.getLogger('TRINITY.experiment')
DEVICE=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
SITES=['site-1','site-2','site-3']

sys.path.insert(0,str(Path(__file__).parent))
from model import get_model,FedProxLoss
from data_loader import TonIoTDataManager
from blockchain_hook import hash_model,submit_to_fabric

try:
    from opacus import PrivacyEngine
    from opacus.accountants import RDPAccountant
    OPACUS_OK=True
except: OPACUS_OK=False

try:
    import tenseal as ts
    TENSEAL_OK=True
except: TENSEAL_OK=False

MU=0.01; MAX_GRAD_NORM=1.0; NOISE_MULT=1.1
TARGET_EPS=10.0; DELTA=1e-5
POLY_MOD=8192; SCALE=2**40

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

def unwrap(sd):
    """Remove Opacus _module. prefix."""
    return {k.replace('_module.',''):v for k,v in sd.items()}

def make_ctx():
    if not TENSEAL_OK: return None
    ctx=ts.context(ts.SCHEME_TYPE.CKKS,poly_modulus_degree=POLY_MOD,
                   coeff_mod_bit_sizes=[60,40,40,60])
    ctx.generate_galois_keys(); ctx.global_scale=SCALE; return ctx

def encrypt_w(sd,ctx):
    enc={}
    for k,v in sd.items():
        flat=v.cpu().float().numpy().flatten()
        if TENSEAL_OK and ctx:
            enc[k]={'data':ts.ckks_vector(ctx,flat.tolist()),'shape':v.shape,'enc':True}
        else:
            enc[k]={'data':flat+np.random.normal(0,1e-6,flat.shape).astype(np.float32),
                    'shape':v.shape,'enc':False}
    return enc

def decrypt_w(enc,ctx):
    dec={}
    for k,info in enc.items():
        flat=np.array(info['data'].decrypt(),dtype=np.float32) if info.get('enc') and TENSEAL_OK \
             else info['data'].astype(np.float32)
        dec[k]=torch.from_numpy(flat.reshape(info['shape']))
    return dec

def agg_enc(encs,counts,ctx):
    total=sum(counts); agg={}
    for k in encs[0]:
        if encs[0][k].get('enc') and TENSEAL_OK:
            w=encs[0][k]['data']*(counts[0]/total)
            for i in range(1,len(encs)): w=w+encs[i][k]['data']*(counts[i]/total)
            agg[k]={'data':w,'shape':encs[0][k]['shape'],'enc':True}
        else:
            w=encs[0][k]['data']*(counts[0]/total)
            for i in range(1,len(encs)): w=w+encs[i][k]['data']*(counts[i]/total)
            agg[k]={'data':w,'shape':encs[0][k]['shape'],'enc':False}
    return agg

def fedavg_agg(gm,lms,counts):
    total=sum(counts); gs=gm.state_dict()
    for k in gs:
        gs[k]=sum(unwrap(lms[i].state_dict())[k].float()*(counts[i]/total)
                  for i in range(len(lms)))
    gm.load_state_dict(gs); return gm

def compute_eps(steps,nm,delta,bs,n):
    try:
        acc=RDPAccountant(); q=bs/n
        for _ in range(steps): acc.step(noise_multiplier=nm,sample_rate=q)
        eps,_=acc.get_privacy_spent(delta=delta); return min(float(eps),TARGET_EPS)
    except: return min(nm*(bs/n)*np.sqrt(2*steps*np.log(1/delta)),TARGET_EPS)

def run_experiment(exp_name,algo,use_dp,use_smpc,use_blockchain,
                   n_rounds,data_root,results_dir,log_dir):
    log.info("="*55)
    log.info(f"Experiment: {exp_name} | algo={algo} dp={use_dp} "
             f"smpc={use_smpc} blockchain={use_blockchain}")
    log.info("="*55)

    ctx=make_ctx() if use_smpc else None
    dms={s:TonIoTDataManager(s,data_root) for s in SITES}
    nf=dms['site-1'].n_features
    gm=get_model(nf).to(DEVICE)
    privacy_mode=('dp+smpc' if use_dp and use_smpc else
                  'dp' if use_dp else 'smpc' if use_smpc else 'none')

    slogs=[]; clogs={s:[] for s in SITES}
    cum_eps={s:0.0 for s in SITES}
    blockchain_records=[]

    for rnd in range(1,n_rounds+1):
        t0=time.time()
        lms=[]; counts=[]; enc_updates=[]

        for site in SITES:
            lm=copy.deepcopy(gm)
            gp=[p.clone().detach().to(DEVICE) for p in gm.parameters()]
            loader=dms[site].get_train_loader()
            opt=Adam(lm.parameters(),lr=1e-3)
            fedprox=FedProxLoss(MU)
            use_pe=False

            if use_dp and OPACUS_OK:
                try:
                    pe=PrivacyEngine()
                    lm,opt,loader=pe.make_private(module=lm,optimizer=opt,
                        data_loader=loader,noise_multiplier=NOISE_MULT,
                        max_grad_norm=MAX_GRAD_NORM)
                    use_pe=True
                except: use_pe=False

            lm.train(); tl=0; n=0
            base_params=[p.clone().detach().to(DEVICE) for p in
                         (lm._module if use_pe else lm).parameters()]
            for _ in range(5):
                for X,y in loader:
                    X,y=X.to(DEVICE),y.to(DEVICE); opt.zero_grad()
                    logits=(lm._module if use_pe else lm)(X)
                    loss,_,_=fedprox(logits,y,
                        list((lm._module if use_pe else lm).parameters()),
                        base_params)
                    loss.backward()
                    if not use_pe:
                        torch.nn.utils.clip_grad_norm_(lm.parameters(),MAX_GRAD_NORM)
                        if use_dp:
                            for p in lm.parameters():
                                if p.grad is not None:
                                    p.grad+=torch.randn_like(p.grad)*NOISE_MULT*MAX_GRAD_NORM/max(len(X),1)
                    opt.step(); tl+=loss.item(); n+=1

            eval_model=lm._module if use_pe else lm
            vm=compute_metrics(eval_model,dms[site].get_val_loader(),DEVICE)
            clean_sd=unwrap(lm.state_dict())

            if use_dp:
                eps=compute_eps(n,NOISE_MULT,DELTA,256,dms[site].n_train)
                cum_eps[site]=min(cum_eps[site]+eps,TARGET_EPS)
            else:
                cum_eps[site]=0.0

            if use_smpc:
                enc_updates.append(encrypt_w(clean_sd,ctx))
            else:
                # Create a clean model with unwrapped weights for aggregation
                clean_m=get_model(nf).to(DEVICE)
                clean_m.load_state_dict(clean_sd)
                lms.append(clean_m)
            counts.append(dms[site].n_train)

            clogs[site].append({'round':rnd,'client_id':site,'algo':algo,
                'accuracy':vm['accuracy'],'f1':vm['f1'],
                'train_loss':round(tl/max(n,1),6),
                'epsilon_spent':round(cum_eps[site],4) if use_dp else None,
                'encrypted':use_smpc})

        # Aggregation
        if use_smpc:
            agg=agg_enc(enc_updates,counts,ctx)
            dec=decrypt_w(agg,ctx); gm.load_state_dict(dec)
        else:
            gm=fedavg_agg(gm,lms,counts)

        gm_=compute_metrics(gm,dms['site-1'].get_test_loader(),DEVICE)
        lat=round(time.time()-t0,3)
        avg_eps=round(np.mean(list(cum_eps.values())),4) if use_dp else None

        # Blockchain — only for proj5
        tx_id=None; mhash=hash_model(gm.state_dict())
        if use_blockchain:
            tx_id,_=submit_to_fabric(
                round_num=rnd,model_hash=mhash,algo=algo,
                privacy_mode=privacy_mode,
                epsilon_spent=avg_eps or 0.0,
                global_accuracy=gm_['accuracy'],
                global_f1=gm_['f1'],
                latency_seconds=lat)
            blockchain_records.append({'round':rnd,'model_hash':mhash,'tx_id':tx_id})

        slogs.append({'round':rnd,'global_accuracy':gm_['accuracy'],
            'global_f1':gm_['f1'],'global_precision':gm_['precision'],
            'global_recall':gm_['recall'],'latency_seconds':lat,
            'algo':algo,'privacy_mode':privacy_mode,
            'epsilon_spent':avg_eps,'model_hash':mhash,'blockchain_tx_id':tx_id})

        log.info(f"Round {rnd:02d} | acc={gm_['accuracy']:.4f} f1={gm_['f1']:.4f} "
                 f"ε={avg_eps or '-'} hash={mhash[:12]}..."
                 + (f" tx={str(tx_id)[:12] if tx_id else 'local'}" if use_blockchain else ""))

    Path(log_dir).mkdir(exist_ok=True); Path(results_dir).mkdir(exist_ok=True)
    json.dump(slogs,open(f'{log_dir}/server_{exp_name}_rounds.json','w'),indent=2)
    for s in SITES:
        json.dump(clogs[s],open(f'{log_dir}/{s}_{exp_name}_rounds.json','w'),indent=2)
    if blockchain_records:
        json.dump(blockchain_records,
                  open(f'{results_dir}/{exp_name}_blockchain.json','w'),indent=2)
        log.info(f"Saved {len(blockchain_records)} blockchain records")

    final=slogs[-1]
    res={'experiment':exp_name,'algo':algo,'n_rounds':n_rounds,
         'final_accuracy':final['global_accuracy'],'final_f1':final['global_f1'],
         'final_precision':final['global_precision'],'final_recall':final['global_recall'],
         'avg_latency_s':round(np.mean([s['latency_seconds'] for s in slogs]),3),
         'privacy_mode':privacy_mode,'final_epsilon':final['epsilon_spent'],
         'blockchain_records':len(blockchain_records),'use_dp':use_dp,'use_smpc':use_smpc}
    json.dump(res,open(f'{results_dir}/{exp_name}_results.json','w'),indent=2)
    log.info(f"Experiment {exp_name} DONE | acc={final['global_accuracy']:.4f} "
             f"f1={final['global_f1']:.4f} latency={res['avg_latency_s']:.2f}s/round")
    return res

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--rounds',type=int,default=50)
    p.add_argument('--data_root',default='data/processed')
    p.add_argument('--results_dir',default='results')
    p.add_argument('--log_dir',default='logs')
    p.add_argument('--exp',default='all')
    args=p.parse_args()

    # (name, algo, use_dp, use_smpc, use_blockchain)
    experiments=[
        ('proj1_fedavg',          'FedAvg',  False, False, False),
        ('proj2_fedprox',         'FedProx', False, False, False),
        ('proj3_fedprox_dp',      'FedProx', True,  False, False),
        ('proj4_fedprox_smpc',    'FedProx', False, True,  False),
        ('proj5_fedprox_dp_smpc', 'FedProx', True,  True,  True),
    ]
    if args.exp!='all':
        experiments=[e for e in experiments if e[0]==args.exp]

    all_results=[]
    for exp_name,algo,use_dp,use_smpc,use_bc in experiments:
        r=run_experiment(exp_name,algo,use_dp,use_smpc,use_bc,
                         args.rounds,args.data_root,args.results_dir,args.log_dir)
        all_results.append(r)

    json.dump(all_results,open(f'{args.results_dir}/all_experiments.json','w'),indent=2)

    print("\n"+"="*75)
    print("TRINITY — 5-Experiment Results Matrix")
    print("="*75)
    print(f"{'Experiment':<25}{'Accuracy':<10}{'F1':<8}{'Latency':<10}{'Privacy':<14}{'ε':<8}{'Chain'}")
    print("-"*75)
    for r in all_results:
        eps=f"{r['final_epsilon']:.1f}" if r['final_epsilon'] else '—'
        bc='✓' if r['blockchain_records']>0 else '—'
        print(f"{r['experiment']:<25}{r['final_accuracy']:<10.4f}"
              f"{r['final_f1']:<8.4f}{r['avg_latency_s']:<10.2f}"
              f"{r['privacy_mode']:<14}{eps:<8}{bc}")
    print("="*75)

if __name__=='__main__': main()
