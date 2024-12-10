# 🎶 MusicBrainz2Notion

Un outil pour synchroniser les données d’artistes et de musique depuis MusicBrainz dans Notion.
Ajoutez simplement les identifiants [MusicBrainz](https://musicbrainz.org/) des artistes dans une base de données Notion, et l’app se chargera de récupérer et de mettre automatiquement à jour leurs informations, dont leurs albums et chansons.

<p align="center">
  <img src="media/musicbrainz_black_and_white.png" alt="Logo">
</p>

## Sommaire <!-- omit from toc -->

- [📥 Téléchargement](#-téléchargement)
- [🏃 Mise en route](#-mise-en-route)
- [➕ Ajouter des artistes](#-ajouter-des-artistes)
- [⚙️ Configuration](#️-configuration)
  - [Fichier de configuration](#fichier-de-configuration)
  - [Variables d’environnement](#variables-denvironnement)
  - [Ligne de commande](#ligne-de-commande)

## 📥 Téléchargement

Téléchargez [ici](https://github.com/Kajiih/MusicBrainz2Notion/releases/latest) la dernière version pour votre système d'exploitation.

## 🏃 Mise en route

1. Dupliquez ce [template Notion](https://steel-pram-3bf.notion.site/El-Music-Box-2-0-10e20647c8df80368434ea6ac7208981) dans votre workpace Notion.
   - 💡 Conservez l’URL de la page dupliquée (cmd/ctrl + L pour la copier dans le presse-papiers), vous en aurez besoin la première fois que vous utiliserez l’application.

2. Configurez une [intégration Notion](https://developers.notion.com/docs/create-a-notion-integration#getting-started) :
   - Créez l’intégration et obtenez la clé d’API Notion.
   N’oubliez pas de donner les autorisations nécessaires à l’intégration pour la page que vous venez de dupliquer.

3. Lancez l’application.

    - Lors du premier lancement, vous serez invité à entrer votre clé d’API Notion ainsi que l’URL de la page dupliquée.

4. Découvrez qui est l’artiste mystère du template et profitez de votre nouvelle base de données musicale 🎶 !

## ➕ Ajouter des artistes

D'abord, trouvez les identifiants MusicBrainz (MBIDs) des artistes que vous souhaitez synchroniser.

- 💡 Vous trouverez le MBID dans l’URL de la page de l’artiste : `https://musicbrainz.org/artist/<MBID>` ou dans l’onglet `details` de la page de l’artiste (par exemple, [ici](https://musicbrainz.org/artist/5b11f4ce-a62d-471e-81fc-a69a8278c7da/details) : 5b11f4ce-a62d-471e-81fc-a69a8278c7da).

Une fois que vous avez les MBIDs, créez de nouvelles pages dans la base de données [Artist](https://steel-pram-3bf.notion.site/10e20647c8df80ae923cfa8e19d109d4?v=10e20647c8df81a58be0000cbafdcff3&pvs=4) et renseignez les MBIDs dans le champ `mbid`.

- 💡 Assurez-vous que le champ `To update` est activé pour que l’application sache quels artistes synchroniser.

La prochaine fois que vous lancerez l’application, tous les albums, chansons et informations sur les artistes seront ajoutés à la base de données 🎉 !

## ⚙️ Configuration

### Fichier de configuration

Modifiez le fichier `settings.toml` pour définir les identifiants des bases de données, les clés d’API, ou personnaliser votre base de données.

### Variables d’environnement

Les paramètres par défaut et ceux du fichier de configuration peuvent être remplacés par des variables d’environnement.
Les variables d’environnement peuvent également être lues depuis le fichier `.env` situé dans le répertoire de l’application.

Pour plus d’informations sur les variables d’environnement disponibles, consultez le fichier `.env` fourni en exemple, ainsi que la commande `--help` du programme en ligne de commande.

### Ligne de commande

Si vous utilisez l’application en ligne de commande, vous pouvez également passer des paramètres pour spécifier la clé Notion, les identifiants de base de données, la clé d'APi de Fanart.tv, etc.

Utilisez la commande `--help` pour plus d’informations :

```bash
python src/musicbrainz2notion/main.py --help
```
