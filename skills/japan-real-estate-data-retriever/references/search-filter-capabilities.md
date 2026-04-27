# Search Filter Capabilities

Use this reference before driving a Cloud Browser or creating a fallback Agent task. It tells the local agent how to translate a user's natural-language request into website search controls.

## Normalized Query Shape

```json
{
  "schema_version": "2026-04-26",
  "intent": "search_real_estate_listings",
  "transaction_type": "sale",
  "property_type": "中古マンション",
  "area": {
    "prefecture": "東京都",
    "city_or_ward": "新宿区",
    "railway_line": null,
    "station": null
  },
  "filters": {
    "min_price_jpy": null,
    "max_price_jpy": 80000000,
    "min_rent_jpy": null,
    "max_rent_jpy": null,
    "management_fee_included": null,
    "deposit_key_money_preference": null,
    "layout": ["1LDK", "2LDK"],
    "min_floor_area_sqm": 40,
    "max_floor_area_sqm": null,
    "min_land_area_sqm": null,
    "max_land_area_sqm": null,
    "max_building_age_years": null,
    "new_building_only": false,
    "max_walk_minutes": 10,
    "bus_allowed": null,
    "floor_min": null,
    "floor_max": null,
    "second_floor_or_higher": null,
    "parking_required": null,
    "pet_allowed": null,
    "separate_bath_toilet": null,
    "auto_lock": null,
    "delivery_box": null,
    "corner_unit": null,
    "south_facing": null,
    "renovated": null
  },
  "sort": {
    "field": "price",
    "direction": "asc"
  },
  "max_results": 10
}
```

## User Intent to Filter Mapping

| User says | Normalized field | Site control to try | Apply as |
| --- | --- | --- | --- |
| Tokyo, Osaka, Fukuoka | `area.prefecture` | 都道府県 | exact filter |
| Shinjuku-ku, Minato-ku | `area.city_or_ward` | 市区町村 / エリア | exact filter |
| near Shibuya Station | `area.station` | 沿線・駅 / 駅 | exact filter |
| Yamanote Line | `area.railway_line` | 沿線 | exact filter |
| buy, purchase | `transaction_type=sale` | 売買 / 買う | exact route/category |
| rent, lease | `transaction_type=rent` | 賃貸 / 借りる | exact route/category |
| used condo | `property_type=中古マンション` | 中古マンション | exact category |
| new condo | `property_type=新築マンション` | 新築マンション | exact category |
| detached house | `property_type=一戸建て` | 新築一戸建て / 中古一戸建て | clarify if needed, else infer from age |
| land | `property_type=土地` | 土地 | exact category |
| under 80 million yen | `filters.max_price_jpy` | 価格上限 | exact filter |
| rent under 200k yen/month | `filters.max_rent_jpy` | 賃料上限 | exact filter |
| no key money | `deposit_key_money_preference` | 礼金なし / 敷金なし | exact if available, otherwise post-filter |
| 1LDK or 2LDK | `filters.layout` | 間取り | exact multi-select |
| at least 40 sqm | `filters.min_floor_area_sqm` | 専有面積 / 建物面積 下限 | exact filter |
| land over 100 sqm | `filters.min_land_area_sqm` | 土地面積 下限 | exact for houses/land |
| built within 10 years | `filters.max_building_age_years` | 築年数 | exact or nearest stricter bucket |
| new only | `filters.new_building_only` | 新築 / 築浅 | exact if available |
| within 10 min walk | `filters.max_walk_minutes` | 駅徒歩 | exact or nearest stricter bucket |
| no bus | `filters.bus_allowed=false` | バス利用なし / 徒歩のみ | post-filter if no control |
| second floor or higher | `filters.second_floor_or_higher` | 2階以上 | exact if available |
| parking | `filters.parking_required` | 駐車場あり | exact if available |
| pets allowed | `filters.pet_allowed` | ペット可 / 相談 | exact if available |
| separate bath/toilet | `filters.separate_bath_toilet` | バス・トイレ別 | exact for rental |
| auto-lock | `filters.auto_lock` | オートロック | exact if available |
| delivery box | `filters.delivery_box` | 宅配ボックス | exact if available |
| corner unit | `filters.corner_unit` | 角部屋 / 角住戸 | exact if available |
| south facing | `filters.south_facing` | 南向き | exact if available |
| renovated | `filters.renovated` | リフォーム / リノベーション | exact if available |

## Filter Priority

Apply filters in this order:

1. Source/category route: sale vs rent, property type.
2. Location: prefecture, city/ward, railway line, station.
3. Hard numeric limits: price/rent, area, walk minutes, age.
4. Layout.
5. Required features: parking, pets, second floor, bath/toilet, equipment.
6. Sort and pagination.
7. Soft preferences: view, sunlight, quiet, brand-name building, neighborhood feel. These usually require detail-page reading or post-filtering.

## Bucket Conversion Rules

Site controls often use buckets, not arbitrary numbers.

- For maximum price/rent, choose the nearest available bucket that is less than or equal to the user's maximum when possible. If that would exclude too much because the bucket is coarse, choose the next higher bucket and post-filter extracted results.
- For minimum floor/land/building area, choose the nearest available bucket that is greater than or equal to the user's minimum when possible. If no such bucket exists, choose the nearest lower bucket and post-filter.
- For maximum building age and maximum walk minutes, choose the nearest stricter bucket first.
- For layout, do not assume every site has exact `1LDK` / `2LDK` controls. If the site groups layouts such as `1K/DK/LDK` or `2K/DK/LDK`, apply the grouped bucket and post-filter detail-page `layout`.
- Record every compromise in `raw.filter_translation_notes`.

## Browser Use Cloud Probe Notes

Validated on 2026-04-26 with Browser Use Cloud against the concrete query: used condo purchase, Tokyo Shinjuku, max price 8000万円, 40㎡+, 1LDK/2LDK, walk 10 minutes.

- SUUMO: reached `suumo.jp/ms/chuko/tokyo/city/` then Shinjuku results. Price, area, station walk, and layout filters were present. Layout was grouped (`1K/DK/LDK`, `2K/DK/LDK`), so exact `1LDK` / `2LDK` needs post-filtering.
- at home: initial navigation may trigger a WAF challenge. Direct used-condo Tokyo/Shinjuku path worked. Price upper, floor-area lower, layout checkboxes, and station walk were applied exactly.
- HOME'S: direct path `homes.co.jp/mansion/chuko/tokyo/shinjuku-city/list/` worked. Price upper, floor-area lower, layout checkboxes, and station walk were applied exactly.
- Yahoo! JAPAN: direct path `realestate.yahoo.co.jp/used/mansion/search/03/13/13104/` worked. Price, area, and walk controls were custom JavaScript dropdowns; layout used checkboxes.

## Cross-Site Capability Matrix

| Filter family | SUUMO | at home | HOME'S | Yahoo! JAPAN |
| --- | --- | --- | --- | --- |
| Transaction category | strong | strong | strong | strong |
| Property type | strong | strong | strong | strong |
| Prefecture/city/ward | strong | strong | strong | strong |
| Railway line/station | strong | strong | strong | strong |
| Price/rent range | strong | strong | strong | strong |
| Layout | strong | strong | strong | strong |
| Floor/building/land area | strong | strong | strong | strong |
| Building age/newness | strong | strong | strong | strong |
| Station walk time | strong | strong | strong | strong |
| Management/common fee | medium | medium | medium | medium |
| Deposit/key money | rental only | rental only | rental only | rental only |
| Floor level / 2F+ | medium | medium | medium | medium |
| Parking | medium | medium | medium | medium |
| Pets/equipment/security | rental-heavy | rental-heavy | rental-heavy | rental-heavy |
| Renovation/corner/south-facing | medium | medium | medium | medium |
| Map search | medium | medium | medium | medium |

`strong` means the filter is commonly available and should be attempted. `medium` means availability varies by transaction/property type; attempt it if visible, otherwise post-filter and record it.
