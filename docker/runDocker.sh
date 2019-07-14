#!/bin/bash

# Build the container
docker-compose build convert_psx

# Run the conversion
docker-compose run convert_psx