# at home Workflow

## Source

- `source`: `athome`
- Start URL: `https://www.athome.co.jp/`

## Search Flow

1. Open at home.
2. Choose sale/rent and property type from the user's query.
3. If the top page triggers a WAF or challenge page, retry with a direct category/area path and stop if the challenge cannot be cleared.
4. Apply area, railway/station, price, floor area, layout, age, and walk-time filters.
5. Open detail pages from the result list.
6. Extract property overview, cost fields, traffic, agency, and media.

## Search Filters to Try

| User/query field | at home control label to look for | Notes |
| --- | --- | --- |
| `transaction_type` | 買う / 借りる / 売買 / 賃貸 | Select route before area. |
| `property_type` | マンション / 一戸建て / 土地 / アパート / 賃貸マンション | Pick sale/rent-specific category. |
| `area.prefecture`, `area.city_or_ward` | 地域から探す / 都道府県 / 市区町村 | Prefer city/ward exact match. |
| `area.railway_line`, `area.station` | 沿線・駅から探す | Use for station-centered requests. |
| `max_price_jpy`, `max_rent_jpy` | 価格 / 賃料 | Use nearest bucket and post-filter if needed. |
| `layout` | 間取り | Multi-select when available. |
| `min_floor_area_sqm` | 専有面積 / 建物面積 | Label depends on property type. |
| `min_land_area_sqm` | 土地面積 | Houses/land. |
| `max_building_age_years`, `new_building_only` | 築年数 / 新築 | Use stricter bucket first. |
| `max_walk_minutes` | 駅徒歩 | Use bus/walk text on detail page for verification. |
| rental cost preferences | 敷金なし / 礼金なし / 管理費込み | Availability varies by rental category. |
| feature flags | こだわり条件 | Try parking, pet, bath/toilet separate, auto-lock, delivery box, second floor, corner room. |

## Verified Search Path

Browser Use Cloud probe on 2026-04-26:

- Direct route reached: `https://www.athome.co.jp/mansion/chuko/tokyo/shinjuku-city/list/`
- Result URL kept filter parameters such as `pref=13`, `cities=shinjuku`, and `basic=...`.
- Applied exactly: max price `8,000万円`, floor area `40m²`, layouts `1LDK` and `2LDK`, station walk `10分以内`.
- Observed controls: `価格(上限)` select, `専有面積` select, `1LDK`/`2LDK` checkboxes, `駅徒歩` select.
- Initial attempt saw a challenge message: `認証にご協力ください`. Treat this as a possible WAF branch, not as a mapping failure.

## Field Mapping Hints

| at home label | Unified field |
| --- | --- |
| 価格 / 賃料 | `price_text`, `price_jpy` |
| 管理費等 | `management_fee_jpy` |
| 修繕積立金 | `repair_reserve_fund_jpy` |
| 敷金 / 礼金 | `deposit_key_money_text` |
| 所在地 | `address`, area fields |
| 交通 | `nearest_stations` |
| 物件種目 | `property_type` |
| 間取り | `layout` |
| 専有面積 | `floor_area_sqm` |
| 土地面積 | `land_area_sqm` |
| 建物面積 | `building_area_sqm` |
| 築年月 | `built_year`, `built_month`, `age_text` |
| 階建 / 階 | `floor`, `total_floors`, `basement_floors` |
| 建物構造 | `structure` |
| 現況 | `current_status` |
| 引渡可能時期 | `delivery_time` |
| 取扱い不動産会社 | `agency_name`, `agency_phone`, `agency_license` |

## Extraction Notes

- at home pages may expose rich tabular labels; preserve unmapped labels in `raw.athome_labels`.
- Some IDs may only be visible in URL segments or hidden page metadata; if not visible, rely on URL fallback.
- Record unavailable search controls in `raw.unapplied_filters`.
