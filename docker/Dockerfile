# docker/Dockerfile
# Defines the container image for the devops-cicd-pipeline Flask API.
# Build context is the repository root, so all COPY paths below are relative
# to that root (i.e. the directory you pass to `docker build`).

# ---------------------------------------------------------------------------
# Base image
# ---------------------------------------------------------------------------
# python:3.11-slim is the official Python image built on Debian with only the
# minimal packages needed to run Python. Choosing "slim" over the full image
# cuts the final image size significantly, reducing pull times and the attack
# surface for security vulnerabilities.
FROM python:3.11-slim

# ---------------------------------------------------------------------------
# Working directory
# ---------------------------------------------------------------------------
# All subsequent instructions (COPY, RUN, CMD) operate relative to /app.
# Docker creates the directory automatically if it does not already exist.
# Using /app is a widely-adopted convention for containerised web services.
WORKDIR /app

# ---------------------------------------------------------------------------
# Install dependencies before copying application code
# ---------------------------------------------------------------------------
# We copy requirements.txt on its own first, then run pip install, BEFORE
# copying the rest of the source code. Docker builds images in layers: each
# instruction produces a cached layer that is reused on subsequent builds as
# long as its inputs have not changed. Because requirements.txt changes far
# less often than application code, this ordering means `pip install` is only
# re-run when dependencies actually change, making iterative builds much
# faster.

# Copy only the dependency manifest from the repository root into /app.
COPY requirements.txt .

# Install the Python packages listed in requirements.txt.
# --no-cache-dir tells pip not to store the downloaded package files on disk
# after installation, which keeps the layer (and therefore the image) smaller.
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Copy application source code
# ---------------------------------------------------------------------------
# Now that the dependency layer is cached, copy the app/ directory into /app.
# Any change to application code will invalidate only this layer and
# everything after it — the expensive `pip install` layer above stays cached.
COPY app/ .

# ---------------------------------------------------------------------------
# Non-root user
# ---------------------------------------------------------------------------
# Running a container as root is a security risk: if an attacker escapes the
# container process they immediately have root on the host. Creating and
# switching to a dedicated, unprivileged user (appuser) limits the blast
# radius of any such exploit.
#
# adduser flags:
#   --disabled-password  no password set — the account cannot be logged into
#   --gecos ""           skip interactive prompts for full name etc.
RUN adduser --disabled-password --gecos "" appuser

# Switch all subsequent instructions (and the final running container) to
# the newly created non-root user.
USER appuser

# ---------------------------------------------------------------------------
# Exposed port
# ---------------------------------------------------------------------------
# Document that the container listens on port 5000 at runtime. EXPOSE is
# informational only — it does not actually publish the port to the host.
# You still need `-p 5000:5000` (or equivalent) when running the container.
# It serves as machine-readable documentation for orchestrators and humans.
EXPOSE 5000

# ---------------------------------------------------------------------------
# Startup command
# ---------------------------------------------------------------------------
# CMD sets the default command executed when the container starts.
# Using the exec form (JSON array) is preferred over the shell form because
# it runs Python as PID 1 directly, so OS signals (SIGTERM, SIGINT) are
# delivered straight to the Python process — ensuring graceful shutdown.
CMD ["python", "app.py"]
