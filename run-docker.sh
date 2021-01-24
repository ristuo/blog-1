#!/bin/bash
if [ -z "$WORDPRESS_BLOG_1_DOMAIN" ]; then
  echo "Define WORDPRESS_BLOG_1_DOMAIN to run!"
  exit 78
fi
directory=own-wordpress-image
cat $directory/000-default.conf_template|envsubst > $directory/000-default.conf
sudo -E docker-compose build
sudo -E docker-compose up -d
