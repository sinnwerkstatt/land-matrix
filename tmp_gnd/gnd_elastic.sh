#!/bin/bash

#podman run --name es_seven -p 9201:9200 -e "discovery.type=single-node" elasticsearch:7.6.0
podman start es_seven

#podman stop es_seven