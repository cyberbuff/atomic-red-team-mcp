FROM python:3.12-slim

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install the 'uv' CLI and make it accessible to appuser
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
	mv /root/.local/bin/uv /usr/local/bin/uv && \
	chmod +x /usr/local/bin/uv

# Set the working directory and change ownership
WORKDIR /app
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Make sure 'uv' is on PATH for the appuser
ENV PATH="/home/appuser/.local/bin:/usr/local/bin:${PATH}"
ENV ART_MCP_TRANSPORT="streamable-http"

# Copy and install only requirements first (caching)
COPY --chown=appuser:appuser pyproject.toml uv.lock ./
RUN uv sync --no-install-project

# Now copy everything from the current directory into /app
COPY --chown=appuser:appuser . .

EXPOSE 8000

# Run the server using the installed CLI command
CMD ["uv", "run", "python", "-m", "atomic_red_team_mcp"]
