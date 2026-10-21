"""132-value observation layout from the authors' observe()/Interface code."""
import numpy as np

HISTORY_ROWS = (0, 2, 4)
HISTORY_BUFFER_LENGTH = 6


def append_history(errors, velocities, error, velocity):
    """Age oldest-first buffers once per policy sample, not per observe call."""
    errors[:-1] = errors[1:].copy()
    velocities[:-1] = velocities[1:].copy()
    errors[-1] = error
    velocities[-1] = velocity


def history_parts(errors, velocities):
    return [part for row in HISTORY_ROWS for part in (errors[row], velocities[row])]


def compose_observation(vertical, velocity, omega, command, q, qd,
                        previous_target, preprevious_target, errors, velocities):
    return np.concatenate([vertical, velocity, omega, command, q, qd,
                           previous_target, preprevious_target,
                           *history_parts(errors, velocities)])
