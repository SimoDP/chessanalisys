# Relazione di calibrazione (M5)

Campione: 100 posizioni da partite rapid valutate del database aperto di Lichess (2026-08), 20 per fascia del giocatore al tratto; annotazione automatica con Stockfish e Maia-2 (profilo `fast`). Errore = una delle 3 mosse successive del giocatore perde almeno 100 cp.

## Campione

| Fascia | Posizioni | Con un errore | Costo medio della mossa giocata (cp) |
| --- | --- | --- | --- |
| lt1200 | 20 | 9 | 151.2 |
| 1200_1600 | 20 | 12 | 95.2 |
| 1600_2000 | 20 | 10 | 65.7 |
| 2000_2400 | 20 | 9 | 19.9 |
| ge2400 | 20 | 5 | 63.1 |

Categorie degli errori (tag della confutazione): piece_activity 37, material 34, initiative_tempo 33, threats_dynamics 27, king_safety 22, pawn_structure 21, space_center 12, transition_plans 5.

## Tranquillità T (θ, k_c, w_c)

Misura: AUC di 100 − T nel prevedere un errore della categoria (0,5 = nessuna capacità, 1 = perfetta), media sulle categorie con almeno 5 errori.

| Parametri | AUC media | Per categoria |
| --- | --- | --- |
| attuali (θ × 1, k × 1, w + 0) | 0.5768 | king_safety 0.68 (21), pawn_structure 0.45 (18), space_center 0.45 (11), piece_activity 0.61 (30), initiative_tempo 0.70 (29), threats_dynamics 0.58 (24), material 0.56 (28), transition_plans 0.58 (5) |
| θ × 0.1, k × 0.1, w +0.45 | 0.649 | king_safety 0.67 (21), pawn_structure 0.50 (18), space_center 0.61 (11), piece_activity 0.70 (30), initiative_tempo 0.72 (29), threats_dynamics 0.65 (24), material 0.63 (28), transition_plans 0.69 (5) |
| θ × 0.15, k × 0.1, w +0.45 | 0.6476 | king_safety 0.67 (21), pawn_structure 0.50 (18), space_center 0.61 (11), piece_activity 0.70 (30), initiative_tempo 0.72 (29), threats_dynamics 0.65 (24), material 0.63 (28), transition_plans 0.69 (5) |
| θ × 0.1, k × 0.15, w +0.45 | 0.6473 | king_safety 0.67 (21), pawn_structure 0.50 (18), space_center 0.60 (11), piece_activity 0.70 (30), initiative_tempo 0.73 (29), threats_dynamics 0.65 (24), material 0.63 (28), transition_plans 0.70 (5) |
| θ × 0.15, k × 0.15, w +0.45 | 0.6467 | king_safety 0.67 (21), pawn_structure 0.50 (18), space_center 0.60 (11), piece_activity 0.70 (30), initiative_tempo 0.73 (29), threats_dynamics 0.65 (24), material 0.63 (28), transition_plans 0.70 (5) |
| θ × 0.1, k × 0.25, w +0.45 | 0.646 | king_safety 0.68 (21), pawn_structure 0.50 (18), space_center 0.59 (11), piece_activity 0.70 (30), initiative_tempo 0.73 (29), threats_dynamics 0.64 (24), material 0.63 (28), transition_plans 0.70 (5) |

Controllo incrociato (fit su metà delle posizioni, AUC sull'altra metà):

| Fit sulla metà | Parametri (θ, k, w) | AUC sull'altra metà | Con i valori attuali |
| --- | --- | --- | --- |
| 1 | × 0.1, × 0.1, +0.15 | 0.6315 | 0.5791 |
| 2 | × 2.0, × 0.15, +0.3 | 0.5504 | 0.5762 |

Il migliore della griglia completa non si adotta: guadagno +0.072 su tutto il campione, ma non almeno 0.02 su entrambe le metà del controllo incrociato (θ instabile).

Secondo passo: θ fisso, solo k_c e w_c, con lo stesso controllo.

| Fit sulla metà | Parametri (k, w) | AUC sull'altra metà | Con i valori attuali |
| --- | --- | --- | --- |
| 1 | × 0.1, +0.15 | 0.6137 | 0.5791 |
| 2 | × 0.15, +0.3 | 0.6111 | 0.5762 |

Scelta con θ fisso: la combinazione interna alla griglia con la migliore AUC sulla metà peggiore (un ottimo sul bordo della griglia è una direzione, non un valore misurato): k × 0.15, w +0.15; AUC media 0.6104 su tutto il campione (guadagno +0.034), 0.6123 sulla metà peggiore.

**Adottati** k_c e w_c del secondo passo (θ invariato).

Tasso di errore per banda di T (tutte le categorie insieme, una riga per posizione e categoria):

| Banda di T | Righe | Errori | Tasso (attuali) | Tasso (scelti) |
| --- | --- | --- | --- | --- |
| < 30 | 80 | 23 | 29% | 35% |
| 30–60 | 54 | 25 | 46% | 37% |
| 60–85 | 126 | 31 | 25% | 19% |
| >= 85 | 540 | 87 | 16% | 14% |

## Selezione delle candidate (A, L_max)

Misura: quota di posizioni in cui la mossa giocata è tra le candidate spiegate, con la migliore di Stockfish sempre tra le spiegate quanto con i valori attuali.

Un valore nuovo si adotta solo se la copertura sale di almeno 10 punti.

| Fascia | Attuali (A, L_max) | Copertura | Migliore della griglia | Copertura | Adottato |
| --- | --- | --- | --- | --- | --- |
| lt1200 | 0.6, 40 | 55% | 0.5, 40 | 55% | no |
| 1200_1600 | 0.5, 40 | 70% | 0.5, 40 | 70% | no |
| 1600_2000 | 0.3, 35 | 90% | 0.3, 35 | 90% | no |
| 2000_2400 | 0.1, 30 | 85% | 0.1, 30 | 85% | no |
| ge2400 | 0.0, 25 | 90% | 0.0, 25 | 90% | no |

## Valori adottati

Applicati a `config/thresholds.yaml: scoring` dopo questa relazione. I numeri qui sopra usano come «attuali» i
valori precedenti. Se si rilancia `chessanalyst calibrate --fit`, il confronto parte dai valori nuovi.

| Categoria | k_c prima → dopo (× 0,15) | w_c prima → dopo (+ 0,15) |
| --- | --- | --- |
| king_safety | 0,5 → 0,075 | 0,8 → 0,95 |
| pawn_structure | 0,8 → 0,12 | 0,3 → 0,45 |
| space_center | 0,8 → 0,12 | 0,3 → 0,45 |
| piece_activity | 0,8 → 0,12 | 0,4 → 0,55 |
| initiative_tempo | 0,6 → 0,09 | 0,6 → 0,75 |
| threats_dynamics | 0,5 → 0,075 | 0,8 → 0,95 |
| material | 0,5 → 0,075 | 0,7 → 0,85 |
| transition_plans | 0,8 → 0,12 | 0,5 → 0,65 |

`practical_complexity` (meta, senza linee), θ, A, B e L_max restano invariati.

Interpretazione:
- **Rischio delle linee.** Il rischio delle linee era pesato troppo poco: con k più piccoli, poche linee rischiose
  bastano ad abbassare T.
- **Parte dinamica.** Con w più grandi T dipende di più dalle linee che dalle feature statiche.
- **Direzione dei dati.** I dati spingono ancora più in là (ottimo sul bordo della griglia, k × 0,1 e w + 0,45). Con
  cento posizioni si è scelto il punto robusto interno; un campione più grande può confermare o spostare il valore.
