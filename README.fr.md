# 🎶 MusicBrainz2Notion

Un outil pour synchroniser les données des artistes et de la musique depuis MusicBrainz vers des bases de données Notion.
Ajoutez simplement les identifiants des artistes (MBID) dans une base de données Notion, et l'application récupérera et mettra automatiquement à jour leurs données, y compris leurs albums et chansons.

## Sommaire <!-- omit from toc -->

- [📦 Prérequis](#-prérequis)
- [🏃 Guide de démarrage](#-guide-de-démarrage)
- [⚙️ Configuration](#️-configuration)
  - [Ajouter des artistes supplémentaires](#ajouter-des-artistes-supplémentaires)
  - [Mettre à jour les données des artistes](#mettre-à-jour-les-données-des-artistes)

## 📦 Prérequis

- 🐍 Python 3.12 ou supérieur
- 🗄️ Une copie des [bases de données Notion](https://steel-pram-3bf.notion.site/El-Music-Box-2-0-10e20647c8df80368434ea6ac7208981) prédéfinies dans votre espace de travail Notion.
  - 🔑 Créez une [intégration Notion](https://developers.notion.com/docs/create-a-notion-integration#getting-started) pour l'application et obtenez la clé API. N'oubliez pas de donner à l'intégration les autorisations d'accès aux pages.
- 🧑🏻‍🎤 Les MBID des artistes que vous souhaitez synchroniser avec Notion (disponibles sur [MusicBrainz](https://musicbrainz.org/)).
  - Les MBID peuvent être trouvés dans l'URL de la page de l'artiste : `https://musicbrainz.org/artist/<MBID>`.

## 🏃 Guide de démarrage

1. **Créer un environnement virtuel**\
   Exemple en utilisant [uv](https://github.com/astral-sh/uv) :

    ```bash
      # Pour python>=3.12
      pip install uv
      uv venv --python 3.12
      source .venv/bin/activate
    ```

2. **Cloner le dépôt et installer les dépendances**

    ```bash
    git clone https://github.com/Kajiih/musicbrainz2notion
    cd musicbrainz2notion
    pip install -r requirements/base.txt
    ```

3. **Configurer les variables d'environnement**
  
   Renommez `.env.example` en `.env` et renseignez la clé API Notion et les IDs des bases de données.

    - Vous pouvez trouver l'ID de la base de données dans l'URL de la base :
      `<https://www.notion.so/><this_is_the_database_id>?v=<view_id>&pvs=4`
    - Vous pouvez également ajouter une [clé API Fanart.tv](https://fanart.tv/get-an-api-key) pour obtenir de meilleures images d'artistes.

4. **Exécuter l'application pour synchroniser les bases de données `Artist`, `Release` et `Track` :**

    ```bash
    python main.py
    ```

## ⚙️ Configuration

### Ajouter des artistes supplémentaires

  Pour ajouter de nouveaux artistes, créez une nouvelle page dans la [base de données Artist](https://steel-pram-3bf.notion.site/10e20647c8df80ae923cfa8e19d109d4?v=10e20647c8df81a58be0000cbafdcff3) et entrez le MBID de l'artiste dans le champ `MBID`.

### Mettre à jour les données des artistes

  Pour mettre à jour les données d'un artiste, activez le champ `To update` de la page de l'artiste et exécutez à nouveau l'application.
