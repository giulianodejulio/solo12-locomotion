# Ricostruzione solo12_rl_ws

Questa directory è l'unica fonte del Dockerfile e degli script di setup.
Prerequisiti host: Git, Python 3, Docker Engine accessibile dall'utente.
Per il viewer: driver NVIDIA, NVIDIA Container Toolkit e sessione X11
(`DISPLAY`, `XAUTHORITY`). Training CPU e validazione OSMesa non richiedono GPU.

## Nuovo PC

```bash
git clone https://github.com/giulianodejulio/solo12-locomotion.git \
  "$HOME/workspaces/solo12_rl_ws/src/solo12-locomotion"
cd "$HOME/workspaces/solo12_rl_ws/src/solo12-locomotion"
bash workspace/recreate.sh "$HOME/workspaces/solo12_rl_ws"
```

`recreate.sh` ricostruisce il checkout corrente, scarica le revisioni registrate
di `rl-tutorials` e `quadruped-rl`, prepara `solo12_mujoco`, costruisce l'immagine,
avvia il container e lancia `paper.validate`. Se eseguito da una copia altrove,
crea il checkout corrente nel target. Non sovrascrive checkout esistenti,
non resetta modifiche e non avvia training.

Revisioni: `repositories.json`. Asset XML/OBJ/STL: `model/manifest.json`.
Il bootstrap preserva `solo12_gen.xml` identico a quello degli esperimenti e
rifiuta modelli o revisioni differenti anziché sovrascriverli.

## Comandi separati

```bash
bash workspace/bootstrap.sh
bash workspace/build.sh
bash workspace/run.sh
docker exec -w "$PWD" docker_solo12_rl_ws python3 -m paper.validate
bash workspace/teleop.sh
```

Default: immagine `solo12_rl_ws:base`, container `docker_solo12_rl_ws`.
`SOLO12_IMAGE` e `SOLO12_CONTAINER` permettono nomi alternativi nei primi tre
script. `teleop.sh` usa l'immagine standard e il container temporaneo
`docker_solo12_teleop`; chiudere il viewer precedente prima di riavviarlo.
Il container persistente monta solo il workspace senza privilegi o rete host.
Il viewer aggiunge GPU, socket X11 e cookie Xauthority in sola lettura.

## Riproducibilità e stato locale

Dockerfile: Ubuntu 22.04, Python 3.10, Torch 2.2.2 CPU, NumPy 1.26.4,
SB3 2.3.2, Gymnasium 0.29.1, MuJoCo 3.14.0. `requirements.lock.txt` fissa
lo stack Python osservato sul desktop, inclusi GLFW e PyOpenGL. Pinocchio
serve solo al vecchio test PyBullet, non alla demo MuJoCo.

Il setup ricrea layout, codice, asset, policy ufficiali e ambiente applicativo.
Non include risultati locali ignorati da Git o driver host. Ubuntu/apt e gli
strumenti pip non sono snapshot immutabili: per identità binaria trasferire
anche l'immagine verificata tramite `docker save`/`docker load`.

```bash
docker save -o /percorso/esterno/solo12-image.tar solo12_rl_ws:base
docker load -i /percorso/esterno/solo12-image.tar
```

Per trasferire checkpoint, CSV, GIF e diagnostiche locali:

```bash
bash workspace/backup-results.sh /percorso/esterno/solo12-results.tar.gz
# Dopo aver ricostruito il workspace, nella nuova repo:
tar -xzf /percorso/esterno/solo12-results.tar.gz -C "$PWD"
```

Estrarre solo in una destinazione nuova o dopo avere confrontato gli output
esistenti. Il backup non contiene credenziali o licenze. Gli output didattici
di `rl-tutorials/results/`, se presenti, vanno trasferiti separatamente.

## Esperimenti

Training: `python3 -m paper.train`; valutazione: `paper.evaluate`;
plot: `paper.plot`; validazione senza training: `paper.validate`.
La run `article_desktop` è stata fermata: non riavviarla automaticamente.
Consultare `docs/training-assessment.md` prima di investire altro budget.

Policy esterna: `python3 -m policies.official`.
Diagnostica: `python3 -m tools.audit`, `python3 -m tools.check_zero_slip`.
Registrazione: `python3 -m demo.record`; GIF: `python3 -m tools.export_gifs`.
Rendering offline GPU: container con `--gpus all`,
`NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute`, `MUJOCO_GL=egl`;
OSMesa è il fallback CPU. Usare `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`.
