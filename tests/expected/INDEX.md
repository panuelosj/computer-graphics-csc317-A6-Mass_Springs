# Public test data: A6-Mass_Springs

These are the exact arrays the public unit checks compare your
functions against — the inputs they feed in and the outputs they
expect back. Everything here is generated from
`a6_golden.npz`; nothing here is secret, and you
are meant to look at it when a check fails.

* `arrays/<name>.txt` — the values, in readable form.
* `images/<name>.png` — the same array as a viewable image, for
  the entries that are pictures.

To load an array yourself:

```python
import numpy as np
g = np.load('tests/golden/a6_golden.npz')
print(g.files)          # every available name
img = g['<name>']       # one array
```

Regenerate this folder with `python export_expected.py <assignment>` from the repository root.

| entry | what it is | values | picture |
|---|---|---|---|
| `A` | shape (5, 5), dtype float64, range [-1, 1] | [A.txt](arrays/A.txt) | — |
| `C` | shape (2, 5), dtype float64, range [0, 1] | [C.txt](arrays/C.txt) | — |
| `E` | shape (5, 2), dtype int64, range [0, 4] | [E.txt](arrays/E.txt) | — |
| `M` | shape (5, 5), dtype float64, range [0, 1] | [M.txt](arrays/M.txt) | — |
| `Q` | shape (5, 5), dtype float64, range [-100, 1e+10] | [Q.txt](arrays/Q.txt) | — |
| `V` | shape (5, 3), dtype float64, range [0, 2] | [V.txt](arrays/V.txt) | — |
| `b` | shape (2,), dtype int64, range [0, 2] | [b.txt](arrays/b.txt) | — |
| `chain_A` | shape (29, 30), dtype float64, range [-1, 1] | [chain_A.txt](arrays/chain_A.txt) | — |
| `chain_C` | shape (2, 30), dtype float64, range [0, 1] | [chain_C.txt](arrays/chain_C.txt) | — |
| `chain_E` | shape (29, 2), dtype int64, range [0, 29] | [chain_E.txt](arrays/chain_E.txt) | — |
| `chain_M` | shape (30, 30), dtype float64, range [0, 1] | [chain_M.txt](arrays/chain_M.txt) | — |
| `chain_Ucur` | shape (30, 3), dtype float64, range [-0.348661, 2.9] | [chain_Ucur.txt](arrays/chain_Ucur.txt) | — |
| `chain_Unext` | shape (30, 3), dtype float64, range [-0.209492, 2.9] | [chain_Unext.txt](arrays/chain_Unext.txt) | — |
| `chain_Uprev` | shape (30, 3), dtype float64, range [0, 2.9] | [chain_Uprev.txt](arrays/chain_Uprev.txt) | — |
| `chain_V` | shape (30, 3), dtype float64, range [0, 2.9] | [chain_V.txt](arrays/chain_V.txt) | — |
| `chain_b` | shape (2,), dtype int64, range [0, 29] | [chain_b.txt](arrays/chain_b.txt) | — |
| `chain_dt` | shape (), dtype float64, range [0.0333333, 0.0333333] | [chain_dt.txt](arrays/chain_dt.txt) | — |
| `chain_fext` | shape (30, 3), dtype float64, range [-9.8, 0] | [chain_fext.txt](arrays/chain_fext.txt) | — |
| `chain_k` | shape (), dtype float64, range [200000, 200000] | [chain_k.txt](arrays/chain_k.txt) | — |
| `chain_m` | shape (30,), dtype float64, range [1, 1] | [chain_m.txt](arrays/chain_m.txt) | — |
| `chain_r` | shape (29,), dtype float64, range [0.1, 0.1] | [chain_r.txt](arrays/chain_r.txt) | — |
| `delta_t` | shape (), dtype float64, range [0.0333333, 0.0333333] | [delta_t.txt](arrays/delta_t.txt) | — |
| `fext` | shape (5, 3), dtype float64, range [-9.8, 0] | [fext.txt](arrays/fext.txt) | — |
| `k` | shape (), dtype float64, range [100, 100] | [k.txt](arrays/k.txt) | — |
| `m` | shape (5,), dtype float64, range [1, 1] | [m.txt](arrays/m.txt) | — |
| `n_steps` | shape (), dtype int64, range [5, 5] | [n_steps.txt](arrays/n_steps.txt) | — |
| `one_Unext` | shape (5, 3), dtype float64, range [-0.0108888, 2] | [one_Unext.txt](arrays/one_Unext.txt) | — |
| `r` | shape (5,), dtype float64, range [1, 1] | [r.txt](arrays/r.txt) | — |
| `si_A` | shape (5, 4), dtype float64, range [-1, 1] | [si_A.txt](arrays/si_A.txt) | — |
| `si_A_sparse` | shape (5, 4), dtype float64, range [-1, 1] | [si_A_sparse.txt](arrays/si_A_sparse.txt) | — |
| `si_E` | shape (5, 2), dtype int64, range [0, 3] | [si_E.txt](arrays/si_E.txt) | — |
| `si_n` | shape (), dtype int64, range [4, 4] | [si_n.txt](arrays/si_n.txt) | — |
| `step_Unext` | shape (5, 3), dtype float64, range [-0.162589, 2] | [step_Unext.txt](arrays/step_Unext.txt) | — |
