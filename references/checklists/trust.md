# Trust and legal surface checklist

Use this when the site sells something, collects leads, runs ads, or presents a
real business. Technical SEO can be green while the trust surface is broken.

## 1. Legal identity

- [ ] Imprint/Impressum exists, loads with HTTP 200 and is linked from every
      page (usually the footer).
- [ ] Privacy policy exists and matches the actual data collection (forms,
      analytics, ads, embeds, cookies).
- [ ] Terms, cancellation/returns and withdrawal pages exist where the business
      model requires them.
- [ ] The legal pages name the same entity, address and phone as the NAP and
      `LocalBusiness` schema.
- [ ] The legal page is on the same domain and brand. A link to another domain
      is a trust finding until ownership is verified.
- [ ] The imprint is not hidden behind a client-only route, a modal that cannot
      be linked, or a PDF that is not crawlable.

## 2. Contact and entity

- [ ] A visible contact route exists with a real phone, email or form.
- [ ] The contact page and footer use the same phone/address as the imprint.
- [ ] The about page names real people/roles and verifiable credentials.
- [ ] The business registration, VAT ID or professional credentials are shown
      where they are expected.
- [ ] The site does not present a virtual office or station address as the
      registered business address without explanation.

## 3. Reviews and claims

- [ ] Reviews/testimonials are genuine, attributable and visible.
- [ ] No invented `aggregateRating`, review counts or awards.
- [ ] No review gating (only asking satisfied customers).
- [ ] Guarantees, prices and availability are true and current.
- [ ] No fake urgency, fake scarcity or misleading "best" claims.

## 4. Security and privacy

- [ ] HTTPS everywhere; no mixed content.
- [ ] Cookie consent covers analytics, ads and third-party embeds where
      required.
- [ ] Forms state what happens with the data and link to the privacy policy.
- [ ] Third-party embeds (maps, chat, video, fonts) are disclosed and do not
      leak data before consent where required.
- [ ] Security headers are present (HSTS, CSP, nosniff, Referrer-Policy,
      Permissions-Policy); their absence is a security/trust finding, not a
      ranking factor.

## 5. Structured data vs. visible content

- [ ] `LocalBusiness`/`Organization` NAP matches the visible page and the
      imprint.
- [ ] `openingHoursSpecification` matches the real hours.
- [ ] `aggregateRating`/`review` matches visible, genuine reviews.
- [ ] `FAQPage` contains visible questions and answers.
- [ ] `Event` data matches a real, public, single-event page.
- [ ] Prices and availability in schema match the page.

## 6. Cross-domain and multi-brand

- [ ] A legal link to another domain is intentional, owned by the same entity
      and explained to the user.
- [ ] A shared checkout, booking or account domain does not hide the legal
      entity.
- [ ] The footer does not link to a different brand's imprint as the only legal
      notice.
- [ ] Canonical, sitemap and hreflang do not mix unrelated brands.

## 7. Evidence and report

- [ ] Each finding has the exact URL, the element/link, and a rule ID
      (`legal-link-cross-domain`, `localbusiness-*`, `noindex`, `security-headers`).
- [ ] Separate what was verified live from what needs a manual legal check.
- [ ] Do not give legal advice. State the observed mismatch and ask the owner
      to confirm the entity.

Trust findings are often conversion and legal risks, not classic ranking
factors. Report them with that framing.
