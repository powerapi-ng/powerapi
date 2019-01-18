
Capteurs énergétiques
=====================

Cette page regroupe tous les types de **Capteurs énergétiques** qui produisent les données brutes nécessaire à **PowerAPI** pour effectuer ses traitements.

.. note::

   Le code de cette page n'est pas encore testé :D

HWPC-Sensor
-----------

Le **HWPC-Sensor** (Hardware Performance Counters Sensor) permet de récupérer des données à partir des compteurs de performance accessible dans les processeurs récents.

Pour l'utiliser, il faut lui mettre à disposition un serveur MongoDB, dans lequel il va stocker ses données.

On peut télécharger l'image Docker de HWPC-sensor avec la commande suivante

.. code-block:: none 

   docker pull gfieni/hwpc-sensor

Une fois l'image téléchargée, la commande suivante lance le capteur qui va nourrir la base de donnée.

.. code-block:: none

  docker run --privileged --name smartwatts-sensor -td \
             -v /sys:/sys \
             -v /var/lib/docker/containers:/var/lib/docker/containers:ro \
             -v /tmp/smartwatts-sensor-reporting:/reporting \
             HWPC_DOCKER_IMAGE -n "SENSOR_NAME" -r "mongodb" -U "mongodb://MONGO_ADDRESS" -D "DATABASE_NAME" -C "COLLECTION_NAME" \
             -c "sys" -e "INSTRUCTIONS_RETIRED" \
             -c "cycles" -e "CYCLES" \
             -c "llc" -e "LLC_MISSES" \
             -c "rapl" -e "RAPL_ENERGY_CORES" -e "RAPL_ENERGY_PKG" -e "RAPL_ENERGY_GPU" -e "RAPL_ENERGY_DRAM"

Il faut penser à changer les variables suivantes:

* **HWPC_DOCKER_IMAGE**: Nom de l'image docker de **HWPC-Sensor**.
* **SENSOR_NAME**: Nom du capteur.
* **MONGO_ADDRESS**: Adresse pour accéder au serveur MongoDB.
* **DATABASE_NAME**: Nom de la base de donnée.
* **COLLECTION_NAME**: Nom de la collection.
