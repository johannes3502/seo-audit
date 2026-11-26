# Keyword map and on-page review

## Input contract

Ask for, or create with the user:

- business goal and money pages
- country/language
- one primary keyword per owner URL
- optional secondary phrases/synonyms
- pages that must not be changed (legal, authenticated, legacy)

JSON shape accepted by `repo_scan.py --keywords`:

```json
{
  "pages": [
    {
      "url": "/",
      "primary": "project management software",
      "secondary": ["team task tracker", "project planning tool"]
    },
    {
      "url": "/pricing",
      "primary": "project management software pricing",
      "secondary": ["plans", "per-seat cost"]
    }
  ]
}
```

A simple `{"/": "primary keyword"}` map also works.

## Review per route

- [ ] The route owns one intent, not three.
- [ ] Primary phrase appears in title, H1 and opening paragraph.
- [ ] Title/H1 sound like language a customer would use.
- [ ] Secondary phrases appear naturally, not as a list.
- [ ] The page answers the query before asking for a conversion.
- [ ] The page links to related owner pages with descriptive anchors.
- [ ] No other route targets the same primary phrase.
- [ ] No keyword stuffing or mass-generated variants.

## Cannibalization

- [ ] Same primary mapped to >1 URL → decide owner.
- [ ] Two URLs swap for the same GSC query → merge/redirect/re-target.
- [ ] A blog post outranks the money page for a commercial query → link and
      consolidate, or change the post's intent.

## Content update vs new page

Create a new page only when there is a distinct intent and enough unique value.
Otherwise update the existing owner page. Ten thin pages for ten variants is a
spam risk and dilutes internal links.

## Measurement

- [ ] Record GSC baseline by page/query before the change.
- [ ] Change title/H1/copy in one batch per template, not everything at once.
- [ ] Wait for recrawl; do not judge after 24 hours.
- [ ] Compare impressions/clicks/position for the same date range length.
- [ ] Keep a change log with URL, date, old/new title, reason.
