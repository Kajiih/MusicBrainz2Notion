import sys

print(f"{sys.path = }")

import os

import numpy as np
from dotenv import load_dotenv

import musicbrainz2notion

print(f" {os.environ["PYTHONPATH"] = }")
load_dotenv()
print(f" {os.getenv("NOTION_TOKEN") = }")
