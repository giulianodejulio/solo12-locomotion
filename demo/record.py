"""Record the teleop controller through its complete command range."""
from pathlib import Path
import json
import mujoco
import numpy as np
from PIL import Image, ImageDraw
from paper.config import load_config
from paper.env import PaperSolo12Env
from policies.official import DEFAULT_POLICY
from demo.controller import TeleopController
from demo.teleop import configure_visual_style


def main():
    output = Path('paper/checks/teleop_demo_full_velocity_sequence.gif')
    output.parent.mkdir(parents=True,exist_ok=True)
    config = load_config()
    config['episode_steps'] = 100000
    env = PaperSolo12Env(config,randomize=False)
    env.model.geom_solref[:,0] = .005
    configure_visual_style(env)
    env.reset(seed=21,options={'command':[0,0,0],'rough':False})
    controller = TeleopController(DEFAULT_POLICY,env.nominal)
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_TRACKING
    camera.trackbodyid = env.base
    camera.distance,camera.azimuth,camera.elevation = .95,120,-23
    frames, events = [], []
    applied = np.zeros(3)
    segments = [(0,0.,2.,'START')]
    for axis,limit in [(0,1.5),(1,1.),(2,1.)]:
        for sign in [1,-1]:
            maximum = sign*limit
            ramp = limit/(.25 if axis<2 else .4)
            segments.extend([(axis,maximum,ramp,'RAMP'),
                             (axis,maximum,1.,'MAX'),
                             (axis,0.,6.,'SPACE / STOP')])
    previous_requested = np.zeros(3)
    k = 0
    with mujoco.Renderer(env.model,height=360,width=540) as renderer:
        for axis,maximum,duration,label in segments:
            for step in range(round(duration/env.control_dt)):
                requested = np.zeros(3)
                if label=='RAMP':
                    requested[axis] = maximum*min(1.,(step+1)*env.control_dt/duration)
                elif label=='MAX':
                    requested[axis] = maximum
                applied += np.clip(requested-applied,-np.array([.5,.5,1.])*env.control_dt,
                                   np.array([.5,.5,1.])*env.control_dt)
                env.command[:] = applied
                action,_ = controller.predict(env,applied)
                _,_,fallen,_,info = env.step(action)
                if k%5==0:
                    renderer.update_scene(env.data,camera=camera)
                    renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = 1
                    renderer.scene.flags[mujoco.mjtRndFlag.mjRND_REFLECTION] = 1
                    renderer.scene.flags[mujoco.mjtRndFlag.mjRND_FOG] = 1
                    frame = Image.fromarray(renderer.render())
                    draw = ImageDraw.Draw(frame)
                    draw.rectangle((0,0,540,49),fill=(15,28,40))
                    draw.text((8,4),f'Solo12 MuJoCo | {label} | t={k*.01:.1f}s',fill='white')
                    draw.text((8,19),'command vx=%+.2f vy=%+.2f wz=%+.2f'%tuple(applied),fill='white')
                    draw.text((8,34),'actual  vx=%+.2f vy=%+.2f wz=%+.2f'%tuple(info['velocity']),fill='white')
                    if fallen:
                        draw.text((350,4),'FALL / AUTO RESET',fill='red')
                    frames.append(frame.quantize(colors=128))
                if fallen:
                    events.append(dict(time=k*.01,command=applied.tolist(),event='fall_reset'))
                    env.reset(options={'command':applied,'hard_reset':True,'rough':False})
                    controller = TeleopController(DEFAULT_POLICY,env.nominal)
                k+=1
            print(label,axis,maximum,'time',k*.01,flush=True)
    frames[0].save(output,save_all=True,append_images=frames[1:],duration=50,loop=0,optimize=False)
    output.with_suffix('.json').write_text(json.dumps(dict(duration=k*.01,events=events),indent=2))
    print(output,flush=True)


if __name__=='__main__':
    main()
