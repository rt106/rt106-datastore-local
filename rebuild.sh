#!/usr/bin/env bash
# Copyright (c) General Electric Company, 2017.  All rights reserved.

echo ""
echo "Removing datastore image."
docker rmi rt106/rt106-datastore-local:latest

echo ""
echo "Building datastore image."
docker build -t rt106/rt106-datastore-local:latest --build-arg http_proxy=$HTTP_PROXY --build-arg https_proxy=$HTTPS_PROXY .

echo ""
docker images
