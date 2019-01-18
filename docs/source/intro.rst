Présentation de Smartwatts
^^^^^^^^^^^^^^^^^^^^^^^^^^

PowerAPI est une suite d'outils utilisée pour mesurer la consommation énergétique logiciel d'une infrastructure. La consommation est mesurée à l'échelle d'un container Docker ou d'un pod Kubernetes (Cgroups). Elle est estimée à partir de données recueillies par des **CAPTEUR** (logiciel ou physique). Cette estimation peut être réalisée au fur et à mesure que les données sont recueillies, ou à partir d'un ensemble de mesure réalisées au préalable.

Mesurer la consomation énergétique
==================================

Mesurer la consommation énergétique d'un container se fait en deux phases :

- recueillir les données grâce à des capteurs (logiciels ou matériels). Chaque capteur recueille des données nécessaires à l'estimation de la consommation énergétique (consommation globale de la machine, compteur de performance processeur, ...). Ces données sont ensuite stockées dans une base de données Mongo DB.

- estimer la consommation énergétique grâce à des modèles de consommation. Un deuxième outils : le wattmetre, utilise des modèles de consommation prédéfinis pour estimer une mesure de consomation énergétique de container à partir des données recueillies par les capteurs. Ce wattmetre récupère les données depuis la base de donnée Mongo DB. Il peux effectuer ses estimations de consomation au fur et a mesure que les données sont écrites en bases ou en utilisant l'intégralitée des données présentes dans la base de données. Les estimations de consomations sont ensuite stocke en base.

.. figure:: _static/powerAPI_archi.png

	    calcul de la consomation énergétique de la machine **HOST**
