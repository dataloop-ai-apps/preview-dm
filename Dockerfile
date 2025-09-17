FROM dataloopai/dtlpy-agent:cpu.py3.10.opencv

USER root
# Add a few extra runtime deps new Blender builds commonly need.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates wget xz-utils \
    libglib2.0-0 libx11-6 libxext6 libxi6 libxrender1 libxfixes3 libxrandr2 \
    libxxf86vm1 libsm6 libfontconfig1 libglu1-mesa \
    libxkbcommon0 libx11-xcb1 libxcb1 libegl1 libgl1 libwayland-client0 \
    libreoffice libreoffice-writer libreoffice-calc libreoffice-impress \
    fonts-dejavu fonts-liberation ghostscript \
 && rm -rf /var/lib/apt/lists/*

# ---- Choose Blender line at build time ----
# For latest stable:
#   docker build --build-arg BLENDER_MM=4.4 --build-arg BLENDER_VERSION=4.4.0 -t myimg .
# For latest LTS (recommended for CI/pipelines):
#   docker build --build-arg BLENDER_MM=4.2 --build-arg BLENDER_VERSION=4.2.13 -t myimg .
ARG BLENDER_MM=4.1
ARG BLENDER_VERSION=4.1.1
ARG BLENDER_BASE_URL=https://download.blender.org/release

# Optionally verify checksum (when you know the sha256 from the mirrors page)
# ARG BLENDER_SHA256=<paste value from blender-<ver>.sha256>

RUN set -eux; \
    PKG="blender-${BLENDER_VERSION}-linux-x64.tar.xz"; \
    URL="${BLENDER_BASE_URL}/Blender${BLENDER_MM}/${PKG}"; \
    echo "Downloading ${URL}"; \
    wget -q "$URL"; \
    # If you want checksum verification, uncomment next 3 lines and set BLENDER_SHA256 above
    # echo "${BLENDER_SHA256}  ${PKG}" > blender.sha256; \
    # sha256sum -c blender.sha256; \
    # rm blender.sha256; \
    mkdir -p /opt && tar -C /opt -xf "${PKG}" && rm "${PKG}"; \
    ln -s /opt/blender-${BLENDER_VERSION}-linux-* /opt/blender

# Use Blender’s bundled Python to install dtlpy (keeps system python clean)
RUN BL_PY="$(/opt/blender/blender -b --python-expr 'import sys; print(sys.executable)' | head -n1)"; \
    "$BL_PY" -m ensurepip --upgrade; \
    "$BL_PY" -m pip install --upgrade pip; \
    "$BL_PY" -m pip install --no-cache-dir dtlpy

ENV PATH="/opt/blender:${PATH}"

RUN pip install --user dtlpy



