#!/bin/bash

# Create db file
sudo mkdir -p /data/db-test
sudo chmod -R go+w /data/db-test

# Stop mongod
sudo mongod --shutdown --dbpath /data/db-test

# Start mongod
sudo mongod --port 27017 --fork --logpath /var/log/mongodb.log --dbpath /data/db-test
mongo mongodb_test_puller.js
mongo mongodb_test_filter.js
mongo mongodb_test_mongodb.js
