# PhytoTerroir

**Community governed plant intelligence, with location aggregation built into the map.**

PhytoTerroir explores medicinal plant occurrence evidence and hypothetical harvest trade-offs. The Vercel web app fetches GBIF records through a serverless API, converts coordinates into H3 cells on the server, then returns aggregate polygons. The browser never receives the live individual coordinates. A scenario lab compares harvest-part assumptions with an illustrative recovery curve.

## Run the Vercel web app locally

The lightweight front end runs from `web/`. Python serves the static app and a local server-side aggregation endpoint:

```powershell
python -m pip install -r requirements.txt
python local_preview.py --port 8502
```

Open `http://127.0.0.1:8502`. Demo mode works offline after page assets load. Live GBIF mode needs network access.

The original Streamlit research prototype remains available:

```powershell
streamlit run app/main.py
```

## Data modes

- **Synthetic demo** uses teaching fixtures in `web/occurrences-demo.csv`.
- **Live GBIF** retrieves coordinate-bearing records for four selected species. The Vercel function at `api/occurrences.js` aggregates records to H3 polygons before sending a response. Records are cached for 30 minutes.

The command line pipeline at `pipeline/run.py` follows the same H3 aggregate export pattern. It does not export individual point features.

## Deploy to Vercel

1. Push this project to a GitHub repository.
2. In Vercel, import that repository. The configuration uses `web/` as the static output directory and `api/occurrences.js` as a Node function.
3. Set `main` as the production branch. Vercel creates preview deployments for other branches and production deployments from the production branch.
4. Add your friend as a GitHub collaborator. When they push approved changes to `main`, Vercel publishes those changes as the production version. For safer review, have them create a pull request, inspect the preview deployment, then merge it into `main`.

Do not store GBIF tokens or other secrets in the repository. The current project has no required secrets.

## GitHub collaboration and final changes

The `main` branch is the source of truth for the final code. Your friend can edit a branch and submit a pull request. Vercel will build a preview for review; changes become final when merged into `main`, which triggers the production deployment. Direct commits to `main` also become production when pushed, if branch protections allow them.

## What the dashboard does

- Aggregates occurrence coordinates to H3 hexagons before rendering. It never draws individual points.
- Summarizes record count, H3 cell count, coordinate-uncertainty metadata and record year span.
- Shows dense cells as observation evidence, not abundance or habitat quality.
- Provides a harvest-part and removal-pressure scenario lab using explicitly hypothetical rates.
- Separates occurrence evidence from compound research questions and data-governance considerations.

## Important limits

The project does **not** contain assay-linked phytochemical data, validated habitat models, partner-dependence evidence, conservation status assessments, or demographic regeneration measurements. The scenario curve does not estimate a safe yield or quota. Do not use the prototype to authorize harvest, trade, conservation action or medical decisions.

H3 aggregation reduces coordinate precision but is **not differential privacy** and does not guarantee anonymity. Sparse cells or joining with external data may still expose a location. A community deployment must establish consent, data stewardship, access controls, benefit sharing, retention rules and a re-identification threat model before importing protected coordinates or traditional knowledge.

## Data and licensing

- [GBIF occurrence search API](https://api.gbif.org/v1/occurrence/search): record licenses vary. Preserve attribution, license and dataset citations, and obtain a GBIF download DOI for reproducible publications. See [GBIF citation guidelines](https://www.gbif.org/citation-guidelines).
- Bundled demo records are synthetic fixtures and should not be cited as field observations.
- Open-Meteo, SoilGrids, IUCN, CITES and phytochemical assays are not integrated. Review their terms and access requirements before adding data.

## Project structure

- `web/`: Vercel static web client.
- `api/occurrences.js`: server-side GBIF retrieval and H3 aggregation.
- `local_preview.py`: local preview server with the same aggregate API response shape.
- `app/main.py`: Streamlit research prototype.
- `pipeline/run.py`: offline/live H3 aggregate GeoJSON pipeline.
- `data/demo/occurrences.csv`: synthetic fixtures for the Streamlit prototype.
- `artifacts/`: generated aggregate GeoJSON and summary JSON.
- `docs/DEVPOST.md`: submission draft.
- `docs/pitch.html` and `docs/speaker_script.md`: pitch deck and script.

## CLI pipeline

```bash
python pipeline/run.py --offline --species "Rhodiola rosea" --resolution 3
python pipeline/run.py --species "Rhodiola rosea" --limit 250 --resolution 3
```

The pipeline writes aggregate H3 polygons and a JSON summary to `artifacts/`. H3 aggregation is not a formal privacy guarantee.
