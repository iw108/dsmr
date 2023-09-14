#!/bin/bash
set -e

influx bucket create \
    -n "${DOCKER_INFLUXDB_INIT_BUCKET}_downsampled" \
    -o ${DOCKER_INFLUXDB_INIT_ORG}

