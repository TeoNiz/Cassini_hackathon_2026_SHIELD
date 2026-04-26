# SHIELD — Satellite-based Hydraulic Infrastructure Evaluation for Leak Detection

![SHIELD concept](idea.png)

**SHIELD** is a proof-of-concept developed for the **CASSINI Hackathon 2026: Space for Water**.  
The project explores how freely available **Copernicus Sentinel satellite data** can support early detection of potential water losses and infrastructure-related anomalies in water distribution systems.

The core idea is simple: if an underground leak or infrastructure failure changes local soil moisture or creates surface-water anomalies, this signal may be visible in time series of satellite-derived indicators. SHIELD uses Sentinel imagery to monitor selected infrastructure points and their surroundings, producing interpretable metrics and visualisations that can help utilities prioritise field inspections.

---

## Problem

Water utilities are under increasing pressure to reduce water losses, improve operational efficiency and modernise infrastructure. This is especially challenging for small and medium-sized utilities, where dense networks of flow meters, pressure sensors or continuous monitoring systems may be limited or absent.

Leaks are often difficult to detect early because they can remain invisible at the surface. At the same time, undetected water losses may increase operational costs, energy consumption, contamination risk and the probability of infrastructure failure.

---

## Our approach

SHIELD investigates whether satellite data can provide an additional, scalable monitoring layer for water infrastructure.

The current repository focuses on the technical proof-of-concept:

- automatic download of Sentinel-2 data for selected areas and time windows,
- extraction of multiple spectral bands and satellite-derived indices,
- computation of local statistics around selected infrastructure points,
- comparison of values across consecutive satellite images,
- basic visualisation of temporal changes in selected indicators.

The prototype currently works with cut-out Sentinel-2 GeoTIFF scenes and point geometries representing monitored locations.

---

## Current prototype features

### 1. Sentinel-2 data download

The script `automatic_download_sentinel_data_for_selected_area.py` uses the Copernicus Data Space / Sentinel Hub Process API to download Sentinel-2 L2A data for a selected bounding box and date range.

The current processing request includes:

- Sentinel-2 reflectance bands:
  - B01, B02, B03, B04, B05, B06, B07, B08, B8A, B09, B11, B12,
- selected spectral indices:
  - NDMI using B8A and B11,
  - NDMI using B08 and B11,
  - NDWI,
  - NDVI,
  - Red-Edge Chlorophyll Index,
  - MCARI.

The downloaded outputs are saved as multi-band GeoTIFF files.

### 2. Spectral index analysis

The notebook `spectral_indices.ipynb` processes multi-band Sentinel-2 GeoTIFF files and calculates selected statistics around points provided as an ESRI Shapefile.

For each image, the workflow can calculate values such as:

- NDVI mean and median,
- NDMI mean and median,
- MNDWI mean and median,
- mean and median values of individual Sentinel-2 bands,
- number of selected pixels,
- number of valid pixels,
- valid pixel fraction.

The output is saved as a CSV file, where each row represents one Sentinel-2 image and its aggregated values for the selected point area.

### 3. Time-series visualisation

The resulting CSV can be used to plot changes in selected indices over time, for example:

- NDVI,
- NDMI,
- MNDWI,
- mean vs. median values,
- sudden changes between consecutive acquisitions.

These visualisations are intended to support early interpretation of whether a location behaves normally or shows a potential anomaly.

---

## Why Sentinel-2 indicators?

The current proof-of-concept uses Sentinel-2 mainly as a surface and vegetation context layer.

Key indicators:

| Indicator | Purpose |
|---|---|
| **NDVI** | vegetation condition and vegetation-cover context |
| **NDMI** | vegetation and surface moisture-related signal |
| **MNDWI** | possible surface water or local wetness anomalies |
| **B11 / B12** | SWIR information useful for moisture and surface-state interpretation |
| **Red-edge bands** | vegetation stress and condition monitoring |

In the target solution, Sentinel-2 indicators should be combined with **Sentinel-1 SAR** data, rainfall information and local background comparison to distinguish true local anomalies from weather-driven regional wetness.

---

## Target users

SHIELD is designed primarily for:

- small and medium-sized water utilities,
- municipal infrastructure operators,
- local governments responsible for water infrastructure,
- maintenance teams planning field inspections,
- insurers and farmers affected by infrastructure-related water damage.

The solution is especially relevant where ground monitoring infrastructure is sparse and where satellite observations can provide a low-cost additional screening layer.

---

## Planned development

### Phase 1 — Hackathon / Proof of Concept

- Build simple scripts for selected Sentinel-based indicators.
- Process selected infrastructure locations.
- Generate first time-series plots.
- Demonstrate whether local moisture-related changes are visible in satellite data.

### Phase 2 — Validation pilot

- Test the approach on real operational or historical failure cases.
- Add rainfall correction and local background comparison.
- Extend the method with Sentinel-1 SAR data.
- Validate whether detected anomalies correspond to relevant field events.

### Phase 3 — Minimum Viable Product

- Build a web dashboard.
- Add alert scoring and anomaly visualisation.
- Track false positives and false negatives.
- Collect feedback from at least one external stakeholder.

### Phase 4 — Commercial beta

- Support several paid pilot customers.
- Add automatic reporting.
- Improve operational robustness.
- Prepare integration with GIS and infrastructure-management tools.

### Phase 5 — Version 1.0 and scaling

- Release a scalable product version.
- Improve detection models using customer feedback.
- Support larger monitored areas and multiple clients.
- Add recurring reporting and operational deployment workflows.

---

## Repository structure

```text
.
├── automatic_download_sentinel_data_for_selected_area.py
├── spectral_indices.ipynb
└── README.md
```

---

## Setup

Create a Python environment and install the main geospatial dependencies:

```bash
pip install requests numpy pandas rasterio geopandas matplotlib
```

Depending on your system, installing GDAL-related packages may require using Conda:

```bash
conda install -c conda-forge gdal rasterio geopandas
```

---

## Authentication

The Sentinel download script expects Copernicus Data Space / Sentinel Hub credentials.

You can provide them as environment variables:

```bash
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
```

or through a local `.env` file:

```text
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
```

or through `config.ini`:

```ini
[auth]
client_id = your_client_id
client_secret = your_client_secret
```

Do not commit credentials to the repository.

---

## Example workflow

1. Define the area of interest as a bounding box.
2. Set the date range and time step.
3. Run the Sentinel-2 download script.
4. Prepare an ESRI Shapefile with points of interest.
5. Run the spectral-index notebook.
6. Export aggregated metrics to CSV.
7. Plot NDVI, NDMI and MNDWI changes over time.

---

## Example output

The current workflow produces a CSV table similar to:

| image_file | date_from | date_to | NDVI_mean | NDMI_mean | MNDWI_mean | valid_fraction |
|---|---:|---:|---:|---:|---:|---:|
| sentinel2_20180704_20180707.tif | 2018-07-04 | 2018-07-07 | ... | ... | ... | ... |
| sentinel2_20180713_20180716.tif | 2018-07-13 | 2018-07-16 | ... | ... | ... | ... |

These values can then be visualised as a time series.

---

## Limitations of the current prototype

This repository is an early hackathon proof-of-concept. It is not yet a production leak-detection system.

Current limitations include:

- Sentinel-2 observations are affected by clouds and cloud shadows.
- The current prototype focuses on Sentinel-2 indicators and does not yet include full Sentinel-1 anomaly detection.
- Satellite signals may be affected by vegetation growth, surface changes, land use and weather.
- The current metrics should be treated as anomaly indicators, not direct measurements of underground leakage.
- Operational validation against real failure records is required.

---

## Next steps

The most important next technical steps are:

- add Sentinel-1 SAR-based local wetness anomaly detection,
- add rainfall correction using weather or reanalysis data,
- compare each monitored point against its local background area,
- add cloud and scene-quality filtering,
- validate detections against known leak or infrastructure-failure events,
- create an interactive dashboard for anomaly review.

---

## Team

SHIELD is developed by an interdisciplinary team combining expertise in:

- environmental engineering,
- hydrology,
- GIS,
- satellite data analysis,
- machine learning,
- software development,
- water utility operations,
- visual communication and design.

---

## Project links

- CASSINI project page: https://taikai.network/cassinihackathons/hackathons/space-for-water/projects/cmnzx2zt202bs1axa8vl2nywy/idea
- Repository: https://github.com/TeoNiz/Cassini_hackathon_2026_SHIELD

---
