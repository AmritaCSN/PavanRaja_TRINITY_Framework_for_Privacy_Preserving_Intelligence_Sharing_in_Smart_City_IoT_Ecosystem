#!/usr/bin/env python3.10
"""TRINITY — ThreatDetectorMLP: 40→256→128→64→2, GroupNorm, ~76K params"""
import torch, torch.nn as nn

class ThreatDetectorMLP(nn.Module):
    def __init__(self, n_features=40, n_classes=2, dropout=0.3):
        super().__init__()
        self.n_features = n_features
        self.network = nn.Sequential(
            nn.Linear(n_features,256), nn.GroupNorm(32,256), nn.ReLU(True), nn.Dropout(dropout),
            nn.Linear(256,128),        nn.GroupNorm(16,128), nn.ReLU(True), nn.Dropout(dropout),
            nn.Linear(128,64),         nn.GroupNorm(8,64),   nn.ReLU(True), nn.Dropout(dropout),
            nn.Linear(64,n_classes),
        )
        for m in self.modules():
            if isinstance(m,nn.Linear):
                nn.init.kaiming_normal_(m.weight,nonlinearity='relu')
                if m.bias is not None: nn.init.zeros_(m.bias)
    def forward(self,x): return self.network(x)
    def predict(self,x):
        with torch.no_grad(): return torch.argmax(self.forward(x),dim=1)
    def count_parameters(self): return sum(p.numel() for p in self.parameters() if p.requires_grad)

class FedProxLoss(nn.Module):
    def __init__(self,mu=0.01):
        super().__init__(); self.mu=mu; self.ce=nn.CrossEntropyLoss()
    def forward(self,logits,labels,local_params,global_params):
        ce=self.ce(logits,labels)
        prox=sum(torch.norm(lp-gp.detach())**2 for lp,gp in zip(local_params,global_params))
        total=ce+(self.mu/2.0)*prox
        return total,ce,prox

def get_model(n_features=40): return ThreatDetectorMLP(n_features=n_features)

if __name__=='__main__':
    m=ThreatDetectorMLP(40)
    print(f"Parameters: {m.count_parameters():,}")
    x=torch.randn(256,40); y=m(x)
    print(f"Forward: {x.shape} → {y.shape} ✓")
