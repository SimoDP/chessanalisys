# Banco dei motivi tattici sui problemi di Lichess

Campione: 934 problemi da [https://database.lichess.org/lichess_db_puzzle.csv.zst](https://database.lichess.org/lichess_db_puzzle.csv.zst) (CC0), file `fixtures/puzzles/lichess_sample.csv`. Rigenera con `python scripts/motif_bench.py`.

**Ritrovati**: quota dei problemi con quel tema in cui il rilevatore del codice scatta su almeno una mossa della soluzione; **alla prima mossa** conta solo la prima mossa del solutore, quella che l'app commenta come mossa candidata. **Falsi allarmi**: quota dei problemi di controllo (nessuno dei temi misurati) in cui scatta comunque; è un limite superiore, perché i temi di Lichess non sono completi.

| Tema di Lichess | Rilevatore | Problemi | Ritrovati | Alla prima mossa | Punteggio < 1500 | Punteggio 1500–1999 | Punteggio >= 2000 | Falsi allarmi | Falsi allarmi alla prima mossa |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fork | fork | 127 | 98 % | 66 % | 100 % | 93 % | 100 % | 18 % | 10 % |
| pin | pin | 120 | 100 % | 67 % | 100 % | 100 % | 100 % | 28 % | 16 % |
| skewer | skewer | 100 | 74 % | 47 % | 81 % | 47 % | 71 % | 4 % | 1 % |
| discoveredAttack | discovered_attack | 156 | 99 % | 67 % | 100 % | 98 % | 100 % | 10 % | 6 % |
| discoveredCheck | discovered_check | 102 | 100 % | 49 % | 100 % | 100 % | 100 % | 0 % | 0 % |
| hangingPiece | hanging_piece | 102 | 100 % | 100 % | 100 % | 100 % | 100 % | 44 % | 7 % |
| deflection | overloaded_piece | 113 | 23 % | 18 % | 13 % | 28 % | 33 % | 10 % | 8 % |
| capturingDefender | overloaded_piece | 100 | 20 % | 15 % | 12 % | 20 % | 39 % | 10 % | 8 % |
| pin | pin_created | 120 | 38 % | 13 % | 45 % | 40 % | 29 % | 4 % | 2 % |

Problemi di controllo: 200.

## Primi problemi non ritrovati

- fork / fork: [00rHa](https://lichess.org/training/00rHa), [06eSF](https://lichess.org/training/06eSF)
- skewer / skewer: [003eP](https://lichess.org/training/003eP), [00DZe](https://lichess.org/training/00DZe), [00baa](https://lichess.org/training/00baa), [0109Y](https://lichess.org/training/0109Y), [01243](https://lichess.org/training/01243)
- discoveredAttack / discovered_attack: [009FS](https://lichess.org/training/009FS)
- deflection / overloaded_piece: [001h8](https://lichess.org/training/001h8), [002Mm](https://lichess.org/training/002Mm), [003IM](https://lichess.org/training/003IM), [0048r](https://lichess.org/training/0048r), [004LZ](https://lichess.org/training/004LZ)
- capturingDefender / overloaded_piece: [00Bp0](https://lichess.org/training/00Bp0), [00EbJ](https://lichess.org/training/00EbJ), [00SyL](https://lichess.org/training/00SyL), [01Tr9](https://lichess.org/training/01Tr9), [01XK2](https://lichess.org/training/01XK2)
- pin / pin_created: [001Hi](https://lichess.org/training/001Hi), [001kG](https://lichess.org/training/001kG), [002e8](https://lichess.org/training/002e8), [002rd](https://lichess.org/training/002rd), [003Ec](https://lichess.org/training/003Ec)
