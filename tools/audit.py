"""Headless tracking/contact diagnostics for published policies; no learning."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
from paper.config import load_config
from paper.env import PaperSolo12Env
from policies.official import OfficialPolicy, DEFAULT_POLICY
from demo.controller import TeleopController


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration', type=float, default=12.)
    parser.add_argument('--output', type=Path, default=Path('paper/checks/official_audit.json'))
    parser.add_argument('--contact-timeconstant', type=float)
    parser.add_argument('--sequence', action='store_true')
    parser.add_argument('--standing', action='store_true')
    args = parser.parse_args()
    config = load_config()
    config['episode_steps'] = round(args.duration/config['control_dt'])
    commands = [[0,0,0],[.5,0,0],[-.3,0,0],[-.5,0,0],
                [0,.3,0],[0,-.3,0],[0,0,.5],[0,0,-.5],[.3,.2,.3]]
    if args.standing:
        commands = [item for command in commands for item in (command,[0,0,0])]
    rows = []
    for source in (['estimator'] if args.sequence else ['estimator', 'truth']):
        env = PaperSolo12Env(config, randomize=False)
        if args.contact_timeconstant:
            env.model.geom_solref[:,0] = args.contact_timeconstant
        for command in ([commands[0]] if args.sequence else commands):
            env.reset(seed=21, options={'command':command,'rough':False})
            policy = (TeleopController(DEFAULT_POLICY, env.nominal, source) if args.standing
                      else OfficialPolicy(DEFAULT_POLICY, env.nominal, source))
            velocities, errors, depths = [], [], []
            started = time.perf_counter()
            applied = np.zeros(3)
            for k in range(config['episode_steps']):
                # Limit command acceleration, as for a joystick ramp.
                if args.sequence:
                    command = commands[min(int(k*env.control_dt/6),len(commands)-1)]
                    applied += np.clip(np.asarray(command)-applied,
                                       -np.array([.5,.5,1.])*env.control_dt,
                                       np.array([.5,.5,1.])*env.control_dt)
                else:
                    applied = np.asarray(command)*min(1., k*env.control_dt)
                env.command[:] = applied
                action, estimate = policy.predict(env, applied)
                _, _, terminated, truncated, info = env.step(action)
                velocities.append(info['velocity'])
                errors.append(np.linalg.norm(estimate-env._body_state()[1]))
                depths.extend(max(0.,-c.dist) for c in env.data.contact
                              if env.terrain_geom in (c.geom1,c.geom2))
                if terminated or truncated:
                    break
            v = np.asarray(velocities)
            row = dict(source=source,command=command,duration=(k+1)*env.control_dt,
                       fallen=info['fallen'],velocity_mean=v[len(v)//2:].mean(0).tolist(),
                       estimator_error=float(np.mean(errors)),
                       max_penetration_m=max(depths,default=0.),
                       realtime_factor=(k+1)*env.control_dt/(time.perf_counter()-started))
            rows.append(row)
            print(json.dumps(row),flush=True)
        env.close()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(rows,indent=2)+'\n')


if __name__ == '__main__':
    main()
