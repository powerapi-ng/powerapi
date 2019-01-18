.. How to create a new Database 

un nouveau ``smartwatts.BaseDB``
================================

Tutoriel de création d'un ``BaseDB``.

* ``MyClassDB`` héritant de ``BaseDB``
* Override...
  * ``load``: Charge le bdd
  * ``get_next``: Renvoie le prochain report de la base
  * ``save``: Sauvegarde un report dans la base
