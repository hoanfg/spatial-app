/*
 * Independent VIIRS 2020 Earth Engine references for three contrasting
 * GADM 4.1 districts. Export images, not app-derived zonal statistics.
 * Keep annual median, coverage, and masked-median products separate.
 */
var cases = [
  {
    slug: 'shanghai_core',
    gid: 'CHN.24.1.10_1',
    bbox: [121.35799408, 31.171072007, 121.571929931, 31.33388900]
  },
  {
    slug: 'shenzhen_baoan',
    gid: 'CHN.6.15.1_1',
    bbox: [113.76775406, 22.403193999, 114.66764100, 22.853141784]
  },
  {
    slug: 'anhui_qimen',
    gid: 'CHN.1.11.1_1',
    bbox: [117.197677612, 29.587049485, 117.95149231, 30.116565705]
  }
];

var viirs = ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG')
  .filterDate('2020-01-01', '2021-01-01');

var validMonthly = viirs.map(function(img) {
  return img.select('avg_rad').updateMask(img.select('cf_cvg').gt(0));
});

var annualMedian = validMonthly.median().unmask(0).toFloat();
var annualMasked = validMonthly.median()
  .unmask({value: -9999, sameFootprint: false}).toFloat();
var monthCount = viirs.map(function(img) {
  return img.select('cf_cvg').gt(0).unmask(0).rename('valid_month');
}).sum().toUint8();

print('VIIRS monthly composites in 2020', viirs.size());

cases.forEach(function(c) {
  // Padding avoids truncating any pixel overlapping the GADM district.
  var p = 0.02;
  var region = ee.Geometry.Rectangle([
    c.bbox[0]-p, c.bbox[1]-p, c.bbox[2]+p, c.bbox[3]+p
  ]);
  var config = {
    folder: 'cross_location_validation_2020',
    region: region,
    crs: 'EPSG:4326',
    scale: 463.83,
    maxPixels: 1e8,
    fileFormat: 'GeoTIFF'
  };
  print(c.slug + ' ' + c.gid, region);
  Export.image.toDrive(Object.assign({}, config, {
    image: annualMedian.clip(region),
    description: c.slug + '_viirs_2020_reference',
    fileNamePrefix: c.slug + '_viirs_2020_reference'
  }));
  Export.image.toDrive(Object.assign({}, config, {
    image: monthCount.clip(region),
    description: c.slug + '_valid_months_2020',
    fileNamePrefix: c.slug + '_valid_months_2020'
  }));
  Export.image.toDrive(Object.assign({}, config, {
    image: annualMasked.clip(region),
    description: c.slug + '_viirs_2020_masked_median',
    fileNamePrefix: c.slug + '_viirs_2020_masked_median',
    formatOptions: {noData: -9999}
  }));
});