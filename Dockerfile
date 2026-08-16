FROM postgres:16-bookworm AS pgclient

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gettext libpq5 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=pgclient /usr/lib/postgresql/16/bin/pg_dump \
                      /usr/lib/postgresql/16/bin/pg_restore \
                      /usr/lib/postgresql/16/bin/createdb \
                      /usr/lib/postgresql/16/bin/dropdb \
                      /usr/local/bin/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]