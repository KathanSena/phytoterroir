import {latLngToCell, cellToBoundary, cellArea} from "h3-js";

const SPECIES = new Set([
  "Rhodiola rosea",
  "Withania somnifera",
  "Nardostachys jatamansi",
  "Hydrastis canadensis",
]);

export default async function handler(req, res) {
  if (req.method !== "GET") {
    res.setHeader("Allow", "GET");
    return res.status(405).json({error: "Use GET."});
  }
  const species = String(req.query.species || "");
  if (!SPECIES.has(species)) return res.status(400).json({error: "Unsupported species."});
  const resolution = Math.max(2, Math.min(5, Number.parseInt(req.query.resolution || "3", 10) || 3));
  const limit = Math.max(50, Math.min(1000, Number.parseInt(req.query.limit || "500", 10) || 500));
  try {
    const rows=[];
    let offset=0;
    while (rows.length < limit) {
      const pageSize=Math.min(300,limit-rows.length);
      const params=new URLSearchParams({scientificName:species,hasCoordinate:"true",hasGeospatialIssue:"false",limit:String(pageSize),offset:String(offset)});
      const response=await fetch(`https://api.gbif.org/v1/occurrence/search?${params}`,{headers:{"User-Agent":"PhytoTerroir/1.0 research prototype"}});
      if (!response.ok) throw new Error(`GBIF returned HTTP ${response.status}`);
      const payload=await response.json();
      const batch=payload.results || [];
      for (const record of batch) {
        if (record.decimalLatitude == null || record.decimalLongitude == null) continue;
        rows.push({lat:Number(record.decimalLatitude),lon:Number(record.decimalLongitude),year:record.year == null ? null : Number(record.year),uncertainty:record.coordinateUncertaintyInMeters == null ? null : Number(record.coordinateUncertaintyInMeters),license:record.license || "Unspecified"});
      }
      offset += batch.length;
      if (!batch.length || batch.length < pageSize) break;
    }
    const groups=new Map();
    const licenses={};
    let uncertaintyCount=0;
    for (const row of rows.slice(0,limit)) {
      const cell=latLngToCell(row.lat,row.lon,resolution);
      if (!groups.has(cell)) groups.set(cell,{cell,records:0,years:[],uncertaintyCount:0});
      const group=groups.get(cell);
      group.records += 1;
      if (row.year != null && Number.isFinite(row.year)) group.years.push(row.year);
      if (row.uncertainty != null && Number.isFinite(row.uncertainty)) {group.uncertaintyCount += 1; uncertaintyCount += 1;}
      licenses[row.license]=(licenses[row.license] || 0)+1;
    }
    const features=[...groups.values()].map(group=>{
      const boundary=cellToBoundary(group.cell).map(([lat,lon])=>[lon,lat]);
      boundary.push(boundary[0]);
      const years=group.years;
      return {type:"Feature",geometry:{type:"Polygon",coordinates:[boundary]},properties:{h3_cell:group.cell,record_count:group.records,year_min:years.length?Math.min(...years):null,year_max:years.length?Math.max(...years):null,uncertainty_metadata_count:group.uncertaintyCount,cell_area_km2:Number(cellArea(group.cell,"km2").toFixed(2))}};
    });
    res.setHeader("Cache-Control","public, s-maxage=1800, stale-while-revalidate=3600");
    res.setHeader("X-Content-Type-Options","nosniff");
    return res.status(200).json({type:"FeatureCollection",features,summary:{species,source:"GBIF occurrence search API",record_count:rows.length,cell_count:features.length,resolution,uncertainty_metadata_share:rows.length?Number((uncertaintyCount/rows.length).toFixed(3)):null,license_counts:licenses,privacy_note:"Coordinates are aggregated server-side to H3 cells before returning. H3 aggregation reduces precision but is not differential privacy or a guarantee of anonymity."}});
  } catch (error) {
    console.error("Occurrence retrieval failed",error);
    return res.status(502).json({error:"Could not retrieve GBIF occurrence data right now. Try again shortly."});
  }
}
