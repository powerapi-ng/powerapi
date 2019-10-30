PowerAPI quick overview
^^^^^^^^^^^^^^^^^^^^^^^

**PowerAPI** is a software framework to build and deploy software-defined power meters. It allows users to measure the energy consumption of virtual environments (containers, virtual machines...). This information is computed from raw metrics collected by some :doc:`sensors <sensors>` (hardware or software). The computed estimations of energy consumption can be reported online or offline (*i.e.*, in real-time or *post-mortem*).

Estimate energy consumption
===========================

There are two steps to report the energy consumption:

1. Collect data from :doc:`sensors <sensors>`. Each :doc:`sensors <sensors>` gathers relevant metrics to estimate the energy consumption (*e.g.*, global computer consumption, processor performance counters). Data are stored in a database, usually  MongoDB.

2. Estimate the energy consumption using pre-trained power models. **PowerAPI** use this pre-trained power models to estimate the energy consumption of the virtual environments from raw metrics collect by :doc:`sensors <sensors>`. Results are then stored in a database, MongoDB or InfluxDB.

.. figure:: _static/powerAPI_archi.png

            Energy consumption compute process of the **HOST**
