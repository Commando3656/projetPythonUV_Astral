import logging
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from auditMarAx.analysis import extension_sizes, find_duplicates, largest_files
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


def show_duplicates(directory: Path) -> None:
    duplicates = find_duplicates(DATABASE, directory)
    if not duplicates:
        print("Aucun doublon trouvé.")
        return

    recoverable = 0
    for size, paths in duplicates:
        recoverable += size * (len(paths) - 1)
        print(f"\nDoublon ({size} octets par fichier) :")
        for path in paths:
            print(f"  {path}")
    print(f"\nEspace récupérable : {recoverable} octets.")


def show_largest_files(directory: Path) -> None:
    files = largest_files(DATABASE, directory)
    if not files:
        print("Aucun fichier indexé. Lancez d'abord un scan.")
        return

    print("\nFichiers les plus volumineux :")
    for path, size in files:
        print(f"{size:>12} octets  {path}")

    print("\nEspace utilisé par extension :")
    for extension, count, size in extension_sizes(DATABASE, directory):
        print(f"{extension or '(sans extension)'} : {count} fichier(s), {size} octets")


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


def main() -> None:
    configure_logging()
    directory: Path | None = None

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
            "2 - Analyser les doublons\n"
            "3 - Classer les fichiers par volume\n"
            "4 - Choisir un répertoire\n"
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
                    print("Choisissez d'abord un répertoire (option 4).")
                    continue
                try:
                    scanned, errors = scan_directory(directory, DATABASE)
                    print(
                        f"Scan terminé : {scanned} fichier(s) analysé(s), "
                        f"{len(errors)} erreur(s)."
                    )
                    if len(errors) > 5:
                        print(f"... et {len(errors) - 5} autre(s) erreur(s).")
                except (OSError, sqlite3.Error) as error:
                    logging.error("Échec du scan : %s", error)
            case "2":
                if directory is None:
                    print("Choisissez d'abord un répertoire (option 4).")
                    continue
                try:
                    show_duplicates(directory)
                except sqlite3.Error as error:
                    print(
                        "Impossible d'analyser la base. Lancez d'abord un scan : "
                        f"{error}"
                    )
                    logging.error("Échec de l'analyse des doublons : %s", error)
            case "3":
                if directory is None:
                    print("Choisissez d'abord un répertoire (option 4).")
                    continue
                try:
                    show_largest_files(directory)
                except sqlite3.Error as error:
                    print(
                        "Impossible d'analyser la base. Lancez d'abord un scan : "
                        f"{error}"
                    )
                    logging.error("Échec du classement des fichiers : %s", error)
            case "4":
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
                print("Choix invalide. Entrez 0, 1, 2, 3 ou 4.")


if __name__ == "__main__":
    main()
