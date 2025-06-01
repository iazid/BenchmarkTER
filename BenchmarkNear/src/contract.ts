import { NearBindgen, call, view, assert } from 'near-sdk-js';

/**
 * Contrat NEAR pour benchmark : version avec wrappers transactionnels
 */
@NearBindgen({})
export class StorageBenchmark {

  

  // -------------------------------------------------------------------
  // Stockage simple
  // -------------------------------------------------------------------
  storedValue: number = 0;

  @call({})
  setValue({ value }: { value: number }): void {
    this.storedValue = value;
  }

  @view({})
  getValue(): number {
    return this.storedValue;
  }
  @call({})
  getValue_tx(): number {
    return this.getValue();
  }

  // -------------------------------------------------------------------
  // Boucle simple : somme linéaire (O(n))
  // -------------------------------------------------------------------
  @view({})
  loopSum({ n }: { n: number }): number {
    let sum = 0;
    for (let i = 0; i < n; i++) sum += i;
    return sum;
  }
  @call({})
  loopSum_tx({ n }: { n: number }): number {
    return this.loopSum({ n });
  }

  // -------------------------------------------------------------------
  // Fibonacci itératif (O(n))
  // -------------------------------------------------------------------
  @view({})
  fibonacciIterative({ n }: { n: number }): number {
    if (n === 0) return 0;
    if (n === 1) return 1;
    let a = 0, b = 1;
    for (let i = 2; i <= n; i++) {
      const c = a + b;
      a = b;
      b = c;
    }
    return b;
  }
  @call({})
  fibonacciIterative_tx({ n }: { n: number }): number {
    return this.fibonacciIterative({ n });
  }

  // -------------------------------------------------------------------
  // Fibonacci récursif (exponentiel, limité n <= 20)
  // -------------------------------------------------------------------
  @view({})
  fibonacciRecursive({ n }: { n: number }): number {
    assert(n <= 20, 'n too high; limit to 20');
    if (n < 2) return n;
    return this.fibonacciRecursive({ n: n - 1 }) + this.fibonacciRecursive({ n: n - 2 });
  }
  @call({})
  fibonacciRecursive_tx({ n }: { n: number }): number {
    return this.fibonacciRecursive({ n });
  }

  // -------------------------------------------------------------------
  // Test de primalité naïf (O(sqrt(n)))
  // -------------------------------------------------------------------
  @view({})
  isPrime({ num }: { num: number }): boolean {
    if (num < 2) return false;
    for (let i = 2; i * i <= num; i++) if (num % i === 0) return false;
    return true;
  }
  @call({})
  isPrime_tx({ num }: { num: number }): boolean {
    return this.isPrime({ num });
  }

  // -------------------------------------------------------------------
  // Factorielle itérative (O(n))
  // -------------------------------------------------------------------
  @view({})
  factorialIterative({ n }: { n: number }): number {
    let r = 1;
    for (let i = 1; i <= n; i++) r *= i;
    return r;
  }
  @call({})
  factorialIterative_tx({ n }: { n: number }): number {
    return this.factorialIterative({ n });
  }

  // -------------------------------------------------------------------
  // Factorielle récursive (O(n))
  // -------------------------------------------------------------------
  @view({})
  factorialRecursive({ n }: { n: number }): number {
    return n === 0 ? 1 : n * this.factorialRecursive({ n: n - 1 });
  }
  @call({})
  factorialRecursive_tx({ n }: { n: number }): number {
    return this.factorialRecursive({ n });
  }

  // -------------------------------------------------------------------
  // Exponentiation par squaring (O(log n))
  // -------------------------------------------------------------------
  @view({})
  expBySquaring({ base, exponent }: { base: number; exponent: number }): number {
    if (exponent === 0) return 1;
    if (exponent % 2 === 0) {
      const half = this.expBySquaring({ base, exponent: exponent / 2 });
      return half * half;
    }
    return base * this.expBySquaring({ base, exponent: exponent - 1 });
  }
  @call({})
  expBySquaring_tx({ base, exponent }: { base: number; exponent: number }): number {
    return this.expBySquaring({ base, exponent });
  }

  // -------------------------------------------------------------------
  // Algorithme d'Euclide pour le GCD (O(log n))
  // -------------------------------------------------------------------
  @view({})
  gcd({ a, b }: { a: number; b: number }): number {
    let x = a, y = b;
    while (y !== 0) {
      [x, y] = [y, x % y];
    }
    return x;
  }
  @call({})
  gcd_tx({ a, b }: { a: number; b: number }): number {
    return this.gcd({ a, b });
  }

  // -------------------------------------------------------------------
  // Tri par insertion (O(n²))
  // -------------------------------------------------------------------
  @view({})
  insertionSort({ arr }: { arr: number[] }): number[] {
    const a = [...arr];
    for (let i = 1; i < a.length; i++) {
      let j = i;
      while (j > 0 && a[j - 1] > a[j]) {
        [a[j], a[j - 1]] = [a[j - 1], a[j]];
        j--;  }
    }
    return a;
  }
  @call({})
  insertionSort_tx({ arr }: { arr: number[] }): number[] {
    return this.insertionSort({ arr });
  }

  // -------------------------------------------------------------------
  // Tri à bulles (O(n²))
  // -------------------------------------------------------------------
  @view({})
  bubbleSort({ arr }: { arr: number[] }): number[] {
    const a = [...arr];
    for (let i = 0; i < a.length - 1; i++) {
      let swapped = false;
      for (let j = 0; j < a.length - i - 1; j++) {
        if (a[j] > a[j + 1]) {
          [a[j], a[j + 1]] = [a[j + 1], a[j]];
          swapped = true;
        }
      }
      if (!swapped) break;
    }
    return a;
  }
  @call({})
  bubbleSort_tx({ arr }: { arr: number[] }): number[] {
    return this.bubbleSort({ arr });
  }

  // -------------------------------------------------------------------
  // Recherche binaire (O(log n))
  // -------------------------------------------------------------------
  @view({})
  binarySearch({ sortedArr, target }: { sortedArr: number[]; target: number }): number {
    let l = 0, r = sortedArr.length;
    while (l < r) {
      const m = l + ((r - l) >> 1);
      if (sortedArr[m] === target) return m;
      if (sortedArr[m] < target) l = m + 1; else r = m;
    }
    return sortedArr.length;
  }
  @call({})
  binarySearch_tx({ sortedArr, target }: { sortedArr: number[]; target: number }): number {
    return this.binarySearch({ sortedArr, target });
  }

  // -------------------------------------------------------------------
  // Multiplication de matrices 2x2 (O(1))
  // -------------------------------------------------------------------
  @view({})
  multiplyMatrix2x2({ m1, m2 }: { m1: Matrix2x2; m2: Matrix2x2 }): Matrix2x2 {
    return { a: m1.a*m2.a + m1.b*m2.c, b: m1.a*m2.b + m1.b*m2.d, c: m1.c*m2.a + m1.d*m2.c, d: m1.c*m2.b + m1.d*m2.d };
  }
  @call({})
  multiplyMatrix2x2_tx({ m1, m2 }: { m1: Matrix2x2; m2: Matrix2x2 }): Matrix2x2 {
    return this.multiplyMatrix2x2({ m1, m2 });
  }

  // -------------------------------------------------------------------
  // Boucles imbriquées (O(n²)), n <= 100
  // -------------------------------------------------------------------
  @view({})
  nestedLoops({ n }: { n: number }): number {
    assert(n <= 100, 'n too high; limit to 100');
    let total = 0;
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) total += i*j;
    return total;
  }
  @call({})
  nestedLoops_tx({ n }: { n: number }): number {
    return this.nestedLoops({ n });
  }

  // -------------------------------------------------------------------
  // Simulation de concurrence
  // -------------------------------------------------------------------
  @view({})
  simulateConcurrency({ fibN, primeN, loopN }: { fibN: number; primeN: number; loopN: number }): SimResult {
    return { fib: this.fibonacciIterative({ n: fibN }), prime: this.isPrime({ num: primeN }), loop: this.loopSum({ n: loopN }) };
  }
  @call({})
  simulateConcurrency_tx({ fibN, primeN, loopN }: { fibN: number; primeN: number; loopN: number }): SimResult {
    return this.simulateConcurrency({ fibN, primeN, loopN });
  }

  // -------------------------------------------------------------------
  // Batch d'opérations
  // -------------------------------------------------------------------
  @view({})
  batchTestOperations({ iterations, fibN, primeN, loopN }: { iterations: number; fibN: number; primeN: number; loopN: number }): number {
    let sum = 0;
    for (let i = 0; i < iterations; i++) sum += this.simulateConcurrency({ fibN, primeN, loopN }).fib;
    return sum;
  }
  @call({})
  batchTestOperations_tx({ iterations, fibN, primeN, loopN }: { iterations: number; fibN: number; primeN: number; loopN: number }): number {
    return this.batchTestOperations({ iterations, fibN, primeN, loopN });
  }

  // -------------------------------------------------------------------  
  // Méthode de référence
  // -------------------------------------------------------------------
  // Cette méthode est utilisée pour mesurer le coût de la transaction
  // de référence et pour la comparaison avec d'autres méthodes
  // dans le cadre de la mesure de complexité. 

  
  
 

  
  @call({})
  reference_tx(): void {
  // Rien du tout
}
}

export interface Matrix2x2 { a: number; b: number; c: number; d: number; }
export interface SimResult { fib: number; prime: boolean; loop: number; }
