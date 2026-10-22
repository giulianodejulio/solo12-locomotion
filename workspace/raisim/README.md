# RaiSim historical runtime and academic activation

Candidate runtime: RaiSim v1.1.7, commit
`afef6dc53a1a2c72fe824eeb32fa6930b50d4703`. This includes RaiSimGymTorch
from the paper's period. The authors do not publish their precise simulator
revision; this is a candidate, not an assertion of their exact binary version.
The full SoloRL trainer has not yet been compiled or validated.

From the repository, after building the normal workspace base image:

```bash
bash workspace/raisim/setup.sh
python3 workspace/raisim/machine_id.py --verify-restart
```

Image `solo12_raisim_ws:base`; persistent container `docker_solo12_raisim_ws`.
The RaiSim checkout lives in `third_party/raisimLib` and is mounted read-only.
This runtime uses CPU and needs no NVIDIA hardware for license activation.
It does not start learning or alter the MuJoCo runtime.

The probe loads the shipped CPython 3.10 bindings and constructs a World.
Without a key, RaiSim intentionally exits with an activation diagnostic,
including the genuine 128-character machine ID. The helper extracts that ID
and verifies it before/after restarting the same container. Runtime identity
uses a fixed container hostname/MAC; recheck the ID after moving PCs or changing
Docker/network configuration. Do not substitute Linux `/etc/machine-id` for
the ID printed by RaiSim.

The ID and its check report are saved under workspace `docker/raisim/`, outside
the Git repository. Fill the official form linked from
<https://raisim.com/sections/License.html> with this ID, institution, academic
email, name and license type Academic. In any available notes, specify Linux
Docker and RaiSim 1.1.7; ask licensing support about legacy-version compatibility
if necessary. No form is submitted automatically.

Save the issued key on the host as:

```text
<workspace>/docker/raisim/license/activation.raisim
```

The directory is already mounted read-only as the container user's `.raisim`.
Do not commit or bake the license into an image. On receipt, test activation:

```bash
docker exec docker_solo12_raisim_ws python3 -c \
 'import sys; sys.path.insert(0,"/opt/raisimLib/raisim/linux/lib"); import raisimpy; w=raisimpy.World(); print("Activation OK")'
```

The machine-ID helper is for the unlicensed stage; after activation succeeds,
World no longer prints the missing-license diagnostic.
