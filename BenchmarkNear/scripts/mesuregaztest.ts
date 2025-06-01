#!/usr/bin/env ts-node

import { connect, keyStores, Contract, Account } from 'near-api-js';
import { promises as fs } from 'fs';
import { statSync } from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const NETWORK_ID = 'testnet';
const NODE_URL = 'https://rpc.testnet.near.org';
const CONTRACT_ACCOUNT = 'benchmarknear.testnet';
const VIEW_RUNS = 50;
const TX_GAS = 300_000_000_000_000n;
const TX_DEPOSIT = 0n;
const WASM_PATH = path.resolve(__dirname, '../build/contract.wasm');

const POSSIBLE_CREDENTIALS_DIRS = [
  path.join(os.homedir(), '.near-credentials'),
  path.join('/mnt/c', 'Users', process.env['USERNAME'] || '', '.near-credentials')
];
const foundDir = POSSIBLE_CREDENTIALS_DIRS.find(dir => {
  try { return statSync(dir).isDirectory(); } catch { return false; }
});
if (!foundDir) throw new Error('No credentials directory found');
const CREDENTIALS_DIR = foundDir;

interface Result {
  testName: string;
  actualGasUsed?: string;
  netGas?: string;
  gasRatio?: string;
  txLatency?: string;
  execTime?: number;
  result: string;
  extra?: string;
}

async function initAccount(): Promise<Account> {
  const keyStore = new keyStores.UnencryptedFileSystemKeyStore(CREDENTIALS_DIR);
  const near = await connect({ networkId: NETWORK_ID, nodeUrl: NODE_URL, deps: { keyStore } });
  return near.account(CONTRACT_ACCOUNT);
}

async function deployContract(account: Account): Promise<void> {
  const wasm = await fs.readFile(WASM_PATH);
  await account.deployContract(wasm);
  console.log(`✅ Contrat déployé sur ${CONTRACT_ACCOUNT}`);
}

async function measureTx(
  name: string,
  account: Account,
  method: string,
  args: any
): Promise<Result> {
  const t0 = Date.now();
  const res = await account.functionCall({
    contractId: CONTRACT_ACCOUNT,
    methodName: method,
    args,
    gas: TX_GAS,
    attachedDeposit: TX_DEPOSIT
  });
  const t1 = Date.now();
  const gas = res.transaction_outcome.outcome.gas_burnt.toString();
  console.log(`[TX] ${name} • gas=${gas} • latence=${t1 - t0}ms`);
  return {
    testName: name,
    actualGasUsed: gas,
    txLatency: (t1 - t0).toFixed(2),
    execTime: 0,
    result: 'Tx executed',
    extra: ''
  };
}

async function main() {
  const account = await initAccount();
  await deployContract(account);

  // on suppose que vous avez déjà déployé un maxDepth pour la recherche dichotomique
  const viewMethods = [
    'getValue', 'loopSum', 'fibonacciIterative', 'fibonacciRecursive',
    'isPrime', 'factorialIterative', 'factorialRecursive', 'expBySquaring', 'gcd',
    'maxDepth'
  ];
  const contract = new Contract(account.connection, CONTRACT_ACCOUNT, {
    viewMethods,
    changeMethods: ['setValue', 'reference_tx', ...viewMethods.map(m => `${m}_tx`)],
    useLocalViewExecution: false
  });

  const results: Result[] = [];
  let gasRef = 0n;

  // 1) Recherche dichotomique maxDepth
  async function findMaxDepth(): Promise<number> {
    let low = 0, high = 200_000;
    while (low < high) {
      const mid = Math.floor((low + high + 1) / 2);
      try {
        await (contract as any).maxDepth({ depth: mid });
        low = mid;
      } catch {
        high = mid - 1;
      }
    }
    console.log(`🎯 Profondeur max supportée : ${low}`);
    return low;
  }
  // si vous avez maxDepth dans le contrat, sinon commentez ces lignes
  const maxDepth = await findMaxDepth();
  results.push({ testName: 'maxDepth', result: 'view', extra: `maxDepth=${maxDepth}` });

  // 2) Transaction de référence
  try {
    const ref = await measureTx('reference_tx', account, 'reference_tx', {});
    gasRef = BigInt(ref.actualGasUsed || '0');
    results.push({ ...ref, netGas: '', gasRatio: '' });
    console.log(`Gas de référence = ${gasRef}`);
  } catch {
    console.log("⚠️ Pas de reference_tx, skip.");
  }

  // 3) setValue
  results.push(await measureTx('setValue', account, 'setValue', { value: 42 }));

  // 4) measureView avec gestion des erreurs
  async function measureView(name: string, args: any): Promise<Result> {
    console.log(`\n===== VIEW: ${name} – runs=${VIEW_RUNS} =====`);

    // warm-up + détection d’erreur immédiate
    try {
      await (contract as any)[name](args);
    } catch (err: any) {
      console.warn(`⚠️ VIEW ${name} warm-up failed: ${err.toString()}`);
      return {
        testName: name,
        result: 'error',
        extra: `warm-up error: ${err.toString()}`,
      };
    }

    const latArr: number[] = [];
    for (let i = 0; i < VIEW_RUNS; i++) {
      try {
        const t0 = Date.now();
        await (contract as any)[name](args);
        latArr.push(Date.now() - t0);
      } catch (err: any) {
        console.warn(`⚠️ VIEW ${name} run #${i+1} failed: ${err.toString()}`);
        return {
          testName: name,
          result: 'error',
          extra: `run #${i+1} error: ${err.toString()}`,
        };
      }
    }

    const sorted = latArr.sort((a, b) => a - b);
    const trim = Math.floor(VIEW_RUNS * 0.025);
    const trimmed = sorted.slice(trim, VIEW_RUNS - trim);
    const mean = trimmed.reduce((a, b) => a + b, 0) / trimmed.length;
    const variance = trimmed.reduce((a, b) => a + (b - mean) ** 2, 0) / (trimmed.length - 1);
    const std = Math.sqrt(variance);
    const margin = 1.96 * std / Math.sqrt(trimmed.length);

    console.log(`Sim: ${mean.toFixed(2)}ms ±${margin.toFixed(2)}ms`);
    return {
      testName: name,
      txLatency: mean.toFixed(2),
      execTime: 0,
      result: 'callStatic',
      extra: `runs=${trimmed.length}, ±${margin.toFixed(2)} ms`
    };
  }

  // 5) Tests VIEW + TX
  const testCases: [string, any[]][] = [
    // on limite fibonacciRecursive pour éviter overflow
    ['fibonacciRecursive', [5, 10].map(n => ({ n }))],
    ['fibonacciIterative', [5, 10, 15, 20, 25].map(n => ({ n }))],
    ['factorialRecursive', [1, 5, 10, 15, 20].map(n => ({ n }))],
    ['factorialIterative', [1, 5, 10, 15, 20].map(n => ({ n }))],
    ['loopSum', [10, 100, 1000, 5000, 10000].map(n => ({ n }))],
    ['isPrime', [7, 97, 197, 997, 9973].map(num => ({ num }))],
    ['expBySquaring', [[2,2],[2,4],[2,8],[2,16],[2,32]].map(([a,b])=>({ a,b }))],
    ['gcd', [[12,8],[48,18],[270,192],[1071,462],[412,56]].map(([a,b])=>({ a,b }))]
  ];

  for (const [fn, argsList] of testCases) {
    for (const args of argsList) {
      const label = `${fn}(${Object.values(args).join(',')})`;
      const viewRes = await measureView(fn, args);
      viewRes.testName = label;
      results.push(viewRes);

      const txName = `${fn}_tx`;
      try {
        const txRes = await measureTx(`${label}_tx`, account, txName, args);
        if (gasRef > 0n && txRes.actualGasUsed) {
          const used = BigInt(txRes.actualGasUsed);
          const net = used > gasRef ? used - gasRef : 0n;
          const ratio = gasRef > 0n ? (Number(used * 100n / gasRef) / 100).toFixed(2) : '';
          txRes.netGas = net.toString();
          txRes.gasRatio = ratio;
          txRes.extra = `netGas=${net}`;
        }
        results.push(txRes);
      } catch {
        // pas de méthode _tx
      }
    }
  }

  // 6️⃣ Export CSV
  const ts = new Date().toISOString().replace(/:/g, '-');
  const outPath = path.resolve(__dirname, `../../Results/GasComparator/benchmark_near_${ts}.csv`);
  await fs.mkdir(path.dirname(outPath), { recursive: true });

  function escapeCell(v: any): string {
    const s = String(v ?? '');
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  }

  const headers = ['TestName','ActualGasUsed','NetGas','GasRatio(%)','TxLatency(ms)','ExecTime','Result','Extra'];
  const refRow = ['__REFERENCE__', gasRef.toString(), '','','','','',''];
  const rows = [headers, refRow, ...results.map(r => [
    r.testName,
    r.actualGasUsed||'',
    r.netGas||'',
    r.gasRatio||'',
    r.txLatency||'',
    r.execTime?.toString()||'',
    r.result,
    r.extra||''
  ])];

  const csv = rows.map(row => row.map(escapeCell).join(',')).join('\n') + '\n';
  await fs.writeFile(outPath, csv, 'utf8');
  console.log(`\n📄 CSV sauvegardé dans ${outPath}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
