"""Check every observation component against the upstream layout and timing."""
import numpy as np
from paper.env import PaperSolo12Env
from policies.official import OfficialPolicy, DEFAULT_POLICY


def main():
    env = PaperSolo12Env(randomize=False)
    env.reset(seed=21,options={'command':[.2,-.1,.3],'rough':False})
    policy = OfficialPolicy(DEFAULT_POLICY,env.nominal,velocity_source='truth')
    # Capture the raw input before normalization/actor, independently of builder.
    def actor(normalized):
        np.testing.assert_allclose(normalized,
            np.clip((expected-policy.mean)/np.sqrt(policy.var+1e-8),-10,10),atol=1e-6)
        return np.zeros(12)
    policy.actor = actor
    errors = [np.zeros(12) for _ in range(6)]
    velocities = [np.zeros(12) for _ in range(6)]
    for step in range(10):
        q = env.data.qpos[env.qadr].copy()
        qd = env.data.qvel[env.vadr].copy()
        rotation,velocity,omega = env._body_state()
        errors = errors[1:]+[policy.target-q]
        velocities = velocities[1:]+[qd]
        previous = policy.target.copy()
        preprevious = policy.previous.copy()
        expected = np.hstack([rotation[2],velocity,omega,env.command,q,qd,
                              previous,preprevious,
                              errors[0],velocities[0],errors[2],velocities[2],
                              errors[4],velocities[4]])
        np.testing.assert_allclose(env.observation(),expected,atol=1e-6)
        policy.predict(env,env.command)
        action = np.sin(np.arange(12)+step)*.1
        policy.target = env.nominal+.3*action
        env.step(action)
        # Reading observations must not advance the history.
        before = env.velocity_history.copy()
        env.observation()
        env.observation()
        np.testing.assert_array_equal(before,env.velocity_history)
    # Numbered samples catch reversed buffers and accidental current-qd reuse.
    env.error_history[:] = np.arange(6)[:,None]+100
    env.velocity_history[:] = np.arange(6)[:,None]+200
    env.data.qvel[env.vadr] = 999
    obs = env.observation()
    np.testing.assert_allclose(obs[24:36],999)
    for offset,index in [(60,0),(84,2),(108,4)]:
        np.testing.assert_allclose(obs[offset:offset+12],100+index)
        np.testing.assert_allclose(obs[offset+12:offset+24],200+index)
    print('All 132 elements, history ages, adapter parity and repeated reads: passed')


if __name__=='__main__':
    main()
