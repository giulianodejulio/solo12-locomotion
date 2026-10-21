# Published policy in MuJoCo

Run from the repository: `bash workspace/teleop.sh`.
The launcher requires X11 and NVIDIA Container Toolkit and prints the actual
OpenGL renderer. The training container is independent.

W/S adjust body-frame vx, A/D vy and Q/E yaw rate by 0.1 per key press.
Space requests zero velocity, R resets, Esc closes. Commands persist until
changed. Acceleration is limited to 0.5 m/s² and 1 rad/s². A dedicated GLFW
window owns the keys, so there are no standard viewer keyboard shortcuts.
Rendering is 30 FPS; control is 100 Hz with physics at 1 kHz. The console reports
simulated seconds / wall seconds (ideally 1).

The adapter loads the upstream w2 actor, observation normalization and velocity
estimator from `third_party/quadruped-rl`. Target-history ordering follows
`cpuMLP/Interface.hpp`: update previous targets before building observations.
It uses deterministic mean actions. Zero commanded velocity still runs the
policy; leg motion is possible while the body stays near rest.

The current teleop adds an explicit standing supervisor (`demo/controller.py`).
At zero applied command and low measured base speed for 0.3 seconds, targets
blend toward the nominal posture over 0.6 seconds and PD gains blend from
3/0.2 to 6/0.4. On a nonzero command the policy resumes over 0.25 seconds.
Target histories retain the targets actually applied. The original actor
weights are unchanged; teleop is now a hybrid controller, not pure policy replay.
The standing supervisor is engaged immediately at startup.

At rest over 20 seconds (first 2 seconds excluded for contact speed), mean
loaded material-point slip decreased from 8.38 to 0.626 mm/s. Base displacement
decreased from 77.4 mm to 0.0264 mm. Report: `checks/zero_slip_standing.json`.
Residual contact creep is nonzero and is not hidden by freezing simulation.

The teleop-only contact profile uses solref time constant 0.005 s instead of
the shared model default 0.02 s. It reduces soft-contact penetration without
editing shared assets or the training environment. Lighting and shadows are
configured only in this viewer. These are simulator-transfer settings, not
the original RaiSim simulator.

## Checks on 2026-10-21

`python3 -m tools.audit` tests stop, vx=0.5/-0.3/-0.5,
vy=+/-0.3, yaw=+/-0.5 and mixed [0.3,0.2,0.3], 12 seconds each,
with both estimated and ground-truth velocity inputs (18 trials).
Repeat with `--contact-timeconstant .005` for the teleop contact profile.
Both suites completed with zero falls (36 trials total).
For the teleop profile with the estimator, mean steady velocities were:

| Command | Measured corresponding axis |
| --- | --- |
| vx=0.5 | 0.485 m/s |
| vx=-0.3 | -0.303 m/s |
| vx=-0.5 | -0.483 m/s |
| vy=0.3 | 0.205 m/s |
| vy=-0.3 | -0.218 m/s |
| yaw=0.5 | 0.346 rad/s |
| yaw=-0.5 | -0.337 rad/s |

Max penetration across these tests: about 1.6 mm, versus 11.1 mm with default
contacts. A 60-second continuous sequence (`--sequence --duration 60
--contact-timeconstant .005`) completed without falling, max penetration 2.0 mm.
Reports are under `paper/checks/official_audit*.json`.

This establishes survival only for those nominal tests. Lateral and yaw tracking
remain biased, also with ground-truth velocity. Arbitrary commands, disturbances
and rough terrain have not been certified. Do not interpret the allowed input
limits (1.5/1/1) as a verified stability envelope.
