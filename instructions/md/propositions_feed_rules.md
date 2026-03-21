# Propositions Feed Rules

Source: `instructions/propositions.pdf`

## Technical requirements

- Feed should refresh every 30 minutes
- If an offer disappears from the feed, it is disabled automatically
- If the feed is unavailable for 3 hours, all propositions are disabled
- Response timeout limit: 30 seconds

## Original source format in the PDF

The PDF describes the propositions feed as a structure with:

- `total`
- `data[]`
- one item per offer with pricing, availability, warranty, installments, dispatch, delivery, and manufacturing metadata

The PDF examples use JSON field names. For this project, the second generator maps the same field set into XML because the requested deliverable is two XML feeds.

## XML mapping used in this project

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OffersFeed>
    <total>2</total>
    <data>
        <offer>
            <code>6689387</code>
            <price>1290</price>
            <old_price>1490</old_price>
            <availability>true</availability>
            <warranty_type>manufacturer</warranty_type>
            <warranty_period>12</warranty_period>
            <max_pay_in_parts>3</max_pay_in_parts>
            <days_to_dispatch>0</days_to_dispatch>
            <delivery_methods>
                <delivery_method>
                    <method>nova-post:branch</method>
                    <price>0</price>
                </delivery_method>
            </delivery_methods>
            <checkout_constraints>
                <multiplicity>2</multiplicity>
            </checkout_constraints>
            <manufacture>
                <country_code>CZ</country_code>
                <year>2025</year>
            </manufacture>
        </offer>
    </data>
</OffersFeed>
```

## Required fields per offer

- `<code>`: unique proposition code
- `<price>`: current price
- `<availability>`: `true` or `false`

## Optional fields per offer

- `<old_price>`
- `<warranty_type>`: `manufacturer`, `merchant`, or `no`
- `<warranty_period>`: months, `999` means unlimited
- `<max_pay_in_parts>`
- `<days_to_dispatch>`: `0` today, `1` tomorrow, `>1` in X days
- `<delivery_methods>`
- `<checkout_constraints>`
- `<manufacture>`

## Delivery methods

Allowed `<method>` values from the PDF:

- `nova-post:branch`
- `nova-post:cargo_branch`
- `nova-post:postomat`
- `courier:nova-post`

Each `<delivery_method>` may also contain:

- `<price>`

## Checkout constraints

- `<multiplicity>`: sale quantity step, for example `2` means only `2, 4, 6...`

## Manufacture block

- `<country_code>`: ISO 3166-1 alpha-2
- `<year>`: production year

## Notes for the current sample source

The sample source file `xml_example/fk-inhome.com.ua.xml` already contains enough data for:

- `code`
- `price`
- `availability`

Warranty, installment, delivery, multiplicity, and manufacture fields are not present in the source feed, so the generator fills them from defaults or per-offer overrides.
