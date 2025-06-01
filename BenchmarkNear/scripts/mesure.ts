import { connect, keyStores, Contract, Account } from 'near-api-js';
import { promises as fsPromises } from 'fs';
import { statSync } from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';

// Adaptation ESM: __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * benchmarks NEAR StorageBenchmark contract
 * Mesure gas (pour transactions et view) et latence
 * Résultats exportés au format CSV
 */

// --- Configuration NEAR ---
const NETWORK_ID = 'testnet';
const NODE_URL = '	https://test.rpc.fastnear.com';
const CONTRACT_ACCOUNT = 'benchmarknear.testnet'; // Remplace par ton compte Testnet

// Support multiple emplacements de credentials (WSL vs Windows native)
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
const TX_GAS = 300_000_000_000_000n; // 30 TGas
const TX_DEPOSIT = 0n;

interface Result {
  testName: string;
  actualGasUsed?: string;
  latencyMs?: number;
  stdLatencyMs?: number;
  ci95ms?: number;
  result: string;
  extra?: string;
}

// Initialise et retourne l'objet Account connecté
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

// Déploie le contrat et mesure gas & latence
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

// Mesure un appel transactionnel (@call)
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

// Mesure un appel en lecture (@view) avec écart type et CI 95%
async function measureView(name: string, contract: any, args: any): Promise<Result> {
  // warm-up
  await contract[name](args);
  const latencies: number[] = [];
  for (let i = 0; i < VIEW_RUNS; i++) {
    const start = Date.now();
    await contract[name](args);
    latencies.push(Date.now() - start);
  }
  const n = latencies.length;
  const mean = latencies.reduce((a, b) => a + b, 0) / n;
  const variance = latencies
    .map(t => (t - mean) ** 2)
    .reduce((a, b) => a + b, 0) / (n - 1);
  const std = Math.sqrt(variance);
  const ci95 = 1.96 * std / Math.sqrt(n);
  const result: Result = {
    testName: name,
    latencyMs: Math.round(mean),
    stdLatencyMs: Math.round(std),
    ci95ms: Number(ci95.toFixed(2)),
    result: 'View OK',
    extra: `runs=${n}`
  };
  console.log(
    `[VIEW] ${name} • mean=${result.latencyMs}ms ±${result.ci95ms}ms (std=${result.stdLatencyMs}ms)`
  );
  return result;
}

async function main() {
  const account = await initAccount();
  const results: Result[] = [];

  // déploiement
  results.push(await deployContract(account));

  // instanciation du contrat avec wrappers transactionnels
  const viewMethods = [
    'getValue','loopSum','fibonacciIterative','fibonacciRecursive','isPrime',
    'factorialIterative','factorialRecursive','expBySquaring','gcd',
    'insertionSort','bubbleSort','binarySearch','multiplyMatrix2x2',
    'nestedLoops','simulateConcurrency','batchTestOperations'
  ];
  const viewTests: [string, any][] = [
    ['getValue', {}],
    ['loopSum', { n: 100000 }],
    ['fibonacciIterative', { n: 30 }],
    ['fibonacciRecursive', { n: 10 }],
    ['isPrime', { num: 1000003 }],
    ['factorialIterative', { n: 10 }],
    ['factorialRecursive', { n: 10 }],
    ['expBySquaring', { base: 2, exponent: 20 }],
    ['gcd', { a: 270, b: 192 }],
    ['insertionSort', { arr: [5,3,8,1,2] }],
    ['bubbleSort', { arr: [4,7,2,9,1] }],
    ['binarySearch', { sortedArr:[1,2,3,4,5], target:4 }],
    ['multiplyMatrix2x2',{ m1:{a:1,b:2,c:3,d:4}, m2:{a:5,b:6,c:7,d:8} }],
    ['nestedLoops',{ n:50 }],
    ['simulateConcurrency',{ fibN:10,primeN:17,loopN:10 }],
    ['batchTestOperations',{ iterations:5,fibN:10,primeN:17,loopN:10 }]
  ];
  // noms wrappers transactionnels (_tx)
  const txWrappers = viewMethods.map(m => `${m}_tx`);

  const contract = new Contract(account.connection, CONTRACT_ACCOUNT, {
    viewMethods,
    changeMethods: ['setValue', ...txWrappers],
    useLocalViewExecution: false
  });

  // bench TX setValue
  results.push(await measureTx('setValue', account, 'setValue', { value: 42 }));

  // bench view + transaction pour chaque méthode
  for (const [name, args] of viewTests) {
    results.push(await measureView(name, contract, args));
    // transaction wrapper
    results.push(await measureTx(`${name}_tx`, account, `${name}_tx`, args));
  }

  // récap console & CSV
  console.log('\n=== Résultats complets ===');
  console.table(results, ['testName','actualGasUsed','latencyMs','stdLatencyMs','ci95ms','result','extra']);

  const ts = new Date().toISOString().replace(/:/g,'-');
  const outPath = path.resolve(__dirname, `../../Results/Data/Near/near-benchmark_${ts}.csv`);
  await fsPromises.mkdir(path.dirname(outPath), { recursive:true });
  const header = 'TestName,GasUsed,LatencyMs,StdMs,CI95ms,Result,Extra\n';
  const csv = results.map(r => [
    r.testName, r.actualGasUsed||'', r.latencyMs, r.stdLatencyMs, r.ci95ms, r.result, r.extra||''
  ].join(',')).join('\n');
  await fsPromises.writeFile(outPath, header + csv);
  console.log(`Saved CSV to ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
