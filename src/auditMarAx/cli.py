import argparse
import logging
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Sequence

from auditMarAx.scanner import scan_directory


DATABASE = Path("auditMarAx.sqlite3")


def choose_directory() -> Path | None:
    root = tk.Tk()
    try:
        root.withdraw()
        selected = filedialog.askdirectory(
            title="Sélectionnez un répertoire à analyser", parent=root
        )
        return Path(selected) if selected else None
    finally:
        root.destroy()


def read_patterns(prompt: str) -> list[str]:
    value = input(prompt).strip()
    return [pattern.strip() for pattern in value.split(",") if pattern.strip()]


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("auditMarAx.log", encoding="utf-8"),
        ],
        force=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scanner de fichiers")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="MOTIF",
        help="Ignorer un nom ou chemin (option répétable)",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="MOTIF",
        help="Ne garder que les noms ou chemins correspondants (répétable)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    configure_logging()
    directory: Path | None = None
    excludes = args.exclude
    includes = args.include

    try:
        directory = choose_directory()
    except tk.TclError as error:
        logging.error("Impossible d'ouvrir le sélecteur de répertoire : %s", error)

    if directory:
        print(f"Répertoire sélectionné : {directory}")
    else:
        print("Aucun répertoire sélectionné. Choisissez-en un dans le menu.")

    while True:
        print(
            "\n===== Menu principal =====\n"
            "1 - Lancer le scan\n"
            "2 - Configurer les filtres\n"
            "3 - Choisir un répertoire\n"
            "0 - Quitter"
        )
        try:
            choice = input("Choisir : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nArrêt du programme.")
            break

        match choice:
            case "1":
                if directory is None:
                    print("Choisissez d'abord un répertoire (option 3).")
                    continue
                try:
                    scanned, skipped, errors = scan_directory(
                        directory, DATABASE, excludes, includes
                    )
                    print(
                        f"Scan terminé : {scanned} fichier(s) analysé(s), "
                        f"{skipped} ignoré(s), {len(errors)} erreur(s)."
                    )
                    if len(errors) > 5:
                        print(f"... et {len(errors) - 5} autre(s) erreur(s).")
                except (OSError, sqlite3.Error) as error:
                    logging.error("Échec du scan : %s", error)
            case "2":
                try:
                    excludes = read_patterns(
                        "Exclusions (motifs séparés par des virgules, "
                        "vide pour aucune) : "
                    )
                    includes = read_patterns(
                        "Inclusions (motifs séparés par des virgules, "
                        "vide pour toutes) : "
                    )
                    print(f"Exclusions : {excludes or 'aucune'}")
                    print(f"Inclusions : {includes or 'tous les fichiers'}")
                except (EOFError, KeyboardInterrupt):
                    print("\nConfiguration des filtres annulée.")
            case "3":
                try:
                    selected = choose_directory()
                    if selected:
                        directory = selected
                        print(f"Répertoire sélectionné : {directory}")
                    else:
                        print("Sélection annulée.")
                except tk.TclError as error:
                    logging.error("Impossible d'ouvrir le sélecteur : %s", error)
            case "0":
                print("Arrêt du programme.")
                break
            case _:
                print("Choix invalide. Entrez 0, 1, 2 ou 3.")


if __name__ == "__main__":
    main()
