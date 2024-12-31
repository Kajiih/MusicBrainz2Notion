# 🎶 MusicBrainz2Notion

A tool for syncing artist and music data from MusicBrainz to Notion databases.
Simply add artist [MusicBrainz](https://musicbrainz.org/) IDs in a Notion database, and the app will automatically fetch and update their data, including albums and songs.

> ✨ MusicBrainz is an open and collaborative music encyclopedia that collects music metadata and makes it available to the public.

<br />
<p align="center">
  <img src="media/screenshots/artist_db.png" alt="MusicBrainz2Notion Artist Database" style="max-width: 850px; height: auto; border-radius: 10px;">
</p>

## 📸 Screenshots <!-- omit from toc -->

<details>
  <summary>Click to expand screenshots</summary>

### Artist Database - Tier List View

![Artist Database](media/screenshots/artist_db.png)

### Release Database - Table View

![Release Database](media/screenshots/release_db.png)

### Tracks Database - Table View

![Track Database](media/screenshots/track_db.png)

</details>

## Contents <!-- omit from toc -->

- [⬇️ Download](#️-download)
- [🏃 Getting Started](#-getting-started)
- [➕ Adding artists](#-adding-artists)
- [⚙️ Configuration](#️-configuration)
  - [📝 Configuration file](#-configuration-file)
  - [🌐 Environment variables](#-environment-variables)
  - [🖥️ Command-Line Arguments](#️-command-line-arguments)
- [⚠️ Current Limitations](#️-current-limitations)

## ⬇️ Download

Find the latest release for your OS [here](https://github.com/Kajiih/MusicBrainz2Notion/releases/latest).

## 🏃 Getting Started

1. Duplicate the [Notion template](https://steel-pram-3bf.notion.site/El-Music-Box-2-0-10e20647c8df80368434ea6ac7208981) to your Notion workspace.
     - The template comes with several views of the databases, like special views for tier lists, but you can customize them at will!

     > 💡 Keep note of the url of the duplicated page (`cmd/ctrl + L` to copy to clipboard), you will need it when using the app for the first time.

2. Set up a [Notion integration](https://developers.notion.com/docs/create-a-notion-integration#getting-started):
   - Create the integration and obtain the Notion API key. Don't forget to grant the permissions to the integration for your newly duplicated page.

3. Run the app.
    - You will be prompted for your notion API key and the url of the main page you duplicated.
    - ❗ The first time you run the app, it will download a small part of MusicBrainz dataset so you need around free 10 GB in the app's folder. But don't worry, after processing the data, it only take only around 200 MB.

4. Discover who is the mystery artist in the template and enjoy your new music database 🎶!

## ➕ Adding artists

First, look up the MusicBrainz IDs (MBIDs) of the artists you want to sync to Notion.

> 💡 [MBIDs](https://musicbrainz.org/doc/MusicBrainz_Identifier) are universal unique identifiers for artists, releases and songs. You can find the MBIDs in the URL of the artist's page: `https://musicbrainz.org/artist/<MBID>` or in the `details` tab of the artist's page (e.g. [here](https://musicbrainz.org/artist/5b11f4ce-a62d-471e-81fc-a69a8278c7da/details): `5b11f4ce-a62d-471e-81fc-a69a8278c7da`).

Once you have the artist IDs, create new pages in the [`Artist database`](https://steel-pram-3bf.notion.site/10e20647c8df80ae923cfa8e19d109d4?v=10e20647c8df81a58be0000cbafdcff3&pvs=4) and enter the MBIDs in the `mbid` field.

> 💡 Make sure that the `To update` field is toggled on so that the app knows which artists to sync.

The next time you will run the app, all albums and songs of the artists, as well as all information about the artists themselves will be added to the database 🎉!

## ⚙️ Configuration

Use the configuration to:

- add a [fanart.tv](https://fanart.tv/) if you want better artist thumbnails
- update the notion api key or database ids
- change the release filters
- change the number of tags per page
- force the update of the database used to find [canonical releases](https://musicbrainz.org/doc/Canonical_MusicBrainz_data)

Configuration is loaded from three sources, from lowest to highest priority:

 1. Configuration file
 2. Environment variables
 3. Command-line arguments

### 📝 Configuration file

Edit the [`settings.toml`](./settings.toml) file located  in the application folder to update your database IDs, API keys, and personalize synchronization settings.

> 💡 When you are prompted for the notion API key and the link of the database, the configuration file is automatically updated.

The configuration file is straightforward and includes comments to guide you through each setting.

### 🌐 Environment variables

Some settings can be overridden by environment variables.
These can also be read from the `.env` file located in the application folder.

For more information on available environment variables, refer to the `.env` template and use the `--help` command with the command-line app.

### 🖥️ Command-Line Arguments

It’s recommended to use a virtual environment for installation (for example with [uv](https://docs.astral.sh/uv/)).
Then install the application with:

```bash
pip install musicbrainz2notion
```

Now you can run the app via the command line and pass parameters such as the Notion API key, database IDs, or your fanart.tv API key.

```bash
musicbrainz2notion --notion YOUR_NOTION_API_KEY
```

Use the `--help` command to see all available options.

## ⚠️ Current Limitations

- **Large Databases**: The app isn’t fully optimized for very large databases yet, which may cause slower startup times as the number of pages increases.
- **Notion API**: The Notion API can sometimes be unreliable, and not every scenario is covered yet—occasional crashes may occur.
- **Canonical release downloads**: Sometimes, the canonical release database has to be updated, which can take some time and requires approximately 10 GB of free disk space during the update process.
