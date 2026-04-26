import os
import json
from datetime import datetime, timedelta, timezone

import requests
from osgeo import gdal

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

import configparser
import os
from pathlib import Path


def load_dotenv_file(dotenv_path: str = ".env") -> None:
    """
    Minimal .env loader without external dependencies.

    Supports lines like:
        CLIENT_ID=abc
        CLIENT_SECRET=xyz

    Existing environment variables are not overwritten.
    """
    path = Path(dotenv_path)

    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        os.environ.setdefault(key, value)


def load_config_file(config_path: str = "config.ini") -> dict[str, str]:
    """
    Loads credentials from config.ini if present.

    Expected format:

        [auth]
        client_id = your_client_id
        client_secret = your_client_secret
    """
    path = Path(config_path)

    if not path.exists():
        return {}

    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")

    if not parser.has_section("auth"):
        return {}

    return {
        "CLIENT_ID": parser.get("auth", "client_id", fallback=""),
        "CLIENT_SECRET": parser.get("auth", "client_secret", fallback=""),
    }


def get_credentials() -> tuple[str, str]:
    """
    Credential priority:
    1. Real environment variables
    2. .env file
    3. config.ini file
    """
    load_dotenv_file(".env")

    config_values = load_config_file("config.ini")

    client_id = os.getenv("CLIENT_ID") or config_values.get("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET") or config_values.get("CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing credentials. Set CLIENT_ID and CLIENT_SECRET in environment, "
            ".env file, or config.ini file."
        )

    return client_id, client_secret

# client credentials
client_id, client_secret = get_credentials()

# Create a session
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Get token for the session
token = oauth.fetch_token(token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
                          client_secret=client_secret, include_client_id=True)
print(token)

SENTINEL_HUB_PROCESS_URL = "https://sh.dataspace.copernicus.eu/process/v1"
# SENTINEL_HUB_PROCESS_URL = "https://services.sentinel-hub.com/api/v1/process"

#ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ3dE9hV1o2aFJJeUowbGlsYXctcWd4NzlUdm1hX3ZKZlNuMW1WNm5HX0tVIn0.eyJleHAiOjE3NzcxOTcwMDMsImlhdCI6MTc3NzE5MzQwMywianRpIjoiMGMwMzYyZDAtNjFjMy00OGUyLTgwMTgtYjM2ZTEzOGIxNGI5IiwiaXNzIjoiaHR0cHM6Ly9zZXJ2aWNlcy5zZW50aW5lbC1odWIuY29tL2F1dGgvcmVhbG1zL21haW4iLCJhdWQiOiJodHRwczovL2FwaS5wbGFuZXQuY29tLyIsInN1YiI6ImY4OWM5NjE3LWNlMmMtNDFmYy1hMzliLTMzM2U4ZTE1ZjQ5MSIsInR5cCI6IkJlYXJlciIsImF6cCI6ImY1YzllZWQ0LTJmNmItNGIxZC1hZTJlLTFlMGNlYWUwZjZiOSIsInNjb3BlIjoiZW1haWwgcHJvZmlsZSIsInBsX3ByaW5jaXBhbF92MiI6InBsOm0ybS9mNWM5ZWVkNC0yZjZiLTRiMWQtYWUyZS0xZTBjZWFlMGY2YjkiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImNsaWVudEhvc3QiOiIxNTYuMTcuMTQ3LjUxIiwicGxfcHJvamVjdCI6ImQ4YzkxMzEwLThjYzYtNGJkMi04MzZkLTBlZTQ3ZjZkMjQ0OCIsInByZWZlcnJlZF91c2VybmFtZSI6InNlcnZpY2UtYWNjb3VudC1mNWM5ZWVkNC0yZjZiLTRiMWQtYWUyZS0xZTBjZWFlMGY2YjkiLCJjbGllbnRBZGRyZXNzIjoiMTU2LjE3LjE0Ny41MSIsImFjY291bnQiOiJkOGM5MTMxMC04Y2M2LTRiZDItODM2ZC0wZWU0N2Y2ZDI0NDgiLCJwbF93b3Jrc3BhY2UiOiJhNmIyZTM5Ni0zNjY5LTQ4YjktYTE5Yi03NmEyZTkwM2NlZjMiLCJjbGllbnRfaWQiOiJmNWM5ZWVkNC0yZjZiLTRiMWQtYWUyZS0xZTBjZWFlMGY2YjkifQ.RsH3xLdGwcsBg2XRRDLGEyIKiN_8Dsex79ylC7ES-uVMBYOoyAXYvjc0pwogpGCq0WeDGIIjANh-9hmfOCmooMMsgukbhbItl98A2mRYdet0WEktjunfiyMtpJJu4icKLnUV1ywcmzjDg6KSJTx30MX3DaFY49xJONq06i0u0ZR5eWRUGMzoRmNgII8g52u1g7CQYa4vt2Uc3z7CxdgidVb4lBqhRwONpUrDt_KlS-dQFTyObOQdsBEpLkNFMiJxTQih6bL_BT72Yn2UAwpKwDo-WlbxNPwagEbGgzzNMbI-VJ5sVcW1EYDUfXbHp52o2ySK_3fVIoXDxrvYlItKUg"
ACCESS_TOKEN = token['access_token']

OUTPUT_DIR = "/mnt/c/Users/MaciejKolczyk/Downloads/sentinel2_downloads_ddz_08_2018_bbox2-test"

#second bbox epsg:32633 POLYGON ((612999.49331500590778887 5619138.53958458639681339, 612968.59329237090423703 5620567.17798305489122868, 614797.39904630649834871 5620607.05724204611033201, 614828.79951258050277829 5619178.42244038730859756, 612999.49331500590778887 5619138.53958458639681339))
BBOX = [
    612999.49331500590778887,
    5619138.53958458639681339,
    614797.39904630649834871,
    5620607.05724204611033201
]
#third bbox POLYGON ((609771.95357188850175589 5619325.38959889020770788, 609738.54233830142766237 5620915.42995613440871239, 611396.48398616339545697 5620950.53488260693848133, 611430.40020454139448702 5619360.4980508042499423, 609771.95357188850175589 5619325.38959889020770788))
# BBOX = [
#     609771.95357188850175589,
#     5619325.38959889020770788,
#     611396.48398616339545697,
#     5620950.53488260693848133
# ]
#fourth bbox POLYGON ((644413.95726400113198906 5662042.62118147779256105, 644291.98924629960674793 5666394.32369121164083481, 648782.82467793230898678 5666522.18712696526199579, 648908.59145775297656655 5662170.52228995133191347, 644413.95726400113198906 5662042.62118147779256105))
# BBOX = [
#     644413.95726400113198906,
#     5662042.62118147779256105,
#     648782.82467793230898678,
#     5666522.18712696526199579
# ]
# fifth bbox POLYGON ((605170.71156961214728653 5632148.78558423556387424, 605170.71156961214728653 5632632.05916688032448292, 605634.39297998649999499 5632632.05916687939316034, 605634.39297998661641032 5632148.78558423556387424, 605170.71156961214728653 5632148.78558423556387424))
# BBOX = [
#     605170.71156961214728653,
#     5632148.78558423556387424,
#     605634.39297998649999499,
#     5632632.05916687939316034,
# ]

CRS = "http://www.opengis.net/def/crs/EPSG/0/32633"

# START_DATE = "2018-07-01"
# END_DATE = "2018-07-31"
START_DATE = "2018-09-01"
END_DATE = "2018-09-30"

STEP_DAYS = 3

BAND_NAMES = [
    "B01 - Coastal aerosol",
    "B02 - Blue",
    "B03 - Green",
    "B04 - Red",
    "B05 - Vegetation red edge 1",
    "B06 - Vegetation red edge 2",
    "B07 - Vegetation red edge 3",
    "B08 - NIR",
    "B8A - B8A",
    "B09 - Water vapour",
    "B11 - SWIR 1",
    "B12 - SWIR 2",
    "NDMI from B8A",
    "NDMI from B08",
    "NDWI",
    "NDVI",
    "Red-Edge Chlorophyll Index",
    "MCARI (Modified Chlorophyll Absorption in Reflectance Index)"
]

EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08","B8A", "B09", "B11", "B12"],
    output: {
        id: "true_color_32float",
        bands: 18,
        sampleType: "FLOAT32"
      }
  }
}

function evaluatePixel(sample) {
  return [
    sample.B01,
    sample.B02,
    sample.B03,
    sample.B04,
    sample.B05,
    sample.B06,
    sample.B07,
    sample.B08,
    sample.B8A,
    sample.B09,
    sample.B11,
    sample.B12,
    ((sample.B8A - sample.B11) / (sample.B8A + sample.B11)),
    ((sample.B08 - sample.B11) / (sample.B08 + sample.B11)),
    ((sample.B03 - sample.B08) / (sample.B03 + sample.B08)),
    ((sample.B08 - sample.B04) / (sample.B08 + sample.B04)),
    ((sample.B08/sample.B05) - 1),
    (((sample.B05 - sample.B04) - 0.2 * (sample.B05 - sample.B03) )* (sample.B05/sample.B04)),
  ]
}
"""


def add_band_names_to_tif(tif_path: str) -> None:
    dataset = gdal.Open(tif_path, gdal.GA_Update)

    if dataset is None:
        raise RuntimeError(f"Could not open GeoTIFF: {tif_path}")

    band_count = dataset.RasterCount

    if band_count != len(BAND_NAMES):
        dataset = None
        raise ValueError(
            f"Expected {len(BAND_NAMES)} bands, but file has {band_count}: {tif_path}"
        )

    for index, band_name in enumerate(BAND_NAMES, start=1):
        band = dataset.GetRasterBand(index)
        band.SetDescription(band_name)
        band.SetMetadataItem("BAND_NAME", band_name)

    dataset.FlushCache()
    dataset = None


def build_request_payload(start_time: datetime, end_time: datetime) -> dict:
    return {
        "input": {
            "bounds": {
                "properties": {
                    "crs": CRS,
                },
                "bbox": BBOX,
            },
            "data": [
                {
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "to": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        }
                    },
                }
            ],
        },
        "output": {
            "resx": 10,
            "resy": 10,
            "responses": [
                {
                    "identifier": "true_color_32float",
                    "format": {
                        "type": "image/tiff",
                    },
                }
            ],
        },
    }


def download_sentinel_image(start_time: datetime, end_time: datetime) -> None:
    payload = build_request_payload(start_time, end_time)

    filename = (
        f"sentinel2_"
        f"{start_time.strftime('%Y%m%d')}_"
        f"{end_time.strftime('%Y%m%d')}.tif"
    )
    output_path = os.path.join(OUTPUT_DIR, filename)

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }

    files = {
        "request": (None, json.dumps(payload), "application/json"),
        "evalscript": (None, EVALSCRIPT, "text/plain"),
    }

    response = requests.post(
        SENTINEL_HUB_PROCESS_URL,
        headers=headers,
        files=files,
        timeout=120,
    )

    if response.status_code == 200:
        with open(output_path, "wb") as file:
            file.write(response.content)

        add_band_names_to_tif(output_path)

        print(f"Downloaded: {output_path}")
    else:
        print(
            f"Failed for {start_time.date()} to {end_time.date()} "
            f"with status {response.status_code}"
        )
        print(response.text)


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    current = datetime.fromisoformat(START_DATE).replace(tzinfo=timezone.utc)
    final = datetime.fromisoformat(END_DATE).replace(tzinfo=timezone.utc)

    while current < final:
        next_date = min(current + timedelta(days=STEP_DAYS), final)

        download_sentinel_image(current, next_date)

        current = next_date


if __name__ == "__main__":
    main()
