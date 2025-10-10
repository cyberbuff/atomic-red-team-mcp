FROM python:3.12-alpine

# Create a non-root user
RUN addgroup -g 1000 appuser && \
	adduser -u 1000 -G appuser -s /bin/sh -D appuser

# Install system dependencies
RUN apk add --no-cache curl ca-certificates git

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
CMD ["uv", "run", "python", "-m", "main"]
