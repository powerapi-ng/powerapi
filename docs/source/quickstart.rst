.. PowerAPI (QuickStart)

Démarrage rapide

Quickstart
**********

This part help you to understand how to use **PowerAPI**. It's assumed that you have a MongoDB database containing exploitable data, obtain from :doc:`sensors <sensors>` support by **PowerAPI**. It's recommended to read the :doc:`PowerAPI quick overview <intro>` before.

PowerAPI CLI on Docker
======================

You have to install `Docker <https://docs.docker.com/install/>`_ to run **PowerAPI**, the command below allow to run the data processing.

.. code-block:: none

   docker run powerapi input_hostname  input_port  input_database_name  input_collection_name  \
                         output_hostname output_port output_database_name output_collection_name \
                         SOCKET

Following parameters configure MongoDB database in input/output.

* **hostname**: Mongo server address. (localhost, IP address, ...)
* **port**: Mongo server port. (usually 27017)
* **database_name**: Database name.
* **collection_name**: Collection name.

If you are using MongoDB server on your localhost, you need to add ``--network=host`` to your Docker command. You can also add ``-v`` in the **PowerAPI** command for display logs readable with ``docker logs container_name``.
