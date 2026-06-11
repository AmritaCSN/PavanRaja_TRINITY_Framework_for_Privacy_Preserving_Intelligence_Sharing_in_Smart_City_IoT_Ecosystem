#!/usr/bin/env python3.10
"""
TRINITY FRAMEWORK — Phase 2: Data Engineering (Real ToN_IoT)
Real dataset: train_test_network.csv (211,044 samples)
"""
import argparse,json,logging,warnings,pickle
from pathlib import Path
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
from scipy.special import rel_entr
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder,StandardScaler
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s — %(message)s')
log=logging.getLogger('TRINITY.preprocess')

SEED=42; ALPHA=0.3
CITY_RATIOS={'site-1':(0.80,0.20),'site-2':(0.50,0.50),'site-3':(0.20,0.80)}

# Real ToN_IoT columns
NUM_COLS=['duration','src_bytes','dst_bytes','missed_bytes','src_pkts',
          'src_ip_bytes','dst_pkts','dst_ip_bytes','src_port','dst_port',
          'dns_qclass','dns_qtype','dns_rcode','dns_AA','dns_RD','dns_RA',
          'dns_rejected','ssl_resumed','ssl_established','http_trans_depth',
          'http_request_body_len','http_response_body_len',
          'http_status_code','weird_notice']
CAT_COLS=['proto','service','conn_state','dns_query','ssl_version',
          'ssl_cipher','ssl_subject','ssl_issuer','http_method','http_uri',
          'http_version','http_user_agent','http_orig_mime_types',
          'http_resp_mime_types','weird_name','weird_addl']
DROP_COLS=['src_ip','dst_ip']

def load_real(path):
    log.info(f"Loading real ToN_IoT: {path}")
    df=pd.read_csv(path,low_memory=False)
    log.info(f"Loaded: {df.shape} | label dist: {df['label'].value_counts().to_dict()}")
    log.info(f"Attack types: {df[df['label']==1]['type'].value_counts().to_dict()}")
    return df

def preprocess(df):
    log.info("Preprocessing...")
    # Drop IP cols
    df=df.drop(columns=[c for c in DROP_COLS if c in df.columns],errors='ignore')
    # Ensure label is binary int
    df['label']=pd.to_numeric(df['label'],errors='coerce').fillna(0).astype(int)
    df.loc[df['label']>1,'label']=1  # cap to binary
    # Numeric
    for c in NUM_COLS:
        if c in df.columns:
            df[c]=pd.to_numeric(df[c],errors='coerce').fillna(0)
    # Categorical
    for c in CAT_COLS:
        if c in df.columns:
            df[c]=df[c].fillna('-').astype(str)
    # Drop duplicates
    before=len(df); df.drop_duplicates(inplace=True)
    log.info(f"Removed {before-len(df)} duplicates → {len(df)} rows")
    return df

def encode_scale(df):
    feat_cols=[c for c in NUM_COLS+CAT_COLS if c in df.columns]
    encoders={}
    for c in CAT_COLS:
        if c not in df.columns: continue
        le=LabelEncoder(); df[c]=le.fit_transform(df[c]); encoders[c]=le
    num_present=[c for c in NUM_COLS if c in df.columns]
    scaler=StandardScaler()
    df[num_present]=scaler.fit_transform(df[num_present].values)
    feat_cols=[c for c in NUM_COLS+CAT_COLS if c in df.columns]
    log.info(f"Features: {len(feat_cols)} — {feat_cols}")
    return df,feat_cols,scaler,encoders

def city_splits(df,feat_cols):
    log.info("Creating non-IID city splits (Dirichlet α=0.3)...")
    rng=np.random.default_rng(SEED)
    normal_df=df[df['label']==0]
    attack_df=df[df['label']==1]
    subtypes=sorted([t for t in attack_df['type'].unique()
                     if str(t).lower() not in ['normal','nan','-']])
    log.info(f"Attack subtypes: {subtypes}")
    # Dirichlet allocation
    alloc=rng.dirichlet([ALPHA]*3,size=len(subtypes))
    city_atk={s:[] for s in CITY_RATIOS}
    for i,st in enumerate(subtypes):
        sub=attack_df[attack_df['type']==st]
        if len(sub)==0: continue
        n=len(sub); props=alloc[i]
        cnts=(props*n).astype(int); cnts[-1]=n-cnts[:-1].sum()
        shuf=sub.sample(frac=1,random_state=SEED); start=0
        for j,site in enumerate(CITY_RATIOS):
            city_atk[site].append(shuf.iloc[start:start+cnts[j]]); start+=cnts[j]
    # Determine samples per city based on dataset size
    n_total=min(len(normal_df)*2, 60000)  # cap at 60K per city
    splits={}
    for site,(nr,ar) in CITY_RATIOS.items():
        nn=int(n_total*nr); na=n_total-nn
        sn=normal_df.sample(n=min(nn,len(normal_df)),
                            replace=len(normal_df)<nn,random_state=SEED)
        sa_all=pd.concat(city_atk[site]) if city_atk[site] else attack_df.sample(na,random_state=SEED)
        sa=sa_all.sample(n=min(na,len(sa_all)),
                         replace=len(sa_all)<na,random_state=SEED)
        splits[site]=pd.concat([sn,sa]).sample(frac=1,random_state=SEED).reset_index(drop=True)
        n_=len(splits[site]); nn_=int((splits[site]['label']==0).sum())
        na_=int((splits[site]['label']==1).sum())
        log.info(f"{site}: {n_} | normal={nn_}({nn_/n_*100:.1f}%) "
                 f"attack={na_}({na_/n_*100:.1f}%)")
    return splits,subtypes

def kl_div(splits,subtypes):
    def dist(df):
        counts=df['type'].value_counts()
        d=np.array([counts.get(t,0) for t in subtypes],dtype=float)
        d=np.clip(d/(d.sum()+1e-10),1e-10,1); return d/d.sum()
    sites=list(splits.keys())
    dists={s:dist(splits[s]) for s in sites}
    mat=pd.DataFrame(index=sites,columns=sites,dtype=float)
    for s1 in sites:
        for s2 in sites:
            mat.loc[s1,s2]=round(float(np.sum(rel_entr(dists[s1],dists[s2]))),4)
    log.info(f"KL divergence:\n{mat}")
    return mat

def save_splits(splits,feat_cols,base):
    for site,df in splits.items():
        sd=Path(base)/site; sd.mkdir(parents=True,exist_ok=True)
        X=df[feat_cols].values.astype(np.float32)
        y=df['label'].values.astype(np.int64)
        X_tr,X_tmp,y_tr,y_tmp=train_test_split(X,y,test_size=0.30,
                                                stratify=y,random_state=SEED)
        X_v,X_te,y_v,y_te=train_test_split(X_tmp,y_tmp,test_size=0.50,
                                            stratify=y_tmp,random_state=SEED)
        for nm,arr in [('X_train',X_tr),('y_train',y_tr),('X_val',X_v),
                       ('y_val',y_v),('X_test',X_te),('y_test',y_te)]:
            np.save(sd/f'{nm}.npy',arr)
        meta={'site':site,'total':len(df),'n_train':len(X_tr),
              'n_val':len(X_v),'n_test':len(X_te),
              'n_features':X_tr.shape[1],
              'n_normal':int((y==0).sum()),'n_attack':int((y==1).sum()),
              'feature_cols':feat_cols,'dataset':'real_ton_iot'}
        json.dump(meta,open(sd/'metadata.json','w'),indent=2)
        log.info(f"Saved {site}: train={len(X_tr)} val={len(X_v)} "
                 f"test={len(X_te)} features={X_tr.shape[1]}")

def make_plots(splits,subtypes,kl_mat,save_dir):
    Path(save_dir).mkdir(parents=True,exist_ok=True)
    # Class distribution
    fig,axes=plt.subplots(1,3,figsize=(14,5))
    fig.suptitle('TRINITY — Non-IID Class Distribution (Real ToN_IoT)',
                 fontsize=13,fontweight='bold')
    titles={'site-1':'City_A\n80% Normal/20% Attack',
            'site-2':'City_B\n50% Normal/50% Attack',
            'site-3':'City_C\n20% Normal/80% Attack'}
    for ax,(site,df) in zip(axes,splits.items()):
        counts=df['label'].value_counts().sort_index()
        vals=[counts.get(0,0),counts.get(1,0)]; total=sum(vals)
        bars=ax.bar(['Normal','Attack'],vals,
                    color=['#2E86AB','#E84855'],edgecolor='white',width=0.5)
        for bar,v in zip(bars,vals):
            ax.text(bar.get_x()+bar.get_width()/2,
                    bar.get_height()+total*0.01,
                    f'{v/total*100:.1f}%',ha='center',va='bottom',
                    fontsize=11,fontweight='bold')
        ax.set_title(titles[site],fontsize=10)
        ax.set_ylim(0,max(vals)*1.15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x,_:f'{int(x):,}'))
    plt.tight_layout()
    plt.savefig(f'{save_dir}/class_distribution_real.png',dpi=300,bbox_inches='tight')
    plt.close()
    # Attack type distribution
    fig,ax=plt.subplots(figsize=(12,6))
    palette=plt.cm.Set3(np.linspace(0,1,len(subtypes)))
    x=np.arange(3); bottoms=np.zeros(3)
    for i,at in enumerate(subtypes):
        vals=[]
        for site in splits:
            adf=splits[site][splits[site]['label']==1]
            vals.append((adf['type']==at).sum()/max(len(adf),1)*100)
        ax.bar(x,vals,0.5,bottom=bottoms,label=at,
               color=palette[i],edgecolor='white',linewidth=0.5)
        bottoms+=np.array(vals)
    ax.set_xticks(x)
    ax.set_xticklabels(['City_A','City_B','City_C'],fontsize=11)
    ax.set_ylabel('% of Attack Samples',fontsize=11)
    ax.set_title('TRINITY — Attack Subtype Distribution (Dirichlet α=0.3, Real ToN_IoT)',
                 fontsize=12,fontweight='bold')
    ax.legend(bbox_to_anchor=(1.15,1),fontsize=9)
    ax.spines['top'].set_visible(False)
    plt.tight_layout()
    plt.savefig(f'{save_dir}/attack_type_real.png',dpi=300,bbox_inches='tight')
    plt.close()
    # KL heatmap
    fig,ax=plt.subplots(figsize=(7,5))
    data=kl_mat.values.astype(float)
    im=ax.imshow(data,cmap='YlOrRd',aspect='auto')
    plt.colorbar(im,ax=ax,label='KL Divergence')
    lbls=['City_A','City_B','City_C']
    ax.set_xticks(range(3)); ax.set_yticks(range(3))
    ax.set_xticklabels(lbls); ax.set_yticklabels(lbls)
    for i in range(3):
        for j in range(3):
            v=data[i,j]; color='white' if v>data.max()*0.6 else 'black'
            ax.text(j,i,f'{v:.3f}',ha='center',va='center',
                    fontsize=11,fontweight='bold',color=color)
    ax.set_title('TRINITY — KL Divergence (Real ToN_IoT)',
                 fontsize=12,fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{save_dir}/kl_divergence_real.png',dpi=300,bbox_inches='tight')
    plt.close()
    log.info(f"Saved 3 plots to {save_dir}")

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data_path',default='data/raw/train_test_network.csv')
    p.add_argument('--output_dir',default='data/processed')
    p.add_argument('--plots_dir',default='results/plots')
    p.add_argument('--results_dir',default='results')
    args=p.parse_args()
    log.info("="*55+"\nTRINITY Phase 2 — Real ToN_IoT Data Engineering\n"+"="*55)
    df=load_real(args.data_path)
    df=preprocess(df)
    df,feat_cols,scaler,encoders=encode_scale(df)
    splits,subtypes=city_splits(df,feat_cols)
    kl_mat=kl_div(splits,subtypes)
    kl_ac=kl_mat.loc['site-1','site-3']
    log.info(f"KL(City_A||City_C) = {kl_ac:.4f} "
             f"{'✓ >0.5' if kl_ac>0.5 else '⚠ <0.5'}")
    save_splits(splits,feat_cols,args.output_dir)
    with open(Path(args.output_dir)/'scaler.pkl','wb') as f: pickle.dump(scaler,f)
    with open(Path(args.output_dir)/'encoders.pkl','wb') as f: pickle.dump(encoders,f)
    Path(args.results_dir).mkdir(exist_ok=True)
    rows=[]
    for site,df2 in splits.items():
        n=len(df2); nn=int((df2['label']==0).sum()); na=int((df2['label']==1).sum())
        rows.append({'Site':site,
                     'City':{'site-1':'City_A','site-2':'City_B','site-3':'City_C'}[site],
                     'Total':n,'Normal':nn,'Attack':na,
                     'Normal_%':round(nn/n*100,1),'Attack_%':round(na/n*100,1),
                     'Train':int(n*0.7),'Val':int(n*0.15),'Test':int(n*0.15),
                     'Dataset':'Real_ToN_IoT'})
    stats=pd.DataFrame(rows)
    stats.to_csv(Path(args.results_dir)/'dataset_statistics_real.csv',index=False)
    kl_mat.to_csv(Path(args.results_dir)/'kl_divergence_real.csv')
    make_plots(splits,subtypes,kl_mat,args.plots_dir)
    cfg={'dataset':'real_ton_iot','random_seed':SEED,
         'alpha_dirichlet':ALPHA,'feature_cols':feat_cols,
         'n_features':len(feat_cols),'attack_subtypes':subtypes,
         'kl_divergences':kl_mat.to_dict()}
    json.dump(cfg,open(Path(args.results_dir)/'phase2_config_real.json','w'),indent=2)
    log.info("="*55)
    log.info("Phase 2 COMPLETE — Real ToN_IoT")
    log.info(f"  Features:  {len(feat_cols)}")
    log.info(f"  KL(A||C):  {kl_ac:.4f}")
    log.info("="*55)
    print(stats[['City','Total','Normal_%','Attack_%','Train','Val','Test']].to_string(index=False))

if __name__=='__main__': main()
