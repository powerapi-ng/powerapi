
Sensors
=======

This page lists the **sensors** which are currently supported by **PowerAPI**. In particular, sensors are in charge of collecting the raw metrics that are further processed to estimate the power consumption of software artefacts.

.. note::

   Code in this page is not tested :D

HWPC-Sensor
-----------

The **HWPC-Sensor** (*Hardware Performance Counters Sensor*) read metrics from the hardware performance counters exposed by the processor. The sensor can export the metrics into a MongoDB endpoint or as a CSV file. The Docker image of **HWPC-Sensor** can be downloaded with the following command:

.. code-block:: none 

   docker pull gfieni/hwpc-sensor

When the image is correctly downloaded, you can run the sensor with the following command:

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

This command monitors the following hardware performance counters: `INSTRUCTIONS_RETIRED`, `CYCLES`, `LLC_MISSES`, `RAPL_ENERGY_CORES`, `RAPL_ENERGY_PKG`, `RAPL_ENERGY_GPU`, `RAPL_ENERGY_DRAM` when available and uploads the collected metrics into a MongoDB endpoint exposed at `mongodb://MONGO_ADDRESS`, as a collection `COLLECTION_NAME` stored in the database `DATABASE_NAME`.

The parameters to be specified are:
* **HWPC_DOCKER_IMAGE**:**HWPC-Sensor** docker image name.
* **SENSOR_NAME**: Sensor name.
* **MONGO_ADDRESS**: MongoDB server address.
* **DATABASE_NAME**: MongoDB database name.
* **COLLECTION_NAME**: MongoDB collection name.
