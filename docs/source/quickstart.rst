.. PowerAPI (QuickStart)

Démarrage rapide
****************

Cette partie permet de voir comment utiliser **PowerAPI**. Il est considéré que vous possédez une base de donnée MongoDB contenant des données exploitables, obtenues à partir d'un des :doc:`Capteurs énergétiques <sensors>` supportés par **PowerAPI**. Il est préférable d'avoir lu la partie :doc:`Présentation PowerAPI <introduction>` avant.

PowerAPI CLI sur Docker
=========================

Il est nécessaire d'installer `Docker <https://docs.docker.com/install/>`_ pour lancer **PowerAPI**, la commande ci-dessous permet de démarrer le traitement des données.

.. code-block:: none

   docker run smartwatts input_hostname  input_port  input_database_name  input_collection_name  \
                         output_hostname output_port output_database_name output_collection_name \
                         SOCKET

Les paramètres permettent de configurer les bases MongoDB en entrée et en sortie.

* **hostname**: Adresse du serveur Mongo. (localhost, adresse IP, ...)
* **port**: Port du serveur Mongo. (27017 le plus souvent)
* **database_name**: Nom de la base de donnée.
* **collection_name**: Nom de la collection.

Si vous utilisez un serveur MongoDB localement, vous devez ajouter l'option ``--network=host`` après ``docker run``. Il est également possible d'ajouter l'option ``-v`` à la fin de la commande pour avoir des logs de retour accessible avec la commande ``docker logs nom_du_conteneur``.
