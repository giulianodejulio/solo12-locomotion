"""Measure material contact-point slip at zero command, without rendering."""
import json
import numpy as np
import mujoco
from paper.config import load_config
from paper.env import PaperSolo12Env
from policies.official import OfficialPolicy, DEFAULT_POLICY
from demo.controller import TeleopController


def main():
    results = []
    for source in ['estimator', 'standing']:
        env = PaperSolo12Env(load_config(), randomize=False)
        env.model.geom_solref[:,0] = .005
        env.reset(seed=21, options={'command':[0,0,0], 'rough':False})
        policy = (TeleopController(DEFAULT_POLICY, env.nominal) if source == 'standing'
                  else OfficialPolicy(DEFAULT_POLICY, env.nominal, source))
        start = env.data.qpos[:2].copy()
        speeds, base, feet, forces = [], [], [], []
        for k in range(2000):
            action, _ = policy.predict(env, np.zeros(3))
            # Direct substeps avoid the training environment's one-second cuts.
            target = env.nominal+.3*action
            for _ in range(env.substeps):
                env._motor_step(target)
            mujoco.mj_forward(env.model, env.data)
            if k < 200:
                continue
            base.append(np.linalg.norm(env._body_state()[1][:2]))
            feet.append(env.data.xpos[env.feet].copy())
            for i, contact in enumerate(env.data.contact):
                if env.terrain_geom not in (contact.geom1,contact.geom2) or contact.dist>0:
                    continue
                other = contact.geom2 if contact.geom1==env.terrain_geom else contact.geom1
                body = env.model.geom_bodyid[other]
                if body not in env.lower:
                    continue
                force = np.zeros(6)
                mujoco.mj_contactForce(env.model,env.data,i,force)
                if force[0] < 1.:
                    continue
                jac = np.zeros((3,env.model.nv))
                mujoco.mj_jac(env.model,env.data,jac,None,contact.pos,body)
                speeds.append(float(np.linalg.norm((jac@env.data.qvel)[:2])))
                forces.append(float(force[0]))
        row = dict(source=source,duration_s=20,settling_excluded_s=2,
                   loaded_contact_threshold_N=1.,
                   contact_speed_mean_m_s=float(np.mean(speeds)),
                   contact_speed_p95_m_s=float(np.percentile(speeds,95)),
                   fraction_contacts_over_1cm_s=float(np.mean(np.asarray(speeds)>.01)),
                   base_speed_mean_m_s=float(np.mean(base)),
                   base_displacement_m=(env.data.qpos[:2]-start).tolist(),
                   foot_frame_range_xyz_m=np.ptp(np.asarray(feet),axis=0).tolist())
        print(json.dumps(row),flush=True)
        results.append(row)
    from pathlib import Path
    Path('paper/checks/zero_slip_standing.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':
    main()
