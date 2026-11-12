"""Synthetic A02 contracts. No Earth Engine credentials or live data."""
import io

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from shapely.geometry import box

from ntl.semantics import QUALITY_BANDS, annual_image_with_quality, cell_quality, year_quality
from ntl.zonal import zonal_stat


class Image:
    """Small masked-array EE double; not evidence of a live EE export."""
    def __init__(self, values, names=("avg_rad",)):
        self.values = np.ma.masked_invalid(np.asarray(values, float))
        self.names = names

    def select(self, name):
        return self

    def unmask(self, value):
        return Image(self.values.filled(value), self.names)

    def mask(self):
        return Image((~np.ma.getmaskarray(self.values)).astype(float))

    def rename(self, name):
        return Image(self.values.filled(np.nan), (name,))

    def lt(self, value):
        return Image(np.ma.where(self.values < value, 1., 0.).filled(np.nan))

    def eq(self, value):
        return Image(np.ma.where(self.values == value, 1., 0.).filled(np.nan))

    def addBands(self, other):
        return Image(np.concatenate([self.values.filled(np.nan), other.values.filled(np.nan)]),
                     self.names + other.names)

    def toFloat(self):
        return self

    def clip(self, roi):
        return self


class Monthly:
    def __init__(self):
        # 2x3: measured zero, no observations, valid negative, low support,
        # bright full support, bright partial support. cf_cvg filtering is
        # represented by NaN; no attempt to simulate atmospheric physics.
        self.values = np.array([[[0, np.nan, -2], [np.nan, 8, 4]],
                                [[0, np.nan, -4], [6, 10, np.nan]],
                                [[0, np.nan, -3], [np.nan, 12, 8]]])

    def median(self):
        return Image(np.ma.median(np.ma.masked_invalid(self.values), axis=0).filled(np.nan)[None])

    def count(self):
        return Image(np.isfinite(self.values).sum(axis=0)[None])


def fixture():
    image = annual_image_with_quality(Monthly(), None)
    with MemoryFile() as mf:
        with mf.open(driver="GTiff", height=2, width=3, count=6, dtype="float32",
                     crs="EPSG:32650", transform=from_origin(0, 1000, 500, 500)) as dst:
            dst.write(image.values.filled(np.nan).astype("float32"))
            for i, name in enumerate(image.names, 1):
                dst.set_band_description(i, name)
        raw = mf.read()
    grid = gpd.GeoDataFrame({"grid_id": [9, 2, 7, 4, 6, 1]}, geometry=[
        box(c*500, 500-r*500, (c+1)*500, 1000-r*500)
        for r in range(2) for c in range(3)], crs="EPSG:32650")
    return raw, grid


def test_monthly_semantics_and_legacy_values():
    raw, grid = fixture()
    # Exact historical band-1 policy: clip annual median after zero filling.
    np.testing.assert_allclose(zonal_stat(raw, grid), [0, 0, 0, 6, 10, 6])
    quality = cell_quality(raw, grid)
    assert quality.dq_status.tolist() == ["observed", "no_observation", "observed",
                                         "observed", "observed", "observed"]
    np.testing.assert_allclose(quality.dq_negative_fraction, [0, 0, 1, 0, 0, 0])
    np.testing.assert_allclose(quality.dq_zero_fraction, [1, 0, 0, 0, 0, 0])
    np.testing.assert_allclose(quality.dq_mean_valid_months, [3, 0, 3, 1, 3, 2])
    np.testing.assert_allclose(quality.dq_low_month_fraction, [0, 1, 0, 1, 0, 1])


def test_partial_polygon_area_and_csv_years():
    raw, grid = fixture()
    grid = grid.iloc[[0]].copy()
    grid.geometry = [box(0, 500, 1000, 1000)]
    quality = cell_quality(raw, grid)
    assert quality.dq_observed_fraction.iloc[0] == pytest.approx(.5)
    assert quality.dq_zero_fraction.iloc[0] == pytest.approx(.5)
    assert quality.dq_status.iloc[0] == "partial_observation"
    csv = pd.concat([year_quality(quality, 2014), year_quality(quality, 2020)], axis=1)
    recovered = pd.read_csv(io.StringIO(csv.to_csv(index=False)))
    pd.testing.assert_frame_equal(csv, recovered)
    assert not csv.columns.duplicated().any()


def test_old_raster_cannot_prove_observation_and_outside_is_unknown():
    raw, grid = fixture()
    with MemoryFile(raw) as mf, mf.open() as src:
        values, profile = src.read(1), src.profile
    profile.update(count=1)
    with MemoryFile() as mf:
        with mf.open(**profile) as dst:
            dst.write(values, 1)
        legacy = mf.read()
    assert cell_quality(legacy, grid).dq_status.eq("unknown").all()
    grid.geometry = grid.geometry.translate(xoff=10000)
    assert cell_quality(raw, grid).dq_status.eq("unknown").all()


def test_reordered_cells_preserve_identity():
    raw, grid = fixture()
    expected = cell_quality(raw, grid)
    order = [4, 0, 5, 1, 3, 2]
    actual = cell_quality(raw, grid.iloc[order])
    pd.testing.assert_frame_equal(actual, expected.iloc[order].reset_index(drop=True))


def _spacetime_app():
    import geopandas as gpd
    import numpy as np
    import pandas as pd
    from shapely.geometry import box
    from ntl.lisa_ui import render_lisa_tab

    grid = gpd.GeoDataFrame({"grid_id": np.arange(36), "ntl_mean": np.arange(36.) + 1,
                            "area_km2": .25, "dq_status": "observed"},
        geometry=[box(i*500, j*500, i*500+500, j*500+500)
                  for j in range(6) for i in range(6)], crs=32650)
    def fetch(year):
        return pd.DataFrame({"ntl_mean": np.arange(36.) + 2, "dq_status": "partial_observation"})
    boundary = gpd.GeoDataFrame(geometry=[box(0, 0, 3000, 3000)], crs=32650).to_crs(4326)
    render_lisa_tab(res={"size": 500, "year": 2020, "ts": "a02", "iso3": "SYN",
                         "boundary_wgs": boundary},
                    grid_utm=grid, export_df=pd.DataFrame(grid.drop(columns="geometry")),
                    lang="en", region_id="synthetic", region_label="Synthetic",
                    fetch_year_ntl_fn=fetch, available_years=[2014, 2020])


def test_spacetime_ui_keeps_quality_for_both_years_on_rerun():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_function(_spacetime_app, default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]
    at.button(key="btn_run_spacetime").click().run()
    assert not at.exception, [e.value for e in at.exception]
    cache = at.session_state["_spacetime_cache"]
    frame = next(iter(cache.values())).st_cell_df
    assert frame.dq_status_2014.eq("partial_observation").all()
    assert frame.dq_status_2020.eq("observed").all()
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    cached = next(iter(at.session_state["_spacetime_cache"].values())).st_cell_df
    assert not cached.columns.duplicated().any()
