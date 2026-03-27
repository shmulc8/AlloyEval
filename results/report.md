# Results Summary

| Task | Short | Passed | Failed | Total | Pass Rate |
|------|-------|-------:|-------:|------:|----------:|
| nl2alloy | NL | 33 | 12 | 45 | 73.3% |
| nl2alloy_guided | NL+G | 31 | 14 | 45 | 68.9% |
| nl2alloy_agent | NL+A | 40 | 5 | 45 | 88.9% |
| nl2alloy_reflect | NL+R | 38 | 7 | 45 | 84.4% |
| alloy2alloy | A2A | 39 | 6 | 45 | 86.7% |
| alloy2alloy_guided | A2A+G | 39 | 6 | 45 | 86.7% |
| alloy2alloy_agent | A2A+A | 43 | 2 | 45 | 95.6% |
| alloy2alloy_reflect | A2A+R | 44 | 1 | 45 | 97.8% |
| sketch2alloy | SKT | 7 | 4 | 11 | 63.6% |
| sketch2alloy_guided | SKT+G | 5 | 6 | 11 | 45.5% |
| sketch2alloy_agent | SKT+A | 7 | 4 | 11 | 63.6% |
| sketch2alloy_reflect | SKT+R | 5 | 6 | 11 | 45.5% |
| **TOTAL** | | **331** | **73** | **404** | **81.9%** |

## Task Key
| Short | Full name |
|-------|-----------|
| NL | nl2alloy |
| NL+G | nl2alloy_guided |
| NL+A | nl2alloy_agent |
| A2A | alloy2alloy |
| A2A+G | alloy2alloy_guided |
| A2A+A | alloy2alloy_agent |
| SKT | sketch2alloy |
| SKT+G | sketch2alloy_guided |
| SKT+A | sketch2alloy_agent |
| NL+R | nl2alloy_reflect |
| A2A+R | alloy2alloy_reflect |
| SKT+R | sketch2alloy_reflect |

---

## Pass / Fail by Property

| Property | NL | NL+G | NL+A | NL+R | A2A | A2A+G | A2A+A | A2A+R | SKT | SKT+G | SKT+A | SKT+R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Antisymmetric | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| Circular | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Connex | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Cycle | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| DAG | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Function | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ |
| Functional | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Irreflexive | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ |
| Reflexive | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ |
| Symmetric | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Transitive | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| graph/complete | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| graph/oriented | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| graph/stronglyConnected | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| graph/transitive | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| graph/undirected | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| graph/weaklyConnected | ✗ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| production_line/inv1 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| production_line/inv10 | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| production_line/inv2 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| production_line/inv3 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| production_line/inv4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| production_line/inv5 | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| production_line/inv6 | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| production_line/inv7 | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| production_line/inv8 | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| production_line/inv9 | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ |
| social_network/inv1 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| social_network/inv2 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| social_network/inv3 | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| social_network/inv4 | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| social_network/inv5 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| social_network/inv6 | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
| social_network/inv7 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| social_network/inv8 | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| trash/inv1 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| trash/inv10 | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| trash/inv2 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| trash/inv3 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| trash/inv4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| trash/inv5 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| trash/inv6 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| trash/inv7 | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| trash/inv8 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| trash/inv9 | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## Error Breakdown

| task | error | count |
|---|---|---|
| A2A | Counterexample | 4 |
| A2A | Syntax Error | 1 |
| A2A | Type Error | 1 |
| A2A+A | Counterexample | 2 |
| A2A+G | Counterexample | 5 |
| A2A+G | Type Error | 1 |
| A2A+R | Counterexample | 1 |
| NL | Counterexample | 11 |
| NL | Type Error | 1 |
| NL+A | Counterexample | 5 |
| NL+G | Counterexample | 14 |
| NL+R | Counterexample | 6 |
| NL+R | Type Error | 1 |
| SKT | Syntax Error | 4 |
| SKT+A | Syntax Error | 3 |
| SKT+A | Counterexample | 1 |
| SKT+G | Syntax Error | 5 |
| SKT+G | Counterexample | 1 |
| SKT+R | Syntax Error | 5 |
| SKT+R | Counterexample | 1 |