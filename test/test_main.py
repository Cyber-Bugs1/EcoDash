import ee

ee.Initialize(project="hackathon-484205")
print("Earth Engine initialized successfully")

india_states = (
    ee.FeatureCollection("FAO/GAUL/2015/level1")
    .filter(ee.Filter.eq("ADM0_NAME", "India"))
)

print("India state boundaries loaded")

aod_image = (
    ee.ImageCollection("MODIS/061/MCD19A2_GRANULES")
    .filterDate("2020-01-01", "2020-12-31")
    .select("Optical_Depth_047")
    .mean()
    .clip(india_states)
)

print("AOD image prepared")

state_aod = aod_image.reduceRegions(
    collection=india_states,
    reducer=ee.Reducer.mean(),
    scale=5000
)

print("State-wise AOD calculated")

export_task = ee.batch.Export.table.toDrive(
    collection=state_aod,
    description="India_Pollution_AOD_2020",
    folder="GEE_Exports",
    fileFormat="CSV"
)

export_task.start()

print("Export started successfully!")
print("Check Google Drive → GEE_Exports → India_Pollution_AOD_2020.csv")