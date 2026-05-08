#!/bin/bash
set -e

apt-get update && apt-get install -y --no-install-recommends libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

docker-php-ext-install mysqli curl

a2enmod rewrite

exec apache2-foreground
