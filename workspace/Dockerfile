FROM ubuntu:22.04@sha256:0a9887931b0e38af2e3487ed39e29436b0535c4f3f52e57745baaf79d1898956

# docker_build script args
ARG USERNAME=rl
ARG USERID=1000
ARG GROUPID=1000
ARG WORKSPACE=/home/rl/workspaces/solo12_rl_ws
ARG WORKSPACE_NAME=solo12_rl_ws

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Rome
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y --no-install-recommends \
  sudo \
  ssh && \
  rm -rf /var/lib/apt/lists/* && \
  apt-get clean

RUN sed -i /etc/sudoers -re 's/^%sudo.*/%sudo ALL=(ALL:ALL) NOPASSWD: ALL/g'

RUN groupadd -g ${GROUPID} ${USERNAME} && \
    useradd ${USERNAME} --create-home --uid ${USERID} --gid ${GROUPID} --shell=/bin/bash && \
    adduser ${USERNAME} sudo && \
    adduser ${USERNAME} video && \
    adduser ${USERNAME} dialout

# System utilities, C++ build chain, robot model helpers, plotting, and OpenGL/X11 libraries commonly needed by MuJoCo and lightweight viewers.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    curl \
    gdb \
    git \
    git-lfs \
    ipython3 \
    lsb-release \
    nano \
    ninja-build \
    pkg-config \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-tk \
    python3-venv \
    python3-wheel \
    texlive-latex-extra \
    texlive-fonts-recommended \
    cm-super \
    dvipng \
    tree \
    unzip \
    wget \
    libeigen3-dev \
    libyaml-cpp-dev \
    libboost-all-dev \
    libgl1-mesa-dev \
    libgl1-mesa-glx \
    libglu1-mesa \
    libglu1-mesa-dev \
    libosmesa6 \
    libegl1 \
    libglfw3 \
    libglfw3-dev \
    libglew-dev \
    libx11-6 \
    libx11-dev \
    libxext6 \
    libxext-dev \
    libxrender1 \
    libsm6 \
    libglib2.0-0 \
    libomp-dev \
    libsdl2-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN python3 -m pip install --upgrade pip setuptools wheel

ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN python3 -m pip install "torch==2.2.2" --index-url ${TORCH_INDEX_URL}

# Lock the Python stack to the versions verified on the desktop. No project
# results, credentials or third-party repositories enter the build context.
COPY requirements.lock.txt /opt/solo12-requirements.lock.txt
RUN python3 -m pip install -r /opt/solo12-requirements.lock.txt

RUN git lfs install --system

USER ${USERNAME}

RUN touch ~/.sudo_as_admin_successful

ENV SOLO12_RL_WS=${WORKSPACE}
ENV MUJOCO_GL=osmesa
WORKDIR ${WORKSPACE}

RUN mkdir -p ${WORKSPACE}/src ${WORKSPACE}/third_party

RUN echo "export PS1='\${debian_chroot:+(\$debian_chroot)}\\[\\033[01;33m\\]\\u\\[\\033[01;33m\\]@\\[\\033[01;33m\\]docker_${WORKSPACE_NAME}\\[\\033[00m\\]:\\[\\033[01;34m\\]\\w\\[\\033[00m\\]\\$ '" >> ~/.bashrc
RUN echo "source ${WORKSPACE}/docker/params.env" >> ~/.bashrc
RUN echo "export PYTHONPATH=${WORKSPACE}/src:\$PYTHONPATH" >> ~/.bashrc
RUN echo "export SOLO12_RL_WS=${WORKSPACE}" >> ~/.bashrc
