#!/usr/bin/env python3
import os
import glob
import re
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Comparative analysis: view TxLatency vs on-chain view gas for EVM networks
# Now using only date (YYYY-MM-DD) from filenames 'benchmark_onchain_YYYY-MM-DD_<i>.csv'

# 1. Configuration
results_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Results'))
ev_nets = ['EthSepolia', 'AvaxFuji', 'Moonbeam']
evm_dir = os.path.join(results_root, 'EVM')
os.makedirs(evm_dir, exist_ok=True)

# 2. CSV reader extracting date-only timestamp and ignoring sequence
pattern = re.compile(r'benchmark_onchain_(\d{4}-\d{2}-\d{2})_\d+\.csv')
def read_evm_csv(path, net):
    # extract date from filename
    fname = os.path.basename(path)
    m = pattern.match(fname)
    run_date = None
    if m:
        run_date = datetime.strptime(m.group(1), '%Y-%m-%d').date()
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        next(f)  # skip header
        for line in f:
            parts = line.rstrip('\n').split(',', 5)
            if len(parts) < 6:
                parts += ['']*(6 - len(parts))
            test, gas, txlat, exect, result, extra = parts
            rows.append({
                'Network': net,
                'RunDate': run_date,
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
    for path in glob.glob(os.path.join(folder, 'benchmark_onchain_*.csv')):
        try:
            df = read_evm_csv(path, net)
        except Exception as e:
            print(f"❌ Failed to parse {path}: {e}")
            continue
        all_df.append(df)
if not all_df:
    raise SystemExit('No EVM data loaded. Check Results/<network>/ folders')
evdf = pd.concat(all_df, ignore_index=True)
print(f"Loaded {len(evdf)} rows for EVM analysis")

# 4. Filter by result type
view_df = evdf[evdf['Result']=='callStatic'].dropna(subset=['TxLatency'])
onchain_df = evdf[evdf['Result']=='onChainView'].dropna(subset=['ActualGasUsed'])

# 5. Time series: average view latency per run. Time series: average view latency per date
ts_lat = (
    view_df
    .groupby(['RunDate','Network'], as_index=False)
    .agg(avg_latency=('TxLatency','mean'))
)
plt.figure(figsize=(10,4), dpi=120)
for net in ev_nets:
    sub = ts_lat[ts_lat['Network']==net].sort_values('RunDate')
    plt.plot(sub['RunDate'], sub['avg_latency'], marker='o', label=net)
plt.xlabel('Date')
plt.ylabel('Avg View Latency (ms)')
plt.title('Daily Avg View Latency by Network')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
fn1 = os.path.join(evm_dir, 'view_latency_daily_timeseries.png')
plt.savefig(fn1)
plt.close()
print(f"Saved daily view latency timeseries: {fn1}")

# 6. Time series: average on-chain view gas per date
ts_gas = (
    onchain_df
    .groupby(['RunDate','Network'], as_index=False)
    .agg(avg_gas=('ActualGasUsed','mean'))
)
plt.figure(figsize=(10,4), dpi=120)
for net in ev_nets:
    sub = ts_gas[ts_gas['Network']==net].sort_values('RunDate')
    plt.plot(sub['RunDate'], sub['avg_gas'], marker='s', label=net)
plt.xlabel('Date')
plt.ylabel('Avg On-Chain View Gas')
plt.title('Daily Avg On-Chain View Gas by Network')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
fn2 = os.path.join(evm_dir, 'onchain_gas_daily_timeseries.png')
plt.savefig(fn2)
plt.close()
print(f"Saved daily on-chain gas timeseries: {fn2}")
