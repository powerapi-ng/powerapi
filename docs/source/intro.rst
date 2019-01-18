Présentation de PowerAPI 
^^^^^^^^^^^^^^^^^^^^^^^^^^

**PowerAPI** est une suite d'outils utilisés pour mesurer la consommation énergétique logiciel d'une infrastructure informatique. La consommation est mesurée à l'échelle d'un conteneur Docker ou d'un pod Kubernetes (Cgroups). Elle est estimée à partir de données recueillies par des :doc:`Capteurs énergétiques <sensors>` (logiciel ou physique). Cette estimation peut être réalisée au fur et à mesure que les données sont recueillies, ou à partir d'un ensemble de mesure réalisées au préalable.

Mesurer la consomation énergétique
==================================

Mesurer la consommation énergétique d'un conteneur se fait en deux phases:

- Recueillir les données grâce à des **Capteurs** (logiciels ou matériels). Chaque capteur récolte des données nécessaires à l'estimation de la consommation énergétique (consommation globale de la machine, compteur de performance processeur, etc.). Ces données sont ensuite stockées dans une base de données MongoDB.

- Estimer la consommation énergétique grâce à des modèles de consommation. Un deuxième outil: le **Wattmetre** utilise des modèles de consommation prédéfinis pour estimer une mesure de consommation énergétique de conteneur à partir des données recueillies par les capteurs. Ce Wattmetre récupère les données depuis la base de donnée MongoDB. Il peut effectuer ses estimations de consommation au fur et a mesure que les données sont écrites en base ou en utilisant l'intégralité des données présentes dans la base de donnée. Les estimations de consommations sont ensuite stockées en base.

.. figure:: _static/powerAPI_archi.png

	    calcul de la consommation énergétique de la machine **HOST**
