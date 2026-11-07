# Speaker script

## 1. The map is missing half the decision (0:00–0:50)
A species map can show where a medicinal plant has been recorded. It rarely tells a harvester whether a collection is chemically useful, whether removing that plant part harms recovery, or whether sharing the location could put the population at risk. PhytoTerroir explores those connected decisions.

## 2. Harvest by chemistry, protect populations (0:50–1:50)
The concept starts with a practical hypothesis: if field and assay data can identify conditions linked to target compounds, a community might meet a defined need with less biomass. That relationship varies by species, tissue, season and site. We treat it as a research question, not an established universal effect.

## 3. Three decisions in one workflow (1:50–2:45)
The proposed workflow has three layers. First, map habitat and ecological vulnerability with uncertainty. Second, estimate compound response from measured environmental conditions and published assays. Third, compare harvest-part scenarios and reveal locations only at a level approved by the data stewards.

## 4. Occurrences are evidence, not certainty (2:45–3:40)
Occurrence records are uneven. Roads, collectors and digitization programs shape the map. A future model needs spatial bias correction, careful taxonomic review, and spatially separated validation. Co-occurrence alone cannot establish that a plant depends on a fungus or pollinator.

## 5. Stress signals need assay validation (3:40–4:35)
The dashboard names candidate compounds but contains no assay-linked training data. It does not produce a potency score. The next step is to assemble traceable assay observations, standardize units and tissues, then test whether environmental features predict held-out sites.

## 6. Harvest part changes the recovery cost (4:35–5:30)
Leaves, bark, roots and rhizomes have different effects on plant survival and regeneration. The simulator makes that distinction visible, but its recovery rates are assumptions. Local demographic studies must replace them before any quota could be considered.

## 7. Privacy belongs in the map design (5:30–6:35)
Precise coordinates can create real risk. The map converts coordinates into H3 cells and renders aggregate polygons rather than individual markers. That reduces precision, but it is not differential privacy and does not guarantee protection. A real deployment would begin with community governance: who can access what, which outputs are acceptable, and how benefits and risks are shared.

## 8. Prototype you can run today (6:35–7:30)
The dashboard runs locally from synthetic fixtures or can retrieve public occurrence records from GBIF. The map aggregates them into H3 polygons. A command-line pipeline exports aggregate GeoJSON and a JSON summary. The README documents setup, licenses to check and limitations.

## 9. What we can claim, and what we cannot (7:30–8:40)
We can show the product shape and a reproducible data path. We cannot claim reduced biomass, reliable potency forecasts, partner dependence, or safe harvest quotas from this prototype. Those require field data, assay measurements, validation and authorization from the people who steward the knowledge.

## 10. A community governed field pilot (8:40–10:00)
We propose a small, community-led pilot with one species and one landscape. First agree on governance and consent. Then curate licensed records, collect environmental and assay measurements, and study recovery by plant part. Validate the models with independent sites. Only then decide whether a restricted decision-support tool offers value. The measure of success is better decisions under local control, not a more detailed public map.


