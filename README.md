# 🎶 MusicBrainz2Notion

A tool for syncing artist and music data from MusicBrainz to Notion databases.
Simply add artist IDs in a Notion database, and the app will automatically fetch and update their data, including albums and songs.

## Contents <!-- omit from toc -->

- [📦 Requirements](#-requirements)
- [🏃 Getting Started](#-getting-started)
- [⚙️ Configuration](#️-configuration)
  - [Adding more artists](#adding-more-artists)
  - [Updating artists' data](#updating-artists-data)

## 📦 Requirements

- 🐍 Python 3.12 or higher
- 🗄️ A copy of the pre-defined [Notion databases](https://steel-pram-3bf.notion.site/El-Music-Box-2-0-10e20647c8df80368434ea6ac7208981) in your Notion workspace.
  - 🔑 Create a Notion [integration](https://developers.notion.com/docs/create-a-notion-integration#getting-started) for the app and obtain the API key. Don't forget to grant the page permissions to the integration.
- 🧑🏻‍🎤 The MBIDs of the artists you want to sync to Notion (find them on [MusicBrainz](https://musicbrainz.org/)).
  - MBIDs can be found in the URL of the artist's page: `https://musicbrainz.org/artist/<MBID>`.

## 🏃 Getting Started

1. **Create virtual environment**\
    Here's an example using [uv](https://github.com/astral-sh/uv?):

    ```bash
      #  For python>=3.12
      pip install uv
      uv venv --python 3.12
      source .venv/bin/activate
    ```

2. **Clone the repository and install dependencies**

    ```bash
    git clone https://github.com/Kajiih/musicbrainz2notion
    cd musicbrainz2notion
    pip install -r requirements/base.txt
    ```

3. **Configure environment variables**
  
   Rename `.env.example` to `.env` and fill in the notion API key and database IDs.

    - You can find the database id with the link of the database:
    `<https://www.notion.so/><this_is_the_database_id>?v=<view_id>&pvs=4`
    - You can also add a [Fanart.tv api key](https://fanart.tv/get-an-api-key) to fetch better artist images.

4. **Run the app to synchronize the `Artist`, `Release` and `Track` databases:**

    ```bash
    python main.py
    ```

## ⚙️ Configuration

### Adding more artists

  To add more artists, create a new page in the [Artist database](https://steel-pram-3bf.notion.site/10e20647c8df80ae923cfa8e19d109d4?v=10e20647c8df81a58be0000cbafdcff3) and enter the artist's MBID in the `MBID` field.

### Updating artists' data

  To update an artist's data, toggle on the `To update` field of the artist's page and run the app again.
