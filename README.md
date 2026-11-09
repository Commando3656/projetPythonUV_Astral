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
2 - Configurer les filtres
3 - Choisir un répertoire
0 - Quitter
```

Les filtres sont des motifs globaux séparés par des virgules, par exemple
`*.pyc, __pycache__`. Les résultats sont enregistrés dans
`auditMarAx.sqlite3`, dans le répertoire courant. Chaque fichier conserve son
chemin, sa taille, ses dates de modification et de création si disponibles,
son hash SHA-256 et son type MIME estimé à partir du nom.

Les erreurs d'accès aux fichiers sont signalées et le scan continue.
