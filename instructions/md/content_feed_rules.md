# Content Feed Rules

Source: `instructions/prices.pdf`

## Technical requirements

- Feed format: XML
- Feed access: public URL
- Refresh frequency: at least every 30 minutes
- Only in-stock products should be included
- Damaged, discounted defect, or showcase items must be excluded

## Required product data

Each `<offer>` must contain:

- `<id>`: product identifier on the source site
- `<code>`: offer code used to match the offer/proposition feed
- `<vendor_code>`: manufacturer vendor code
- `<title>`: Ukrainian product title, up to 100 characters
- `<barcode>`: product barcode
- `<category>`: leaf category, in Ukrainian
- `<category_id>`: category code or id
- `<brand>`: brand name
- `<availability>`: only available products should be exported
- `<weight>`: package weight in kg
- `<height>`, `<width>`, `<length>`: package dimensions in cm
- `<description>`: HTML wrapped in `CDATA`
- `<image_link>` with one or more `<picture>` entries
- `<tags>` with one or more `<param name="...">value</param>` entries

## Title rules

- Ukrainian language only
- Max length: 100 characters
- Recommended structure:
  `Тип товару + Бренд + Модель + Інші характеристики + Колір + (Вендор-код)`
- Do not use all caps, promo words, contact data, links, or irrelevant punctuation

## Description rules

- Must be short, structured, unique, and relevant to the product
- Allowed markup in description:
  - `<h5>`
  - `<br>`
  - `<p>`
  - `<ul>`
  - `<li>`
  - `<img alt="" src="...">`
- Description must not include payment, delivery, warranty history, contacts, or unrelated advertising

## Feed structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Market>
    <offers>
        <offer>
            <id>752247</id>
            <code>3792142</code>
            <vendor_code>21N50012RA2</vendor_code>
            <title>Смартфон ZTE Blade L9 1/32GB Dual Sim Gray</title>
            <barcode>69021760617522</barcode>
            <category>smartphones</category>
            <category_id>35</category_id>
            <brand>ZTE</brand>
            <availability>Є в наявності</availability>
            <weight>2.75</weight>
            <height>5</height>
            <width>14.5</width>
            <length>7.5</length>
            <description><![CDATA[
                <h5>Game Assistant 4.0</h5>
                <br>
                <p>...</p>
            ]]></description>
            <image_link>
                <picture>https://example.com/image-1.jpg</picture>
            </image_link>
            <tags>
                <param name="Bluetooth">Bluetooth 4.2</param>
            </tags>
        </offer>
    </offers>
</Market>
```

## Notes for the current sample source

The sample source file `xml_example/fk-inhome.com.ua.xml` does not contain all fields required by this spec.
Missing or partially missing fields include:

- barcode
- image gallery URLs
- package weight
- package dimensions

The generator therefore supports per-offer overrides for these fields.
