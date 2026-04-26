# Yahoo! JAPAN Real Estate Workflow

## Source

- `source`: `yahoo_japan`
- Start URL: `https://realestate.yahoo.co.jp/`

## Search Flow

1. Open Yahoo! JAPAN 不動産.
2. Select listing category: mansion, detached house, land, rental, or investment if available.
3. For used condominium purchase, a direct city code URL such as `https://realestate.yahoo.co.jp/used/mansion/search/03/13/13104/` can reach Shinjuku-ku results.
4. Apply user location and filter requirements.
5. Open detail pages and extract property, price, access, building, agency, and media fields.

## Search Filters to Try

| User/query field | Yahoo control label to look for | Notes |
| --- | --- | --- |
| `transaction_type` | 買う / 借りる / 中古 / 新築 / 賃貸 | Route/category names vary by page. |
| `property_type` | 中古マンション / 新築マンション / 一戸建て / 土地 / 賃貸マンション | Use the closest visible category. |
| `area.prefecture`, `area.city_or_ward` | 都道府県 / 市区町村 | Public city pages expose additional condition filters. |
| `area.railway_line`, `area.station` | 沿線 / 駅 | Use when visible; otherwise navigate by area and post-filter access. |
| `max_price_jpy`, `max_rent_jpy` | 価格 / 賃料 | Use nearest bucket. |
| `layout` | 間取り | Public pages expose layout filters. |
| `min_floor_area_sqm` | 専有面積 / 建物面積 | Public used-mansion pages expose 専有面積. |
| `min_land_area_sqm` | 土地面積 | Houses/land. |
| `max_building_age_years`, `new_building_only` | 築年数 | Public used-mansion pages expose 築年数. |
| `max_walk_minutes` | 駅からの徒歩分 / 駅徒歩 | Public used-mansion pages expose walk-minute filters. |
| feature flags | こだわり条件 | Availability varies; try only if visible and post-filter otherwise. |

## Verified Search Path

Browser Use Cloud probe on 2026-04-26:

- Direct route reached: `https://realestate.yahoo.co.jp/used/mansion/search/03/13/13104/`
- Filters are in the left sidebar under `検索条件の変更`.
- Applied exactly: max price `8000万円`, floor area `40㎡`, layouts `1LDK` and `2LDK`, station walk `10分以内`.
- Price, floor area, and walk time were custom JavaScript dropdowns opened by anchor-like controls, not plain select elements.
- Observed price upper buckets include `7000万円`, `7500万円`, `8000万円`, `9000万円`.
- Observed walk buckets include `5分以内`, `7分以内`, `10分以内`, `15分以内`.

## Field Mapping Hints

| Yahoo label | Unified field |
| --- | --- |
| 価格 / 賃料 | `price_text`, `price_jpy` |
| 管理費 | `management_fee_jpy` |
| 修繕積立金 | `repair_reserve_fund_jpy` |
| 所在地 | `address`, area fields |
| 交通 | `nearest_stations` |
| 種別 | `property_type` |
| 間取り | `layout` |
| 専有面積 | `floor_area_sqm` |
| 土地面積 | `land_area_sqm` |
| 建物面積 | `building_area_sqm` |
| 階建 / 所在階 | `floor`, `total_floors`, `basement_floors` |
| 構造 | `structure` |
| 築年月 | `built_year`, `built_month`, `age_text` |
| 総戸数 | `total_units` |
| 方位 | `orientation` |
| 駐車場 | `parking` |
| 土地権利 | `rights` |
| 現況 | `current_status` |
| 引き渡し時期 | `delivery_time` |
| 情報提供会社 | `agency_name`, `agency_phone`, `agency_license` |

## Extraction Notes

- Yahoo pages may aggregate data from partner sources. Keep both Yahoo source identity and any visible partner label in `raw`.
- If the detail URL redirects, use the final visible detail URL as `source_url`.
- Record unavailable search controls in `raw.unapplied_filters`.
