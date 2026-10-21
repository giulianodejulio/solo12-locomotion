# Decisione di interrompere article_desktop (2026-10-21)

Budget previsto: 3e8 transizioni; 6 worker; batch PPO 3e4.
Ultimo CSV osservato prima dell'arresto: 67260000 transizioni.
Ultima coppia completa policy/normalizzazione: 66000000.
SIGINT seguito dall'arresto del container dedicato; nessun salvataggio
aggiuntivo dei pesi in memoria è dichiarato. Tutti gli output locali conservati.

## Evidenza

| Checkpoint | Valutazione nominale |
| --- | --- |
| 1.5e7 | x02 sopravvive, x05/yaw cadono |
| 3e7 | 3/3 cadute, durate 0.39–0.46 s |
| 4.5e7 | 3/3 cadute, durate 0.46–0.48 s |
| 6e7 | 0/3 cadute, ma errori circa uguali ai comandi (quasi fermo) |
| 6.6e7 | 4/4 cadute in x02/x05/reverse/yaw; errore medio 1.803 |

L'ultima valutazione usa 5 s richiesti per comando, azione media, normalizzazione
congelata e condizioni nominali. Le durate effettive si leggono nel CSV locale
`paper/results/article_desktop/evaluations/000066000000/full/episodes.csv`.
Negli ultimi 100 buffer osservati: errore training medio 1.98, circa 584 eventi
di caduta per 3e4 transizioni e 0.27 contatti medi. Il reward non costituisce
evidenza di buona locomozione.

## Decisione e limiti

Non investire il restante budget nella stessa run senza diagnosticare
ottimizzazione e specifica dell'ambiente. L'interruzione non dimostra che il
metodo originale non funzioni. La policy ufficiale funziona nel nostro simulatore
con un adattatore dedicato, ma input/history e supervisore della demo sono
diversi dal training sperimentale. Quest'ultimo non è stato modificato per
nascondere il collasso. I risultati pre-migrazione conservano le copie dei
sorgenti e dei manifest originali nei rispettivi run directory.
