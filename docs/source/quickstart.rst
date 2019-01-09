.. SmartWatts (QuickStart)

Guide de démarrage rapide
*************************

SmartWatts ?
============

SmartWatts est un framework permettant d'estimer la consommation énergétique d'environnement informatique (notamment des conteneurs ``Docker``).

Comment l'utiliser ?
====================

Installer les dépendances
-------------------------

Les dépendances s'installer grâce à...

Démarrer avec Docker
--------------------

.. code-block:: none

   docker run --network=host smartwatts localhost 27017 smartwatts hwrep \
                                        localhost 27017 sm_res sm_res19  \
                                        SOCKET
