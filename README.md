# Solo12 locomotion

Locomozione Solo12 in MuJoCo: port sperimentale di un metodo RaiSim, valutazione
di policy pubblicate e demo interattiva con key teleop. Il percorso didattico
precedente resta in [rl-tutorials](https://github.com/giulianodejulio/rl-tutorials).

## Fasi e responsabilità

| Directory | Fase |
| --- | --- |
| `paper/` | Port del paper, ambiente, PPO, curriculum, checkpoint e valutazione |
| `policies/` | Inferenza dei pesi RaiSim ufficiali e normalizzazione originale |
| `demo/` | Viewer NVIDIA, key teleop, rampe, supervisore di arresto e registrazione |
| `tools/` | Diagnostica tracking/contatti, misura slip ed esportazione GIF |
| `docs/` | Esiti degli esperimenti, limiti, migrazione e uso della demo |
| `workspace/` | Dockerfile, dipendenze fissate, bootstrap e ricostruzione workspace |

Il modulo `paper` mantiene il nome originario per conservare i comandi e la
compatibilità dei checkpoint. Il training non importa la demo: contatti più
rigidi, rampe e postura di arresto appartengono solo al controllo interattivo.

## Workspace

```text
solo12_rl_ws/
├── src/
│   ├── rl-tutorials/
│   └── solo12-locomotion/
└── third_party/
    ├── solo12_mujoco/
    └── quadruped-rl/
```

`docker/` contiene solo configurazione runtime locale. La directory `.vscode/`
è opzionale. I repository esterni sono scaricati dal bootstrap nelle revisioni
registrate, senza duplicarne i pesi nella cronologia di questo progetto.

## Avvio

Seguire [workspace/README.md](workspace/README.md) per ricostruire il workspace.
Da questa repository:

```bash
bash workspace/bootstrap.sh
bash workspace/build.sh
bash workspace/run.sh
docker exec -w "$PWD" docker_solo12_rl_ws python3 -m paper.validate
bash workspace/teleop.sh
```

Il viewer richiede NVIDIA Container Toolkit e X11. W/S: vx; A/D: vy; Q/E: yaw;
Spazio: arresto; R: reset; Esc: chiudi. Il controllo è ibrido: policy ufficiale
in marcia e postura PD durante l'arresto. Vedi [docs/teleop.md](docs/teleop.md).

## Stato scientifico

La run locale `article_desktop` è stata interrotta a circa `6.73e7` transizioni
dopo ripetuti collassi. L'ultimo checkpoint completo è a `6.6e7`; la sua
valutazione nominale ha prodotto 4 cadute su 4. Non è una policy convergente.
Vedi [docs/training-assessment.md](docs/training-assessment.md).

La demo usa invece una policy già addestrata dagli autori, recuperata da
`quadruped-rl`. I risultati positivi della demo non validano il nostro training.
Il port MuJoCo non è una riproduzione esatta di RaiSim: [paper/SOURCES.md](paper/SOURCES.md).

Checkpoint, CSV, GIF e report generati restano in `paper/results/` e
`paper/checks/`, ignorati da Git. Per trasferire lo stato locale completo
inclusi questi output usare [workspace/README.md](workspace/README.md).
