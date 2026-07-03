#!/bin/bash
# Crea bases separadas para LiteLLM y Langfuse dentro del mismo Postgres.
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE DATABASE litellm;
  CREATE DATABASE langfuse;
EOSQL
echo "✔ Bases 'litellm' y 'langfuse' creadas."
