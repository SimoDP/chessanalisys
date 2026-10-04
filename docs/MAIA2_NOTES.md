# Note su Maia-2 (M0)

Verifica dell'interfaccia attesa in §3.2, fatta **leggendo il codice installato** di `maia2` 0.11.0
(PyPI, wheel del 2026-07-15, `Requires-Python >=3.10,<3.13`, dipende da `torch>=2.8,<2.9`).
Le differenze restano confinate in `src/chessanalyst/engines/maia2.py` (unico modulo che importa `maia2`).

## Stato della verifica

| Punto della checklist (App. B.3) | Stato |
| --- | --- |
| Funzioni di inferenza (singola e a lotti) | Verificato sul codice (sotto) |
| Tipo di modello | `rapid` (default) e `blitz` |
| Fasce Elo lette dal codice | Verificato: coincidono con il segnaposto di `config/maia2_limits.yaml` |
| Lato di `win_prob` | Verificato sul codice: **Bianco** (l'adattatore converte in «chi muove») |
| Comportamento oltre il limite alto | Verificato sul codice: ogni Elo ≥ 2000 cade nella fascia 10 |
| Test di §3.2 sul modello vero | Superati (`pytest -m engines`): chiavi tutte legali, somma 1 ± 1e-6, risposta identica con orologi diversi, Bianco e Nero al tratto |
| Tempo per posizione su CPU/GPU | CPU (4 core x86-64, torch 2.8.0): ≈ 0,02 s per chiamata (39 chiamate di `golden --data`, massimo 0,03 s); caricamento del modello ≈ 2,6 s alla prima chiamata. GPU non misurata |

I test di §3.2 sono in `tests/engines/test_real_engines.py::test_maia_real` (marker `engines`); gli stessi
controlli sono coperti senza pesi da `tests/engines/test_maia_adapter.py` con `FakeMaiaBackend`.

**Saturazione osservata.** In `fixtures/golden_maia.json` le ancore 1900 (2025 Lichess) e 2400 (2400 Lichess)
producono policy e risultato atteso **identici** su tutti i nodi: entrambe cadono nella fascia 10. È l'esito
previsto da D-24 (`maia.confidence = "low"`, `p_up = null`). A 1500 FIDE (1700, fascia 7) la policy differisce
(radice: Bg5 29%, Be3 17%, Bc4 15%; a 1900/2400: Bg5 32%, Be3 20%, f3 13%).

## API reale

### Caricamento

```python
from maia2 import model, inference
m = model.from_pretrained(type="rapid", device="auto", save_root="data/maia2_models")
prepared = inference.prepare()
```

- `from_pretrained(type, device="auto", save_root="./maia2_models")`: scarica con `gdown` da Google Drive
  `rapid_model.pt` (o `blitz_model.pt`) in `save_root` e ne verifica lo SHA-256
  (`rapid`: `65aae846…7e997`, `blitz`: `5090d5d0…c44b2`). Un file già presente e valido non viene
  riscaricato: **i pesi si possono copiare a mano** in `data/maia2_models/`.
- `device`: `auto` sceglie `cuda`, poi `mps`, poi `cpu`; `cuda` richiesto ma assente → `RuntimeError`.
- La configurazione dell'architettura è un dato del pacchetto (`maia2/configs/maia2-training.yaml`).

### Chiamata singola

```python
move_probs, win_prob = inference.inference_each(m, prepared, fen, elo_self, elo_oppo)
```

- `move_probs`: dizionario UCI → probabilità **solo sulle mosse legali** (softmax mascherato), ordinato per
  probabilità decrescente e **arrotondato a 4 decimali** dal pacchetto: la somma può differire da 1 di
  qualche 1e-4, per questo l'adattatore rinormalizza (§3.2).
- Con il Nero al tratto la scacchiera viene specchiata e le mosse riconvertite (`mirror_move`): le chiavi sono
  sempre UCI della posizione reale; l'arrocco è `e1g1`/`e8g8` come in `python-chess`.
- `win_prob`: il valore della testa `value` è calcolato per chi muove sulla scacchiera specchiata; il pacchetto
  restituisce `1 − v` quando muove il Nero, quindi `win_prob` è **dal punto di vista del Bianco**.
  `MaiaEngine.expected_score` lo riporta a chi muove (`1 − win_prob` se muove il Nero).
- Posizione senza mosse legali → `ValueError` (le posizioni terminali sono già rifiutate in ingresso).

### Chiamata a lotti

```python
data, acc = inference.inference_batch(data, model, verbose, batch_size, num_workers)
```

`data` è un `pandas.DataFrame` con le colonne obbligatorie `board` (FEN), `move`, `active_elo`,
`opponent_elo`; restituisce il DataFrame con le colonne `win_probs` e `move_probs` aggiunte e l'accuratezza
rispetto a `move`. In M0 l'adattatore usa la chiamata singola; quella a lotti servirà al filtro delle linee (M3).

### Fasce Elo (`maia2.utils.create_elo_dict` / `map_to_category`)

`< 1100` → 0; `1100–1199` → 1; …; `1900–1999` → 9; `≥ 2000` → 10. Ampiezza 100, nessun limite superiore:
3000 cade nella fascia 10 come 2000. `config/maia2_limits.yaml` coincide con il codice (nessun valore da
cambiare). Tabella per le ancore con la conversione segnaposto (§3-bis):

| Ancora (FIDE) | `elo_maia` | Fascia | `saturated` |
| --- | --- | --- | --- |
| 1500 | 1700 | 7 | no |
| 1900 | 2025 | 10 | sì (atteso, D-24) |
| 2400 | 2400 | 10 | sì |

### Storia e orologi

Ingresso = FEN singola (nessuna storia, D-04). Il modello non usa i contatori della FEN: l'adattatore
interroga sull'EPD con contatori neutri `0 1` e la cache usa l'EPD come chiave.

## Download dei pesi

`scripts/setup_engines.py` chiama `from_pretrained` una volta: `rapid_model.pt` (279 704 570 byte) finisce in
`data/maia2_models/` con verifica SHA-256. Servono `drive.google.com` e `drive.usercontent.google.com`.
