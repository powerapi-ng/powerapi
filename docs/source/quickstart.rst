.. PowerAPI (QuickStart)

Démarrage rapide

Quickstart
**********

This part helps you to understand how to use **PowerAPI**. It is assumed that you already deployed a MongoDB database containing exploitable metrics, obtained from :doc:`sensors <sensors>` supported by **PowerAPI**. It is recommended to read the :doc:`PowerAPI quick overview <intro>` before.

PowerAPI CLI on Docker
======================

You have to install `Docker <https://docs.docker.com/install/>`_ to run **PowerAPI**, the command below allows to run the data processing.

.. code-block:: none

   docker run powerapi input_hostname input_database_name  input_collection_name  \
                         output_hostname output_database_name output_collection_name \
                         SOCKET

The following parameters are used to configure MongoDB database in input/output:
* **hostname**: Mongo server address (localhost, IP address...),
* **database_name**: Database name,
* **collection_name**: Collection name.

If you are using MongoDB server on your localhost, you need to add ``--network=host`` to your Docker command. You can also add ``-v`` in the **PowerAPI** command for display logs readable with ``docker logs container_name``.
