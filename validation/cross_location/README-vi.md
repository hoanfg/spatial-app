# Kiểm chứng VIIRS 2020 tại nhiều địa bàn

**Trạng thái:** V11 đã hoàn tất kiểm chứng cho cả ba địa bàn. Manifest kiểm toán phục hồi ghi danh mục CSV ứng dụng, raster tương ứng, kết quả ô biên và các gói lưu trữ kèm mã băm. Checkout hiện tại không bung mọi đầu vào nhị phân để chạy mới; đây là giới hạn đóng gói tái lập, không phải kiểm chứng chưa hoàn thành.

Các nhãn bên dưới là giả thuyết lấy mẫu cho những bối cảnh không gian khác nhau có chủ đích, không phải phân loại đã được kiểm chứng về nền kinh tế của từng nơi. Xem [kiểm toán phát biểu khoa học](../evidence/README-vi.md#kiểm-toán-phát-biểu-khoa-học) để phân biệt bằng chứng tổng hợp đã ghi với phép kiểm thực địa có thể tái lập độc lập.

## 1. Thiết kế ba trường hợp

| Vai trò thử nghiệm | Địa bàn theo GADM 4.1 | GID_2 | Diện tích gần đúng (km²) | Ô 500 m tối thiểu theo diện tích |
|---|---|---|---:|---:|
| Lõi đô thị | Thượng Hải / Nội đô Thượng Hải | `CHN.24.1.10_1` | ~197,7 | ~791 |
| Đô thị–công nghiệp/ven đô, nhiều thành phần hình học | Thâm Quyến / Quận Bảo An | `CHN.6.15.1_1` | ~1.655,5 | ~6.623 |
| Đối chứng ít đô thị hơn | An Huy / Hoàng Sơn / Huyện Kỳ Môn | `CHN.1.11.1_1` | ~2.206,9 | ~8.828 |

Các diện tích trên là **ước lượng bằng phép chiếu phẳng gần đúng** từ tọa độ GeoJSON trên GitHub; không thay cho diện tích UTM và không phải số ô đã cắt theo ranh giới. Nhãn cấu trúc vùng là giả thuyết thiết kế mẫu, chưa được xác nhận từ VIIRS/GHSL. Bảo An có nhiều thành phần hình học rời, hữu ích để kiểm tra phép cắt biên.

GeoJSON ranh giới có sẵn trong repository:

- `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Shanghai/CHN_Shanghai_Shanghai_District.geojson`
- `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Guangdong_Shenzhen/CHN_Guangdong_Shenzhen_Bao'an_District.geojson`
- `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Anhui_Huangshan/CHN_Anhui_Huangshan_Qimen_District.geojson`

## 2. Dữ liệu đầu vào cần có

Chạy `gee_viirs_2020.js` trong trình soạn thảo Google Earth Engine, thực thi **9 tác vụ xuất** (ba sản phẩm cho mỗi địa bàn): trung vị năm tham chiếu, số tháng có `cf_cvg > 0` và trung vị giữ NoData.

Trên `spatial-app`, chạy **năm 2020, lưới 500 m, NTL thô, Queen, 999 hoán vị, hạt ngẫu nhiên 42 và FDR 0,05**, rồi xuất CSV có `grid_id`, `area_km2`, `ntl_mean`, `centroid_lon`, `centroid_lat` và `centroid_x_epsg{E}` / `centroid_y_epsg{E}` theo mã UTM EPSG được chọn. Xuất cả CSV LISA để đối chiếu giá trị p và phần tư. Không cần xuất toàn thành phố hoặc đổi giới hạn RAM.

Dữ liệu Earth Engine và ứng dụng cần độc lập về phép tính trung bình vùng. Có thể dùng cùng sản phẩm NOAA/VIIRS, nhưng không dùng lại kết quả trích xuất theo ô từ ứng dụng làm dữ liệu tham chiếu.

## 3. Chạy phép kiểm chứng raster và đa giác

Cần Python với `geopandas`, `numpy`, `pandas`, `rasterio` và `shapely`:

```bash
python validation/cross_location/compare_raster_cells.py \
  --boundary data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Shanghai/CHN_Shanghai_Shanghai_District.geojson \
  --raster shanghai_core_viirs_2020_reference.tif \
  --csv shanghai_core_app_2020_500m.csv \
  --out-csv shanghai_core_cell_comparison.csv \
  --out-json shanghai_core_metrics.json
```

Lặp lại cho Bảo An và Kỳ Môn bằng đúng GeoJSON/GeoTIFF/CSV tương ứng.

## Vì sao phép so V11 được thiết kế như vậy?

**Đại lượng được so:** với mỗi `grid_id` của ứng dụng, dựng trung bình NTL độc lập `sum(pixel_value × overlap_area) / sum(overlap_area)` trên polygon lưới đã xuất, sau đó tính `abs(NTL_ref - NTL_app)`. Dùng cùng sản phẩm VIIRS và năm để **cô lập sai lệch trích xuất**, không dùng một sản phẩm vệ tinh khác để đánh giá “độ đúng” vật lý. Vì đa giác do ứng dụng xuất, phép thử không tự xác nhận thuật toán sinh lưới từ GADM.

**Vì sao ba địa bàn:** khác nhau về quy mô, mức độ đô thị hóa giả định và hình học cắt biên. Đây là **chọn mẫu theo rủi ro kỹ thuật có chủ đích**, không phải mẫu ngẫu nhiên đại diện cho mọi huyện Trung Quốc.

**Vì sao dung sai `0.00005`:** `ntl_mean` chỉ giữ bốn chữ số thập phân trong CSV; khi đối chiếu với số thực có độ chính xác cao hơn, nửa đơn vị thập phân cuối là `0.00005`. Mốc phụ `0.0000501` chỉ chẩn đoán nhiễu điểm động, không phải “nới chuẩn” khoa học. Báo **sai số tuyệt đối theo ô**, tỷ lệ đạt, ô biên, thiếu phủ, cực trị; không dùng chỉ mỗi hệ số tương quan để tuyên bố khớp.

**Vì sao kiểm LISA riêng:** phép trích xuất NTL đúng không bảo đảm mạng láng giềng, phép hoán vị và BH-FDR đúng. Local Moran dùng độ lệch chuẩn hóa `z_i` và trung bình láng giềng `lag(z)_i`; dạng triển khai là `I_i = z_i × lag(z)_i / [sum(z²)/(m-1)]`. Hoán vị có điều kiện giữ giá trị ô đang kiểm định, lấy các ô khác **không hoàn lại**, dùng quy tắc hai đuôi có tính trường hợp bằng nhau và hiệu chỉnh `(count+1)/(B+1)`. BH hiệu chỉnh trong **đúng họ ô được kiểm định**. Vì CSV làm tròn và RNG độc lập, cần báo sai khác nhãn thay vì ép bằng tuyệt đối.

**Ý nghĩa kết quả:** đối chiếu V11 xác nhận các phép tính raster theo đúng đầu vào và dung sai đã nêu tại ba địa bàn. Nó không kiểm chứng ý nghĩa kinh tế của HH/LL, quan hệ nhân quả, hay tính hợp lệ của p-value LISA khi giả thuyết hoán vị sai.

## 4. Tiêu chí đánh giá (đã định trước)

1. **Hình học:** số ô, `grid_id`, diện tích và tâm ô theo UTM/WGS84 khớp CSV app. Dung sai diện tích là 0,00005 km²; dung sai tâm ô theo mức làm tròn 0,1 m và sáu chữ số thập phân của độ. Kiểm tra này từ chối tráo hai ID cùng diện tích.
2. **NTL:** toàn bộ ô có raster đủ độ phủ khớp trong sai số làm tròn CSV ±0,00005 nW/cm²/sr; báo cáo mọi missing/fail, không xóa ô ngoại lệ.
3. **Kiểm tra dữ liệu thiếu:** so trung vị năm với trung vị giữ mặt nạ NoData; phân tích `cf_cvg` theo tháng, mọi giá trị âm và ảnh hưởng tới trung bình vùng theo đa giác. Không giả định mọi điểm ảnh có đủ 12 tháng như Diên Khánh.
4. **LISA:** tái tính quan hệ láng giềng Queen, Local Moran và giá trị p/FDR trên lưới 500 m bằng mã kiểm chứng riêng; dùng hạt ngẫu nhiên cố định, nêu rõ cách đếm trường hợp bằng nhau và hai đuôi; báo cáo nhãn HH/LL cùng các ngoại lệ.
5. **Khả năng khái quát:** chỉ coi V11 hoàn tất khi cả ba địa bàn đã có kết quả và bằng chứng đính kèm; không yêu cầu tỷ lệ diện tích HH giống Diên Khánh vì các địa bàn có cấu trúc khác nhau.
6. **Lưu trữ:** đính kèm raster/CSV, mã kiểm thử, danh mục SHA-256, mã commit, kết quả theo ô và báo cáo; cập nhật đúng [hướng dẫn kiểm chứng](../README-vi.md) và [hướng dẫn dữ liệu/phương pháp](../../docs/README-vi.md) ở cả hai ngôn ngữ.

## 5. Trạng thái hiện tại

- **Kết quả đã hoàn tất:** V11 kiểm chứng nội đô Thượng Hải, Bảo An và Kỳ Môn, kèm giới hạn về làm tròn và hạt ngẫu nhiên trong [hướng dẫn kiểm chứng](../README-vi.md).
- **Có thể chạy từ repo:** ba tệp ranh giới, mã xuất Earth Engine và trình đối chiếu Python độc lập đã được lưu. Trình đối chiếu kiểm tra tâm UTM/WGS84 để phát hiện hai ô cùng diện tích bị tráo ID.
- **Nguồn gốc lưu trữ:** manifest phục hồi ghi CSV ứng dụng, raster nguồn Thượng Hải và Kỳ Môn, bảng từng ô biên cùng các gói kiểm chứng có mã băm. Không phải mọi đầu vào đều được bung thành tệp trực tiếp trong checkout; điều đó không mở lại kết luận khoa học V11 đã hoàn tất.
