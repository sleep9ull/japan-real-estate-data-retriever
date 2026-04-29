# SUUMO Workflow

## Source

- `source`: `suumo`
- Start URL: `https://suumo.jp/`
- Common detail URLs often contain source-specific listing codes. Extract the most stable ID visible in the URL or page metadata.

## Search Flow

1. Open SUUMO.
2. Select transaction category from the user query, such as sale mansion, detached house, land, or rental.
3. Apply area or station filters.
4. For used condominium purchase, a direct path like `https://suumo.jp/ms/chuko/tokyo/city/` can lead to city selection, then Shinjuku-ku results.
5. Apply price, layout, walking distance, floor area, age, and other filters when available.
6. Open each result detail page in turn.
7. Extract detail page fields and image URLs.

## Search Filters to Try

| User/query field | SUUMO control label to look for | Notes |
| --- | --- | --- |
| `transaction_type` | 買う / 借りる / 売買 / 賃貸 | Route first; controls differ by route. |
| `property_type` | 新築マンション / 中古マンション / 新築一戸建て / 中古一戸建て / 土地 / 賃貸マンション | Use the closest category. |
| `area.prefecture`, `area.city_or_ward` | エリア / 都道府県 / 市区郡 | Prefer exact city/ward. |
| `area.railway_line`, `area.station` | 沿線・駅 | Use station search when the user says "near X station". |
| `max_price_jpy`, `max_rent_jpy` | 価格 / 賃料 | Use the nearest available bucket. |
| `layout` | 間取り | Used-condo probe showed grouped buckets such as `1K/DK/LDK`, `2K/DK/LDK`; apply grouped buckets and post-filter exact layout. |
| `min_floor_area_sqm` | 専有面積 / 建物面積 | For condos use 専有面積; for houses use 建物面積. |
| `min_land_area_sqm` | 土地面積 | Houses and land only. |
| `max_building_age_years`, `new_building_only` | 築年数 / 新築 / 築浅 | Use stricter bucket first. |
| `max_walk_minutes` | 駅徒歩 | Common buckets include 5, 10, 15 minutes. |
| feature flags | こだわり条件 / 特徴 | Try parking, pet, 2階以上, 角住戸, 南向き, リフォーム/リノベーション when visible. |

## Verified Search Path

Browser Use Cloud probe on 2026-04-26:

- Start: `https://suumo.jp/`
- Used condominium city route: `https://suumo.jp/ms/chuko/tokyo/city/`
- Shinjuku result URL pattern: `https://suumo.jp/jj/bukken/ichiran/JJ010FJ001/?...&sc=13104...`
- Observed controls: `価格上限`, `専有面積下限`, `駅徒歩`, `間取り`.
- Observed station-walk buckets: `1分以内`, `3分以内`, `5分以内`, `7分以内`, `10分以内`, `15分以内`, `20分以内`, `指定なし`.
- Observed floor-area lower buckets include `20m2以上`, `30m2以上`, `40m2以上`, `50m2以上`.
- Important: the probe reached the result page and found controls, but only area/city was fully applied before stopping; apply the remaining controls and verify the resulting URL or active filter chips.

## Field Mapping Hints

| SUUMO label | Unified field |
| --- | --- |
| 価格 / 賃料 | `price_text`, `price_jpy` |
| 管理費 | `management_fee_jpy` |
| 修繕積立金 | `repair_reserve_fund_jpy` |
| 所在地 | `address`, area fields |
| 交通 | `nearest_stations` |
| 間取り | `layout` |
| 専有面積 | `floor_area_sqm` |
| 土地面積 | `land_area_sqm` |
| 建物面積 | `building_area_sqm` |
| バルコニー | `balcony_area_sqm` |
| 所在階 / 階建 | `floor`, `total_floors`, `basement_floors` |
| 構造 | `structure` |
| 築年月 | `built_year`, `built_month`, `age_text` |
| 総戸数 | `total_units` |
| 向き | `orientation` |
| 駐車場 | `parking` |
| 権利 | `rights` |
| 引渡し | `delivery_time` |
| 会社情報 | `agency_name`, `agency_phone`, `agency_license` |

## Extraction Notes

- Prefer the detail page table over result card snippets.
- If pagination is needed, stop after `max_results` detail pages are extracted.
- Keep SUUMO-specific labels in `raw.suumo_labels`.
- Record unavailable search controls in `raw.unapplied_filters`.
