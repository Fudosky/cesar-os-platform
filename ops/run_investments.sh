#!/bin/sh
docker exec cesar-os-hermes-1 python /opt/data/ops/investment_tracker/main.py >> /var/log/investment_tracker.host.log 2>&1
