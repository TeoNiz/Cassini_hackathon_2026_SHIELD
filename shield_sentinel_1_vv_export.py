import os
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

import requests

SENTINEL_HUB_PROCESS_URL = "https://services.sentinel-hub.com/api/v1/process"


def load_config(config_path="config.json"):
    with open(config_path, "r") as f:
        return json.load(f)


config = load_config()


def get_access_token(client_id: str, client_secret: str) -> str:
    response = requests.post(
        "https://services.sentinel-hub.com/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()["access_token"]


coords = config["coordinates"]

xs = [c[0] for c in coords]
ys = [c[1] for c in coords]

bbox = [
    min(xs),
    min(ys),
    max(xs),
    max(ys),
]

crs = f"http://www.opengis.net/def/crs/EPSG/0/{config['crs']}"

os.makedirs(config["output_dir"], exist_ok=True)

polarization = config.get("polarization", "VV")

evalscript = f"""
//VERSION=3

function setup() {{
    return {{
        input: [{{
            bands: ["{polarization}", "dataMask"]
        }}],
        output: {{
            id: "default",
            bands: 1,
            sampleType: "FLOAT32"
        }},
        mosaicking: "ORBIT"
    }};
}}

function evaluatePixel(samples) {{
    var values = [];

    for (var i = 0; i < samples.length; i++) {{
        if (
            samples[i].dataMask === 1 &&
            samples[i].{polarization} > 0
        ) {{
            values.push(
                10 * Math.log10(samples[i].{polarization})
            );
        }}
    }}

    if (values.length === 0) {{
        return [NaN];
    }}

    values.sort(function(a, b) {{
        return a - b;
    }});

    var half = Math.floor(values.length / 2);

    return values.length % 2
        ? [values[half]]
        : [(values[half - 1] + values[half]) / 2.0];
}}
"""


def build_payload(start_date: str, end_date: str) -> dict:
    return {
        "input": {
            "bounds": {
                "properties": {
                    "crs": crs,
                },
                "bbox": bbox,
            },
            "data": [
                {
                    "type": "sentinel-1-grd",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{start_date}T00:00:00Z",
                            "to": f"{end_date}T00:00:00Z",
                        },
                        "resolution": "HIGH",
                    },
                    "processing": {
                        "orthorectify": True,
                        "backCoeff": "SIGMA0_ELLIPSOID",
                    },
                }
            ],
        },
        "output": {
            "resx": config["resolution"],
            "resy": config["resolution"],
            "responses": [
                {
                    "identifier": "default",
                    "format": {
                        "type": "image/tiff",
                    },
                }
            ],
        },
    }


def download_image(
    access_token: str,
    start_date: str,
    end_date: str,
    output_path: str,
) -> None:
    payload = build_payload(start_date, end_date)

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    files = {
        "request": (
            None,
            json.dumps(payload),
            "application/json",
        ),
        "evalscript": (
            None,
            evalscript,
            "text/plain",
        ),
    }

    response = requests.post(
        SENTINEL_HUB_PROCESS_URL,
        headers=headers,
        files=files,
        timeout=180,
    )

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"Saved: {output_path}")

    else:
        print(f"Error for range {start_date} - {end_date}: " f"{response.status_code}")
        print(response.text)


def main():
    access_token = get_access_token(
        config["sh_client_id"],
        config["sh_client_secret"],
    )

    current_date = datetime.strptime(
        config["start_date"],
        "%Y-%m-%d",
    )

    end_date = datetime.strptime(
        config["end_date"],
        "%Y-%m-%d",
    )

    print(f"Exporting to: {config['output_dir']} " f"| CRS: EPSG:{config['crs']}")

    while current_date < end_date:
        next_date = current_date + relativedelta(
            **{config["interval_unit"]: config["interval_value"]}
        )

        d_start = current_date.strftime("%Y-%m-%d")
        d_end = next_date.strftime("%Y-%m-%d")

        filename = (
            f"{config['base_name']}_"
            f"{d_start}_"
            f"{polarization}_"
            f"EPSG{config['crs']}.tif"
        )

        output_path = os.path.join(
            config["output_dir"],
            filename,
        )

        try:
            download_image(
                access_token=access_token,
                start_date=d_start,
                end_date=d_end,
                output_path=output_path,
            )

        except Exception as e:
            print(f"Download error " f"{d_start} - {d_end}: {e}")

        current_date = next_date


if __name__ == "__main__":
    main()
