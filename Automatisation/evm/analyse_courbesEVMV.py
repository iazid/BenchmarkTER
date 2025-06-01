#!/usr/bin/env python3
import os
import glob
import re
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Comparative analysis: view TxLatency vs on-chain view gas over time for EVM networks
# Networks: EthSepolia, AvaxFuji, Moonbeam

# 1. Configuration
results_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Results'))
ev_nets = ['EthSepolia', 'AvaxFuji', 'Moonbeam']
evm_dir = os.path.join(results_root, 'EVMV')
os.makedirs(evm_dir, exist_ok=True)

# 2. CSV reader with timestamp extraction
# Expects filenames like 'benchmark_onchain_2025-04-27T21-11-18.676Z.csv'
def read_evm_csv(path, net):
    # extract run timestamp from filename
    fname = os.path.basename(path)
    m = re.search(r'benchmark_onchain_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})', fname)
    run_ts = datetime.strptime(m.group(1), '%Y-%m-%dT%H-%M-%S') if m else pd.NaT
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        next(f)
        for line in f:
            parts = line.rstrip('\n').split(',', 5)
            if len(parts) < 6:
                parts += [''] * (6 - len(parts))
            test, gas, txlat, exect, result, extra = parts
            rows.append({
                'Network': net,
                'RunTimestamp': run_ts,
                'TestName': test,
                'TxLatency': pd.to_numeric(txlat, errors='coerce'),
                'ActualGasUsed': pd.to_numeric(gas, errors='coerce'),
                'Result': result
            })
    return pd.DataFrame(rows)

# 3. Load data
all_df = []
for net in ev_nets:
    folder = os.path.join(results_root, net)
    if not os.path.isdir(folder):
        print(f"⚠️ Folder not found: {folder}")
        continue
    files = glob.glob(os.path.join(folder, 'benchmark_onchain_*.csv'))
    for path in files:
        try:
            df = read_evm_csv(path, net)
        except Exception as e:
            print(f"❌ Error parsing {path}: {e}")
            continue
        all_df.append(df)
if not all_df:
    raise SystemExit('No EVM data loaded. Check Results/<network>/ folders')
evdf = pd.concat(all_df, ignore_index=True)
print(f"Loaded {len(evdf)} records for EVM")

# 4. Filter view vs on-chain view
view_df = evdf[evdf['Result']=='callStatic'].dropna(subset=['TxLatency'])
onchain_df = evdf[evdf['Result']=='onChainView'].dropna(subset=['ActualGasUsed'])

# 5. Time series: avg view latency per run
ts_lat = (view_df
    .groupby(['RunTimestamp','Network'], as_index=False)
    .agg(avg_latency=('TxLatency','mean'))
)
plt.figure(figsize=(10,4), dpi=120)
for net in ev_nets:
    sub = ts_lat[ts_lat['Network']==net].sort_values('RunTimestamp')
    plt.plot(sub['RunTimestamp'], sub['avg_latency'], marker='o', label=net)
plt.xlabel('Run Timestamp')
plt.ylabel('Avg View Latency (ms)')
plt.title('Time Series of View Latency by Network')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
fn1 = os.path.join(evm_dir, 'view_latency_timeseries.png')
plt.savefig(fn1)
plt.close()
print(f"Saved view latency timeseries: {fn1}")

# 6. Time series: avg on-chain view gas per run
ts_gas = (onchain_df
    .groupby(['RunTimestamp','Network'], as_index=False)
    .agg(avg_gas=('ActualGasUsed','mean'))
)
plt.figure(figsize=(10,4), dpi=120)
for net in ev_nets:
    sub = ts_gas[ts_gas['Network']==net].sort_values('RunTimestamp')
    plt.plot(sub['RunTimestamp'], sub['avg_gas'], marker='s', label=net)
plt.xlabel('Run Timestamp')
plt.ylabel('Avg On-Chain View Gas')
plt.title('Time Series of On-Chain View Gas by Network')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
fn2 = os.path.join(evm_dir, 'onchain_gas_timeseries.png')
plt.savefig(fn2)
plt.close()
print(f"Saved on-chain view gas timeseries: {fn2}")
