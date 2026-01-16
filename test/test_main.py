import ee
import pandas as pd

ee.Initialize(project = "hackathon-484205")
print("Earth Engine initialized successfully")

india = ee.FeatureCollection("FAO/GAUL/2015/level1") \
    .filter(ee.Filter.eq("ADM0_NAME", "India"))
aod = (
    ee.ImageCollection("MODIS/061/MCD19A2_GRANULES")
    .filterDate("2020-01-01", "2020-12-31")
    .select("Optical_Depth_047")
    .mean()
    .clip(india)
)

print("AOD Image ready")

state_aod = aod.reduceRegions(
    collection=india,
    reducer=ee.Reducer.mean(),
    scale=1000
)

features = state_aod.getInfo()["features"]

rows=[]
for f in features:
    props=f['properties']
    rows.append({
        "State":props.get("ADM1_NAME"),
        "aod":props.get("mean")
    })

df=pd.DataFrame(rows)

print(df.head())

df.to_csv("Poll_2020.csv",index=False)
print("Save")