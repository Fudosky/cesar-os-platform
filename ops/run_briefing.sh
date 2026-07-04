#!/bin/sh
# Briefing Maestro diario — 06:00 America/Mexico_City (= 12:00 UTC)
docker exec cesar-os-hermes-1 python /opt/data/ops/maestro_briefing/main.py >> /var/log/maestro_briefing.host.log 2>&1
