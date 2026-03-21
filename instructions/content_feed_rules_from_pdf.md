# Content Feed Rules From PDF

Source: `instructions/prices.pdf`
Document title: `Завантаження контенту | Інтеграція партнерів`

## Technical requirements

- Feed format: XML
- Feed access: public URL
- Refresh frequency: at least every 30 minutes
- If image URLs are not public, the partner should whitelist these IPs so the platform can fetch images:
  - `13.53.52.37`
  - `16.16.42.238`
  - `13.50.222.109`
  - `16.171.78.185`
  - `13.48.150.45`

## Mandatory content-level requirements

- Export only products that are in stock.
- Do not export damaged, discounted defect, or showcase items.
- Full product content is required:
  - brand
  - vendor code
  - code
  - title
  - barcode
  - category
  - full characteristics from the site
  - original gallery images
  - concise but informative description
  - package dimensions
- Category must be the leaf category and must be in Ukrainian.
- Photos should be original and as large as possible, at least `1000px`, in `JPG`, `JPEG`, or `PNG`.

## Required tags inside each `<offer>`

- `<id>`: product identifier on the partner site
- `<code>`: offer code used to match the offers/propositions feed
- `<vendor_code>`: manufacturer vendor code
- `<title>`: product title
- `<barcode>`: product barcode
- `<category>`: product category
- `<category_id>`: category id or code
- `<brand>`: product brand
- `<availability>`: should indicate an in-stock product; the PDF example uses `Є в наявності`
- `<weight>`: package weight in kilograms
- `<height>`: package height in centimeters
- `<width>`: package width in centimeters
- `<length>`: package length in centimeters
- `<description>`: HTML description, typically wrapped in `CDATA`
- `<image_link>`: gallery container
- `<image_link><picture>`: one or more image URLs
- `<tags>`: all product attributes and characteristics
- `<tags><param name="...">value</param>`: attribute name and value

## Title rules

- Title must be in Ukrainian.
- Maximum length: `100` characters.
- Recommended structure:
  `Особливість + Бренд + Модель + Інші характеристики + Колір (Вендор-код)`
- Forbidden in titles:
  - all caps
  - punctuation such as dots, commas, and dashes when they are not part of the model
  - jargon and special symbols such as `§`, `≠`, `≥`
  - words like `Акція`, `Знижка`, `Розпродаж`, `Уцінка`, `Copy`, `Original`
  - links, site names, or contact data

## Description rules

- Description should be concise and informative.
- Description should include the main characteristics, functions, and compatible models when relevant.
- Description text should be unique and free of spelling, grammar, and style errors.
- The PDF explicitly lists these tags for descriptions:
  - `<h5>`
  - `<br>`
  - `<ul>`
  - `<li>`
  - `<img alt="" src="">`
- The PDF examples also use `<p>` repeatedly, so `<p>` is part of the practical example format even though it is not listed in the short tag list.
- The description must not include:
  - payment information
  - delivery information
  - brand history
  - warranty information
  - package contents / configuration
  - contact data
  - links to third-party resources
  - advertising for unrelated products or services
  - unrelated information

## Attribute formatting

- Export all characteristics and attribute values that are present on the site.
- Boolean attributes should use `Так` or `Ні`.
- Values should include units of measure exactly as on the site when units exist, for example `Вт`, `г`, `мм`, `см`.
- For multiselect attributes, emit multiple `<param>` tags with the same `name`.

## Escaping rules

- Special characters such as `&`, `<`, `>`, and `"` should be escaped with XML entities or wrapped in `CDATA`.
- The PDF gives examples of using `CDATA` both for `<title>` and `<description>`.

## Feed structure shown in the PDF

The PDF example uses this hierarchy:

- `<Market>`
- `<offers>`
- `<offer>`
- nested product tags inside each `<offer>`

The sample structure in the PDF includes:

- `id`
- `code`
- `vendor_code`
- `title`
- `barcode`
- `category`
- `category_id`
- `brand`
- `availability`
- `weight`
- `height`
- `width`
- `length`
- `description`
- `image_link`
- `tags`

## Additional notes from the PDF

- Brand is explicitly mandatory because products without a brand cannot be linked to master cards in the system.
- Vendor code is explicitly mandatory for the same reason.
- Barcode is explicitly mandatory for additional proposition matching.
- Availability and prices are handled through the separate offers/propositions feed, even though the content feed example still contains the `availability` tag to indicate that only available products should be exported.
