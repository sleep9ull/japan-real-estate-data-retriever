# LIFULL HOME'S Workflow

## Source

- `source`: `homes`
- Start URL: `https://www.homes.co.jp/`

## Search Flow

1. Open HOME'S.
2. Pick sale/rent/investment category and property type.
3. For used condominium purchase, a direct path like `https://www.homes.co.jp/mansion/chuko/tokyo/city/` can lead to city selection.
4. Apply location filters by prefecture, city/ward, railway line, station, or commute constraints.
5. Apply budget, area, layout, walk minutes, age, floor, and building conditions.
6. Open each detail page and extract structured overview fields.

## Search Filters to Try

| User/query field | HOME'S control label to look for | Notes |
| --- | --- | --- |
| `transaction_type` | 買う / 借りる / 売る / 賃貸 | Route first. |
| `property_type` | マンション / 一戸建て / 土地 / 賃貸マンション / アパート | Use sale/rent category. |
| `area.prefecture`, `area.city_or_ward` | 地域 / 都道府県 / 市区町村 | Prefer exact municipality. |
| `area.railway_line`, `area.station` | 路線・駅 | Use station filters when available. |
| `max_price_jpy`, `max_rent_jpy` | 価格 / 賃料 | Use nearest bucket. |
| `layout` | 間取り | Multi-select if possible. |
| `min_floor_area_sqm` | 専有面積 / 建物面積 | Condos/rentals vs houses. |
| `min_land_area_sqm` | 土地面積 | Houses/land. |
| `max_building_age_years`, `new_building_only` | 築年数 / 新築 | Use stricter bucket first. |
| `max_walk_minutes` | 駅徒歩 | Verify detail page access text. |
| rental cost preferences | 敷金なし / 礼金なし / 管理費込み | Rental categories. |
| feature flags | こだわり条件 / 設備条件 | Try parking, pet, bath/toilet separate, auto-lock, delivery box, second floor, south-facing, renovation. |

## Verified Search Path

Browser Use Cloud probe on 2026-04-26:

- Start: `https://www.homes.co.jp/`
- Used condominium city route: `https://www.homes.co.jp/mansion/chuko/tokyo/city/`
- Shinjuku results: `https://www.homes.co.jp/mansion/chuko/tokyo/shinjuku-city/list/`
- Applied exactly: max price `8,000万円`, floor area `40m²`, layouts `1LDK` and `2LDK`, station walk `10分以内`.
- Observed controls: `価格上限` select, `専有面積下限` select, `間取り` checkboxes, `駅徒歩` select.
- The result count/search button may be dynamic; after changing controls, click the visible result/search button and verify the result URL or active conditions.

## Field Mapping Hints

| HOME'S label | Unified field |
| --- | --- |
| 価格 / 賃料 | `price_text`, `price_jpy` |
| 管理費等 | `management_fee_jpy` |
| 修繕積立金 | `repair_reserve_fund_jpy` |
| 所在地 | `address`, area fields |
| 交通 | `nearest_stations` |
| 物件種別 | `property_type` |
| 間取り | `layout` |
| 専有面積 | `floor_area_sqm` |
| 土地面積 | `land_area_sqm` |
| 建物面積 | `building_area_sqm` |
| バルコニー面積 | `balcony_area_sqm` |
| 階数 | `floor`, `total_floors`, `basement_floors` |
| 構造 | `structure` |
| 築年月 | `built_year`, `built_month`, `age_text` |
| 総戸数 | `total_units` |
| 主要採光面 | `orientation` |
| 駐車場 | `parking` |
| 土地権利 | `rights` |
| 現況 | `current_status` |
| 引渡し | `delivery_time` |
| 取扱い不動産会社 | `agency_name`, `agency_phone`, `agency_license` |

## Extraction Notes

- HOME'S often has result-card comparison fields; still prefer detail page fields.
- Preserve unsure labels in `raw.homes_labels`.
- Record unavailable search controls in `raw.unapplied_filters`.
