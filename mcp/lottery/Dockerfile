FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir .

EXPOSE 8001

ENTRYPOINT ["signeddata-mcp-lottery"]
CMD ["mega-sena"]
