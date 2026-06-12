.
├── 0.5
├── =1.48.2
├── api
│   └── wallet
├── bin
├── data
│   ├── processed
│   │   ├── encoders.pkl
│   │   ├── scaler.pkl
│   │   ├── site-1
│   │   │   ├── metadata.json
│   │   │   ├── X_test.npy
│   │   │   ├── X_train.npy
│   │   │   ├── X_val.npy
│   │   │   ├── y_test.npy
│   │   │   ├── y_train.npy
│   │   │   └── y_val.npy
│   │   ├── site-2
│   │   │   ├── metadata.json
│   │   │   ├── X_test.npy
│   │   │   ├── X_train.npy
│   │   │   ├── X_val.npy
│   │   │   ├── y_test.npy
│   │   │   ├── y_train.npy
│   │   │   └── y_val.npy
│   │   └── site-3
│   │       ├── metadata.json
│   │       ├── X_test.npy
│   │       ├── X_train.npy
│   │       ├── X_val.npy
│   │       ├── y_test.npy
│   │       ├── y_train.npy
│   │       └── y_val.npy
│   └── raw
│       ├── ton-iot-network-dataset.zip
│       ├── TON_IoT_synthetic.csv
│       └── train_test_network.csv
├── docker-compose.yml
├── docs
│   ├── architecture.md
│   ├── deployment-guide.md
│   ├── experiment-results.md
│   ├── PRD.md
│   ├── security-analysis.md
│   └── threat-model.md
├── fabric-network
│   ├── chaincode
│   ├── config
│   │   └── genesis.block
│   ├── crypto-config
│   │   ├── ordererOrganizations
│   │   │   └── trinity.local
│   │   │       └── orderers
│   │   │           └── orderer.trinity.local
│   │   │               ├── msp
│   │   │               │   └── keystore
│   │   │               └── tls
│   │   └── peerOrganizations
│   │       ├── city_a.trinity.local
│   │       │   └── peers
│   │       │       └── peer0.city_a.trinity.local
│   │       │           ├── msp
│   │       │           │   └── keystore
│   │       │           └── tls
│   │       ├── city_b.trinity.local
│   │       │   └── peers
│   │       │       └── peer0.city_b.trinity.local
│   │       │           ├── msp
│   │       │           │   └── keystore
│   │       │           └── tls
│   │       ├── city_c.trinity.local
│   │       │   └── peers
│   │       │       └── peer0.city_c.trinity.local
│   │       │           ├── msp
│   │       │           │   └── keystore
│   │       │           └── tls
│   │       └── trinity.local
│   │           └── ca
│   └── scripts
├── fl_project
│   └── trinity_fl
│       ├── prod_00
│       │   ├── admin@trinity.local
│       │   │   ├── local
│       │   │   ├── startup
│       │   │   │   ├── client.crt
│       │   │   │   ├── client.key
│       │   │   │   ├── client.pfx
│       │   │   │   ├── fed_admin.json
│       │   │   │   ├── fl_admin.sh
│       │   │   │   ├── readme.txt
│       │   │   │   └── rootCA.pem
│       │   │   └── transfer
│       │   ├── server
│       │   │   ├── local
│       │   │   │   ├── authorization.json.default
│       │   │   │   ├── log.config.default
│       │   │   │   ├── privacy.json.sample
│       │   │   │   └── resources.json.default
│       │   │   ├── readme.txt
│       │   │   ├── startup
│       │   │   │   ├── fed_server.json
│       │   │   │   ├── rootCA.pem
│       │   │   │   ├── server.crt
│       │   │   │   ├── server.key
│       │   │   │   ├── server.pfx
│       │   │   │   ├── signature.json
│       │   │   │   ├── start.sh
│       │   │   │   ├── stop_fl.sh
│       │   │   │   └── sub_start.sh
│       │   │   └── transfer
│       │   ├── site-1
│       │   │   ├── local
│       │   │   │   ├── authorization.json.default
│       │   │   │   ├── log.config.default
│       │   │   │   ├── privacy.json.sample
│       │   │   │   └── resources.json.default
│       │   │   ├── readme.txt
│       │   │   ├── startup
│       │   │   │   ├── client.crt
│       │   │   │   ├── client.key
│       │   │   │   ├── client.pfx
│       │   │   │   ├── fed_client.json
│       │   │   │   ├── rootCA.pem
│       │   │   │   ├── signature.json
│       │   │   │   ├── start.sh
│       │   │   │   ├── stop_fl.sh
│       │   │   │   └── sub_start.sh
│       │   │   └── transfer
│       │   ├── site-2
│       │   │   ├── local
│       │   │   │   ├── authorization.json.default
│       │   │   │   ├── log.config.default
│       │   │   │   ├── privacy.json.sample
│       │   │   │   └── resources.json.default
│       │   │   ├── readme.txt
│       │   │   ├── startup
│       │   │   │   ├── client.crt
│       │   │   │   ├── client.key
│       │   │   │   ├── client.pfx
│       │   │   │   ├── fed_client.json
│       │   │   │   ├── rootCA.pem
│       │   │   │   ├── signature.json
│       │   │   │   ├── start.sh
│       │   │   │   ├── stop_fl.sh
│       │   │   │   └── sub_start.sh
│       │   │   └── transfer
│       │   └── site-3
│       │       ├── local
│       │       │   ├── authorization.json.default
│       │       │   ├── log.config.default
│       │       │   ├── privacy.json.sample
│       │       │   └── resources.json.default
│       │       ├── readme.txt
│       │       ├── startup
│       │       │   ├── client.crt
│       │       │   ├── client.key
│       │       │   ├── client.pfx
│       │       │   ├── fed_client.json
│       │       │   ├── rootCA.pem
│       │       │   ├── signature.json
│       │       │   ├── start.sh
│       │       │   ├── stop_fl.sh
│       │       │   └── sub_start.sh
│       │       └── transfer
│       ├── resources
│       │   └── master_template.yml
│       └── state
│           └── cert.json
├── jobs
│   ├── proj1
│   │   ├── config
│   │   └── custom
│   ├── proj2
│   │   ├── config
│   │   └── custom
│   ├── proj3
│   ├── proj4
│   └── proj5
├── PROJECT_TREE.txt
├── project.yml
├── requirements.txt
├── results
│   ├── all_experiments.json
│   ├── dataset_statistics.csv
│   ├── dataset_statistics_real.csv
│   ├── enhanced_metrics.json
│   ├── fedavg_results.json
│   ├── fedprox_dp_results.json
│   ├── fedprox_results.json
│   ├── fedprox_smpc_results.json
│   ├── kl_divergence_matrix.csv
│   ├── kl_divergence_real.csv
│   ├── multiseed_results.json
│   ├── phase2_config.json
│   ├── phase2_config_real.json
│   ├── plots
│   │   ├── accuracy_f1_comparison.png
│   │   ├── all_convergence_curves.png
│   │   ├── attack_type_distribution.png
│   │   ├── attack_type_real.png
│   │   ├── class_distribution.png
│   │   ├── class_distribution_real.png
│   │   ├── cm_FedProx_final.png
│   │   ├── cm_proj1_fedavg.png
│   │   ├── cm_proj2_fedprox.png
│   │   ├── cm_proj3_fedprox_dp.png
│   │   ├── cm_proj4_fedprox_smpc.png
│   │   ├── cm_proj5_fedprox_dp_smpc.png
│   │   ├── convergence_all_5_subplots.png
│   │   ├── convergence_proj1_fedavg.png
│   │   ├── convergence_proj2_fedprox.png
│   │   ├── convergence_proj3_fedprox_dp.png
│   │   ├── convergence_proj4_fedprox_smpc.png
│   │   ├── convergence_proj5_fedprox_dp_smpc.png
│   │   ├── dp_budget_consumption.png
│   │   ├── dp_budget_per_city.png
│   │   ├── kl_divergence_heatmap.png
│   │   ├── kl_divergence_real.png
│   │   ├── latency_breakdown.png
│   │   ├── latency_comparison.png
│   │   ├── metrics_heatmap.png
│   │   ├── privacy_utility_tradeoff.png
│   │   ├── proj5_full_pipeline.png
│   │   ├── radar_comparison.png
│   │   ├── roc_all_experiments.png
│   │   └── roc_FedProx_final.png
│   ├── proj1_fedavg_blockchain.json
│   ├── proj1_fedavg_results.json
│   ├── proj2_fedprox_blockchain.json
│   ├── proj2_fedprox_results.json
│   ├── proj3_fedprox_dp_results.json
│   ├── proj4_fedprox_smpc_results.json
│   ├── proj5_fedprox_dp_smpc_blockchain.json
│   ├── proj5_fedprox_dp_smpc_results.json
│   └── roc_auc_summary.json
└── scripts
    ├── add_data_noise.py
    ├── adversarial_demo.py
    ├── blockchain_hook.py
    ├── data_loader.py
    ├── dp_trainer.py
    ├── enhanced_evaluation.py
    ├── fix_plots.py
    ├── generate_docs.py
    ├── model.py
    ├── multiseed_validation.py
    ├── plot_results.py
    ├── preprocess.py
    ├── run_fl_simulation.py
    ├── run_full_experiment.py
    ├── smpc_trainer.py
    ├── start_all.sh
    ├── teardown.sh
    └── validate_phase1.py

82 directories, 173 files
