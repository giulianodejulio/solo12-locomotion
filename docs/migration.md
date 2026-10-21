# Migrazione dal percorso didattico (2026-10-21)

Origine: `rl-tutorials` commit 80f4795 e aggiunte locali della demo.
Il percorso didattico e gli esperimenti preliminari `solo12/` restano in quella
repository. `paper/` e `workspace/` sono stati trasferiti qui con risultati,
checkpoint e registrazioni locali. La cronologia remota non è stata riscritta.

## Nuovi comandi

| Prima | Adesso, da src/solo12-locomotion |
| --- | --- |
| paper.train / evaluate / validate / plot | invariati |
| paper.evaluate_official | policies.official |
| paper.teleop_official | demo.teleop |
| paper.record_teleop | demo.record |
| paper.audit_official | tools.audit |
| paper.check_zero_slip | tools.check_zero_slip |
| paper.split_teleop_gifs | tools.export_gifs |

Le modifiche all'ambiente di training non sono parte di questa migrazione:
`paper/env.py` e `paper/config.py` mantengono i digest necessari a risolvere
i checkpoint esistenti. Le copie `source/` nei risultati restano intatte,
anche quando riportano vecchi percorsi assoluti.

## Backup e dipendenze

Il backup dei risultati del desktop è in
`docker/backups/solo12-results-20261021.tar.gz` (locale, non pubblicato).
La copia precauzionale precedente alla riorganizzazione è in
`/tmp/solo12-before-reorganization-20261021.tar.gz` (temporanea).
Modelli e pesi esterni sono identificati da commit e SHA256 nei manifest
di `workspace/`. Il bootstrap non sostituisce checkout modificati.

Gli asset condivisi e i pesi ufficiali non sono duplicati nella nuova repo.
La copia del codice di riferimento soloRL sotto `paper/reference/` conserva
provenienza e attribuzione; vale quanto documentato in `paper/SOURCES.md`.
Il repository quadruped-rl è distribuito upstream con BSD-2-Clause.
