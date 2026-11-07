"""Fetch occurrence evidence and export only aggregate H3 polygons."""
from __future__ import annotations
import argparse
import csv
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import h3

ROOT=Path(__file__).resolve().parents[1]
SPECIES=["Withania somnifera","Nardostachys jatamansi","Rhodiola rosea","Hydrastis canadensis"]

def get_json(url: str, params: dict) -> dict:
    request=Request(url+"?"+urlencode(params),headers={"User-Agent":"PhytoTerroir/1.0 research prototype"})
    with urlopen(request,timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))

def fetch_gbif(name: str, limit: int) -> list[dict]:
    rows=[]; offset=0
    while len(rows)<limit:
        take=min(300,limit-len(rows))
        data=get_json("https://api.gbif.org/v1/occurrence/search",{"scientificName":name,"hasCoordinate":"true","hasGeospatialIssue":"false","limit":take,"offset":offset})
        results=data.get("results",[])
        for item in results:
            lat=item.get("decimalLatitude"); lon=item.get("decimalLongitude")
            if lat is None or lon is None: continue
            rows.append({"lat":float(lat),"lon":float(lon),"year":item.get("year"),"uncertainty":item.get("coordinateUncertaintyInMeters"),"license":item.get("license")})
        if len(results)<take: break
        offset+=len(results); time.sleep(.2)
    return rows[:limit]

def load_demo(name: str) -> list[dict]:
    with (ROOT/"data/demo/occurrences.csv").open(encoding="utf-8-sig",newline="") as file:
        return [{"lat":float(row["lat"]),"lon":float(row["lon"]),"year":row.get("year"),"uncertainty":row.get("coordinateUncertaintyInMeters"),"license":"Synthetic fixture"} for row in csv.DictReader(file) if row["species"]==name]

def aggregate(records: list[dict], resolution: int) -> tuple[list[dict],dict]:
    buckets={}
    for record in records:
        cell=h3.latlng_to_cell(record["lat"],record["lon"],resolution)
        item=buckets.setdefault(cell,{"records":0,"years":[],"uncertainty_count":0})
        item["records"]+=1
        if record.get("year"):
            try: item["years"].append(int(record["year"]))
            except (TypeError,ValueError): pass
        if record.get("uncertainty") not in (None,""): item["uncertainty_count"]+=1
    features=[]
    for cell,item in buckets.items():
        ring=[[lon,lat] for lat,lon in h3.cell_to_boundary(cell)]
        ring.append(ring[0])
        years=item["years"]
        features.append({"type":"Feature","geometry":{"type":"Polygon","coordinates":[ring]},"properties":{"h3_cell":cell,"record_count":item["records"],"year_min":min(years) if years else None,"year_max":max(years) if years else None,"records_with_coordinate_uncertainty":item["uncertainty_count"],"cell_area_km2":round(h3.cell_area(cell,unit="km^2"),2)}})
    total_uncertainty=sum(item["uncertainty_count"] for item in buckets.values())
    summary={"records_aggregated":len(records),"h3_resolution":resolution,"aggregate_cells":len(features),"records_with_coordinate_uncertainty":total_uncertainty,"coordinate_uncertainty_metadata_share":round(total_uncertainty/len(records),3) if records else None,"privacy_note":"H3 aggregation reduces coordinate precision but is not differential privacy and does not guarantee anonymity."}
    return features,summary

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--species",choices=SPECIES,default="Rhodiola rosea")
    parser.add_argument("--limit",type=int,default=250)
    parser.add_argument("--resolution",type=int,choices=[2,3,4,5],default=3)
    parser.add_argument("--offline",action="store_true",help="Use synthetic demo fixtures instead of GBIF")
    args=parser.parse_args()
    records=load_demo(args.species) if args.offline else fetch_gbif(args.species,args.limit)
    if not records: raise SystemExit("No coordinate-bearing records returned. Try --offline or another species.")
    features,summary=aggregate(records,args.resolution)
    summary.update({"species":args.species,"source":"synthetic demo fixture" if args.offline else "GBIF occurrence search API","model":"occurrence evidence only; no habitat, chemistry or harvest prediction"})
    out=ROOT/"artifacts"; out.mkdir(exist_ok=True)
    geo={"type":"FeatureCollection","metadata":{"species":args.species,"source":summary["source"],"note":summary["privacy_note"]},"features":features}
    (out/"occurrences.geojson").write_text(json.dumps(geo,indent=2),encoding="utf-8")
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(f"Wrote {len(features)} H3 aggregate cells from {len(records)} records to {out}")
if __name__=="__main__": main()




