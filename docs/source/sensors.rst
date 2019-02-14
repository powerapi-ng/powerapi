
Sensors
=======

Here you can find every kind of **sensors** collecting raw data useable by **PowerAPI** to compute energetic estimation.

.. note::

   Code in this page is not tested :D

HWPC-Sensor
-----------

The **HWPC-Sensor** (Hardware Performance Counters Sensor) get data from hardware performance counters reachable in recent processor. You have to provide him a MongoDB database for saving data. Docker image can be downloaded with the following command:

.. code-block:: none 

   docker pull gfieni/hwpc-sensor

When the image is correctly downloaded, you can run the sensor with the next following command:

.. code-block:: none

  docker run --privileged --name powerapi-sensor -td \
             -v /sys:/sys \
             -v /var/lib/docker/containers:/var/lib/docker/containers:ro \
             -v /tmp/powerapi-sensor-reporting:/reporting \
             HWPC_DOCKER_IMAGE -n "SENSOR_NAME" -r "mongodb" -U "mongodb://MONGO_ADDRESS" -D "DATABASE_NAME" -C "COLLECTION_NAME" \
             -c "sys" -e "INSTRUCTIONS_RETIRED" \
             -c "cycles" -e "CYCLES" \
             -c "llc" -e "LLC_MISSES" \
             -c "rapl" -e "RAPL_ENERGY_CORES" -e "RAPL_ENERGY_PKG" -e "RAPL_ENERGY_GPU" -e "RAPL_ENERGY_DRAM"


These parameters had to be configure:

* **HWPC_DOCKER_IMAGE**:**HWPC-Sensor** docker image name.
* **SENSOR_NAME**: Sensor name.
* **MONGO_ADDRESS**: MongoDB server address.
* **DATABASE_NAME**: MongoDB database name.
* **COLLECTION_NAME**: MongoDB collection name.
