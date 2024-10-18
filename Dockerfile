# Base Image with CUDA 11.8
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu20.04
# FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu20.04
# FROM nvidia/cuda:12.6.0-cudnn-devel-ubuntu20.04

# Latch environment building
COPY --from=812206152185.dkr.ecr.us-west-2.amazonaws.com/latch-base-cuda:fe0b-main /bin/flytectl /bin/flytectl
WORKDIR /root

ENV VENV /opt/venv
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONPATH /root
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y libsm6 libxext6 libxrender-dev build-essential procps rsync openssh-server

RUN apt-get install -y software-properties-common &&\
    add-apt-repository -y ppa:deadsnakes/ppa &&\
    apt-get install -y python3.9 python3-pip python3.9-distutils curl

RUN python3.9 -m pip install --upgrade pip && python3.9 -m pip install awscli

RUN curl -L https://github.com/peak/s5cmd/releases/download/v2.0.0/s5cmd_2.0.0_Linux-64bit.tar.gz -o s5cmd_2.0.0_Linux-64bit.tar.gz &&\
    tar -xzvf s5cmd_2.0.0_Linux-64bit.tar.gz &&\
    mv s5cmd /bin/ &&\
    rm CHANGELOG.md LICENSE README.md

COPY --from=812206152185.dkr.ecr.us-west-2.amazonaws.com/latch-base-cuda:fe0b-main /root/Makefile /root/Makefile
COPY --from=812206152185.dkr.ecr.us-west-2.amazonaws.com/latch-base-cuda:fe0b-main /root/flytekit.config /root/flytekit.config

WORKDIR /tmp/docker-build/work/

SHELL [ \
    "/usr/bin/env", "bash", \
    "-o", "errexit", \
    "-o", "pipefail", \
    "-o", "nounset", \
    "-o", "verbose", \
    "-o", "errtrace", \
    "-O", "inherit_errexit", \
    "-O", "shift_verbose", \
    "-c" \
]
ENV TZ='Etc/UTC'
ENV LANG='en_US.UTF-8'

ARG DEBIAN_FRONTEND=noninteractive

# Install system requirements
RUN apt-get update --yes && \
    xargs apt-get install --yes aria2 git wget unzip curl fuse && \
    apt-get install --fix-broken

# ObjectiveFS
RUN curl --location --fail --remote-name https://objectivefs.com/user/download/an7dzrz65/objectivefs_7.2_amd64.deb && \
    dpkg -i objectivefs_7.2_amd64.deb && \
    mkdir /etc/objectivefs.env

COPY credentials/* /etc/objectivefs.env/

RUN apt-get install --yes pkg-config libfuse-dev

# ObjectiveFS performance tuning
ENV CACHESIZE="50Gi"
ENV DISKCACHE_SIZE="200Gi"

# Latch SDK
# DO NOT REMOVE
RUN pip install latch==2.53.0
RUN mkdir /opt/latch

# Install Mambaforge
RUN apt-get update --yes && \
    apt-get install --yes curl && \
    curl \
        --location \
        --fail \
        --remote-name \
        https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh && \
    `# Docs for -b and -p flags: https://docs.anaconda.com/anaconda/install/silent-mode/#linux-macos` \
    bash Mambaforge-Linux-x86_64.sh -b -p /opt/conda -u && \
    rm Mambaforge-Linux-x86_64.sh

# Set conda PATH
ENV PATH=/opt/conda/bin:$PATH

# Install ESM inverse folding
RUN conda create -n esminverse python=3.9 -y && \
    conda run -n esminverse conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y && \
    conda run -n esminverse  conda install pyg=*=*cu* -c pyg -y

RUN conda run -n esminverse pip install biotite && \
    conda run -n esminverse pip install git+https://github.com/facebookresearch/esm.git

RUN conda run -n esminverse pip install numpy==1.26.4

ENV PATH=/opt/conda/envs/esminverse/bin:$PATH

ENV DGLBACKEND=pytorch

# Copy workflow data (use .dockerignore to skip files)
COPY . /root/

# Latch workflow registration metadata
# DO NOT CHANGE
ARG tag
# DO NOT CHANGE
ENV FLYTE_INTERNAL_IMAGE $tag

WORKDIR /root
