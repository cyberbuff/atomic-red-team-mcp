FROM python:3.12-slim

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Install system dependencies
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    at \
    build-essential \
    ca-certificates \
    ccrypt \
    clang \
    cron \
    curl \
    ed \
    git \
    gnupg \
    golang \
    iproute2 \
    iputils-ping \
    kmod \
    less \
    libpam0g-dev \
    lsof \
    netcat-openbsd \
    net-tools \
    nmap \
    p7zip \
    rsync \
    samba \
    selinux-utils \
    ssh \
    sshpass \
    sudo \
    tcpdump \
    telnet \
    tor \
    ufw \
    vim \
    wget \
    whois \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Install the 'uv' CLI and make it accessible to appuser
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -LsSf https://astral.sh/uv/install.sh | UV_UNMANAGED_INSTALL="/usr/local/bin" UV_VERSION="0.11.4" sh

# Set the working directory and change ownership
WORKDIR /app
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Make sure 'uv' is on PATH for the appuser
ENV PATH="/home/appuser/.local/bin:/usr/local/bin:${PATH}"
ENV ART_MCP_TRANSPORT="streamable-http"
ENV PYTHONUNBUFFERED=1

# Copy and install only requirements first (caching)
COPY --chown=appuser:appuser pyproject.toml uv.lock ./
RUN uv sync --no-install-project --locked

# Now copy everything from the current directory into /app
COPY --chown=appuser:appuser . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the server using the installed CLI command
CMD ["uv", "run", "python", "-m", "atomic_red_team_mcp"]
