.. How to create a Report 

un nouveau ``powerapi.Report``
=====================================

Tutoriel de création d'un ``Report``.

* ``MyClassReport`` héritant de ``Report``
* Override...
  * ``serialize``: Retourne le report sous forme JSON
  * ``deserialize``: Remplit le report avec les données du JSON en param
* ``MyClassModel`` héritant de ``Model``
* Override
  * ``from_xxx``: Permet à partir de transformé une donnée brute en BDD vers un JSON utilisable pour le ``Report``
