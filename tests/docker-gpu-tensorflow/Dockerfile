FROM tensorflow/tensorflow:2.9.1-gpu
# Dependencies for glvnd and X11.
RUN apt-get update \
  && apt-get install -y -qq --no-install-recommends \
    libxext6 \
    libx11-6 \
    libglvnd0 \
    libgl1 \
    libglx0 \
    libegl1 \
    freeglut3-dev \
  && rm -rf /var/lib/apt/lists/*
# Env vars for the nvidia-container-runtime.
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES graphics,utility,compute
# Add gym.
RUN pip install --upgrade pip \
  && pip install gym==0.17.2 box2d==2.3.10

