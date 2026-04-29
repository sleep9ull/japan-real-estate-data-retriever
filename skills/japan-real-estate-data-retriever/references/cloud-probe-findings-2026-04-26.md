# Browser Use Cloud Probe Findings, 2026-04-26

Probe query: used condominium purchase, Tokyo Shinjuku-ku, max price 8000万円, floor area 40㎡+, layout 1LDK or 2LDK, station walk 10 minutes.

## Summary

All four sites had a workable used-condominium search path and exposed the core filters: area, price, floor area, layout, and station walk time. The main rule adjustment is that control shape differs: SUUMO may group layout buckets, Yahoo uses custom JavaScript dropdowns, and at home may show a WAF challenge before direct navigation succeeds.

## SUUMO

- Reached result page: yes.
- Route: `https://suumo.jp/` -> `https://suumo.jp/ms/chuko/tokyo/city/` -> Shinjuku result list.
- Observed controls: `価格上限`, `専有面積下限`, `駅徒歩`, `間取り`.
- Layout buckets observed as grouped values like `1K/DK/LDK` and `2K/DK/LDK`; use post-filtering for exact `1LDK` / `2LDK`.
- Area/city was applied. Remaining controls were present but should be explicitly applied and verified by active conditions or URL parameters.

## at home

- Reached result page: yes.
- Route: direct used-condo Tokyo/Shinjuku list path.
- Applied exactly: price upper `8,000万円`, floor area `40m²`, `1LDK`, `2LDK`, station walk `10分以内`.
- Initial navigation may show `認証にご協力ください`; retrying/direct category navigation can still work.

## HOME'S

- Reached result page: yes.
- Route: `https://www.homes.co.jp/` -> `https://www.homes.co.jp/mansion/chuko/tokyo/city/` -> Shinjuku list.
- Applied exactly: price upper `8,000万円`, floor area `40m²`, `1LDK`, `2LDK`, station walk `10分以内`.
- Search/result count button can be dynamic after filter changes.

## Yahoo! JAPAN

- Reached result page: yes.
- Route: `https://realestate.yahoo.co.jp/used/mansion/search/03/13/13104/`.
- Filters live under `検索条件の変更`.
- Applied exactly: price upper `8000万円`, floor area `40㎡`, `1LDK`, `2LDK`, station walk `10分以内`.
- Price, area, and walk controls are custom JavaScript dropdowns; layout is checkbox-based.

