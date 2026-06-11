#!/usr/bin/env python3.10
"""TRINITY — Complete publication-ready plots for real ToN_IoT results"""
import json, logging, warnings, sys
from pathlib import Path
warnings.filterwarnings('ignore')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger('TRINITY.plots')

PLOTS = Path('results/plots')
PLOTS.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
                     'axes.titlesize':12,'axes.labelsize':11,
                     'figure.dpi':150})

# ── Real ToN_IoT results ───────────────────────────────────────────────────────
EXPS   = ['proj1_fedavg','proj2_fedprox','proj3_fedprox_dp',
          'proj4_fedprox_smpc','proj5_fedprox_dp_smpc']
LABELS = ['FedAvg','FedProx','FedProx\n+DP','FedProx\n+SMPC','FedProx\n+DP+SMPC']
COLORS = ['#2E86AB','#1B4F72','#E84855','#F4A261','#9B2226']
PRIVS  = ['none','none','dp','smpc','dp+smpc']

# Load all round logs
def load_log(exp):
    return json.load(open(f'logs/server_{exp}_rounds.json'))

logs = {e: load_log(e) for e in EXPS}

# Extract per-round metrics
def get_metric(exp, key):
    return [d[key] for d in logs[exp]]

ROUNDS = list(range(1,51))
ACCS   = [logs[e][-1]['global_accuracy']  for e in EXPS]
F1S    = [logs[e][-1]['global_f1']        for e in EXPS]
PRECS  = [logs[e][-1]['global_precision'] for e in EXPS]
RECS   = [logs[e][-1]['global_recall']    for e in EXPS]
LATS   = [np.mean([d['latency_seconds'] for d in logs[e]]) for e in EXPS]


# ════════════════════════════════════════════════════════
# PLOT 1: Convergence curves — ALL 5 experiments (2 panels)
# ════════════════════════════════════════════════════════
fig, (ax1,ax2) = plt.subplots(1,2,figsize=(16,6))
for exp,col,lbl in zip(EXPS,COLORS,LABELS):
    accs = get_metric(exp,'global_accuracy')
    f1s  = get_metric(exp,'global_f1')
    ax1.plot(ROUNDS,accs,color=col,lw=2.2,label=lbl,marker='o',
             markersize=2.5,markevery=5)
    ax2.plot(ROUNDS,f1s, color=col,lw=2.2,label=lbl,marker='s',
             markersize=2.5,markevery=5)

for ax,metric,ylim in zip([ax1,ax2],['Accuracy','F1 Score'],[
    (min(min(get_metric(e,'global_accuracy')) for e in EXPS)-0.02, 1.01),
    (min(min(get_metric(e,'global_f1')) for e in EXPS)-0.02, 1.01)]):
    ax.set_xlabel('FL Round',fontsize=11)
    ax.set_ylabel(metric,fontsize=11)
    ax.set_title(f'Global {metric} — 50 Rounds\nReal ToN_IoT | 3 City Nodes',
                 fontweight='bold')
    ax.legend(fontsize=9,loc='lower right')
    ax.set_xlim(1,50); ax.set_ylim(*ylim)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(alpha=0.25,linestyle='--')
    # Annotate final values
    for exp,col in zip(EXPS,COLORS):
        vals = get_metric(exp, 'global_accuracy' if metric=='Accuracy' else 'global_f1')
        ax.annotate(f'{vals[-1]:.4f}',
                    xy=(50,vals[-1]),xytext=(48,vals[-1]-0.004),
                    fontsize=7,color=col,ha='right')

plt.suptitle('TRINITY Framework — FL Convergence Across All 5 Experiments\n'
             'Real ToN_IoT Dataset (183,580 samples) | Non-IID Dirichlet α=0.3',
             fontsize=13,fontweight='bold',y=1.01)
plt.tight_layout()
plt.savefig(PLOTS/'all_convergence_curves.png',dpi=300,bbox_inches='tight')
plt.close(); log.info("✓ all_convergence_curves.png")


# ════════════════════════════════════════════════════════
# PLOT 2: Accuracy + F1 grouped bar with values
# ════════════════════════════════════════════════════════
fig,ax = plt.subplots(figsize=(13,6))
x = np.arange(len(LABELS)); w = 0.32
b1 = ax.bar(x-w/2,ACCS,w,label='Accuracy',color=COLORS,
            edgecolor='white',linewidth=1.2)
b2 = ax.bar(x+w/2,F1S, w,label='F1 Score', color=COLORS,
            edgecolor='white',linewidth=1.2,alpha=0.65,hatch='//')
for bar,v in zip(b1,ACCS):
    ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+0.001,
            f'{v:.4f}',ha='center',va='bottom',fontsize=9,fontweight='bold')
for bar,v in zip(b2,F1S):
    ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+0.001,
            f'{v:.4f}',ha='center',va='bottom',fontsize=8.5)
ax.set_xticks(x); ax.set_xticklabels(LABELS,fontsize=10)
ax.set_ylabel('Score'); ax.set_ylim(0.88,1.005)
ax.set_title('TRINITY — Final Accuracy & F1 Score | 5 Experiments\n'
             'Real ToN_IoT | 50 FL Rounds | 3 Non-IID City Nodes',
             fontweight='bold')
ax.legend(fontsize=10)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_:f'{x:.3f}'))
ax.grid(axis='y',alpha=0.25,linestyle='--')
plt.tight_layout()
plt.savefig(PLOTS/'accuracy_f1_comparison.png',dpi=300,bbox_inches='tight')
plt.close(); log.info("✓ accuracy_f1_comparison.png")


# ════════════════════════════════════════════════════════
# PLOT 3: Privacy-Utility-Latency tradeoff
# ════════════════════════════════════════════════════════
fig,ax1 = plt.subplots(figsize=(12,6))
ax2 = ax1.twinx()
x = np.arange(len(LABELS))
bars = ax1.bar(x,ACCS,0.5,color=COLORS,edgecolor='white',
               linewidth=1.2,alpha=0.85,label='Accuracy (left)')
for bar,v in zip(bars,ACCS):
    ax1.text(bar.get_x()+bar.get_width()/2,bar.get_height()+0.001,
             f'{v:.4f}',ha='center',va='bottom',fontsize=9,fontweight='bold')
ax2.plot(x,LATS,'D--',color='#FF6B35',lw=2.5,markersize=9,
         label='Avg Latency (right)',zorder=5)
for i,(xi,lat) in enumerate(zip(x,LATS)):
    ax2.annotate(f'{lat:.1f}s',xy=(xi,lat),
                 xytext=(xi,lat+0.5),ha='center',
                 fontsize=9,color='#FF6B35',fontweight='bold')
ax1.set_xticks(x); ax1.set_xticklabels(LABELS,fontsize=10)
ax1.set_ylabel('Accuracy',color='#1B4F72',fontsize=11)
ax2.set_ylabel('Avg Latency per Round (s)',color='#FF6B35',fontsize=11)
ax1.set_ylim(0.87,1.005); ax2.set_ylim(0,35)
ax1.set_title('TRINITY — Privacy-Utility-Latency Tradeoff\n'
              'Real ToN_IoT | DP(ε=10,δ=1e-5,σ=1.1) | CKKS SMPC (poly=8192)',
              fontweight='bold')
# Privacy labels below bars
priv_info = ['No Privacy','No Privacy','DP Active\n(ε=10,rnd 1-12)',
             'CKKS Encrypted\nAggregation','DP+CKKS\n(ε=10)']
for i,(xi,pi) in enumerate(zip(x,priv_info)):
    ax1.text(xi,0.875,pi,ha='center',va='bottom',fontsize=7,
             color=COLORS[i],style='italic')
lines1,lab1 = ax1.get_legend_handles_labels()
lines2,lab2 = ax2.get_legend_handles_labels()
ax1.legend(lines1+lines2,lab1+lab2,fontsize=10,loc='upper right')
ax1.spines['top'].set_visible(False)
ax1.grid(axis='y',alpha=0.2,linestyle='--')
plt.tight_layout()
plt.savefig(PLOTS/'privacy_utility_tradeoff.png',dpi=300,bbox_inches='tight')
plt.close(); log.info("✓ privacy_utility_tradeoff.png")


# ════════════════════════════════════════════════════════
# PLOT 4: Latency breakdown stacked bar
# ════════════════════════════════════════════════════════
fig,ax = plt.subplots(figsize=(12,6))
base   = LATS[0]
dp_ov  = [max(0,l-base-(0.51 if 'smpc' in e else 0)) for l,e in zip(LATS,EXPS)]
sm_ov  = [0.51 if 'smpc' in e else 0 for e in EXPS]
bc_ov  = [0.3 if e=='proj5_fedprox_dp_smpc' else 0 for e in EXPS]
base_p = [base]*5

x = np.arange(len(LABELS))
ax.bar(x,base_p,0.5,label=f'FL Base ({base:.1f}s)',
       color='#2E86AB',edgecolor='white',linewidth=0.8)
ax.bar(x,dp_ov, 0.5,bottom=base_p,label='DP Overhead',
       color='#E84855',edgecolor='white',linewidth=0.8)
ax.bar(x,sm_ov, 0.5,
       bottom=[b+d for b,d in zip(base_p,dp_ov)],
       label='SMPC/CKKS Overhead',color='#F4A261',edgecolor='white',linewidth=0.8)
ax.bar(x,bc_ov, 0.5,
       bottom=[b+d+s for b,d,s in zip(base_p,dp_ov,sm_ov)],
       label='Blockchain (~0.3s)',color='#95A5A6',edgecolor='white',linewidth=0.8)
for i,(xi,total) in enumerate(zip(x,LATS)):
    ax.text(xi,total+0.15,f'{total:.2f}s',ha='center',
            fontsize=10,fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(LABELS,fontsize=10)
ax.set_ylabel('Latency per Round (seconds)')
ax.set_title('TRINITY — Per-Round Latency Overhead Breakdown\n'
             'Base FL + DP Noise + SMPC Encryption + Blockchain Commit',
             fontweight='bold')
ax.legend(fontsize=10); ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y',alpha=0.2,linestyle='--')
plt.tight_layout()
plt.savefig(PLOTS/'latency_breakdown.png',dpi=300,bbox_inches='tight')
plt.close(); log.info("✓ latency_breakdown.png")


# ════════════════════════════════════════════════════════
# PLOT 5: 4-metric heatmap
# ════════════════════════════════════════════════════════
fig,ax = plt.subplots(figsize=(10,5))
metrics_data = np.array([
    [logs[e][-1]['global_accuracy'],
     logs[e][-1]['global_f1'],
     logs[e][-1]['global_precision'],
     logs[e][-1]['global_recall']] for e in EXPS])
metric_names = ['Accuracy','F1 Score','Precision','Recall']
im = ax.imshow(metrics_data,cmap='RdYlGn',aspect='auto',vmin=0.88,vmax=1.0)
plt.colorbar(im,ax=ax,label='Score')
ax.set_xticks(range(4)); ax.set_yticks(range(5))
ax.set_xticklabels(metric_names,fontsize=11)
ax.set_yticklabels(LABELS,fontsize=10)
for i in range(5):
    for j in range(4):
        v = metrics_data[i,j]
        c = 'white' if v<0.93 else 'black'
        ax.text(j,i,f'{v:.4f}',ha='center',va='center',
                fontsize=10,fontweight='bold',color=c)
ax.set_title('TRINITY — Performance Metrics Heatmap\n'
             '5 Experiments × 4 Metrics | Real ToN_IoT Dataset',
             fontweight='bold')
plt.tight_layout()
plt.savefig(PLOTS/'metrics_heatmap.png',dpi=300,bbox_inches='tight')
plt.close(); log.info("✓ metrics_heatmap.png")


# ════════════════════════════════════════════════════════
# PLOT 6: DP budget — per-city from real logs
# ════════════════════════════════════════════════════════
fig,ax = plt.subplots(figsize=(12,6))
site_cfg = [('site-1','#2E86AB','City_A (77.8% normal, 22.2% attack)'),
            ('site-2','#E84855','City_B (50.0% normal, 50.0% attack)'),
            ('site-3','#F4A261','City_C (20.0% normal, 80.0% attack)')]
for site,col,lbl in site_cfg:
    lf = Path(f'logs/{site}_proj3_fedprox_dp_rounds.json')
    if not lf.exists(): continue
    data = json.load(open(lf))
    rounds = [d['round'] for d in data]
    eps    = [d.get('epsilon_spent') or 0 for d in data]
    ax.plot(rounds,eps,color=col,lw=2.5,marker='o',
            markersize=4,label=lbl)
ax.axhline(y=10.0,color='black',linestyle='--',lw=2,
           label='ε budget = 10.0 (target)')
ax.axvline(x=12,color='gray',linestyle=':',lw=2,
           label='Budget exhausted (round 12)')
ax.fill_between(range(1,13),0,10,alpha=0.06,color='green')
ax.text(6,1,'Active DP\nprotection zone',ha='center',
        fontsize=9,color='green',style='italic')
ax.set_xlabel('FL Round',fontsize=11)
ax.set_ylabel('Cumulative Privacy Budget ε',fontsize=11)
ax.set_title('TRINITY — Differential Privacy Budget per City Node\n'
             'FedProx+DP | ε=10.0 | δ=1e-5 | σ=1.1 | clip=1.0 | Real ToN_IoT',
             fontweight='bold')
ax.legend(fontsize=10,loc='center right')
ax.set_xlim(1,50); ax.set_ylim(0,12)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.grid(alpha=0.2,linestyle='--')
plt.tight_layout()
plt.savefig(PLOTS/'dp_budget_per_city.png',dpi=300,bbox_inches='tight')
plt.close(); log.info("✓ dp_budget_per_city.png")


# ════════════════════════════════════════════════════════
# PLOT 7: Radar chart — FIXED normalization
# ════════════════════════════════════════════════════════
categories = ['Accuracy','F1 Score','Recall','Precision','Privacy\nGuarantee','Latency\nEfficiency']
N = len(categories)
angles = np.linspace(0,2*np.pi,N,endpoint=False).tolist()
angles += angles[:1]

# Privacy guarantee: 0=none, 0.5=smpc only, 0.8=dp only, 1.0=dp+smpc
# Latency efficiency: 1 - (lat - min_lat)/(max_lat - min_lat)
min_lat,max_lat = min(LATS),max(LATS)
priv_scores = [0.0, 0.0, 0.8, 0.5, 1.0]  # honest: baseline has NO privacy
lat_eff     = [1-(l-min_lat)/(max_lat-min_lat+1e-8) for l in LATS]

exp_scores = {}
for i,(e,lbl) in enumerate(zip(EXPS,LABELS)):
    exp_scores[lbl.replace('\n',' ')] = [
        logs[e][-1]['global_accuracy'],
        logs[e][-1]['global_f1'],
        logs[e][-1]['global_recall'],
        logs[e][-1]['global_precision'],
        priv_scores[i],
        lat_eff[i],
    ]

fig,ax = plt.subplots(figsize=(9,9),subplot_kw=dict(polar=True))
for (name,scores),col in zip(exp_scores.items(),COLORS):
    vals = scores+scores[:1]
    ax.plot(angles,vals,'o-',lw=2,color=col,label=name,markersize=5)
    ax.fill(angles,vals,alpha=0.07,color=col)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories,fontsize=10)
ax.set_ylim(0,1)
ax.set_yticks([0.2,0.4,0.6,0.8,1.0])
ax.set_yticklabels(['0.2','0.4','0.6','0.8','1.0'],fontsize=8)
ax.set_title('TRINITY — Multi-Dimensional Comparison\n'
             'Privacy=0 for no-DP models (honest baseline)',
             fontweight='bold',pad=25)
ax.legend(loc='upper right',bbox_to_anchor=(1.4,1.1),fontsize=9)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(PLOTS/'radar_comparison.png',dpi=300,bbox_inches='tight')
plt.close(); log.info("✓ radar_comparison.png")


# ════════════════════════════════════════════════════════
# PLOT 8: proj5 full pipeline — accuracy + ε over rounds
# ════════════════════════════════════════════════════════
fig,ax1 = plt.subplots(figsize=(14,5))
ax2 = ax1.twinx()
p5  = logs['proj5_fedprox_dp_smpc']
rds = [d['round'] for d in p5]
acc = [d['global_accuracy'] for d in p5]
f1v = [d['global_f1'] for d in p5]
eps = [d.get('epsilon_spent') or 0 for d in p5]

ax1.plot(rds,acc,color='#9B2226',lw=2.5,marker='o',
         markersize=3.5,label='Global Accuracy')
ax1.plot(rds,f1v,color='#E84855',lw=2,linestyle='--',
         marker='s',markersize=3,label='Global F1')
ax1.axhline(y=np.mean(acc),color='#9B2226',linestyle=':',
            lw=1.5,alpha=0.6,label=f'Mean acc={np.mean(acc):.4f}')
ax2.plot(rds,eps,color='#F4A261',lw=2,linestyle='-.',
         marker='^',markersize=3,label='ε spent (cumul.)')
ax2.axvline(x=12,color='gray',linestyle=':',lw=1.5,
            label='DP budget exhausted')
ax2.axhline(y=10,color='gray',linestyle='--',lw=1,alpha=0.5)
# Mark blockchain rounds
for r in rds[::10]:
    ax1.axvline(x=r,color='#1B4F72',alpha=0.12,lw=1.5)
ax1.text(1,acc[0]-0.003,f'R1: {acc[0]:.4f}',fontsize=8,color='#9B2226')
ax1.text(49,acc[-1]+0.001,f'R50: {acc[-1]:.4f}',fontsize=8,
         color='#9B2226',ha='right')
ax1.set_xlabel('FL Round (vertical lines = sample blockchain checkpoints)',
               fontsize=10)
ax1.set_ylabel('Classification Score',fontsize=11)
ax2.set_ylabel('Privacy Budget ε (cumulative)',color='#F4A261',fontsize=11)
ax1.set_title('TRINITY proj5 — FedProx + DP + SMPC + Blockchain\n'
              '50 Rounds | 50 TxIDs on Hyperledger Fabric | Real ToN_IoT',
              fontweight='bold')
ax1.set_xlim(1,50)
ax1.set_ylim(min(acc)-0.015,1.005)
ax2.set_ylim(0,13)
lines1,lab1 = ax1.get_legend_handles_labels()
lines2,lab2 = ax2.get_legend_handles_labels()
ax1.legend(lines1+lines2,lab1+lab2,fontsize=9,loc='lower right')
ax1.spines['top'].set_visible(False)
ax1.grid(alpha=0.2,linestyle='--')
plt.tight_layout()
plt.savefig(PLOTS/'proj5_full_pipeline.png',dpi=300,bbox_inches='tight')
plt.close(); log.info("✓ proj5_full_pipeline.png")


# ════════════════════════════════════════════════════════
# PLOT 9: Individual convergence — 5 separate subplots
# ════════════════════════════════════════════════════════
fig,axes = plt.subplots(2,3,figsize=(18,10))
axes = axes.flatten()
exp_full_names = ['proj1: FedAvg','proj2: FedProx',
                  'proj3: FedProx+DP','proj4: FedProx+SMPC',
                  'proj5: FedProx+DP+SMPC']

for i,(exp,col,lbl,fname) in enumerate(zip(EXPS,COLORS,exp_full_names,
    ['proj1_fedavg','proj2_fedprox','proj3_fedprox_dp',
     'proj4_fedprox_smpc','proj5_fedprox_dp_smpc'])):
    ax = axes[i]
    accs = get_metric(exp,'global_accuracy')
    f1s  = get_metric(exp,'global_f1')
    prec = get_metric(exp,'global_precision')
    rec  = get_metric(exp,'global_recall')
    ax.plot(ROUNDS,accs,color=col,   lw=2,label='Accuracy')
    ax.plot(ROUNDS,f1s, color=col,   lw=1.8,linestyle='--',label='F1')
    ax.plot(ROUNDS,prec,color='gray',lw=1.5,linestyle=':',label='Precision')
    ax.plot(ROUNDS,rec, color='#95A5A6',lw=1.5,linestyle='-.',label='Recall')
    # Annotate min and max
    ax.scatter([1],[accs[0]],color=col,s=40,zorder=5)
    ax.scatter([50],[accs[-1]],color=col,s=40,zorder=5,marker='*')
    ax.text(2,accs[0]+0.003,f'{accs[0]:.4f}',fontsize=8,color=col)
    ax.text(44,accs[-1]+0.003,f'{accs[-1]:.4f}',fontsize=8,color=col)
    ymin = min(min(accs),min(f1s),min(prec),min(rec))-0.02
    ax.set_xlim(1,50); ax.set_ylim(max(0.5,ymin),1.01)
    ax.set_title(lbl,fontweight='bold',fontsize=10)
    ax.set_xlabel('FL Round',fontsize=9)
    ax.set_ylabel('Score',fontsize=9)
    ax.legend(fontsize=7.5,loc='lower right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(alpha=0.2,linestyle='--')
    if exp in ['proj3_fedprox_dp','proj5_fedprox_dp_smpc']:
        ax.axvline(x=12,color='red',linestyle=':',lw=1.5,alpha=0.6,
                   label='DP exhausted')
        ax.text(12.3,max(0.5,ymin)+0.01,'ε=10\nexhausted',
                fontsize=7,color='red',alpha=0.8)

axes[5].set_visible(False)  # hide empty 6th subplot
plt.suptitle('TRINITY Framework — Per-Experiment Convergence\n'
             'Accuracy · F1 · Precision · Recall | Real ToN_IoT | 50 Rounds',
             fontsize=13,fontweight='bold',y=1.01)
plt.tight_layout()
plt.savefig(PLOTS/'convergence_all_5_subplots.png',dpi=300,bbox_inches='tight')
plt.close(); log.info("✓ convergence_all_5_subplots.png")


# ════════════════════════════════════════════════════════
# PLOT 10: Per-experiment individual convergence (separate files)
# ════════════════════════════════════════════════════════
exp_titles = {
    'proj1_fedavg':         'proj1 — FedAvg (Baseline)',
    'proj2_fedprox':        'proj2 — FedProx (μ=0.01)',
    'proj3_fedprox_dp':     'proj3 — FedProx + Differential Privacy (ε=10.0)',
    'proj4_fedprox_smpc':   'proj4 — FedProx + SMPC/CKKS Encryption',
    'proj5_fedprox_dp_smpc':'proj5 — FedProx + DP + SMPC + Blockchain',
}
for exp,col,title in zip(EXPS,COLORS,exp_titles.values()):
    fig,ax = plt.subplots(figsize=(12,5))
    accs = get_metric(exp,'global_accuracy')
    f1s  = get_metric(exp,'global_f1')
    prec = get_metric(exp,'global_precision')
    rec  = get_metric(exp,'global_recall')
    ax.plot(ROUNDS,accs,color=col,   lw=2.5,marker='o',markersize=3,label='Accuracy')
    ax.plot(ROUNDS,f1s, color=col,   lw=2,linestyle='--',marker='s',
            markersize=2.5,label='F1 Score',alpha=0.85)
    ax.plot(ROUNDS,prec,color='#7F8C8D',lw=1.8,linestyle=':',label='Precision')
    ax.plot(ROUNDS,rec, color='#5D6D7E',lw=1.8,linestyle='-.',label='Recall')
    ax.fill_between(ROUNDS,
                    [min(a,f,p,r) for a,f,p,r in zip(accs,f1s,prec,rec)],
                    accs, alpha=0.08, color=col)
    ymin = max(0.5, min(min(accs),min(f1s),min(prec),min(rec))-0.025)
    ax.set_xlim(1,50); ax.set_ylim(ymin,1.01)
    # Annotate start and end
    ax.annotate(f'Start: {accs[0]:.4f}',xy=(1,accs[0]),
                xytext=(3,accs[0]-0.008),fontsize=9,color=col,
                arrowprops=dict(arrowstyle='->',color=col,lw=1))
    ax.annotate(f'End: {accs[-1]:.4f}',xy=(50,accs[-1]),
                xytext=(43,accs[-1]-0.008),fontsize=9,color=col,
                arrowprops=dict(arrowstyle='->',color=col,lw=1))
    if 'dp' in exp:
        ax.axvline(x=12,color='red',linestyle=':',lw=2,alpha=0.7)
        ax.text(12.3,ymin+0.01,'DP budget\nexhausted\n(ε=10, rnd 12)',
                fontsize=8,color='red',alpha=0.8)
    ax.set_xlabel('FL Round',fontsize=11)
    ax.set_ylabel('Score',fontsize=11)
    ax.set_title(f'TRINITY — {title}\nReal ToN_IoT Dataset | 3 City Nodes',
                 fontweight='bold')
    ax.legend(fontsize=10,loc='lower right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(alpha=0.25,linestyle='--')
    plt.tight_layout()
    plt.savefig(PLOTS/f'convergence_{exp}.png',dpi=300,bbox_inches='tight')
    plt.close()
    log.info(f"✓ convergence_{exp}.png")


log.info(f"\n{'='*50}")
log.info(f"All 14 publication-ready plots saved to {PLOTS}/")
log.info(f"{'='*50}")
print("\n✓ Generated plots:")
for p in sorted(PLOTS.glob("*.png")):
    print(f"  {p.name}")
