"""Explicit locomotion/standing supervisor for interactive simulation."""
import numpy as np
from policies.official import OfficialPolicy


class TeleopController:
    def __init__(self, directory, nominal, velocity_source='estimator'):
        self.policy = OfficialPolicy(directory, nominal, velocity_source)
        self.stand_weight = 1.
        self.quiet_time = 0.

    def predict(self, env, command):
        action, estimate = self.policy.predict(env, command)
        _, velocity, omega = env._body_state()
        zero = np.max(np.abs(command)) < 1e-6
        quiet = np.linalg.norm(velocity[:2]) < .10 and abs(omega[2]) < .15
        self.quiet_time = self.quiet_time+env.control_dt if zero and quiet else 0.
        desired = float(zero and (self.quiet_time >= .3 or self.stand_weight > .99))
        self.stand_weight += np.clip(desired-self.stand_weight,
                                     -env.control_dt/.25, env.control_dt/.6)
        action = (1-self.stand_weight)*action
        env.kp = 3.+3.*self.stand_weight
        env.kd = .2+.2*self.stand_weight
        # Histories must describe the target actually sent to the motors.
        self.policy.target = env.nominal+.3*action
        return action, estimate
