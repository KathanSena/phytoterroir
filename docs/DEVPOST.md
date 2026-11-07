# Devpost submission draft: PhytoTerroir

## Tagline
Explore medicinal plant occurrence evidence and harvest trade-offs with H3 location aggregation built into the map.

## Inspiration
Medicinal plant decisions connect ecology, chemistry, harvesting practice and knowledge stewardship. Occurrence maps can support research, but exact locations may also put rare populations at risk. We built a prototype that makes location aggregation visible in the product itself and separates recorded evidence from unvalidated assumptions.

## What it does
PhytoTerroir is a local decision exploration dashboard. Users can choose one of four medicinal species, view synthetic demo records or retrieve public occurrence records from GBIF, and inspect the records as H3 aggregate cells. The map never renders individual occurrence points. A second workspace explores hypothetical harvest-part and removal-pressure scenarios using a clearly labeled illustrative recovery curve.

The chemistry panel names candidate compounds while stating that no assay-linked training data are included. The governance panel explains why H3 aggregation is not a privacy guarantee and why communities must control sensitive data use.

## How we built it
Python, Streamlit, Pandas, NumPy, PyDeck, H3 and the GBIF occurrence API. The app keeps coordinates in process memory, aggregates to H3 cells, and sends aggregate polygons to the map. Synthetic CSV fixtures make the experience usable offline. A command-line pipeline uses the same H3 aggregation and exports aggregate polygons plus a JSON summary.

## What makes the prototype different
Privacy is part of the map data path, not a cosmetic overlay: the map receives H3 cell polygons and aggregate counts rather than individual records. The experience also distinguishes observed occurrence records from scenario assumptions and missing evidence.

## What's next
A responsible field pilot needs community-defined governance, licensed and curated occurrence data, environmental measurements, species- and tissue-specific assays, partner-species evidence, population regeneration studies and independent spatial validation. Formal privacy analysis and access controls should be designed with data stewards before sensitive local data are used.

## Responsible use
This prototype does not estimate phytochemical potency, habitat suitability, a sustainable harvest quota or population abundance. Scenario outputs are educational placeholders and must not guide harvest authorization, trade or medical decisions. Publicly available records may still include sensitive locations. H3 aggregation reduces precision but does not guarantee anonymity. Consult the README for limitations, licensing and governance guidance.

## Data and licenses
Live mode requests coordinate-bearing GBIF records. GBIF record licenses and attribution vary by source dataset. Check record-level terms and cite the relevant datasets and download DOI before reuse or publication. Demo records are synthetic. No IUCN, CITES, SoilGrids, Open-Meteo or assay data are integrated.

## Built with
Python, Streamlit, Pandas, NumPy, PyDeck, H3, GBIF API

