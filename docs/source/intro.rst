PowerAPI quick overview
^^^^^^^^^^^^^^^^^^^^^^^

**PowerAPI** is a framework used as a power meter. It allows to measure the energetic consumption of containerized environments (with cgroups). These data are computed using raws metrics collected by some :doc:`sensors <sensors>` (hardware or software). The computed estimation of consumption can be made online or offline. (in real time or after collecting data on a database) 

Measure energetic consumption
=============================

There are two steps for measure the energetic consumption:

- Collect data from :doc:`sensors <sensors>`. Each :doc:`sensors <sensors>` gather useful data for compute the estimation of energetic consumption (e.g. global computer consumption, processor performance counter, etc.). Data are saved in a Database, usually a MongoDB.

- Compute the energetic consumption using pre-trained model. **PowerAPI** use this pre-trained consumption model to estimate a measure of energetic consumption of the containers from all data collect by :doc:`sensors <sensors>`. Results are then saved in a Database, usually (still) a MongoDB.

.. figure:: _static/powerAPI_archi.png

            Energetic consumption compute process of the **HOST**
