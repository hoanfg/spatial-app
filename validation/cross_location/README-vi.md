# Cross-location Validation cho VIIRS 2020

**Trạng thái:** Đã chọn mẫu và kiểm chứng công cụ; **chưa** có dữ liệu NTL/LISA của ba địa bàn mới. Không đánh dấu V11 là PASS khi chưa đối chiếu raster–CSV.

## 1. Thiết kế ba trường hợp

| Vai trò thử nghiệm | Địa bàn theo GADM 4.1 | GID_2 | Diện tích gần đúng (km²) | Ô 500 m tối thiểu theo diện tích |
|---|---|---|---:|---:|
| Lõi đô thị | Thượng Hải / Nội đô Thượng Hải | `CHN.24.1.10_1` | ~197,7 | ~791 |
| Đô thị–công nghiệp/ven đô, nhiều thành phần hình học | Thâm Quyến / Quận Bảo An | `CHN.6.15.1_1` | ~1.655,5 | ~6.623 |
| Đối chứng ít đô thị hơn | An Huy / Hoàng Sơn / Huyện Kỳ Môn | `CHN.1.11.1_1` | ~2.206,9 | ~8.828 |

Các diện tích trên là **ước lượng bằng phép chiếu phẳng gần đúng** từ tọa độ GeoJSON GitHub; không thay cho diện tích UTM và không phải số ô clipping đã quan sát. Nhãn cấu trúc vùng là giả thuyết thiết kế mẫu, chưa được xác nhận từ VIIRS/GHSL. Bao'an có nhiều thành phần hình học rời, hữu ích để thử kiểm tra cắt biên.

GeoJSON ranh giới có sẵn trong repository:

- `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Shanghai/CHN_Shanghai_Shanghai_District.geojson`
- `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Guangdong_Shenzhen/CHN_Guangdong_Shenzhen_Bao'an_District.geojson`
- `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Anhui_Huangshan/CHN_Anhui_Huangshan_Qimen_District.geojson`

## 2. Dữ liệu đầu vào cần có

Chạy `gee_viirs_2020.js` trong Google Earth Engine Code Editor, thực thi **9 tác vụ Export** (ba sản phẩm cho mỗi địa bàn): annual median tham chiếu, số tháng có `cf_cvg > 0`, và median giữ NoData.

Trên `spatial-app`, chạy **2020, lưới 500 m, raw NTL, Queen, 999 permutations, seed 42, FDR 0.05**, rồi xuất CSV chứa ít nhất `grid_id, area_km2, ntl_mean`; xuất cả CSV LISA đầy đủ để có thể đối chiếu p-value/quadrant. Không cần xuất toàn thành phố hoặc thay đổi cơ chế bảo vệ RAM của ứng dụng.

Dữ liệu Earth Engine và app cần độc lập về phép tính zonal mean. Có thể dùng cùng sản phẩm NOAA/VIIRS, nhưng không dùng lại kết quả trích xuất theo ô từ app làm “reference”.

## 3. Chạy phép kiểm chứng raster–polygon

Cần Python với `geopandas`, `numpy`, `pandas`, `rasterio` và `shapely`:

```bash
python validation/cross_location/compare_raster_cells.py \
  --boundary data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Shanghai/CHN_Shanghai_Shanghai_District.geojson \
  --raster shanghai_core_viirs_2020_reference.tif \
  --csv shanghai_core_app_2020_500m.csv \
  --out-csv shanghai_core_cell_comparison.csv \
  --out-json shanghai_core_metrics.json
```

Lặp lại cho Bao'an và Qimen bằng đúng GeoJSON/GeoTIFF/CSV tương ứng.

## 4. Tiêu chí đánh giá (đã định trước)

1. **Hình học:** số ô, `grid_id`, diện tích từng ô khớp với CSV app trong dung sai diện tích 0,00005 km².
2. **NTL:** toàn bộ ô có raster đủ độ phủ khớp trong sai số làm tròn CSV ±0,00005 nW/cm²/sr; báo cáo mọi missing/fail, không xóa ô ngoại lệ.
3. **Kiểm tra dữ liệu thiếu:** so annual median với masked median; phân tích `cf_cvg` theo tháng, mọi giá trị âm và ảnh hưởng tới polygon zonal mean. Không giả định tất cả pixel có 12 tháng như Yanqing.
4. **LISA:** tái tính Queen adjacency, Local Moran và p-value/FDR trên 500 m bằng script kiểm chứng riêng; ngẫu nhiên có seed cố định, nêu rõ cách đếm tie/tail; báo cáo nhãn HH/LL và các ngoại lệ.
5. **Khả năng khái quát:** chỉ coi V11 hoàn tất khi cả ba địa bàn đã có kết quả và bằng chứng đính kèm; không yêu cầu HH area share giống Yanqing — các địa bàn khác nhau về cấu trúc là điều được mong đợi.
6. **Lưu trữ:** đính kèm raster/CSV, mã kiểm thử, manifest SHA-256, phiên bản commit, kết quả theo ô và báo cáo; cập nhật đồng bộ hai bản `docs/VALIDATION MASTER.md` và `docs/VALIDATION MASTER-vi.md` theo đúng nội dung mới.

## 5. Tình trạng thực thi

- **Đã thực hiện:** xác nhận tồn tại ba ranh giới trong GitHub, mã GID, bbox, diện tích gần đúng; chuẩn bị script Earth Engine và comparator Python; comparator đã được chạy trên Yanqing 2020 và đạt **8.333/8.333** ô (sai số lớn nhất ~0,00004999).
- **Chưa thực hiện:** xuất GeoTIFF 2020 ba vùng, CSV app cho ba vùng, kiểm chứng raster từng ô và LISA từng vùng, so sánh GHSL độc lập.
- **Quyết định:** giữ V11 là `PENDING` cho tới khi có bằng chứng cho cả ba địa bàn.
