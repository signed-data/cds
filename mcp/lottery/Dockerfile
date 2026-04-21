FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY sdk/python /tmp/sdk/python
COPY mcp/lottery /tmp/mcp/lottery

RUN pip install --no-cache-dir /tmp/sdk/python /tmp/mcp/lottery \
    && rm -rf /tmp/sdk /tmp/mcp

EXPOSE 8001

ENTRYPOINT ["python", "-m", "cds_mcp_lottery"]
CMD ["mega-sena"]
