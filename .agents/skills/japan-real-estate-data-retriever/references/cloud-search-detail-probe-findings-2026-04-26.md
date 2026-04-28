# Browser Use Cloud Search and Detail Probe Findings, 2026-04-26

Probe query: used condominium purchase, Tokyo Shinjuku-ku, max price 8000万円, floor area 40㎡+, layout 1LDK or 2LDK, station walk 10 minutes.

Raw local probe files:

- `data/raw/cloud-search-detail-probe-results.json`
- `data/raw/cloud-detail-field-probe-results.json`

The second file contains deeper detail-page extraction for at home and Yahoo! JAPAN. SUUMO and HOME'S could not be re-run in the second detail-only pass because the Browser Use Cloud task quota was reached, but their first-pass search/detail runs completed successfully.

## Search Paths and Filters

### SUUMO

- Result path: `https://suumo.jp/ms/chuko/tokyo/city/` -> Shinjuku selection -> `https://suumo.jp/jj/bukken/ichiran/JJ012FC001/?...`
- Result URL included parameters for Shinjuku, price upper `8000`, area lower `40`, and station walk `10`.
- Available filters observed:
  - `価格`: select; sample values `500万円未満`, `1000万円未満`, `1500万円未満`, `2000万円未満`, `2500万円未満`.
  - `専有面積`: select; sample values `下限なし`, `20m2以上`, `30m2以上`, `40m2以上`, `50m2以上`.
  - `駅徒歩`: select; sample values `1分以内`, `3分以内`, `5分以内`, `7分以内`, `10分以内`.
  - `間取り`: available, but used-condo buckets may be grouped such as `1K/DK/LDK` and `2K/DK/LDK`.

### at home

- Result path: direct URL pattern `https://www.athome.co.jp/mansion/chuko/tokyo/shinjuku-city/list/`.
- Filtered URL parameters observed: `PRICETO=kp115`, `MENSEKI=kt106`, `EKITOHO=ke004`, `km005=1`, `km010=1`.
- Available filters observed:
  - `価格 (上限)`: select; sample values `8,000万円`, `1,000万円`.
  - `専有面積 (下限)`: select; sample values `40m²`, `100m²`.
  - `駅徒歩`: select; sample values `10分以内`, `5分以内`.
  - `間取り`: checkbox; sample values `1LDK`, `2LDK`.
- Direct category/list URLs are useful when a WAF challenge appears on the top page.

### LIFULL HOME'S

- Result path: `https://www.homes.co.jp/mansion/chuko/tokyo/shinjuku-city/list/`.
- Available filters observed:
  - `価格上限`: select; sample values `3,000万円`, `5,000万円`, `8,000万円`.
  - `専有面積下限`: select; sample values `20m²`, `40m²`, `60m²`.
  - `間取り`: checkbox; sample values `1LDK`, `2LDK`, `3LDK`.
  - `駅徒歩`: select; sample values `5分以内`, `10分以内`, `15分以内`.
- Search button can be a dynamic submit control after filter changes.

### Yahoo! JAPAN Real Estate

- Result path: `https://realestate.yahoo.co.jp/used/mansion/search/03/13/13104/`.
- Filtered URL pattern observed: `?baTo=8000&maFrom=40&rlDtl=3,5&minSt=10`.
- Available filters observed:
  - `価格`: custom dropdown/trigger.
  - `間取り`: checkbox; sample values `ワンルーム`, `1K/1DK`, `1LDK`, `2K/2DK`, `2LDK`.
  - `専有面積`: custom dropdown/trigger.
  - `駅からの徒歩分`: custom dropdown/trigger.
- Direct URL parameters are more reliable than clicking custom JS dropdowns.

## Detail Fields Observed

### SUUMO

Detail URL: `https://suumo.jp/ms/chuko/tokyo/sc_shinjuku/nc_20483964/`

Important structured labels observed:

- Property identity and price: `物件名`, `価格`, `間取り`, `販売戸数`, `最多価格帯`.
- Area and floor: `専有面積`, `その他面積`, `所在階`, `所在階/構造・階建`, `構造・階建て`.
- Building: `総戸数`, `完成時期（築年月）`, `完成時期(築年月)`, `施工`.
- Location/access: `住所`, `所在地`, `交通`.
- Costs: `管理費`, `修繕積立金`, `修繕積立基金`, `諸費用`.
- Transaction/legal: `引渡可能時期`, `敷地の権利形態`, `用途地域`, `その他制限事項`, `その他概要・特記事項`.
- Quality/energy: `リフォーム`, `エネルギー消費性能`, `断熱性能`, `目安光熱費`.
- Parking/orientation: `向き`, `駐車場`.
- Agency/update: `会社概要`, `問い合わせ先`, `情報提供日`, `次回更新予定日`, `取引条件有効期限`.

Ignore inquiry form labels and mortgage/support promotional blocks unless the user explicitly asks for inquiry workflow data.

### at home

Detail URL: `https://www.athome.co.jp/mansion/6988537845/`

Important structured labels observed:

- Location/access: `所在地`, `交通`.
- Price/cost: `価格`, `平米単価`, `管理費等`, `修繕積立金`.
- Building/unit: `建物名・部屋番号`, `間取り`, `専有面積`, `バルコニー`, `階建 / 階`, `建物構造`, `築年月`, `総戸数`.
- Legal/management: `土地権利`, `管理形態／管理員の勤務形態`.
- Investment/remarks: `備考`, with values including `主要採光面`, `利回り`, and `年間予定賃料収入`.
- Equipment/features: `設備・サービス`, `その他`.
- Transaction/status: `現況`, `引渡可能時期`, `取引態様`, `物件番号`, `情報公開日`, `次回更新予定日`.
- Agency: `掲載会社名`, `所在地`, `交通`, `営業時間`, `定休日`, `免許番号`.
- Media: multiple `物件画像` URLs.

The sampled detail page was an investment/small-room listing and did not match all search filters. Keep search/filter verification and detail-field capability verification separate.

### LIFULL HOME'S

Detail URL: `https://www.homes.co.jp/mansion/b-76710015140/`

Important structured labels observed:

- Price/cost: `価格`, `管理費`, `修繕積立金`.
- Unit/building: `レイアウト`, `面積`, `築年数`, `階数`, `構造`, `総戸数`.
- Location/access: `住所`, `アクセス`.
- Legal: `権利`.
- Agency: `会社名`.
- Media: image count observed as `94`.

The first-pass extraction was shallower than at home/Yahoo; keep source table rows in `source_structured_fields` when running production extraction.

### Yahoo! JAPAN Real Estate

Detail URL: `https://realestate.yahoo.co.jp/used/mansion/detail_corp/b0024620279/`

Important structured labels observed:

- Price/cost: `価格`, `管理費`, `修繕積立金`.
- Location/access: `所在地`, `交通`.
- Unit/building: `間取り`, `専有面積`, `築年月`, `主要採光面`, `所在階 / 階建`, `総戸数`, `建物状況`, `構造・工法`.
- Status/transaction: `建物現況`, `引き渡し可能時期`, `用途地域`, `土地権利形態`, `管理人`, `管理形態`, `駐車場・車庫`, `備考`.
- Description/update: `おすすめポイント`, `情報掲載開始日`, `情報更新日`, `次回更新予定日`.
- Agency: `商号`, `住所`, `交通`, `営業時間`, `定休日`, `取引態様`, `免許番号`.
- Media: `画像枚数`, image captions such as `外観写真`, `現況写真`, `玄関`, `建物エントランス`.

## Schema Implications

The project schema should include normalized fields for the common high-value attributes and a generic `source_structured_fields` array for every original label/value pair that does not fit cleanly. This prevents data loss as sites change labels or expose source-specific sections.

