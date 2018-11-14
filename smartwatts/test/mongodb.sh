#!/bin/bash

# Create db file
sudo mkdir -p /data/db
sudo chmod -R go+w /data/db

# Stop mongod
sudo mongod --shutdown

# Start mongod
sudo mongod --port 27017 --fork --logpath /var/log/mongodb.log
mongo mongodb_test.js
