# auditMarAx

## Lancer l'application

Depuis la racine du projet :

```bash
uv run auditMarAx
```

Le sélecteur Tkinter sert uniquement à choisir un répertoire. Ensuite, tout se
fait dans le terminal :

```text
1 - Lancer le scan
2 - Analyser les doublons
3 - Classer les fichiers par volume
4 - Choisir un répertoire
0 - Quitter
```

Les résultats sont enregistrés dans `auditMarAx.sqlite3`, dans le répertoire
courant. Chaque fichier conserve son chemin, sa taille, ses dates de
modification et de création si disponibles, son hash SHA-256 et son type MIME
estimé à partir du nom.

L'analyse des doublons compare les hash SHA-256 et estime l'espace récupérable
en gardant un exemplaire de chaque fichier identique. Le classement affiche
les dix fichiers les plus volumineux et l'espace utilisé par extension.
Effectuez un scan avant de lancer ces analyses.

Les erreurs d'accès aux fichiers sont signalées et le scan continue.
Elles sont affichées dans la console et écrites dans `auditMarAx.log`. Les
tests se lancent avec `uv run python -m unittest discover -s tests`.

## Organisation du code

- `cli.py` : menu, arguments et sélection du répertoire.
- `scanner.py` : parcours des fichiers et extraction des métadonnées.
- `database.py` : création/mise à jour de la base SQLite.
- `analysis.py` : doublons, classement des plus gros fichiers et répartition par extension.
- `tests/` : tests du scan, des analyses et de la base.
