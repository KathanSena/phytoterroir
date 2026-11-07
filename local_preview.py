"""Serve the Vercel frontend locally, including a server-side GBIF aggregation route."""
from __future__ import annotations
import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pipeline.run import SPECIES, aggregate, fetch_gbif

ROOT=Path(__file__).resolve().parent
WEB=ROOT/"web"

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(WEB),**kwargs)
    def do_GET(self):
        parsed=urlparse(self.path)
        if parsed.path!="/api/occurrences": return super().do_GET()
        query=parse_qs(parsed.query); species=query.get("species",[""])[0]
        if species not in SPECIES: return self.send_json(400,{"error":"Unsupported species."})
        try:
            resolution=max(2,min(5,int(query.get("resolution",["3"])[0])))
            limit=max(50,min(1000,int(query.get("limit",["500"])[0])))
            records=fetch_gbif(species,limit)
            features,summary=aggregate(records,resolution)
            summary={"species":species,"source":"GBIF occurrence search API","record_count":summary["records_aggregated"],"cell_count":summary["aggregate_cells"],"resolution":summary["h3_resolution"],"uncertainty_metadata_share":summary["coordinate_uncertainty_metadata_share"],"privacy_note":summary["privacy_note"]}
            self.send_json(200,{"type":"FeatureCollection","features":features,"summary":summary},[("Cache-Control","no-store")])
        except Exception as exc:
            self.send_json(502,{"error":"Could not retrieve GBIF occurrence data right now. Try again shortly."})
    def send_json(self,status,payload,headers=()):
        body=json.dumps(payload).encode()
        self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(body)))
        for key,value in headers:self.send_header(key,value)
        self.end_headers();self.wfile.write(body)
    def log_message(self,fmt,*args): print(fmt%args)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--port",type=int,default=8502);args=parser.parse_args()
    server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
    print(f"PhytoTerroir Vercel preview at http://127.0.0.1:{args.port}")
    server.serve_forever()


