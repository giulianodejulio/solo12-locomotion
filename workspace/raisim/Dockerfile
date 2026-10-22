ARG BASE_IMAGE=solo12_rl_ws:base
FROM ${BASE_IMAGE}

# Separate runtime for historical RaiSim / RaiSimGymTorch. Dependencies and
# compiler come from the workspace base; the RaiSim checkout is bind-mounted.
ENV RAISIM_ROOT=/opt/raisimLib
ENV CMAKE_PREFIX_PATH=/opt/raisimLib/raisim/linux
ENV LD_LIBRARY_PATH=/opt/raisimLib/raisim/linux/lib
WORKDIR /opt/raisimLib
