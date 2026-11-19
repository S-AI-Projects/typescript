# Test Execution Results: Reference vs. Alternative

- **Date:** 2026-11-19
- **Exercise:** `exercises/practice/bowling`
- **Total Canonical Cases:** 31

---

## 1. Summary

Both the maintained reference implementation (`.meta/proof.ci.ts`) and the independently developed alternative implementation (`work/R47-T026/alternative.ts`) were executed in isolated environments against all 31 canonical test cases.

| Implementation | Executed | Passed | Failed | Exit Code | Outcome |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Reference Implementation** (`proof.ci.ts`) | 31 | 31 | 0 | 0 | **ALL PASSED** |
| **Alternative Implementation** (`alternative.ts`) | 31 | 31 | 0 | 0 | **ALL PASSED** |

---

## 2. Verification of Named Test Cases

| Test Case Name | Expected Outcome | Reference Result | Alternative Result | Agreement |
| :--- | :---: | :---: | :---: | :---: |
| `should be able to score a game with all zeros` | `0` | Passed | Passed | YES |
| `should be able to score a game with no strikes or spares` | `90` | Passed | Passed | YES |
| `a spare followed by zeros is worth ten points` | `10` | Passed | Passed | YES |

---

## 3. Full Canonical Suite Verification

All 31 canonical test cases passed under both implementations:

1. `should be able to score a game with all zeros` (passed)
2. `should be able to score a game with no strikes or spares` (passed)
3. `a spare followed by zeros is worth ten points` (passed)
4. `points scored in the roll after a spare are counted twice` (passed)
5. `consecutive spares each get a one roll bonus` (passed)
6. `a spare in the last frame gets a one roll bonus that is counted once` (passed)
7. `a strike earns ten points in a frame with a single roll` (passed)
8. `points scored in the two rolls after a strike are counted twice as a bonus` (passed)
9. `consecutive strikes each get the two roll bonus` (passed)
10. `a strike in the last frame gets a two roll bonues that is counted once` (passed)
11. `rolling a spare with the two roll bonus does not get a bonus roll` (passed)
12. `strikes with the two roll bonus do not get bonus rolls` (passed)
13. `last two strikes followed by only last bonus with non strike points` (passed)
14. `a strike with the one roll bonus after a spare in the last frame does not get a bonus` (passed)
15. `all strikes is a perfect game` (passed)
16. `rolls cannot score negative points` (passed)
17. `a roll cannot score more than 10 points` (passed)
18. `two rolls in a frame cannot score more than 10 points` (passed)
19. `bonus roll after a strike in the last frame cannot score more than 10 points` (passed)
20. `two bonus rolls after a strike in the last frame cannot score more than 10 points` (passed)
21. `two bonus rolls after a strike in the last frame can score more than 10 points if one is a strike` (passed)
22. `the second bonus rolls after a strike in the last frame cannot be a strike if the first one is not a strike` (passed)
23. `second bonus roll after a strike in the last frame cannot score more than 10 points` (passed)
24. `an unstarted game cannot be scored` (passed)
25. `an incomplete game cannot be scored` (passed)
26. `cannot roll if game already has ten frames` (passed)
27. `bonus rolls for a strike in the last frame must be rolled before score can be calculated` (passed)
28. `both bonus rolls for a strike in the last frame must be rolled before score can be calculated` (passed)
29. `bonus roll for a spare in the last frame must be rolled before score can be calculated` (passed)
30. `cannot roll after bonus roll for spare` (passed)
31. `cannot roll after bonus rolls for strike` (passed)
