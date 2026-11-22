// G10/G18 independent SOURCE evidence export for Earth Engine Code Editor.
//
// PREREQUISITES: draw or import one real district polygon as "geometry".
// Set YEAR to a genuine candidate with incomplete observation support.
// This exports one source-grid-aligned 3-band raster; it is not a field
// validation until the source scene, grid identity and extraction are checked.
// The output does not replace the app's annual NTL composite.

var YEAR = 2020;
var ROI = geometry;  // Must be a user-drawn/imported Earth Engine geometry.
var DATASET = 'NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG';

var monthly = ee.ImageCollection(DATASET)
  .filterDate(YEAR + '-01-01', (YEAR + 1) + '-01-01')
  .filterBounds(ROI);

var source = ee.Image(monthly.first()).select('avg_rad').projection().getInfo();
var monthlyValid = monthly.map(function(image) {
  return image.select('avg_rad')
    .updateMask(image.select('cf_cvg').gt(0));
});

// Annual observed support and month count match the A02 source definitions.
var observed = monthlyValid.median().mask().unmask(0)
  .rename('ref_observed_fraction');
var validMonths = monthlyValid.count().unmask(0)
  .rename('ref_mean_valid_months');
// Cloud-free observations, NOT a count of months. A month may include
// multiple cloud-free individual observations at the same source pixel.
var cfTotal = monthly.select('cf_cvg').sum().unmask(0)
  .rename('ref_cf_cvg_total');

var evidence = ee.Image.cat([observed, validMonths, cfTotal])
  .toFloat().clip(ROI);
print('Input monthly scenes', monthly.size());
Map.centerObject(ROI);
Map.addLayer(cfTotal.clip(ROI), {min: 0, max: 80}, 'cf_cvg source observations');

Export.image.toDrive({
  image: evidence,
  description: 'G10_G18_source_support_' + YEAR,
  folder: 'spatial-app-scientific-evidence',
  fileNamePrefix: 'g10_g18_source_support_' + YEAR,
  region: ROI,
  crs: source.crs,
  crsTransform: source.transform,
  maxPixels: 100000000
});
