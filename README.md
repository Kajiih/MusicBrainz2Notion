# 🎶 MusicBrainz2Notion

<!-- TODO: Don't talk about MusicBrainz from the 1st paragraph, explain what it does on a high level and explain what is MusicBrainz -->
<!-- MusicBrainz2Notion is an automated tool that syncs artist and music data to Notion, making it easy to keep your music database up-to-date. By adding artist IDs to a Notion database, the app automatically retrieves and updates data about artists, albums, and songs, providing a centralized place to browse and organize your favorite music.

MusicBrainz2Notion integrates with MusicBrainz, an open-source music database with comprehensive data on artists, albums, and songs. Users simply add the MusicBrainz IDs of artists they want to track in a Notion database, and MusicBrainz2Notion takes care of the rest, fetching artist details and album information and syncing it with Notion. -->
A tool for syncing artist and music data from MusicBrainz to Notion databases.
Simply add artist IDs in a Notion database, and the app will automatically fetch and update their data, including albums and songs.

<!-- TODO: Explain how it works (read the database, looks at `To update` artists and get the data of Artist, their albums and songs from MusicBrainz, and update the database) -->

<p align="center">
  <img src="media/musicbrainz_black_and_white.png" alt="Logo">
</p>

## Contents <!-- omit from toc -->

- [📥 Download](#-download)
- [🏃 Getting Started](#-getting-started)
- [⚙️ Configuration](#️-configuration)
  - [WIP](#wip)

## 📥 Download

Find the latest release for your OS [here](https://github.com/Kajiih/MusicBrainz2Notion/releases).

## 🏃 Getting Started

1. Duplicate the [Notion template](https://steel-pram-3bf.notion.site/El-Music-Box-2-0-10e20647c8df80368434ea6ac7208981) to your Notion workspace.
   - 💡 Note the Artist, Release, and Track database IDs (found in the database page URL: `https://www.notion.so/<workspace>/<database_id>?v=<view_id>`).

2. Set up a [Notion integration](https://developers.notion.com/docs/create-a-notion-integration#getting-started):
   - Create the integration and obtain the Notion API key. Don't forget to grant the permissions to the integration for your newly duplicated page.

3. Look up the [MusicBrainz](https://musicbrainz.org/) IDs (MBIDs) of the artists you want to sync to Notion.
   - 💡 You can find the MBIDs in the URL of the artist's page: `https://musicbrainz.org/artist/<MBID>` or in the `details` tab of the artist's page (e.g. [here](https://musicbrainz.org/artist/5b11f4ce-a62d-471e-81fc-a69a8278c7da/details)).

4. Create new pages in the [`Artist database`](https://steel-pram-3bf.notion.site/10e20647c8df80ae923cfa8e19d109d4?v=10e20647c8df81a58be0000cbafdcff3&pvs=4) and enter the MBIDs in the `mbid` field.
   - 💡 Make sure that the `To update` field is toggled on so that the app knows which artists to sync.

5. [Optional] Configure settings:
   - Edit the [`settings.toml`](./settings.toml) file to set the database IDs and API keys or personalize your database (see [Configuration](#️-configuration)).

6. Run the app and enjoy your new music database 🎶!

## ⚙️ Configuration

### WIP
