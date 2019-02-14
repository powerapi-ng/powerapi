.. Concept page

PowerAPI - Guide développeur
******************************

Smartwatts est implémenté autour d'un cadriciel d'acteur, les acteurs communiquent grâce à la bibliothèque `pyzmq <https://pyzmq.readthedocs.io/en/latest/>`_ qui est une implémentation python de la librairie `ZeroMQ <http://zeromq.org/>`_. Ce guide défini les principaux concepts dont la compréhension est nécessaire pour utiliser ces acteurs.

Définition d'un acteur
======================

Les acteurs utilisés dans powerapi reposent tous sur la même classe abstraite :class:`powerapi.Actor <powerapi.actor.actor.Actor>` qui hérite elle même de la classe `multiprocessing.Process <https://docs.python.org/3/library/multiprocessing.html>`_. Cette classe définie un acteur comme une entité autonome adaptant son comportement en fonction des messages qu'elle reçoit.

Concrètement, un acteur est un processus système. Ce processus possède un comportement prédéfini (son comportement métier), un état (un ensemble de valeur stocké par l'acteur tout au long de son exécution) et une interface de communication avec les autres acteurs. Il est capable d'envoyer/recevoir des messages à/depuis d'autres processus. En fonction des messages reçus, l'acteur peut :

- modifier son état
- produire des effets de bord (contacter/créer d'autres acteurs, intéragir avec le système, ...)
- changer son comportement métier.

Interface client/serveur
========================

Une interface client/serveur expose les fonctions permettant de manipuler les acteurs (communication, configuration, ...)

l'interface serveur regroupe l'ensemble des fonctions internes à l'acteur (communication avec d'autres processus, modification de l'état de l'acteur, ...). Ces fonctions sont exécutées dans le processus de l'acteur. Elles regroupent : la configuration de l'acteur côté serveur, la réception et le traitement des messages.

l'interface client regroupe l'ensemble des fonctions permettant de lancer et configurer un acteur ainsi que les fonctions permettant à un autre processus de communiquer avec l'acteur. Elles sont exécutées dans les processus souhaitant communiquer avec l'acteur. Ces fonctions servent à initialiser/configurer les variables de communication avec l'acteur et lui envoyer des messages.

- le code de la classe :class:`powerapi.Actor <powerapi.actor.actor.Actor>` regroupe à la fois les fonctions de l'interface client comme celle de l'interface serveur. La méthode :func:`Actor.start` de l'acteur va dupliquer (fork) le code de la classe acteur et créer le processus système. Les variables permettant d'utiliser l'interface serveur seront alors initialisées dans le nouveau processus. Ainsi, les fonctions de l'interface serveur ne peuvent être utilisées dans le processus client.
- La méthode :func:`Actor.connect() <powerapi.actor.actor.Actor.connect>` permet d'initialiser les variables permettant d'utiliser l'interface client dans un processus souhaitant communiquer avec le serveur.

Composantes d'un acteur
=======================

La classe :class:`powerapi.Actor <powerapi.actor.actor.Actor>` encapsule plusieurs composants. Chacun pouvant être enrichie pour personnaliser le comportement de l'acteur.

État
-----

L'état de l'acteur est un ensemble de valeurs utilisées par l'acteur lorsqu'il traite un message. Cet état est implémenté par la classe :class:`powerapi.BasicState <powerapi.actor.state.BasicState>`.

Cette classe contient les valeurs suivantes :

- l'interface de communication
- deux booléens, indiquant si l'acteur est vivant et initialisé
- un pointeur vers une fonction définissant le comportement métier de l'acteur (voir plus bas)

Les valeurs de l'état peuvent être modifiées par l'acteur lors de la réception d'un message.

Socket Interface
----------------

Afin de communiquer avec les autres acteurs/processus, chaque acteur possède une interface de communication reposant sur des sockets zmq. Cette interface est implémentée par la classe :class:`powerapi.SocketInterface <powerapi.actor.socket_interface.SocketInterface>`

L'acteur possède deux canaux de communication, un **canal de données** et un **canal de monitoring**.

Le **canal de données** sert à envoyer/recevoir les messages "metier" de l'acteur. Plusieurs processus peuvent se connecter sur ce canal pour envoyer des messages à l'acteur. Ce canal est uni-directionel : Les processus souhaitant communiquer avec l'acteur ne peuvent qu'envoyer des données sur ce canal et l'acteur ne peux utiliser ce canal que pour recevoir des messages.

Le **canal de monitoring** sert à envoyer/recevoir les messages utilisés pour la supervision de l'acteur (tuer l'acteur, initialiser l'acteur). Ce canal ne peut être utilisé que par un seul processus, chargé de monitorer l'acteur. Les messages envoyés sur ce canal sont traités par l'acteur en priorité par rapport aux messages envoyés sur le canal de données.

La classe de l'acteur encapsule un unique socket interface. Cette interface sera dupliquée entre les processus client et serveur de l'acteur et initialisée par chacun d'entre eux. Le socket interface côté client contient les fonctions permettant à un processus externe d'envoyer des messages sur le canal de données ou de communiquer (envoyer/recevoir des messages) par le canal de monitoring. Côté serveur, le socket interface contient les fonctions permettant de recevoir des messages par le canal de données et de communiquer (envoyer/recevoir des messages) par le canal de monitoring.

Comportement d'un acteur
------------------------

Tous les acteurs se comportent selon le même schéma. Après sa création, il est nécessaire d'appeler la fonction :func:`Actor.start` à partir de l'interface client de l'acteur. Une fois cette méthode appelée, l'acteur va exécuter, dans le processus serveur, trois comportements, les uns à la suite des autres puis s'arrêter :

- la configuration des variables de base (socket, variables métiers, ...) grâce à la fonction :func:`Actor.setup() <powerapi.actor.actor.Actor.setup>`
- l'exécution du comportement métier tant que l'acteur est en vie. Tant que l'état de l'acteur indique que l'acteur est en vie, l'acteur va exécuter la fonction pointé par l'attribut :attr:`powerapi.BasicState.behaviour` dans l'état de l'acteur. Cette fonction peut accéder à toute l'interface serveur de l'acteur.
- Lorsque l'état de l'acteur indique que l'acteur est mort, l'acteur s'arrête après la dernière exécution de la fonction pointé par :attr:`powerapi.BasicState.behaviour`. Une fonction :func:`Actor.terminated_behaviour() <powerapi.actor.actor.Actor.terminated_behaviour>` est alors appelée pour terminer correctement l'acteur (fermeture des sockets, des interfaces de communication avec l'extérieur, ...)

Changement de comportement
--------------------------

Chacune de ces fonctions peut être modifiée comme suit:

- la fonction :func:`Actor.setup() <powerapi.actor.actor.Actor.setup>` peut être enrichie pour exécuter des actions de configuration avant de lancer le comportement métier. Pour cela, la fonction :func:`Actor.setup() <powerapi.actor.actor.Actor.setup>` doit être réécrite dans une classe héritant de :class:`powerapi.Actor <powerapi.actor.actor.Actor>`. La méthode :func:`Actor.setup() <powerapi.actor.actor.Actor.setup>` exécute déjà une configuration de base de l'acteur, pour conserver cette configuration, cette méthode doit être rappelée lors de la réécriture de la méthode.

- la fonction :attr:`powerapi.BasicState.behaviour` peut être modifiée en changeant le pointeur de fonction de l'état vers une nouvelle fonction. Le pointeur peut être modifié pendant l'exécution de la précédente fonction :attr:`powerapi.BasicState.behaviour`, le changement de comportement sera alors effectif lorsque la fonction précédente aura terminée son exécution.

- la fonction :func:`Actor.terminated_behaviour() <powerapi.actor.actor.Actor.terminated_behaviour>` peut être implémentée pour exécuter un comportement spécifique avant de terminer un acteur.

Comportement métier par défaut
==============================

Par défaut la fonction :attr:`powerapi.BasicState.behaviour`, pointé par l'état de l'acteur, attend un message et exécute un comportement spécifique en fonction du type de message reçus. Un comportement est implémenté par une classe :class:`powerapi.AbstractHandler <powerapi.handler.abstract_handler.AbstractHandler>` pour chaque type de message auquel l'acteur peut répondre. Lorsque l'acteur reçoit un message, il cherche le :class:`powerapi.AbstractHandler <powerapi.handler.abstract_handler.AbstractHandler>` correspondant au type de message reçu puis traite ce message grâce au Handler. Si aucun handler n'est trouvé, l'acteur crash en levant l'exception ``UnknowMessageTypeException``.

Par défaut, un acteur ne possède aucun handler. Il est possible d'ajouter un handler en le liant à un type de message grâce à la méthode :func:`Actor.add_handler() <powerapi.actor.actor.Actor.add_handler>`

AbstractHandler
---------------

Un handler est une classe héritant de :class:`powerapi.AbstractHandler <powerapi.handler.abstract_handler.AbstractHandler>`. Cette classe possède une méthode :func:`AbstractHandler.handle() <powerapi.handler.abstract_handler.AbstractHandler.handle>` qui prend en argument le message reçu et l'état courant de l'acteur. En fonction de la valeur du message reçu, cette fonction va modifier et renvoyer le nouvel état de l'acteur.

AbstractInitHandler
-------------------

La plupart des acteurs présents dans PowerAPI ont besoin d'initialiser leurs interfaces de communication avec d'autres acteurs ou avec le système (pour utiliser une base de données par exemple). Certains handler ne peuvent fonctionner sans cette initialisation. La classe abstraite :class:`powerapi.AbstractInitHandler <powerapi.handler.abstract_handler.AbstractInitHandler>` ignore les messages reçus tant que l'acteur n'a pas été initialisé.

TimeoutHandler
--------------

Le comportement par défaut peut être configuré pour activer un handler particulier dans le cas ou l'acteur n'a pas reçu de message depuis un certain temps. Cette fonction peut être modifiée en faisant pointer l'attribut :func:`Actor.timeout_handler <powerapi.actor.actor.Actor.timeout_handler` sur la fonction à exécuter dans ce cas.

Report
======

Report
------

Un :class:`powerapi.Report <powerapi.report.report.Report>` correspond à une donnée récupérée dans une base de donnée. La classe permet de simplifier la sérialisation / désérialisation de la donnée. Pour être plus précis, lorsque l’on récupère une donnée dans la BDD, celle-ci nous est retourné brute et pas forcément formaté de la manière dont on le souhaiterait, la plupart du temps sous un format JSON (qui est un format basique en python). La classe :class:`powerapi.ReportModel <powerapi.report_model.report_model.ReportModel>` va redéfinir le format de la donnée pour qu’elle soit désérialisable pour la classe :class:`powerapi.Report <powerapi.report.report.Report>`

.. image:: _static/schema_report.png

ReportModel
-----------

Le :class:`powerapi.ReportModel <powerapi.report_model.report_model.ReportModel>` est une classe qui définit la façon de formater les données selon le type de base de donnée lue. Il est nécessaire de définir un XXXModel, pour chaque XXXReport, et de redéfinir une méthode pour chaque type de base de donnée que l’on souhaite utiliser.

Schéma explicatif :

BDD => Json XXX brut => XXXModel => Json XXX format => XXXReport

Database
========

Une base de donnée permet de stocker des données dans un format et avec des spécificités différentes.
A ce jour, il est possible d’utiliser les types de base de donnée suivantes :

* MongoDB
* Csv

Les bases de données implémentées dans PowerAPI héritent toutes de la classe :class:`powerapi.BaseDB <powerapi.database.base_db.BaseDB>` qui permet de définir une liste de méthode utilisable de façon transparente indépendamment du type de base. Une base est définit par deux choses, d'abord le type de BDD (MongoDB, csv...), et aussi le type de donnée à récupérer. Le second paramètre est donné à la création d'un :class:`powerapi.BaseDB <powerapi.database.base_db.BaseDB>`.  

Message
=======

Les échanges entre les différents acteurs sont effectués par l’envoie de message par leur sockets, et sont divisibles en deux catégories distinctes, les messages de données et les messages de contrôle.

Un message de donnée est en fait un :class:`powerapi.Report <powerapi.report.report.Report>` sérialisé à l’aide de la bibliotèque `pickle <https://docs.python.org/3/library/pickle.html>`_. Ce message est toujours un objet héritant de la classe abstraite :class:`powerapi.Report <powerapi.report.report.Report>`.
Un message de contrôle permet de demander à un acteur d’effectuer une action, qui peuvent dépendre du contexte et du moment ou il reçoit ce message. On peut trouver les messages suivants :

* :class:`powerapi.PoisonPillMessage <powerapi.message.message.PoisonPillMessage>`: Demande à un acteur de s’arrêter.
* :class:`powerapi.StartMessage <powerapi.message.message.StartMessage>`: Demande à un acteur de procéder à son initialisation.
* :class:`powerapi.OKMessage <powerapi.message.message.OKMessage>`: Après l’envoie d’un :class:`powerapi.StartMessage <powerapi.message.message.StartMessage>`, le processus étant en charge de l’initialisation doit attendre une réponse, :class:`powerapi.OKMessage <powerapi.message.message.OKMessage>` est la réponse dans le cas ou l’initialisation s’est bien passé.
* :class:`powerapi.ErrorMessage <powerapi.message.message.ErrorMessage>`: Après l’envoie d’un :class:`powerapi.StartMessage <powerapi.message.message.StartMessage>`, le processus étant en charge de l’initialisation doit attendre une réponse, :class:`powerapi.ErrorMessage <powerapi.message.message.ErrorMessage>` est la réponse dans le cas ou l’initialisation a échoué.
