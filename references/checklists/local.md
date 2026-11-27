# Local business and entity checklist

Use this for a local service business, a multi-location business, a store,
restaurant, rental or any site where the Local Pack and Google Business Profile
(GBP) can matter more than a homepage H1.

## 1. Business context

- [ ] What is sold, where, and to whom? Local, regional, national or online-only?
- [ ] What are the money pages (service, location, product, booking)?
- [ ] How many real locations? Is there a service area without a storefront?
- [ ] Is there a GBP? Is it claimed and verified?
- [ ] What is the legal entity and registered address? It may differ from an
      operating location; record both.
- [ ] Which languages and countries are actually served?

## 2. NAP and entity consistency

NAP = name, address, phone. Check the same values on:

- [ ] visible header/footer/contact block
- [ ] contact and location pages
- [ ] imprint/Impressum and privacy pages
- [ ] `LocalBusiness` JSON-LD
- [ ] Google Business Profile
- [ ] the main directory citations

Red flags:

- [ ] Schema address is a station, coworking space or virtual office while the
      imprint uses a different city or entity.
- [ ] The phone is missing from the schema or from the visible page.
- [ ] Opening hours claim 24/7 for locations that keep other hours.
- [ ] The legal page links to another domain or another brand with no
      explanation.
- [ ] The visible NAP block does not exist; the address only lives in JSON-LD.

## 3. LocalBusiness schema

- [ ] Correct type: `LocalBusiness` or a specific subtype (`Store`,
      `Restaurant`, `ProfessionalService`, …).
- [ ] `name`, `address` (`PostalAddress`), `telephone`, `url`.
- [ ] `openingHoursSpecification` per location, not one generic claim for all.
- [ ] `geo` (latitude/longitude) when it matches the real location.
- [ ] `areaServed` for a service-area business.
- [ ] `sameAs` links to the GBP and verified profiles; do not invent profiles.
- [ ] `priceRange` only when it is true.
- [ ] No fake `aggregateRating` or `review`; reviews must be genuine and
      visible.
- [ ] Schema matches the visible page and the legal entity.

## 4. Google Business Profile and citations

This data is not in the HTML. Mark it as manual/not checked unless the user
provides access.

- [ ] Claimed and verified.
- [ ] Primary and secondary categories are correct.
- [ ] Services/products and attributes are complete.
- [ ] Hours, holiday hours and special hours are current.
- [ ] Photos and videos are recent and geolocated where appropriate.
- [ ] Posts, Q&A and messages are monitored.
- [ ] Reviews are genuine, responded to, and not gated.
- [ ] The website link and UTM parameters point to the right landing page.
- [ ] Name, address and phone match the site and the main citations.
- [ ] Duplicate or old listings are closed or merged.

## 5. Location and service pages

- [ ] Each location has a crawlable URL with unique content: address, hours,
      phone, directions, staff, services, parking/transport, local proof.
- [ ] Service-area pages are not doorway pages with only the city swapped.
- [ ] Location pages are linked from the footer, contact page and relevant
      service pages.
- [ ] Each page has a self-referencing canonical and is in the sitemap.
- [ ] LocalBusiness/Place schema is per location, not a copy of the same NAP.
- [ ] Embedded maps are privacy-friendly and do not block the main content.

## 6. Reviews, content and trust

- [ ] Reviews/testimonials are real, attributable and not edited into fake
      ratings.
- [ ] No review gating (only asking happy customers).
- [ ] Local partnerships, sponsorships, events and case studies are real.
- [ ] Credentials, certifications and guarantees are verifiable.
- [ ] Prices and availability are clear; no fake urgency.

## 7. Events

For event rich results, Google expects a **dedicated leaf page for one event**,
not a multi-event list on a homepage.

- [ ] One event per URL.
- [ ] `name`, `startDate`, `location` (`Place` with name/address or
      `VirtualLocation`).
- [ ] `endDate`, `eventStatus`, `image`, `description`, `offers`, `performer`
      and `organizer` when true.
- [ ] The organizer is the real organizer, not the site brand for third-party
      events.
- [ ] The event is public and bookable/attendance is possible.
- [ ] Expired events are removed or marked cancelled/postponed.
- [ ] The visible event list and the JSON-LD list match.

If the markup cannot meet these rules, remove the Event markup. Refreshing the
dates alone does not make an ineligible list page eligible.

## 8. Evidence and report

- [ ] NAP source: page URL, schema file/JSON-LD, legal page, GBP (manual).
- [ ] Each finding has a URL and a rule ID (`localbusiness-*`, `event-*`,
      `legal-link-cross-domain`).
- [ ] GBP/citation checks are labeled `manual` or `not checked`; do not infer
      them from the website.
- [ ] The report states what was not checked.

Do not invent GBP categories, review counts, rankings or search volume.
