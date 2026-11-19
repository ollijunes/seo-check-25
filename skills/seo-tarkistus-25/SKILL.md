---
name: seo-tarkistus-25
description: Tekninen ja sisällöllinen SEO-tarkistus mille tahansa sivustolle 25 kohdan listalla - SSR, sitemap, Search Console, robots.txt ja AI-botit, noindex, ohjausketjut, 404:t, canonical, meta description, yksi h1, UKK-sisältö, murupolut, orposivut, alt-tekstit, kuvaformaatit, CLS/INP/LCP, konemainen teksti, kirjoittaja, backlinkit, spam-käytännöt, snippet-kontrollit, main content, Bing. Käytä, kun pyydetään SEO-läpikäyntiä, SEO-tarkistusta sivustolle tai buildille tai kun sivuston kunto pitää todeta ennen julkaisua.
---

# SEO-tarkistus: 25 kohtaa

Käy jokainen kohta läpi järjestyksessä. Raportoi jokaisesta tila, todiste (komento, URL tai tiedosto ja rivi) ja korjaus.

Tilat: **OK / KORJATTAVA / TARKISTA / EI SOVELLU / EI TARKISTETTU**. Älä merkitse kohtaa OK:ksi ilman todistetta. EI TARKISTETTU on rehellinen vastaus, kunhan kerrot syyn.

Kohdat 1–20 ovat perustarkistus. Kohdat 21–25 koskevat spam-käytäntöjä ja sitä, miten hakukoneet ja tekoälyominaisuudet käyttävät sivua. Kohdat 9, 10 ja 14 ovat hygieniaa: raportoi ne, mutta älä nosta niitä yhteenvedon kärkeen. Kärkeen kuuluvat indeksoitavuus, sisällön laatu ja spam-käytännöt.

## Rajat (lue ensin)

- **Tarkistus on lukemista.** Tuotannon robots.txt:tä, noindexiä, ohjauksia, palvelinasetuksia, DNS:ää tai julkaisuja ei muuteta tarkistuksen sivuvaikutuksena. Korjaukset tehdään haaraan ja pull requestiin. Julkaisuun tarvitaan omistajan lupa.
- **Salasanan takana oleva esikatselu on tarkoituksella noindex.** Jos sivusto on ennen julkaisua basic authin takana, tarkista indeksoitavuus buildin tiedostoista (`dist/robots.txt`, HTML:n robots-meta), älä live-otsakkeista. Kirjaa tämä raporttiin.
- **Search Consoleen ja Bingiin lähettäminen sekä backlinkkien pyytäminen ovat omistajan toimia.** Valmistele ne (sitemapin osoite, lista, viestiluonnokset). Älä lähetä äläkä ota yhteyttä ulkopuolisiin.
- **Kuormitus:** enintään kaksi rinnakkaista pyyntöä tuotantoon. Käytä build-kansiota aina, kun se on saatavilla.
- Lue repon oma `AGENTS.md` tai `CLAUDE.md` ja noudata sitä.

## Aloitus

1. Domain, repo ja build-komento (Astro: `npm run build` kirjoittaa kansioon `dist/`).
2. Sivulista: `dist/sitemap*.xml` tai `find dist -name index.html`.
3. Jos `seo-check` on asennettu, aja se ensin buildille. Se vastaa niihin kohtiin, joihin kone pystyy, ja listaa loput:
   ```sh
   seo-check dist --site https://example.com
   ```
   Sen tilat ovat englanniksi: FIX on KORJATTAVA, REVIEW on TARKISTA, N/A on EI SOVELLU ja NOT CHECKED on EI TARKISTETTU.
4. Pääsy Search Consoleen, Bing Webmaster Toolsiin ja backlink-indeksiin, jos omistaja on sen antanut.

## Julkaistun sivun tarkistus

Voit tarkistaa yhden julkisen sivun [Firecrawl Localilla](https://crates.io/crates/firecrawl-local)
ja [SEOmatorilla](https://github.com/seo-skills/seo-audit-skill). Komennot on testattu
Firecrawl Localin versiolla 0.1.1 ja SEOmatorin versiolla 8.0.1. Aja ne peräkkäin
tyhjässä työhakemistossa.

```sh
page=https://example.com/
FIRECRAWL_CLOUD=off firecrawl-local scrape --public-only --browser never \
  --format markdown "$page" > page.json
seomator audit "$page" --categories core,images,content,schema,htmlval \
  --concurrency 1 --no-cwv --no-save --fail-under 0 --format json > audit.json
seo-check-evidence "$page" --firecrawl page.json --seomator audit.json
```

Firecrawl poimii sivun tekstin. SEOmator hakee sivun, robots.txt-tiedoston ja saatavilla
olevat sivukartat. Yhdistetty JSON kertoo lähdeosoitteen, HTTP-tilakoodin, poimitun
tekstin pituuden ja sääntöjen tulokset ryhmittäin. Voit antaa komennolle myös vain
toisen raportin. Yksittäisten sääntöjen tunnisteet ja sivulta poimittu teksti löytyvät
alkuperäisistä raporteista. Kirjaa havainto sen sivun ja tarkistuskohdan yhteyteen,
jota se koskee. Sivuston laajuiset tarkistukset, Search Console ja oikeiden käyttäjien
latausajat tarvitsevat omat aineistonsa.

## Kohdat

| # | Kohta | Miten tarkistetaan | Hyväksytty |
|---|---|---|---|
| 1 | Renderöinti palvelimella | `curl -s URL \| grep -c '<h1'`. Teksti ja linkit ovat HTML:ssä ilman JavaScriptiä, myös hinnat, UKK-vastaukset, välilehdet ja avattavat osiot. Googlebot lukee HTML-, CSS- ja JS-tiedostosta ensimmäiset 2 Mt (purettuna): `curl -s URL \| wc -c` ja bundlejen koot; tärkein sisältö alkuun. JavaScript-säännöt: noindex ei tule JS:llä, canonical ei muutu JS:llä, robots-meta on `<head>`-osassa. Oleta, että AI-botit eivät suorita JavaScriptiä. | Pääsisältö, h1, linkit ja metatiedot ovat raakatekstinä HTML:ssä; tiedostot alle 2 Mt |
| 2 | Sitemap | `curl -sI /sitemap.xml`. Vertaa URL-listaa sivulistaan. Ei noindex-, ohjaus- tai 404-osoitteita. | Kaikki kanoniset 200-sivut mukana, `lastmod` järkevä |
| 3 | Sitemap Search Consoleen | Search Console tai omistajan vahvistus. Domain-omaisuus vahvistettu. Lue sivujen indeksoinnin tilat (nimet englanninkielisestä käyttöliittymästä): "Crawled, currently not indexed", "Discovered, currently not indexed", "Soft 404", "Duplicate without user-selected canonical". | Sitemap lähetetty ja tila onnistunut; ongelmatilat selitetty. Muuten: kirjoita omistajalle ohje |
| 4 | Googlebot pääsee sisään | `curl -s /robots.txt`. Ei riviä `Disallow: /` Googlebotille. `Sitemap:`-rivi löytyy. Googlebotin esto poistaa sivun myös Googlen tekoälyominaisuuksista. `Google-Extended` ohjaa vain Geminin koulutus- ja grounding-käyttöä eikä vaikuta hakuun. AI-botit: kohta 22. | Googlebot pääsee kaikkiin julkisiin polkuihin; CSS ja JS sallittu |
| 5 | Turhat noindexit pois | `grep -rl 'noindex' dist`; `curl -sI` ei näytä otsaketta `X-Robots-Tag: noindex` julkisilla sivuilla. | noindex vain tarkoituksella (404, kiitossivu, hakutulokset) |
| 6 | Ohjausketjut pois | `curl -sIL -o /dev/null -w '%{num_redirects} %{url_effective}'` vanhoille osoitteille sekä www- ja http-muodoille. | Enintään yksi hyppy, 301, suoraan lopulliseen osoitteeseen |
| 7 | 404:t kuntoon | Sisäiset linkit: kerää buildin `href`-arvot ja tarkista, että kohde on olemassa. Backlink-indeksi: rikkinäiset ulkoa tulevat linkit. | Ei sisäisiä 404:iä; arvokkaat vanhat osoitteet ohjataan 301:llä |
| 8 | Canonical joka sivulle | Yksi `<link rel="canonical">` sivua kohti: absoluuttinen, https, oikea domain, sivun oma osoite, loppukauttaviiva samalla tavalla kaikkialla. | Yksi sivua kohti ja osoittaa itseensä (paitsi tarkoituksella) |
| 9 | Meta description joka sivulle | Kerää `meta[name=description]`: puuttuvat ja kaksoiskappaleet. | Jokaisella oma, noin 120–160 merkkiä |
| 10 | Yksi h1 sivua kohti | `grep -o '<h1' tiedosto \| wc -l` sivuittain. | Täsmälleen yksi |
| 11 | UKK-sisältö (FAQ-merkintä valinnainen) | Google lopetti FAQ-rikastulosten näyttämisen 7.5.2026. `FAQPage` on yhä kelvollinen schema.org-tyyppi. Tarkista, että kysymykset ja vastaukset ovat näkyvää tekstiä eivätkä JavaScriptin takana ja että mahdollinen `FAQPage`-merkintä vastaa niitä; validoi JSON. Älä lisää uutta FAQPage-merkintää rikastuloksen toivossa. Älä poista toimivaa. | Näkyvä UKK-teksti; mahdollinen merkintä on kelvollinen ja vastaa tekstiä |
| 12 | Murupolut | Näkyvä murupolku ja `BreadcrumbList`-JSON-LD ensimmäistä tasoa syvemmillä sivuilla. | Kaikilla toisen tason ja sitä syvemmillä sivuilla |
| 13 | Orposivut linkitetään | Sitemapin osoitteet, joihin ei osoita yksikään sisäinen linkki. | Ei orpoja; tavoite kaksi sisäistä linkkiä joka sivulle |
| 14 | Alt-teksti joka kuvaan | `<img>` ilman `alt`-attribuuttia tai sisältökuva, jonka `alt` on tyhjä. | Kuvaava alt sisältökuvissa, koristekuvissa `alt=""` |
| 15 | Kuvat WebP-muotoon | Buildin kuvatiedostojen tyypit ja koot; listaa yli 300 kt:n kuvat. | Sisältökuvat WebP- tai AVIF-muodossa, `width` ja `height` mukana, näkymän alapuolella lazy-lataus |
| 16 | Asettelun siirtymät pois | Kenttädata ensin: CrUX, PageSpeed Insights tai Search Consolen Core Web Vitals, 75. persentiili. Laboratoriotyökalut syyn etsimiseen. Fonteille `font-display`, kuville mitat. Lisäksi INP: raskaat tapahtumankäsittelijät ja kolmannen osapuolen skriptit. | CLS ≤ 0,1 ja INP ≤ 200 ms kenttädatan p75:ssä |
| 17 | Nopea lataus | LCP kenttädatasta; TTFB komennolla `curl -w '%{time_starttransfer}'`. Core Web Vitals on osa sivukokemusta, ei yksinään vahva sijoitustekijä. Älä lupaa sijoitusnousua. | LCP ≤ 2,5 s kenttädatan p75:ssä |
| 18 | Konemainen teksti pois | Lue sisältösivut. Aja kielen tyylitarkistin, jos sellainen on. Ihminen tarkistaa kaiken generoidun ennen julkaisua, myös otsikot, meta descriptionit, JSON-LD:n ja alt-tekstit. Pyydä todiste tarkistuksesta, älä pistemäärää. Katso kohta 24. | Ei keksittyjä faktoja; generoitu teksti ja metatiedot ihmisen tarkistamia |
| 19 | Oikea kirjoittaja | Kirjoittajasivu: nimi, tausta, kuva ja yhteystieto; `Person`-merkintä; artikkeleissa kirjoittajan nimi ja linkki sivulle. | Oikea henkilö ja tarkistettavat tiedot. Ei mitään keksittyä |
| 20 | Laadukkaat backlinkit | Backlink-indeksi: viittaavat domainit, kilpailijoiden linkit, linkittämättömät brändimaininnat. | Lista kymmenestä realistisesta kohteesta perusteluineen. Ei ostettuja linkkejä |
| 21 | Spam-käytännöt | Lue Googlen spam-käytännöt ja tarkista jokainen: (a) scaled content abuse: syötteestä tai mallipohjasta massatuotetut sivut ilman lisäarvoa; (b) expired domain abuse; (c) doorway-sivut: aluesivut, joissa vain paikkakunta vaihtuu; (d) cloaking: `curl -A Googlebot` ja selain saavat saman sisällön; (e) harhaanjohtavat ohjaukset; (f) takaisin-painikkeen kaappaus: `grep -rE 'history\.(push\|replace)State' dist` ja sivun latauksessa tehtävät historian muutokset; (g) site reputation abuse: kolmannen osapuolen sisältö alikansiossa ilman toimituksen valvontaa; (h) ostetut linkit, avainsanatäyttö, scraping; (i) arvostelut: ei kannustinarvosteluja ilman ilmoitusta. | Ei osumia. Jokainen osuma on estävä havainto |
| 22 | AI-bottien pääsy | robots.txt sekä palomuuri tai CDN. Raportoi taulukkona. **Hakubotit, salli jos tavoite on näkyvyys:** `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`, `Googlebot`, `Bingbot`. **Koulutusbotit, liiketoimintapäätös, kirjaa se:** `GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`, `CCBot`. **Käyttäjän käynnistämät haut** (`ChatGPT-User`, `Claude-User`, `Perplexity-User`) eivät välttämättä noudata robots.txt:tä; hallitse niitä palomuurilla. Tila kullekin: sallittu, estetty, ei mainittu. Tarkista, ettei CDN:n "block AI bots" -kytkin tai hallittu robots.txt ole päällä vahingossa. Kokeile todellista pääsyä: `curl -s -o /dev/null -w '%{http_code}' -A "OAI-SearchBot" URL` ja vertaa selaimeen: ei 403:a eikä JavaScript-haastetta. Tarkista user agent -nimet kunkin toimittajan ajantasaisesta dokumentaatiosta joka kerta. | Hakubotit saavat 200 ja saman sisällön; koulutusbottien tila on jonkun tekemä päätös |
| 23 | Snippet-kontrollit | `grep -rEo 'nosnippet\|data-nosnippet\|max-snippet[^"]*\|max-image-preview[^"]*\|noarchive\|unavailable_after' dist` ja `X-Robots-Tag`-otsakkeet. `nosnippet` ja `max-snippet:0` rajoittavat myös sitä, miten Googlen tekoälyominaisuudet voivat käyttää sivua. | Ei vahingossa jäänyttä nosnippet- tai max-snippet:0-ehtoa julkisilla sivuilla |
| 24 | Main content | Lue rahasivut ja avainartikkelit neljällä akselilla. **Vaiva:** näkyykö ihmisen työ, vai onko sivu koottu syötteestä tai generoitu valvomatta? Lähdeviite ei korvaa omaa työtä. **Omaperäisyys:** onko sivulla jotain, mitä kärkituloksissa ei jo ole: omaa dataa, kokemusta, laskuri, valokuva? **Taito:** selkeä kirjoitus ja toimivat työkalut. **Tarkkuus:** luvut ja väitteet on tarkistettu, etenkin raha-, laki- ja terveysaiheissa. Välilehdet, avattavat osiot ja käyttäjien kommentit lasketaan pääsisällöksi, joten niiden pitää olla raaka-HTML:ssä (kohta 1). | Jokaisesta avainsivusta perusteltu arvio neljällä akselilla todisteineen; heikot korjauslistalle |
| 25 | Bing-indeksi | Bing Webmaster Tools: sivusto vahvistettu, sitemap lähetetty, IndexNow käytössä, sivut indeksissä. Copilot siteeraa Bingin indeksistä. Vahvistus ja lähetys ovat omistajan toimia: kirjoita ohje. | Vahvistettu ja lähetetty. Muuten: ohje omistajalle |

## Raportti

Kirjoita raportti repoon (esimerkiksi `docs/seo/seo-tarkistus-VVVV-KK-PP.md`) tai tehtävässä annettuun polkuun, jos repoon ei saa kirjoittaa.

1. Yhteenveto: kolmesta viiteen tärkeintä korjausta vaikutusjärjestyksessä.
2. Taulukko 25 kohdasta: tila, todiste, korjaus ja työmäärä (S/M/L).
3. Estävät havainnot erikseen muista: indeksoinnin estävät viat, rikkinäiset ohjaukset, spam-käytäntöjen osumat ja estetyt hakubotit.
4. Mitä ei tarkistettu ja miksi.
5. Jos liikenne on heilunut: vertaa päivämääriä Googlen Search Status Dashboardiin ja kutsu osumaa **hypoteesiksi**, älä syyksi, varsinkin kun päivitysikkunat menevät päällekkäin.

Kun korjaat: haara, yksi kohta tai looginen nippu commitia kohti, build ja testit, pull request. Ei julkaisua ilman omistajan lupaa.

## Lähteet ja varmuus

Tarkistettu hakukoneiden ja bottitoimittajien omilta sivuilta 19.11.2026. Hakukoneet muuttavat dokumentaatiotaan, joten tarkista väite alkuperäisestä lähteestä ennen kuin toistat sen asiakasraportissa.

**Googlen omasta dokumentaatiosta ja blogista:** Googlebot lukee jokaisesta HTML-, CSS- ja JS-tiedostosta ensimmäiset 2 Mt purettuna ja HTTP-otsakkeet mukaan lukien, PDF-tiedostosta 64 Mt (Googlebotin dokumentaatio ja Search Centralin blogi, maaliskuu 2026). FAQ-rikastulokset päättyivät 7.5.2026, ja Google on poistanut niiden dokumentaation (Search Centralin muutosloki). Search Centralin AI-optimointiopas (toukokuu 2026) sanoo, että Googlen tekoälyominaisuudet käyttävät samoja sijoitus- ja laatujärjestelmiä kuin haku eikä niitä varten tarvita erikoistiedostoja, merkintöjä tai tekstin pilkkomista, ja ohjaa Search Consolen Generative AI performance -raporttiin. Takaisin-painikkeen kaappaus mainitaan spam-käytännöissä. AI features -dokumentaation mukaan snippet-kontrollit ja Googlebotin pääsy ohjaavat käyttöä tekoälyominaisuuksissa. Core Web Vitalsin rajat: LCP 2,5 s, INP 200 ms, CLS 0,1.

**Toimittajien crawler-dokumentaatiosta:** OpenAI, Anthropic ja Perplexity ajavat eri botteja hakuun, koulutukseen ja käyttäjän käynnistämiin hakuihin. Kohdan 22 nimet tarkistettiin 19.11.2026.

**Minkään hakukoneen vahvistamatonta, älä käytä perusteena:** prosenttiluvut siitä, kuinka usein tekoälyvastaukset siteeraavat tietynlaista sivua, tuoreuskertoimet, väitteet yksittäisen Core Web Vital -mittarin noususta sijoitustekijäksi tiettynä päivänä ja väite, että ChatGPT Search toimisi Bingin indeksin varassa.

**Ei tässä tarkistuksessa:** hreflang, paikallinen SEO ja yritysprofiilit, migraatiot, evästesuostumus ja mittaus, kuva- ja videohaku sekä linkkiprofiilin laatu.
