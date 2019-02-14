.. Operation (PowerAPI - Fonctionnement)

PowerAPI - Guide utilisateur
******************************

PowerAPI permet de calculer des modèles à partir de données de consommation énergétique. Pour une utilisation simple, il est possible de lancer PowerAPI directement dans un conteneur docker en lui spécifiant certains paramètres, mais pour une utilisation plus fine, il devient intéressant d'utiliser sois-même la librarie.

Le schéma ci-dessous résume l'architecture de l'application pour deux configurations différentes, la première étant très simple et la seconde plus complexe.

.. image:: _static/schema_full.png

On trouve 4 acteurs principaux:

* Le **Puller** qui gère la lecture d'une base de donnée et la répartition de ces données vers les dispatchers.
* Le **Dispatcher** qui à partir des données qu'il reçoit, va se charger de gérer un ensemble de Formula et répartir les données selon des critères précis.
* La **Formula** qui va se charger de traiter les données reçues et renvoyer un résultat.
* Le **Pusher** qui gère la sauvegarde en base de donnée des résultats obtenus par les Formulas.

Puller
======

Un :class:`Puller <powerapi.puller.puller_actor.PullerActor>` permet de gérer la lecture d'une base de donnée et la répartition de ces données vers les :class:`Dispatcher <powerapi.dispatcher.dispatcher_actor.DispatcherActor>`. Il est définit par trois variables:

* **Le type de base de donnée**, les types compatibles sont énumérés ici. (lien vers types compatibles)
* **Le type de donnée** qui correspond en fait à un objet héritant de la classe :class:`ReportModel <powerapi.report_model.report_model.ReportModel>`
* **Le filtre** qui va pour chaque donnée récupérée, lister les :class:`Dispatcher <powerapi.dispatcher.dispatcher_actor.DispatcherActor>` à qui envoyer cette donnée selon des règles bien précise.

.. image:: _static/schema_puller.png

Un :class:`Puller <powerapi.puller.puller_actor.PullerActor>` sera de ce fait toujours lié à un type de base de donnée et un type de donnée. Le filtre permet entre autre de trier les données afin de n'envoyer que les données jugées utiles et ainsi de ne pas envoyer des données à un :class:`Dispatcher <powerapi.dispatcher.dispatcher_actor.DispatcherActor>` qui n'en a pas besoin. 

.. literalinclude:: ../../test/doc/user_puller_example.py
   :language: python
   :linenos:

Dispatcher et Formula
=====================

Dispatcher
----------

Un :class:`Dispatcher <powerapi.pusher.pusher_actor.DispatcherActor>` se charge de répartir les données qu'il reçoit parmi un ensemble de :class:`Formula <powerapi.formula.formula_actor.FormulaActor>` qu'il gère. Il est paramétrable par différentes variables: 

* Une **factory de Formula** qui lui permet de créer un certain type de **Formula** quand il en a besoin.
* Des règles **GroupBy** qui vont lier pour chaque type de donnée des règles pour répartir les données.

Factory de Formula
^^^^^^^^^^^^^^^^^^

Tout d'abord parlons de la **factory de Formula**. Cette **factory** doit être une fonction qu'on donne en paramètre à la création du :class:`Dispatcher <powerapi.dispatcher.dispatcher_actor.DispatcherActor>`. On peut la définir sous deux formes, soit par une fonction basique, soit par une fonction lambda.

.. literalinclude:: ../../test/doc/user_dispatcher_factory_example.py
   :language: python
   :linenos:

.. note::
   Il est parfaitement possible d'ajouter des paramètres à l'initialisation de la formula (ici XXXFormulaActor) là ou se trouve les "...".

GroupBy
^^^^^^^

Ensuite, expliquons plus en détail ce que sont les règles de **GroupBy**. Mais avant ça, quelques rappels sur le :class:`Report <powerapi.report.report.Report>`. Les données que l'on récupère sont toujours encapsulées dans une classe héritante de :class:`Report <powerapi.report.report.Report>`. Les données auront toujours 3 champs en communs, le **timestamp**, le **sensor** et la **target**. Le reste dépend du type de donnée que l'on traite. Prenons l'exemple du type :class:`HWPCReport <powerapi.report.hwpc_report.HWPCReport>`. Ce type là peut être groupé à différent niveau:

* **ROOT** qui va correspondre à la clé ``(sensor)``
* **SOCKET** qui va correspondre à la clé ``(sensor, socket)``
* **CORE** qui va correspondre à la clé ``(sensor, socket, core)``

.. image:: _static/schema_hwpcreport.png

Dans notre exemple, nous choisissons de grouper par **SOCKET**, soit avec la clé ``(sensor, socket)``. Dans ce cas, à chaque fois qu'un :class:`HWPCReport <powerapi.report.hwpc_report.HWPCReport>` est reçu, il va vérifier si une Formula avec cette clé existe, si elle existe, il lui envoie la donnée, sinon il la crée, puis lui envoie.

.. image:: _static/schema_hwpcreport2.png

Si on considère que les :class:`HWPCReport <powerapi.report.hwpc_report.HWPCReport>` auront toutes le même **sensor**, et ont deux **sockets** différents, on aura au maximum 2 **Formulas** créées qui recevront les données entourées dans le schéma ci-dessus (en orange et en bleu).

.. literalinclude:: ../../test/doc/user_dispatcher_groupby_example.py
   :language: python
   :linenos:

.. note::
   Il est possible de spécifier plusieurs :func:`group_by() <powerapi.dispatcher.dispatcher_actor.DispatcherActor.group_by>` à la suite afin de gérer plusieurs types de :class:`Report <powerapi.report.report.Report>`, c'est là que le paramètre ``primary`` devient important. C'est par rapport à sa clé que les Formulas seront créées.


TODO: expliquer avec plusieurs group_by les * dans les clés.

Pusher
======

Un :class:`powerapi.PusherActor <powerapi.pusher.pusher_actor.PusherActor>` permet 


