
export INFLUX2_ORG='org_powerapi_influxdb2'
export INFLUX2_URL='http://localhost:8087'
export INFLUX2_PORT=8087
export INFLUX2_BUCKET_NAME='acceptation_test_gh'

export INFLUX2_DOCKER_CONTAINER_NAME='influxdb-action-gh'
export INFLUX2_USER_NAME='powerapi'
export INFLUX2_PASSWORD='powerapi...12352'

# docker run --name $INFLUX2_DOCKER_CONTAINER_NAME -d \
#  -p 8087:8086 \
#  --volume `pwd`/influxdb2:/var/lib/influxdb2 \
#  influxdb

# configure influxdb
sudo docker exec $INFLUX2_DOCKER_CONTAINER_NAME influx setup \
  --bucket $INFLUX2_BUCKET_NAME \
  --org $INFLUX2_ORG \
  --password $INFLUX2_PASSWORD \
  --username $INFLUX2_USER_NAME \
  --force


# get the token
export INFLUX2_TOKEN=`sudo docker exec $INFLUX2_DOCKER_CONTAINER_NAME influx auth list | awk -v username=$INFLUX2_USER_NAME '$5 ~ username {print $4 " "}'`
