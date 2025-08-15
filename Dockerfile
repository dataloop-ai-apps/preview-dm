FROM dataloopai/dtlpy-agent:cpu.py3.10.opencv
USER root
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates wget xz-utils \
    libglib2.0-0 libx11-6 libxext6 libxi6 libxrender1 libxfixes3 libxrandr2 \
    libxxf86vm1 libsm6 libfontconfig1 libglu1-mesa && rm -rf /var/lib/apt/lists/*

# Install Blender (linux-x64). On Apple Silicon, build with --platform=linux/amd64
ARG BLENDER_VERSION=3.6.9
RUN PKG=blender-${BLENDER_VERSION}-linux-x64.tar.xz \
 && wget -q https://download.blender.org/release/Blender3.6/${PKG} \
 && mkdir -p /opt \
 && tar -C /opt -xf ${PKG} \
 && rm ${PKG} \
 && ln -s /opt/blender-${BLENDER_VERSION}-linux-* /opt/blender

ENV PATH="/opt/blender:${PATH}"
COPY usd_to_gltf.py /opt/convert.py


