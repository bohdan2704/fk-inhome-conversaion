# Propositions Feed Rules From PDF

Source: `instructions/propositions.pdf`
Document title: `Фід з пропозиціями | Інтеграція партнерів`

## Operational requirements

- The feed is used to update:
  - prices
  - product availability
  - delivery conditions
  - warranty information
  - installment availability
- Scheduled refresh runs every `30` minutes starting at `00:00:00`, so the feed should be ready at times like `00:00`, `00:30`, `01:00`, `01:30`, and so on.
- The refresh interval can be changed on request to a value between `5` and `60` minutes.
- If an offer disappears from the feed, that proposition is automatically disabled.
- If the feed is unavailable for `3` hours, all propositions are automatically disabled.
- Response timeout limit: `30` seconds.
- When loading fails, the platform retries until the feed returns a correct response or the retry limit is reached.

## Authorization options mentioned in the PDF

- Bearer token
- Basic auth
- OAuth 2.0 on request
- Token in a query parameter

## Feed structure

The PDF documents logical fields rather than XML tags. In repository terms, these map naturally to the same names as XML tags.

- `total`: total number of propositions, type `int`, optional
- `data`: array of propositions, required

## Offer fields

Each proposition item contains the following logical fields:

- `code`
  - type: `string`
  - required: yes
  - meaning: unique proposition code used in order creation
- `price`
  - type: `int`
  - required: yes
  - meaning: current proposition price
- `old_price`
  - type: `int | null`
  - required: no
  - default: `null`
  - meaning: old price for discount display
- `availability`
  - type: `boolean`
  - required: yes
- `warranty_type`
  - type: enum string
  - allowed values: `manufacturer`, `merchant`, `no`
  - default: `no`
- `warranty_period`
  - type: `int`
  - default: `0`
  - notes:
    - `999` means lifetime warranty
    - value is displayed in months
    - if empty or `0`, warranty is treated as absent
    - the maximum warranty shown by the platform is `120` months
- `max_pay_in_parts`
  - type: `int`
  - default: `3`
  - meaning: maximum number of installment payments
- `days_to_dispatch`
  - type: `int`
  - default: `1`
  - meaning:
    - `0` = today
    - `1` = tomorrow
    - `>1` = in X days
- `delivery_methods`
  - type: `array`
  - default: all delivery methods available
- `checkout_constraints`
  - type: `object`
  - default: `null`
- `manufacture`
  - type: `object`
  - default: `null`

## Delivery method structure

Each delivery method item contains:

- `method`
  - type: enum string
  - required: yes
  - allowed values:
    - `nova-post:branch`
    - `nova-post:cargo_branch`
    - `nova-post:postomat`
    - `courier:nova-post`
- `price`
  - type: `number`
  - default: `0`
  - note: the PDF says delivery from the marketplace is currently always free, and this field exists for future updates

## Checkout constraints structure

- `multiplicity`
  - type: `int`
  - default: `null`
  - meaning: sale quantity step, for example `2` means the basket can contain only `2`, `4`, `6`, `8`, and so on

## Manufacture structure

- `country_code`
  - type: `string`
  - default: `null`
  - meaning: production country code in `ISO 3166-1 alpha-2`
- `year`
  - type: `number`
  - default: `null`
  - meaning: manufacturing year

## Additional notes from the PDF

- The propositions document describes business fields and behavior, not a fixed XML wrapper.
- When auditing the generated XML feed in this repository, the relevant check is whether the XML provides the same logical fields and values described above.
