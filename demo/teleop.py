"""Keyboard teleoperation of the upstream RaiSim policy in MuJoCo.

Keys: W/S = +/-vx, A/D = +/-vy, Q/E = +/-yaw rate, Space = stop,
R = reset, H = print help, Esc = close the viewer.
"""
import argparse
import threading
import time

import mujoco
import mujoco.viewer
import glfw
from OpenGL.GL import (glGetString, GL_RENDERER, GL_VERSION, glGetFloatv,
                       glBindTexture, glTexParameterf, GL_TEXTURE_2D)
import numpy as np

from paper.config import load_config
from paper.env import PaperSolo12Env
from policies.official import DEFAULT_POLICY, OfficialPolicy
from demo.controller import TeleopController


HELP = """Keyboard teleop
  W / S     increase / decrease forward velocity vx
  A / D     increase left / right velocity vy
  Q / E     increase left / right yaw rate wz
  Space     set all commands to zero
  R         reset the robot and policy history
  H         print this help
  Esc       close the viewer
"""


class TeleopState:
    def __init__(self, linear_step, yaw_step):
        self.command = np.zeros(3)
        self.linear_step = linear_step
        self.yaw_step = yaw_step
        self.reset_requested = False
        self.lock = threading.Lock()

    def key(self, keycode):
        key = chr(keycode).upper() if 0 <= keycode < 256 else ''
        with self.lock:
            if key == 'W':
                self.command[0] += self.linear_step
            elif key == 'S':
                self.command[0] -= self.linear_step
            elif key == 'A':
                self.command[1] += self.linear_step
            elif key == 'D':
                self.command[1] -= self.linear_step
            elif key == 'Q':
                self.command[2] += self.yaw_step
            elif key == 'E':
                self.command[2] -= self.yaw_step
            elif keycode == 32:
                self.command[:] = 0
            elif key == 'R':
                self.reset_requested = True
            elif key == 'H':
                print(HELP, flush=True)
            self.command[:] = np.clip(self.command, [-1.5, -1., -1.], [1.5, 1., 1.])

    def snapshot(self):
        with self.lock:
            command = self.command.copy()
            reset = self.reset_requested
            self.reset_requested = False
        return command, reset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy-dir', default=DEFAULT_POLICY)
    parser.add_argument('--linear-step', type=float, default=.1)
    parser.add_argument('--yaw-step', type=float, default=.1)
    parser.add_argument('--velocity-source', choices=['estimator','truth'], default='estimator')
    args = parser.parse_args()
    if args.linear_step <= 0 or args.yaw_step <= 0:
        parser.error('command increments must be positive')

    config = load_config()
    config['episode_steps'] = 100_000_000
    config['continuation_probability'] = 0.
    env = PaperSolo12Env(config, randomize=False, reward_scale=1., noise_scale=0.)
    # Teleop transfer profile: reduce visible soft-contact penetration.
    # This only changes this process's in-memory model.
    env.model.geom_solref[:, 0] = .005
    configure_visual_style(env)
    state = TeleopState(args.linear_step, args.yaw_step)

    def reset():
        command, _ = state.snapshot()
        env.reset(options={'command': command, 'hard_reset': True, 'rough': False})
        return TeleopController(args.policy_dir, env.nominal, args.velocity_source)

    policy = reset()
    wall_start, sim_start = time.monotonic(), env.data.time
    next_report = wall_start+5
    print(HELP, flush=True)
    with KeyboardViewer(env.model, env.data, state.key) as viewer:
        viewer.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        viewer.cam.trackbodyid = env.base
        viewer.cam.distance, viewer.cam.azimuth, viewer.cam.elevation = .95, 120, -23
        applied = np.zeros(3)
        deadline = time.monotonic()
        while viewer.is_running():
            started = time.monotonic()
            command, reset_requested = state.snapshot()
            if reset_requested:
                policy = reset()
                applied[:] = 0
                wall_start, sim_start = time.monotonic(), env.data.time
                command, _ = state.snapshot()
            applied += np.clip(command-applied, -np.array([.5,.5,1.])*env.control_dt,
                               np.array([.5,.5,1.])*env.control_dt)
            env.command[:] = applied
            action, estimate = policy.predict(env, applied)
            _, _, terminated, _, info = env.step(action)
            measured = info['velocity']
            viewer.set_texts((
                mujoco.mjtGridPos.mjGRID_TOPLEFT,
                mujoco.mjtFontScale.mjFONTSCALE_100,
                'Official RaiSim policy / MuJoCo',
                f'command  vx={command[0]:+.2f}  vy={command[1]:+.2f}  wz={command[2]:+.2f}\n'
                f'applied  vx={applied[0]:+.2f}  vy={applied[1]:+.2f}  wz={applied[2]:+.2f}\n'
                f'measured vx={measured[0]:+.2f}  vy={measured[1]:+.2f}  wz={measured[2]:+.2f}\n'
                f'estimate vx={estimate[0]:+.2f}  vy={estimate[1]:+.2f}  vz={estimate[2]:+.2f}\n'
                f'standing blend={policy.stand_weight:.2f}\n'
                'W/S vx | A/D vy | Q/E wz | Space stop | R reset',
            ))
            viewer.sync()
            now = time.monotonic()
            if now >= next_report:
                print(f'Realtime factor={(env.data.time-sim_start)/max(now-wall_start,1e-6):.3f}',flush=True)
                next_report = now+5
            if terminated:
                print('Fall/contact detected: automatic reset.', flush=True)
                with state.lock:
                    state.command[:] = 0
                applied[:] = 0
                policy = reset()
                wall_start, sim_start = time.monotonic(), env.data.time
            deadline += env.control_dt
            remaining = deadline-time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
            elif remaining < -.1:
                # Do not run a burst of stale controls after dragging/minimizing.
                deadline = time.monotonic()


def configure_visual_style(env):
    """Render the original checker plane while retaining heightfield contacts."""
    model = env.model
    model.geom_rgba[env.terrain_geom, 3] = 0
    model.geom_rgba[env.floor] = [1, 1, 1, 1]
    material = model.geom_matid[env.floor]
    if material >= 0:
        model.mat_reflectance[material] = .35
        model.mat_shininess[material] = .7
        model.mat_specular[material] = .5
        model.mat_texrepeat[material] = [5, 5]
    model.vis.headlight.active = 1
    model.vis.headlight.ambient[:] = .35
    model.vis.headlight.diffuse[:] = .7
    model.vis.headlight.specular[:] = .15
    model.vis.quality.shadowsize = 2048
    model.vis.rgba.haze[:] = [.15, .25, .35, 1]
    # These distances are scaled by model.stat.extent in MuJoCo.
    # Fade distant checker cells before they become subpixel patterns.
    model.vis.map.fogstart = 2.5/model.stat.extent
    model.vis.map.fogend = 8./model.stat.extent
    model.vis.map.znear = .02/model.stat.extent
    model.vis.map.zfar = 30./model.stat.extent


class KeyboardViewer:
    """Single-threaded renderer with exclusive teleop keys, no UI shortcuts."""
    def __init__(self, model, data, callback):
        if not glfw.init():
            raise RuntimeError('GLFW initialization failed')
        glfw.window_hint(glfw.SAMPLES, 4)
        self.window = glfw.create_window(960, 640, 'Solo12 / official policy teleop', None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError('Cannot create OpenGL window')
        glfw.make_context_current(self.window)
        glfw.swap_interval(0)
        print('OpenGL renderer:', glGetString(GL_RENDERER).decode(), flush=True)
        print('OpenGL version:', glGetString(GL_VERSION).decode(), flush=True)
        def key(window, code, scancode, action, mods):
            if action == glfw.PRESS:
                if code == glfw.KEY_ESCAPE:
                    glfw.set_window_should_close(window, True)
                else:
                    callback(code)
        glfw.set_key_callback(self.window, key)
        self.model, self.data = model, data
        self.scene = mujoco.MjvScene(model, maxgeom=10000)
        self.context = mujoco.MjrContext(model, mujoco.mjtFontScale.mjFONTSCALE_150)
        # GL_EXT_texture_filter_anisotropic: oblique floor texture minification.
        # NVIDIA supports this; gracefully retain mipmaps on other renderers.
        if glfw.extension_supported('GL_EXT_texture_filter_anisotropic'):
            anisotropy = min(16., float(glGetFloatv(0x84FF)))
            for index, texture in enumerate(self.context.texture[:self.context.ntexture]):
                if model.tex_type[index] != mujoco.mjtTexture.mjTEXTURE_2D:
                    continue
                glBindTexture(GL_TEXTURE_2D, int(texture))
                glTexParameterf(GL_TEXTURE_2D, 0x84FE, anisotropy)
            glBindTexture(GL_TEXTURE_2D, 0)
        self.cam = mujoco.MjvCamera()
        self.option = mujoco.MjvOption()
        self.text = ''
        self.next_frame = 0.

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.context.free()
        self.scene.free()
        glfw.destroy_window(self.window)
        glfw.terminate()

    def is_running(self):
        return not glfw.window_should_close(self.window)

    def set_texts(self, text):
        self.text = text[3]

    def sync(self):
        glfw.poll_events()
        now = time.monotonic()
        if now < self.next_frame:
            return
        self.next_frame = now+1/30
        width, height = glfw.get_framebuffer_size(self.window)
        if width <= 0 or height <= 0:
            return
        mujoco.mjv_updateScene(self.model, self.data, self.option, None, self.cam,
                              mujoco.mjtCatBit.mjCAT_ALL, self.scene)
        self.scene.flags[mujoco.mjtRndFlag.mjRND_WIREFRAME] = 0
        self.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = 1
        self.scene.flags[mujoco.mjtRndFlag.mjRND_REFLECTION] = 1
        self.scene.flags[mujoco.mjtRndFlag.mjRND_FOG] = 1
        viewport = mujoco.MjrRect(0,0,width,height)
        mujoco.mjr_render(viewport, self.scene, self.context)
        mujoco.mjr_overlay(mujoco.mjtFont.mjFONT_NORMAL, mujoco.mjtGridPos.mjGRID_TOPLEFT,
                           viewport, self.text, '', self.context)
        glfw.swap_buffers(self.window)


if __name__ == '__main__':
    main()
