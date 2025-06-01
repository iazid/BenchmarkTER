#!/usr/bin/env python3
import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Comparative analysis: view TxLatency vs on-chain view gas for EVM networks
# Networks: EthSepolia, AvaxFuji, Moonbeam

# 1. Configuration
results_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Results'))
ev_nets = ['EthSepolia', 'AvaxFuji', 'Moonbeam']
evm_dir = os.path.join(results_root, 'EVM')
os.makedirs(evm_dir, exist_ok=True)

# 2. Robust CSV reader splitting on first 5 commas
# Columns expected: TestName,ActualGasUsed,TxLatency,ExecTime,Result,Extra
def read_evm_csv(path):
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        next(f)  # skip header line
        for line in f:
            parts = line.rstrip('\n').split(',', 5)
            if len(parts) < 6:
                parts += [''] * (6 - len(parts))
            test, gas, txlat, exect, result, extra = parts
            rows.append({
                'TestName': test,
                'ActualGasUsed': pd.to_numeric(gas, errors='coerce'),
                'TxLatency': pd.to_numeric(txlat, errors='coerce'),
                'Result': result
            })
    return pd.DataFrame(rows)

# 3. Load and concatenate data
all_df = []
for net in ev_nets:
    folder = os.path.join(results_root, net)
    if not os.path.isdir(folder):
        print(f"⚠️ Folder not found: {folder}")
        continue
    files = glob.glob(os.path.join(folder, '*.csv'))
    if not files:
        print(f"⚠️ No CSV files in {folder}")
        continue
    for path in files:
        try:
            df = read_evm_csv(path)
        except Exception as e:
            print(f"❌ Failed to parse {path}: {e}")
            continue
        df['Network'] = net
        all_df.append(df[['Network','TestName','Result','TxLatency','ActualGasUsed']])

if not all_df:
    raise SystemExit('No EVM data loaded. Check Results/<network>/ folders')
evdf = pd.concat(all_df, ignore_index=True)
print(f"Loaded {len(evdf)} rows for EVM analysis")

# 4. Separate view vs on-chain view
view_df = evdf[evdf['Result'] == 'callStatic'].copy()
onchain_df = evdf[evdf['Result'] == 'onChainView'].copy()

# 5. Boxplot: TxLatency (view) per network
plt.figure(figsize=(8,4), dpi=120)
view_data = [view_df[view_df['Network']==net]['TxLatency'].dropna().values for net in ev_nets]
plt.boxplot(view_data, tick_labels=ev_nets, patch_artist=True, showfliers=False)
plt.ylabel('View Latency (ms)')
plt.title('Distribution of View Latency by Network')
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
view_box = os.path.join(evm_dir, 'view_latency_boxplot.png')
plt.savefig(view_box)
plt.close()
print(f"Saved view latency boxplot: {view_box}")

# 6. Bar chart: average TxLatency ± SEM (IC95%) per network
lat_stats = view_df.groupby('Network')['TxLatency'].agg(['mean','std','count']).reindex(ev_nets)
lat_stats['sem'] = lat_stats['std'] / np.sqrt(lat_stats['count'])
# 95% CI half-width
lat_stats['ci95'] = lat_stats['sem'] * 1.96
plt.figure(figsize=(8,4), dpi=120)
plt.bar(lat_stats.index, lat_stats['mean'], yerr=lat_stats['ci95'], capsize=5)
plt.ylabel('Avg View Latency (ms)')
plt.title('Average View Latency ± IC95% by Network')
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
lat_bar = os.path.join(evm_dir, 'view_latency_avg_bar.png')
plt.savefig(lat_bar)
plt.close()
print(f"Saved view latency avg bar chart: {lat_bar}")

# 7. Boxplot: On-chain view gas per network
plt.figure(figsize=(8,4), dpi=120)
gas_data = [onchain_df[onchain_df['Network']==net]['ActualGasUsed'].dropna().values for net in ev_nets]
plt.boxplot(gas_data, tick_labels=ev_nets, patch_artist=True, showfliers=False)
plt.ylabel('On-Chain View Gas')
plt.title('Distribution of On-Chain View Gas by Network')
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
gas_box = os.path.join(evm_dir, 'onchain_view_gas_boxplot.png')
plt.savefig(gas_box)
plt.close()
print(f"Saved on-chain view gas boxplot: {gas_box}")

# 8. Bar chart: average gas ± std per network
gas_summary = onchain_df.groupby('Network')['ActualGasUsed'].agg(['mean','std']).reindex(ev_nets)
plt.figure(figsize=(8,4), dpi=120)
plt.bar(gas_summary.index, gas_summary['mean'], yerr=gas_summary['std'], capsize=5)
plt.ylabel('Avg On-Chain View Gas')
plt.title('Average On-Chain View Gas ± STD by Network')
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
gas_bar = os.path.join(evm_dir, 'onchain_view_gas_avg_bar.png')
plt.savefig(gas_bar)
plt.close()
print(f"Saved gas avg bar chart: {gas_bar}")
