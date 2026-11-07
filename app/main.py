import h3
import numpy as np
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
SPECIES = {
    "Rhodiola rosea": {"compound": "Salidroside and rosavins", "region": "Alpine and subalpine habitats"},
    "Withania somnifera": {"compound": "Withanolides", "region": "Dry and semi-arid habitats"},
    "Nardostachys jatamansi": {"compound": "Jatamansone and related sesquiterpenes", "region": "Himalayan alpine habitats"},
    "Hydrastis canadensis": {"compound": "Berberine", "region": "Eastern North American forests"},
}
PARTS = {
    "Leaf": {"factor": 1.0, "label": "Lower assumed impact", "copy": "Leaf removal can be less damaging, though repeated defoliation still affects plant health."},
    "Flower / fruit": {"factor": 1.7, "label": "Moderate assumed impact", "copy": "Removing reproductive parts can reduce seed production and future recruitment."},
    "Bark": {"factor": 3.0, "label": "High assumed impact", "copy": "Bark removal can injure or girdle woody plants. Species and technique matter."},
    "Root / rhizome": {"factor": 5.0, "label": "Very high assumed impact", "copy": "Removing underground organs can kill the individual or delay recovery."},
}

st.set_page_config(page_title="PhytoTerroir | Field intelligence", page_icon="🌿", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{--forest:#183a2f;--moss:#3e7252;--lime:#c5df91;--paper:#f5f5ee;--ink:#1c3027;--muted:#728077;--line:#dfe5da;}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:var(--ink)}.stApp{background:var(--paper)!important;color:var(--ink)!important}.stApp [data-testid="stMarkdownContainer"],.stApp [data-testid="stMarkdownContainer"] *{color:var(--ink)!important}.stApp [data-testid="stWidgetLabel"] p,.stApp [data-testid="stCaptionContainer"]{color:var(--muted)!important}.stApp [data-testid="stMarkdownContainer"] .hero,.stApp [data-testid="stMarkdownContainer"] .hero p,.stApp [data-testid="stMarkdownContainer"] .hero h1,.stApp [data-testid="stMarkdownContainer"] .hero .eyebrow,.stApp [data-testid="stMarkdownContainer"] .hero .hero-chip{color:#f6f4e9!important}.stApp [data-testid="stMarkdownContainer"] .hero .eyebrow{color:var(--lime)!important}.stApp [data-testid="stMarkdownContainer"] .metric-label,.stApp [data-testid="stMarkdownContainer"] .metric-foot{color:var(--muted)!important}.stApp [data-testid="stMarkdownContainer"] .risk-box{color:#554720!important}.stApp [data-testid="stMarkdownContainer"] .evidence{color:#324a3c!important}
.block-container{max-width:1440px;padding-top:1.2rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#edf0e7;border-right:1px solid var(--line)}
.hero{position:relative;overflow:hidden;background:var(--forest);border-radius:22px;padding:34px 40px;color:#f6f4e9;margin-bottom:22px}
.hero:after{content:'✳';position:absolute;right:7%;top:-74px;font-size:250px;color:#ffffff0b;line-height:1}
.hero h1{-webkit-text-fill-color:#f6f4e9!important;color:#f6f4e9!important;font:800 clamp(38px,5vw,62px) 'Manrope',sans-serif;letter-spacing:-.055em;margin:3px 0 8px;color:#f6f4e9}
.hero p{max-width:780px;color:#d2ddcf;font-size:17px;line-height:1.55;margin:0}.eyebrow{font:500 11px 'DM Mono',monospace;letter-spacing:.16em;text-transform:uppercase;color:var(--lime)}
.hero-chip{position:absolute;right:32px;bottom:27px;border:1px solid #ffffff38;border-radius:30px;padding:8px 13px;font:11px 'DM Mono',monospace;color:#e0ebd6;z-index:1}
.metric-card{height:110px;border:1px solid var(--line);border-radius:15px;background:#fff;padding:16px 19px;box-shadow:0 3px 12px #193c2910}
.metric-label{font:500 10px 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.12em;color:var(--muted)}
.metric-value{font:700 31px 'Manrope',sans-serif;color:var(--forest);margin-top:5px;letter-spacing:-.04em}
.metric-foot{font-size:11px;color:var(--muted);margin-top:1px}
.section-label{font:500 11px 'DM Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--moss);margin:6px 0 8px}
.evidence{background:#e9efe3;border-left:4px solid var(--moss);border-radius:0 12px 12px 0;padding:15px 18px;color:#324a3c;font-size:14px;line-height:1.55}
.risk-box{background:#f7edcf;border-left:4px solid #c49736;border-radius:0 12px 12px 0;padding:14px 17px;color:#554720;font-size:13px;line-height:1.5}
div[data-testid="stTabs"] button{font-weight:600}.stButton>button{border-radius:10px}.stSelectbox label,.stSlider label,.stRadio label{font-weight:600;color:var(--forest)}
footer{visibility:hidden}#MainMenu{visibility:hidden}header[data-testid="stHeader"]{background:transparent}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800, show_spinner=False)
def load_live(species: str, limit: int) -> tuple[list[dict], str | None]:
    """Retrieve coordinate-bearing GBIF records. Keep precise coordinates in session memory only."""
    records=[]
    try:
        params={"scientificName":species,"hasCoordinate":"true","hasGeospatialIssue":"false","limit":min(limit,300),"offset":0}
        while len(records)<limit:
            params["limit"]=min(300,limit-len(records)); params["offset"]=len(records)
            response=requests.get("https://api.gbif.org/v1/occurrence/search",params=params,headers={"User-Agent":"PhytoTerroir/1.0 research prototype"},timeout=25)
            response.raise_for_status(); payload=response.json(); batch=payload.get("results",[])
            for item in batch:
                lat=item.get("decimalLatitude"); lon=item.get("decimalLongitude")
                if lat is None or lon is None: continue
                records.append({"species":species,"lat":float(lat),"lon":float(lon),"year":item.get("year"),"basis":item.get("basisOfRecord"),"uncertainty_m":item.get("coordinateUncertaintyInMeters"),"license":item.get("license"),"gbif_id":item.get("gbifID"),"dataset_key":item.get("datasetKey")})
            if not batch or len(batch)<params["limit"]: break
        return records[:limit], None
    except Exception as exc:
        return [], f"GBIF request failed: {exc}"

def load_demo(species: str) -> list[dict]:
    frame=pd.read_csv(ROOT/"data/demo/occurrences.csv")
    return [{"species":r.species,"lat":float(r.lat),"lon":float(r.lon),"year":int(r.year),"basis":r.basisOfRecord,"uncertainty_m":float(r.coordinateUncertaintyInMeters),"license":"Synthetic fixture","gbif_id":None,"dataset_key":"demo"} for r in frame[frame.species==species].itertuples()]

def aggregate_h3(records: list[dict], resolution: int) -> tuple[list[dict], int]:
    """Aggregate records into H3 cells and return polygon features; never return point features."""
    buckets={}
    years=[]
    for record in records:
        cell=h3.latlng_to_cell(record["lat"],record["lon"],resolution)
        bucket=buckets.setdefault(cell,{"cell":cell,"records":0,"years":[],"uncertainties":[]})
        bucket["records"]+=1
        if record.get("year"): bucket["years"].append(int(record["year"]))
        if record.get("uncertainty_m") is not None: bucket["uncertainties"].append(float(record["uncertainty_m"]))
    max_count=max((v["records"] for v in buckets.values()),default=1)
    polygons=[]
    for cell,bucket in buckets.items():
        # H3 returns lat/lon boundary vertices. DeckGL expects lon/lat pairs.
        boundary=h3.cell_to_boundary(cell)
        coords=[[lon,lat] for lat,lon in boundary]
        coords.append(coords[0])
        intensity=int(90+110*bucket["records"]/max_count)
        polygons.append({"cell_label":cell,"records":bucket["records"],"polygon":coords,"fill_color":[52,112,78,intensity],"year_span":f"{min(bucket['years'])}–{max(bucket['years'])}" if bucket["years"] else "Year not recorded"})
    cell_area_km2=sum(h3.cell_area(p["cell_label"],unit="km^2") for p in polygons)
    return polygons, int(round(cell_area_km2))

def metric(label: str,value: str,foot: str):
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-foot">{foot}</div></div>',unsafe_allow_html=True)

st.markdown('''<div class="hero"><div class="eyebrow">Community governed plant intelligence</div><h1>PhytoTerroir</h1><p>Explore where medicinal plant records cluster, examine harvest trade-offs, and keep sensitive locations aggregated from the start.</p><div class="hero-chip">EVIDENCE FIRST · FIELD SAFE</div></div>''',unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🌱 Explore a species")
    species=st.selectbox("Target species",list(SPECIES),index=0)
    source=st.radio("Occurrence dataset",["Demo data","Live GBIF"],help="Demo data are synthetic. Live mode retrieves public records from GBIF and aggregates them before display.")
    resolution=st.select_slider("Map aggregation",options=[2,3,4,5],value=3,format_func=lambda v:f"H3 resolution {v}")
    limit=st.select_slider("Live record cap",options=[100,250,500,1000],value=500,disabled=source!="Live GBIF")
    st.markdown("---")
    st.markdown("**Location protection**")
    st.caption("The map shows H3 cell areas only. Raw points are never drawn or exported. Aggregation lowers precision but does not guarantee anonymity, especially where records are sparse.")
    st.markdown("---")
    st.caption("Occurrence records are evidence of recorded observations, not population counts or harvest permissions.")

if source=="Live GBIF":
    with st.spinner("Fetching occurrence records and aggregating locations…"):
        records,error=load_live(species,limit)
    if error:
        st.error(error); records=[]
    dataset_label="Live GBIF occurrence records"
else:
    records=load_demo(species); dataset_label="Synthetic demo records"
    st.info("You are viewing synthetic teaching records. Switch to **Live GBIF** for public occurrence data.",icon="🧪")

if not records:
    st.warning("No coordinate-bearing records are available for this selection. Try another species or use demo data.")
    st.stop()

cells,coverage_km2=aggregate_h3(records,int(resolution))
coordinate_quality=sum(1 for r in records if r.get("uncertainty_m") is not None)/len(records)
years=[int(r["year"]) for r in records if r.get("year")]
cell_frame=pd.DataFrame(cells).sort_values("records",ascending=False)
left,right=st.columns([1.4,1],gap="large")
with left:
    metric("Records in this view",f"{len(records):,}",dataset_label)
with right:
    metric("H3 cells shown",f"{len(cells):,}",f"Resolution {resolution} · approximately {coverage_km2:,} km² of cell area")

st.markdown("<div class='section-label'>01 / Occurrence evidence</div>",unsafe_allow_html=True)
map_col,context_col=st.columns([1.65,1],gap="large")
with map_col:
    polygons=pdk.Layer("PolygonLayer",data=cells,get_polygon="polygon",get_fill_color="fill_color",get_line_color=[245,245,238,190],get_line_width=50,line_width_min_pixels=1,stroked=True,filled=True,pickable=True,auto_highlight=True)
    cell_centers=[h3.cell_to_latlng(p["cell_label"]) for p in cells]
    center_lat=float(np.mean([center[0] for center in cell_centers])); center_lon=float(np.mean([center[1] for center in cell_centers]))
    view=pdk.ViewState(latitude=center_lat,longitude=center_lon,zoom=3,pitch=0)
    deck=pdk.Deck(layers=[polygons],initial_view_state=view,tooltip={"html":"<b>{cell_label}</b><br/>{records} record(s)<br/>{year_span}","style":{"backgroundColor":"#183a2f","color":"#f5f5ee"}},map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json")
    st.pydeck_chart(deck,use_container_width=True)
    st.caption("Each polygon is an H3 aggregate. No individual occurrence point is drawn.")
with context_col:
    st.markdown("#### What the records say")
    st.markdown(f"**{species}** records are being explored across {SPECIES[species]['region'].lower()}.")
    st.markdown(f"**{coordinate_quality:.0%}** include coordinate uncertainty metadata.")
    if years: st.markdown(f"Record years range from **{min(years)} to {max(years)}**.")
    else: st.markdown("Record year is missing from this selection.")
    st.markdown("#### Densest reported cells")
    st.dataframe(cell_frame[["cell_label","records","year_span"]].rename(columns={"cell_label":"H3 cell","records":"Records","year_span":"Record years"}).head(6),hide_index=True,use_container_width=True)
    st.markdown('<div class="evidence"><b>Read this as sampling evidence.</b><br>Dense cells can reflect observation effort, access and digitization. They do not prove abundance, habitat quality or safe harvest capacity.</div>',unsafe_allow_html=True)

st.markdown("<div class='section-label'>02 / Decision lab</div>",unsafe_allow_html=True)
tab_scenario,tab_chemistry,tab_governance=st.tabs(["Harvest impact explorer","Chemistry evidence","Data governance"])
with tab_scenario:
    st.markdown("### Explore a hypothetical harvest pressure")
    st.write("Change the harvest part and annual removal assumption to see how a simple recovery sketch responds. The curve is educational and uses explicit placeholder rates.")
    control,chart=st.columns([.85,1.4],gap="large")
    with control:
        part=st.selectbox("Harvested part",list(PARTS),index=3)
        pressure=st.slider("Annual removal pressure",0,20,5,step=1,format="%d%%")
        rain_scenario=st.select_slider("Rainfall scenario",options=[-30,-15,0,15,30],value=0,format_func=lambda v:f"{v:+d}%" if v else "Baseline")
        st.markdown(f"**{PARTS[part]['label']}**")
        st.caption(PARTS[part]["copy"])
    with chart:
        years_axis=np.arange(0,11)
        assumed_recovery={"Leaf":0.13,"Flower / fruit":0.09,"Bark":0.065,"Root / rhizome":0.055}[part]
        net_change=float(np.clip(assumed_recovery*(1+rain_scenario/100)-pressure/100*PARTS[part]["factor"],-.25,.20))
        trajectory=100*np.power(1+net_change,years_axis)
        frame=pd.DataFrame({"Year":years_axis,"Illustrative index (year 0 = 100)":trajectory})
        st.line_chart(frame,x="Year",y="Illustrative index (year 0 = 100)",color="#3e7252",height=300)
        st.caption(f"Illustration only · assumed annual net change {net_change:+.1%} · no species-specific demographic data used")
    st.markdown('<div class="risk-box"><b>Do not use this curve to set a quota.</b> Recovery rates, rainfall effects and removal penalties are placeholders. Local population studies and community authorization are required before any management decision.</div>',unsafe_allow_html=True)
with tab_chemistry:
    st.markdown("### Chemistry is a research question, not a map score")
    st.markdown(f"**Candidate compound family:** {SPECIES[species]['compound']}.")
    st.markdown("This prototype contains no verified, assay-linked dataset for this species. It therefore does not estimate potency or identify an optimal harvest site.")
    st.markdown("#### What a credible next model needs")
    st.markdown("1. Traceable chemical assays with method, tissue, season and site metadata.\n2. Environmental measurements matched to assay locations.\n3. Spatially independent validation and uncertainty calibration.\n4. Review of whether collecting or publishing each observation is authorized.")
    st.info("A literature relationship is a hypothesis to test. It is not a reliable predictor until validated on independent field samples.",icon="🧪")
with tab_governance:
    st.markdown("### Location data carries real risk")
    st.markdown("The dashboard converts precise coordinates into H3 cells in memory and shows aggregate polygons only. It never renders individual markers. Lower H3 resolution means larger cells.")
    st.markdown("#### Safeguards in this prototype")
    st.markdown("- Raw coordinates are not displayed in the UI or included in downloads.\n- Map features contain only aggregate cell IDs, record counts and year ranges.\n- Demo mode uses synthetic locations.\n- Live records remain subject to record-level licensing and attribution requirements.")
    st.warning("H3 aggregation is not differential privacy. Sparse cells, external datasets or a small H3 resolution can still expose a sensitive location. Do not load community-held coordinates without explicit governance, consent, access controls and a threat review.")
    st.markdown("**Community authority comes first:** agree who controls access, what may be analyzed, who benefits, and what must never be published.")

st.markdown("---")
source_note="GBIF public occurrence search API" if source=="Live GBIF" else "Synthetic fixture bundled with this prototype"
st.caption(f"Data source: {source_note} · H3 resolution {resolution} · {len(records)} records aggregated · values shown are exploratory, not conservation assessments or harvest recommendations.")





