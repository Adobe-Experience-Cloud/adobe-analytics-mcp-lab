"""
Frozen **fake-dataset example** for this ``demo_example/`` folder only.

The shared skill workflow is **user-driven**: agents must use the user’s
``dataViewId`` and preferences — never assume this snapshot’s data view.
Regenerate this file when refreshing the optional preview bundle.
"""
from __future__ import annotations

# --- Fake dataset for static preview only (not a real customer data view) ---
DATA_VIEW_ID = "dv_69b9b1ab3d60bb87c5701251"
DATA_VIEW_DISPLAY_NAME = "Fake dataset (demo example)"

# listComponentUsage top-10 per type (raw), then filtered via EXCLUDE in component_network_lib
USAGE_ROWS: list[tuple[str, str, int]] = [
    ("variables/daterangeday", "dimension", 1486),
    ("variables/eventType", "dimension", 536),
    ("variables/daterangehour", "dimension", 514),
    ("variables/platformdatasetid", "dimension", 316),
    ("variables/69c276736b4f866ac4db7790.string_loyalty_tier", "dimension", 267),
    ("variables/69c3d9c0849bf329a2f5c253.product_id.string_product_id", "dimension", 235),
    ("variables/productListItems.name", "dimension", 223),
    ("variables/string_campaign_id", "dimension", 191),
    ("variables/web.webPageDetails.name", "dimension", 146),
    ("variables/69c3d8faf826a7df98006eb2.string_campaign_name", "dimension", 110),
    ("metrics/occurrences", "metric", 2606),
    ("metrics/commerce.order.priceTotal", "metric", 217),
    ("metrics/commerce.purchases.value", "metric", 197),
    ("metrics/web.webPageDetails.pageViews.value", "metric", 191),
    ("metrics/visitors", "metric", 174),
    ("metrics/commerce.productViews.value", "metric", 109),
    ("metrics/visits", "metric", 77),
    ("metrics/adobe_returnsessions", "metric", 65),
    ("metrics/69c3d8faf826a7df98006eb2.string_campaign_name", "metric", 61),
    ("metrics/adobe_firsttimesessions", "metric", 46),
    ("cm_average_revenue_per_cart_defaultmetric", "calculatedMetric", 12),
    ("cm331621C069661E8F0A495CD7@AdobeOrg_69c6cc41e722db1af3834549", "calculatedMetric", 7),
    ("cm_average_orders_per_product_defaultmetric", "calculatedMetric", 4),
    ("cm_orders_visits_defaultmetric", "calculatedMetric", 2),
    ("cm331621C069661E8F0A495CD7@AdobeOrg_69d52cfa36045a61ab60d46b", "calculatedMetric", 2),
    ("cm331621C069661E8F0A495CD7@AdobeOrg_69c6cf964cba1f0c7cbdad57", "calculatedMetric", 1),
    ("s331621C069661E8F0A495CD7@AdobeOrg_69c62e10d8c59b6c5dacc573", "segment", 509),
    ("s331621C069661E8F0A495CD7@AdobeOrg_69c4e08bb1a6d95bf486c59a", "segment", 116),
    ("one_time_purchasers", "segment", 87),
    ("s331621C069661E8F0A495CD7@AdobeOrg_69c6328ab8f7ad5865f3f59b", "segment", 36),
    ("s331621C069661E8F0A495CD7@AdobeOrg_69c586b32582137462844875", "segment", 36),
    ("s331621C069661E8F0A495CD7@AdobeOrg_69c62f77a7eae51d7345efd6", "segment", 28),
    ("repeat_visitors", "segment", 22),
    ("s331621C069661E8F0A495CD7@AdobeOrg_69c62dc2c429ad70fa48bb97", "segment", 12),
    ("s331621C069661E8F0A495CD7@AdobeOrg_69c62f56ce535703b06d1166", "segment", 12),
    ("s331621C069661E8F0A495CD7@AdobeOrg_69c52e58997a1a71d83d6186", "segment", 10),
]

DISPLAY_NAMES: dict[str, str] = {
    "variables/eventType": "Event Type [core]",
    "variables/platformdatasetid": "Platform Dataset ID [core]",
    "variables/69c276736b4f866ac4db7790.string_loyalty_tier": "Loyalty Tier [lab schema]",
    "variables/69c3d9c0849bf329a2f5c253.product_id.string_product_id": "Product ID [DataMirror AZB]",
    "variables/productListItems.name": "Product Name [multi]",
    "variables/string_campaign_id": "Campaign ID [lab schema]",
    "variables/web.webPageDetails.name": "Page Name [web,app]",
    "variables/69c3d8faf826a7df98006eb2.string_campaign_name": "Campaign Name [lab schema]",
    "metrics/commerce.order.priceTotal": "Price Total [multi]",
    "metrics/commerce.purchases.value": "Orders [multi]",
    "metrics/web.webPageDetails.pageViews.value": "Page Views [web,app]",
    "metrics/commerce.productViews.value": "Product Views [web,app]",
    "metrics/adobe_returnsessions": "Return Sessions",
    "metrics/69c3d8faf826a7df98006eb2.string_campaign_name": "Campaign Name",
    "metrics/adobe_firsttimesessions": "First-time Sessions",
    "cm_average_revenue_per_cart_defaultmetric": "Average Revenue Per Cart",
    "cm331621C069661E8F0A495CD7@AdobeOrg_69c6cc41e722db1af3834549": "Orders per Session Conversion Rate",
    "cm_average_orders_per_product_defaultmetric": "Average Orders Per Product",
    "cm_orders_visits_defaultmetric": "Orders / Visits",
    "cm331621C069661E8F0A495CD7@AdobeOrg_69d52cfa36045a61ab60d46b": "Order conversion rate (orders / session) [fake dataset]",
    "cm331621C069661E8F0A495CD7@AdobeOrg_69c6cf964cba1f0c7cbdad57": "Orders per person (%) [fake dataset]",
    "s331621C069661E8F0A495CD7@AdobeOrg_69c62e10d8c59b6c5dacc573": "Platform dataset filter (web traffic, lab)",
    "s331621C069661E8F0A495CD7@AdobeOrg_69c4e08bb1a6d95bf486c59a": "Platform Dataset ID [core] = 69c3b82db4bf20912c88187e",
    "one_time_purchasers": "One-time purchasers",
    "s331621C069661E8F0A495CD7@AdobeOrg_69c6328ab8f7ad5865f3f59b": "Platform dataset filter (web traffic, lab)",
    "s331621C069661E8F0A495CD7@AdobeOrg_69c586b32582137462844875": "Platform Dataset ID [core] = 69c3b82db4bf20912c88187e",
    "s331621C069661E8F0A495CD7@AdobeOrg_69c62f77a7eae51d7345efd6": "Platform Dataset Names exists",
    "repeat_visitors": "Repeat visitors",
    "s331621C069661E8F0A495CD7@AdobeOrg_69c62dc2c429ad70fa48bb97": "Platform Dataset Names",
    "s331621C069661E8F0A495CD7@AdobeOrg_69c62f56ce535703b06d1166": "Platform Dataset Names",
    "s331621C069661E8F0A495CD7@AdobeOrg_69c52e58997a1a71d83d6186": "Platform Dataset ID [core] = (69b828b4cdc68834993ffc17 OR …)",
}

# listFrequentlyUsedWith (canonical ids). dateRange / project rows omitted at merge time.
FUW_COUSAGE: dict[str, list[dict]] = {
    "metrics/commerce.order.priceTotal": [
        {"componentId": "variables/eventType", "componentType": "dimension", "count": 323},
        {"componentId": "variables/platformdatasetid", "componentType": "dimension", "count": 206},
        {"componentId": "metrics/occurrences", "componentType": "metric", "count": 128},
        {"componentId": "metrics/commerce.purchases.value", "componentType": "metric", "count": 102},
        {"componentId": "metrics/web.webPageDetails.pageViews.value", "componentType": "metric", "count": 80},
        {"componentId": "variables/productListItems.name", "componentType": "dimension", "count": 77},
        {"componentId": "metrics/commerce.productViews.value", "componentType": "metric", "count": 74},
    ],
    "metrics/commerce.purchases.value": [
        {"componentId": "metrics/web.webPageDetails.pageViews.value", "componentType": "metric", "count": 134},
        {"componentId": "metrics/commerce.productViews.value", "componentType": "metric", "count": 105},
        {"componentId": "metrics/commerce.order.priceTotal", "componentType": "metric", "count": 102},
        {"componentId": "metrics/occurrences", "componentType": "metric", "count": 77},
        {"componentId": "metrics/visitors", "componentType": "metric", "count": 49},
        {"componentId": "metrics/commerce.productListAdds.value", "componentType": "metric", "count": 38},
        {"componentId": "variables/productListItems._experienceshowcase.core.mainCategory", "componentType": "dimension", "count": 33},
    ],
    "metrics/web.webPageDetails.pageViews.value": [
        {"componentId": "metrics/commerce.purchases.value", "componentType": "metric", "count": 134},
        {"componentId": "metrics/commerce.productViews.value", "componentType": "metric", "count": 96},
        {"componentId": "metrics/commerce.order.priceTotal", "componentType": "metric", "count": 80},
        {"componentId": "metrics/occurrences", "componentType": "metric", "count": 77},
        {"componentId": "variables/web.webPageDetails.name", "componentType": "dimension", "count": 43},
        {"componentId": "metrics/commerce.productListAdds.value", "componentType": "metric", "count": 30},
        {"componentId": "metrics/adobe_returnsessions", "componentType": "metric", "count": 30},
        {"componentId": "variables/_experienceshowcase.interactionDetails.core.channel", "componentType": "dimension", "count": 28},
    ],
    "metrics/commerce.productViews.value": [
        {"componentId": "metrics/commerce.purchases.value", "componentType": "metric", "count": 105},
        {"componentId": "metrics/web.webPageDetails.pageViews.value", "componentType": "metric", "count": 96},
        {"componentId": "metrics/commerce.order.priceTotal", "componentType": "metric", "count": 74},
        {"componentId": "metrics/occurrences", "componentType": "metric", "count": 45},
        {"componentId": "metrics/commerce.productListAdds.value", "componentType": "metric", "count": 36},
        {"componentId": "metrics/adobe_returnsessions", "componentType": "metric", "count": 22},
        {"componentId": "metrics/adobe_firsttimesessions", "componentType": "metric", "count": 17},
        {"componentId": "metrics/visitors", "componentType": "metric", "count": 15},
    ],
    "variables/eventType": [
        {"componentId": "variables/platformdatasetid", "componentType": "dimension", "count": 256},
        {"componentId": "metrics/occurrences", "componentType": "metric", "count": 161},
        {"componentId": "one_time_purchasers", "componentType": "segment", "count": 71},
        {"componentId": "variables/productListItems.name", "componentType": "dimension", "count": 71},
        {"componentId": "metrics/commerce.order.priceTotal", "componentType": "metric", "count": 62},
    ],
    "variables/platformdatasetid": [
        {"componentId": "variables/eventType", "componentType": "dimension", "count": 469},
        {"componentId": "metrics/occurrences", "componentType": "metric", "count": 137},
        {"componentId": "variables/productListItems.name", "componentType": "dimension", "count": 75},
        {"componentId": "one_time_purchasers", "componentType": "segment", "count": 69},
        {"componentId": "metrics/commerce.order.priceTotal", "componentType": "metric", "count": 65},
    ],
    "variables/69c276736b4f866ac4db7790.string_loyalty_tier": [
        {"componentId": "metrics/occurrences", "componentType": "metric", "count": 266},
        {"componentId": "s331621C069661E8F0A495CD7@AdobeOrg_69c62e10d8c59b6c5dacc573", "componentType": "segment", "count": 141},
        {"componentId": "s331621C069661E8F0A495CD7@AdobeOrg_69c6328ab8f7ad5865f3f59b", "componentType": "segment", "count": 8},
        {"componentId": "s331621C069661E8F0A495CD7@AdobeOrg_69c586b32582137462844875", "componentType": "segment", "count": 8},
    ],
    "one_time_purchasers": [
        {"componentId": "variables/eventType", "componentType": "dimension", "count": 375},
        {"componentId": "variables/platformdatasetid", "componentType": "dimension", "count": 212},
        {"componentId": "metrics/occurrences", "componentType": "metric", "count": 87},
        {"componentId": "variables/productListItems.name", "componentType": "dimension", "count": 69},
        {"componentId": "metrics/commerce.order.priceTotal", "componentType": "metric", "count": 68},
        {"componentId": "metrics/visitors", "componentType": "metric", "count": 9},
        {"componentId": "repeat_visitors", "componentType": "segment", "count": 9},
    ],
    "s331621C069661E8F0A495CD7@AdobeOrg_69c62e10d8c59b6c5dacc573": [
        {"componentId": "metrics/occurrences", "componentType": "metric", "count": 507},
        {"componentId": "variables/69c276736b4f866ac4db7790.string_loyalty_tier", "componentType": "dimension", "count": 141},
        {"componentId": "variables/69c3d9c0849bf329a2f5c253.product_id.string_product_id", "componentType": "dimension", "count": 76},
        {"componentId": "variables/string_campaign_id", "componentType": "dimension", "count": 71},
        {"componentId": "variables/69c3d8faf826a7df98006eb2.string_campaign_name", "componentType": "dimension", "count": 25},
    ],
    "cm331621C069661E8F0A495CD7@AdobeOrg_69c6cc41e722db1af3834549": [
        {"componentId": "metrics/commerce.order.priceTotal", "componentType": "metric", "count": 7},
        {"componentId": "variables/productListItems._experienceshowcase.core.mainCategory", "componentType": "dimension", "count": 7},
        {"componentId": "metrics/commerce.purchases.value", "componentType": "metric", "count": 7},
    ],
}
