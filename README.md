# 🎶 MusicBrainz2Notion

<!-- TODO: Don't talk about MusicBrainz from the 1st paragraph, explain what it does on a high level and explain what is MusicBrainz -->
<!-- MusicBrainz2Notion is an automated tool that syncs artist and music data to Notion, making it easy to keep your music database up-to-date. By adding artist IDs to a Notion database, the app automatically retrieves and updates data about artists, albums, and songs, providing a centralized place to browse and organize your favorite music.
-->
A tool for syncing artist and music data from MusicBrainz to Notion databases.
Simply add artist [MusicBrainz](https://musicbrainz.org/) IDs in a Notion database, and the app will automatically fetch and update their data, including albums and songs.

<!-- TODO: Explain how it works (read the database, looks at `To update` artists and get the data of Artist, their albums and songs from MusicBrainz, and update the database) -->

<p align="center">
  <img src="media/musicbrainz_black_and_white.png" alt="Logo" width="300">
</p>

## Contents <!-- omit from toc -->

- [📥 Download](#-download)
- [🏃 Getting Started](#-getting-started)
- [➕ Adding artist](#-adding-artist)
- [⚙️ Configuration](#️-configuration)
  - [Configuration file](#configuration-file)
  - [Environment variables](#environment-variables)
  - [Command Line](#command-line)

## 📥 Download

Find the latest release for your OS [here](https://github.com/Kajiih/MusicBrainz2Notion/releases/latest).

## 🏃 Getting Started

1. Duplicate the [Notion template](https://steel-pram-3bf.notion.site/El-Music-Box-2-0-10e20647c8df80368434ea6ac7208981) to your Notion workspace.
   - 💡 Keep note of the url of the duplicated page (`cmd/ctrl + L` to copy to clipboard), you will need it when using the app for the first time.

2. Set up a [Notion integration](https://developers.notion.com/docs/create-a-notion-integration#getting-started):
   - Create the integration and obtain the Notion API key. Don't forget to grant the permissions to the integration for your newly duplicated page.

3. Run the app.
    - You will be prompted for your notion API key and the url of the main page you duplicated.

4. Discover who is the mystery artist in the template and enjoy your new music database 🎶!

## ➕ Adding artist

First, look up the [MusicBrainz](https://musicbrainz.org/) IDs (MBIDs) of the artists you want to sync to Notion.

- 💡 You can find the MBIDs in the URL of the artist's page: `https://musicbrainz.org/artist/<MBID>` or in the `details` tab of the artist's page (e.g. [here](https://musicbrainz.org/artist/5b11f4ce-a62d-471e-81fc-a69a8278c7da/details): `5b11f4ce-a62d-471e-81fc-a69a8278c7da`).

Once you have the artist IDs, create new pages in the [`Artist database`](https://steel-pram-3bf.notion.site/10e20647c8df80ae923cfa8e19d109d4?v=10e20647c8df81a58be0000cbafdcff3&pvs=4) and enter the MBIDs in the `mbid` field.

- 💡 Make sure that the `To update` field is toggled on so that the app knows which artists to sync.

The next time you will run the app, all albums and songs of the artists, as well as all information about the artists themselves will be added to the database 🎉!

## ⚙️ Configuration

### Configuration file

Edit the [`settings.toml`](./settings.toml) file to set the database IDs and API keys or personalize your database.

WIP

### Environment variables

Default settings and settings from the configuration file can be overridden by environment variables.
Environment variables can also be read from the `.env` file in the app folder.

You can find more information an available environment variables in the `.env` template and the `--help` command of the command line.

### Command Line

If you use the app with the command line, you can also use parameters to add the notion key, database IDS, fanart.tv API key, etc.

Use the `--help` command for more information

```bash
python src/musicbrainz2notion/main.py --help
```
