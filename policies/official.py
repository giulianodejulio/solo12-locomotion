"""Evaluate an upstream RaiSim-trained Solo12 policy in the MuJoCo port.

This is a zero-shot simulator-transfer diagnostic.  It reconstructs the
deployment observation used by paleziart/quadruped-rl, including its six-slot
history sampled at indices 0, 2 and 4 and its learned base-velocity estimator.
It never trains or updates the published networks.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from paper.config import load_config
from paper.env import PaperSolo12Env
from paper.evaluate import render_trace


WORKSPACE = Path(__file__).resolve().parents[3]
UPSTREAM = WORKSPACE/'third_party'/'quadruped-rl'
DEFAULT_POLICY = UPSTREAM/'tmp_checkpoints'/'sym_pose'/'energy'/'6cm'/'w2'
STATE_ESTIMATOR = (UPSTREAM/'tmp_checkpoints'/'state_estimation'/
                   'symmetric_state_estimator.npy')


class MLP:
    def __init__(self, dimensions):
        self.weights = [np.empty((b, a), np.float32) for a, b in zip(dimensions, dimensions[1:])]
        self.biases = [np.empty(b, np.float32) for b in dimensions[1:]]

    def load(self, path):
        state = np.load(path, allow_pickle=True).item()
        for i, (weight, bias) in enumerate(zip(self.weights, self.biases)):
            weight[:] = state[f'architecture.{2*i}.weight']
            bias[:] = state[f'architecture.{2*i}.bias']

    def __call__(self, value):
        for weight, bias in zip(self.weights[:-1], self.biases[:-1]):
            value = np.where((value := weight@value+bias) > 0, value, 1e-2*value)
        return self.weights[-1]@value+self.biases[-1]


class OfficialPolicy:
    def __init__(self, directory, nominal, velocity_source='estimator'):
        self.velocity_source = velocity_source
        directory = Path(directory)
        self.actor = MLP([132, 256, 128, 32, 12])
        self.actor.load(directory/'full_2000.npy')
        self.estimator = MLP([123, 256, 128, 3])
        self.estimator.load(STATE_ESTIMATOR)
        self.mean = np.loadtxt(directory/'mean2000.csv', dtype=np.float32)
        self.var = np.loadtxt(directory/'var2000.csv', dtype=np.float32)
        self.nominal = np.asarray(nominal).copy()
        self.errors = np.zeros((6, 12))
        self.velocities = np.zeros((6, 12))
        self.target = self.nominal.copy()
        self.previous = self.nominal.copy()
        self.preprevious = self.nominal.copy()

    def predict(self, env, command):
        q, qd = env.data.qpos[env.qadr].copy(), env.data.qvel[env.vadr].copy()
        rotation, true_velocity, omega = env._body_state()
        self.errors[:-1], self.errors[-1] = self.errors[1:], self.target-q
        self.velocities[:-1], self.velocities[-1] = self.velocities[1:], qd
        # Upstream update_history updates both targets BEFORE constructing obs.
        self.preprevious, self.previous = self.previous.copy(), self.target.copy()
        common = np.concatenate([
            rotation[2], q, qd, self.previous, self.preprevious,
            self.errors[0], self.velocities[0], self.errors[2], self.velocities[2],
            self.errors[4], self.velocities[4]])
        estimated_velocity = self.estimator(common)
        observation = np.concatenate([
            rotation[2], true_velocity if self.velocity_source == 'truth' else estimated_velocity,
            omega, command, q, qd,
            self.previous, self.preprevious,
            self.errors[0], self.velocities[0], self.errors[2], self.velocities[2],
            self.errors[4], self.velocities[4]])
        normalized = np.clip((observation-self.mean)/np.sqrt(self.var+1e-8), -10, 10)
        action = np.clip(self.actor(normalized), -np.pi, np.pi)
        self.target = self.nominal + .3*action
        return action, estimated_velocity


def run(policy_dir, output, command, duration):
    config = load_config()
    config['episode_steps'] = round(duration/config['control_dt'])
    config['continuation_probability'] = 0.
    env = PaperSolo12Env(config, randomize=False, reward_scale=1., noise_scale=0.)
    env.reset(seed=20261021, options={'command': command, 'hard_reset': True, 'rough': False})
    policy = OfficialPolicy(policy_dir, env.nominal)
    qpos, qvel = [env.data.qpos.copy()], [env.data.qvel.copy()]
    targets, contacts, velocities, estimates, records = [], [], [], [], []
    start = env.data.qpos[:3].copy()
    for _ in range(config['episode_steps']):
        action, estimate = policy.predict(env, np.asarray(command))
        _, _, terminated, truncated, info = env.step(action)
        qpos.append(env.data.qpos.copy())
        qvel.append(env.data.qvel.copy())
        targets.append(env.last_target.copy())
        contacts.append(env._contacts()[0])
        velocities.append(info['velocity'])
        estimates.append(estimate)
        records.append(info)
        if terminated or truncated:
            break
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    trajectory = dict(qpos=np.asarray(qpos), qvel=np.asarray(qvel), targets=np.asarray(targets),
                      contacts=np.asarray(contacts), velocity=np.asarray(velocities),
                      estimated_velocity=np.asarray(estimates), command=np.asarray(command),
                      control_dt=env.control_dt, terrain=env.heights.astype(np.float32),
                      reward_full=np.asarray([r['full_reward'] for r in records]),
                      kp=env.kp, kd=env.kd, seed=20261021)
    np.savez_compressed(output/'trajectory.npz', **trajectory)
    render_trace(env, trajectory, output/'official_raisim_w2_mujoco.gif', 'upstream mean')
    measured = np.asarray(velocities)
    metrics = dict(policy=str(policy_dir), simulator='MuJoCo', command=list(command),
                   requested_duration=duration, duration=len(records)*env.control_dt,
                   fallen=bool(records[-1]['fallen']),
                   displacement=(env.data.qpos[:3]-start).tolist(),
                   final_height=float(records[-1]['height']),
                   velocity_mean=measured.mean(axis=0).tolist(),
                   velocity_error_mean=float(np.linalg.norm(measured-np.asarray(command), axis=1).mean()),
                   slip_mean=float(np.mean([r['slip'] for r in records])))
    (output/'metrics.json').write_text(json.dumps(metrics, indent=2)+'\n')
    print(json.dumps(metrics, indent=2))
    print(f'Saved: {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy-dir', type=Path, default=DEFAULT_POLICY)
    parser.add_argument('--output', type=Path,
                        default=Path(__file__).parents[1]/'paper'/'checks'/'official_raisim_policy_mujoco')
    parser.add_argument('--command', type=float, nargs=3, default=[.5, 0., 0.])
    parser.add_argument('--duration', type=float, default=8.)
    args = parser.parse_args()
    if args.duration <= 0:
        parser.error('duration must be positive')
    run(args.policy_dir, args.output, args.command, args.duration)


if __name__ == '__main__':
    main()
