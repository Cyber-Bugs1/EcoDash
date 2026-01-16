import ee


ee.Initialize(project="hackathon-484205")
print("Earth Engine initialized successfully")


india_states = (
    ee.FeatureCollection("FAO/GAUL/2015/level1")
    .filter(ee.Filter.eq("ADM0_NAME", "India"))
)

print("India state boundaries loaded")


months = [
    ("01", "31"),
    ("02", "29"),  
    ("03", "31"),
    ("04", "30"),
    ("05", "31"),
    ("06", "30"),
    ("07", "31"),
    ("08", "31"),
    ("09", "30"),
    ("10", "31"),
    ("11", "30"),
    ("12", "31"),
]

for month, last_day in months:
    print(f"Processing month: {month}")


    aod_image = (
        ee.ImageCollection("MODIS/061/MCD19A2_GRANULES")
        .filterDate(f"2020-{month}-01", f"2020-{month}-{last_day}")
        .select("Optical_Depth_047")
        .mean()
        .clip(india_states)
    )

    state_aod = aod_image.reduceRegions(
        collection=india_states,
        reducer=ee.Reducer.mean(),
        scale=5000
    )


    task = ee.batch.Export.table.toDrive(
        collection=state_aod,
        description=f"India_Pollution_AOD_2020_{month}",
        folder="GEE_Exports",
        fileFormat="CSV"
    )

    task.start()
    print(f"Export started for month {month}")
