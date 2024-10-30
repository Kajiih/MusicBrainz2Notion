# 🎶 MusicBrainz2Notion

Un outil pour synchroniser les données d'artistes et de musique de MusicBrainz dans des bases de données Notion.
Ajoutez simplement les identifiants d'artistes dans une base de données Notion, et l'application récupérera et mettra automatiquement à jour leurs informations, y compris les albums et chansons.

<p align="center">
  <img src="media/musicbrainz_black_and_white.png" alt="Logo">
</p>

## Sommaire <!-- omit from toc -->

- [📥 Téléchargement](#-téléchargement)
- [🏃 Mise en route](#-mise-en-route)
- [⚙️ Configuration](#️-configuration)
  - [WIP](#wip)

## 📥 Téléchargement

Trouvez la dernière version pour votre système d'exploitation [ici](https://github.com/Kajiih/MusicBrainz2Notion/releases).

## 🏃 Mise en route

1. Dupliquez la [template Notion](https://steel-pram-3bf.notion.site/El-Music-Box-2-0-10e20647c8df80368434ea6ac7208981) dans votre espace de travail Notion.
   - 💡 Notez les identifiants des bases de données Artist, Release, et Track (trouvés dans l'URL de la page de la base de données : `https://www.notion.so/<workspace>/<database_id>?v=<view_id>`).

2. Configurez une [intégration Notion](https://developers.notion.com/docs/create-a-notion-integration#getting-started) :
   - Créez l'intégration et obtenez la clé API Notion. N'oubliez pas de donner les autorisations nécessaires à l'intégration pour votre nouvelle page dupliquée.

3. Recherchez les identifiants MusicBrainz (MBIDs) des artistes que vous souhaitez synchroniser dans Notion.
   - 💡 Vous pouvez trouver les MBIDs dans l'URL de la page de l'artiste : `https://musicbrainz.org/artist/<MBID>` ou dans l'onglet "details" de la page de l'artiste (par exemple, [ici](https://musicbrainz.org/artist/5b11f4ce-a62d-471e-81fc-a69a8278c7da/details)).

4. Créez de nouvelles pages dans la base de données [`Artist`](https://steel-pram-3bf.notion.site/10e20647c8df80ae923cfa8e19d109d4?v=10e20647c8df81a58be0000cbafdcff3&pvs=4) et entrez les MBIDs dans le champ `mbid`.
   - 💡 Assurez-vous que le champ `To update` est activé pour que l'application sache quels artistes synchroniser.

5. [Optionnel] Configurez les paramètres :
   - Modifiez le fichier [`settings.toml`](./settings.toml) pour définir les identifiants des bases de données et les clés API, ou pour personnaliser votre base de données (voir [Configuration](#️-configuration)).

6. Lancez l'application et profitez de votre nouvelle base de données de musique 🎶 !

## ⚙️ Configuration

### WIP
