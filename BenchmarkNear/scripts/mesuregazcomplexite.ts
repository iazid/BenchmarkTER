import { connect, keyStores, Contract, Account } from 'near-api-js';
import { promises as fsPromises } from 'fs';
import { statSync } from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const NETWORK_ID = 'testnet';
const NODE_URL = 'https://rpc.testnet.near.org';
const CONTRACT_ACCOUNT = 'benchmarknear.testnet';

const POSSIBLE_CREDENTIALS_DIRS = [
  path.join(os.homedir(), '.near-credentials'),
  path.join('/mnt/c', 'Users', process.env['USERNAME'] || '', '.near-credentials')
];
const foundDir = POSSIBLE_CREDENTIALS_DIRS.find(dir => {
  try { return statSync(dir).isDirectory(); } catch { return false; }
});
if (!foundDir) {
  throw new Error(
    `Aucun répertoire de credentials valide trouvé parmi: ${POSSIBLE_CREDENTIALS_DIRS.join(', ')}`
  );
}
const CREDENTIALS_DIR = foundDir;
console.log('Utilisation du répertoire de credentials :', CREDENTIALS_DIR);

const WASM_PATH = path.resolve(__dirname, '../build/contract.wasm');
const VIEW_RUNS = 50;
const TX_GAS = 300_000_000_000_000n;
const TX_DEPOSIT = 0n;

interface Result {
  testName: string;
  actualGasUsed?: string;
  latencyMs?: number;
  stdLatencyMs?: number;
  ci95ms?: number;
  result: string;
  extra?: string;
  gasRatioToRef?: string;
}

async function initAccount(): Promise<Account> {
  const keyStore = new keyStores.UnencryptedFileSystemKeyStore(CREDENTIALS_DIR);
  const keyPair = await keyStore.getKey(NETWORK_ID, CONTRACT_ACCOUNT);
  if (!keyPair) {
    throw new Error(
      `Aucune clé trouvée pour le compte ${CONTRACT_ACCOUNT}. Veuillez exécuter 'near login' et réessayer.`
    );
  }
  const near = await connect({ networkId: NETWORK_ID, nodeUrl: NODE_URL, deps: { keyStore } });
  return near.account(CONTRACT_ACCOUNT);
}

async function deployContract(account: Account): Promise<Result> {
  const wasm = await fsPromises.readFile(WASM_PATH);
  const start = Date.now();
  const res = await account.deployContract(wasm);
  const end = Date.now();
  const gas = res.transaction_outcome.outcome.gas_burnt.toString();
  const result: Result = { testName: 'deployContract', actualGasUsed: gas, latencyMs: end - start, result: 'deployed' };
  console.log(`[DEPLOY] ${result.testName} • gas=${result.actualGasUsed} • latency=${result.latencyMs}ms`);
  return result;
}

async function measureTx(name: string, account: Account, method: string, args: any): Promise<Result> {
  const start = Date.now();
  const res = await account.functionCall({
    contractId: CONTRACT_ACCOUNT,
    methodName: method,
    args,
    gas: TX_GAS,
    attachedDeposit: TX_DEPOSIT
  });
  const end = Date.now();
  const gasUsed = res.transaction_outcome.outcome.gas_burnt.toString();
  const result: Result = { testName: name, actualGasUsed: gasUsed, latencyMs: end - start, result: 'Tx Success' };
  console.log(`[TX]    ${name} • gas=${result.actualGasUsed} • latency=${result.latencyMs}ms`);
  return result;
}

async function measureView(name: string, contract: any, args: any): Promise<Result> {
    try {
      // warm-up dans le try
      await contract[name](args);
  
      const latencies: number[] = [];
      for (let i = 0; i < VIEW_RUNS; i++) {
        const start = Date.now();
        await contract[name](args);
        latencies.push(Date.now() - start);
      }
      const n = latencies.length;
      const mean = latencies.reduce((a, b) => a + b, 0) / n;
      const variance = latencies.map(t => (t - mean) ** 2).reduce((a, b) => a + b, 0) / (n - 1);
      const std = Math.sqrt(variance);
      const ci95 = 1.96 * std / Math.sqrt(n);
  
      return {
        testName: name,
        latencyMs: Math.round(mean),
        stdLatencyMs: Math.round(std),
        ci95ms: Number(ci95.toFixed(2)),
        result: 'View OK',
        extra: `runs=${n}`
      };
    } catch (err: any) {
      console.error(`[ERROR:VIEW] ${name}(${JSON.stringify(args)}): ${err.message}`);
      return {
        testName: name,
        result: 'View Error',
        extra: err.message
      };
    }
  }
  

async function measureReference(account: Account): Promise<bigint> {
  const res = await account.functionCall({
    contractId: CONTRACT_ACCOUNT,
    methodName: 'reference',
    args: {},
    gas: TX_GAS,
    attachedDeposit: TX_DEPOSIT
  });
  return BigInt(res.transaction_outcome.outcome.gas_burnt);
}

async function main() {
  const account = await initAccount();
  const results: Result[] = [];

  results.push(await deployContract(account));

  const viewMethods = [
    'getValue', 'loopSum', 'fibonacciIterative', 'fibonacciRecursive', 'isPrime',
    'factorialIterative', 'factorialRecursive', 'expBySquaring', 'gcd',
    'insertionSort', 'bubbleSort', 'binarySearch', 'multiplyMatrix2x2',
    'nestedLoops', 'simulateConcurrency', 'batchTestOperations', 'reference'
  ];
  const txWrappers = viewMethods.map(m => `${m}_tx`);
  const contract = new Contract(account.connection, CONTRACT_ACCOUNT, {
    viewMethods,
    changeMethods: ['setValue', ...txWrappers],
    useLocalViewExecution: false
  });

  const refGas = await measureReference(account);
  console.log(`[REF]   Gas utilisé par 'reference': ${refGas.toString()}`);

  results.push(await measureTx('setValue', account, 'setValue', { value: 42 }));

  const parametricTests: [string, string, any[]][] = [
    ['fibonacciRecursive', 'n', [5, 10, 15, 20]],
    ['factorialIterative', 'n', [1, 5, 10, 15, 20]],
    ['loopSum', 'n', [10, 100, 1000, 5000, 10000]],
    ['isPrime', 'num', [7, 37, 97]],
    ['gcd', 'args', [
      { a: 12, b: 8 },
      { a: 48, b: 18 },
      { a: 270, b: 192 },
      { a: 1071, b: 462 },
      { a: 412, b: 56 },
    ]]
  ];
  

  for (const [name, param, values] of parametricTests) {
    for (const val of values) {
      const args = { [param]: val };
      const viewResult = await measureView(name, contract, args);
      viewResult.testName = `${name}(${JSON.stringify(val)})`;
      results.push(viewResult);

      const txName = `${name}_tx(${JSON.stringify(val)})`;
      const txResult = await measureTx(txName, account, `${name}_tx`, args);
      txResult.testName = txName;
      results.push(txResult);
    }
  }

  for (const r of results) {
    if (r.actualGasUsed) {
        r.gasRatioToRef = (Number(BigInt(r.actualGasUsed)!) / Number(refGas)).toFixed(2);
    }
  }

  console.log('\n=== Résultats complets ===');
  console.table(results, ['testName', 'actualGasUsed', 'latencyMs', 'stdLatencyMs', 'ci95ms', 'result', 'extra', 'gasRatioToRef']);

  const ts = new Date().toISOString().replace(/:/g, '-');
  const outPath = path.resolve(__dirname, `../../Results/Data/Near/near-benchmark_${ts}.csv`);
  await fsPromises.mkdir(path.dirname(outPath), { recursive: true });
  const header = 'TestName,GasUsed,LatencyMs,StdMs,CI95ms,Result,Extra,GasRatioToRef\n';
  const csv = results.map(r => [
    r.testName, r.actualGasUsed || '', r.latencyMs, r.stdLatencyMs,
    r.ci95ms, r.result, r.extra || '', r.gasRatioToRef || ''
  ].join(',')).join('\n');
  await fsPromises.writeFile(outPath, header + csv);
  console.log(`Saved CSV to ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
