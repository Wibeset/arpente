# Travailler sur le site d’Arpente

Du HTML statique, une feuille de style et un petit script, publiés par GitHub Pages. Le design est celui de
Reliure (`../reliure`) : fond encre `#0a0a0b`, titres en Headland One (`assets/fonts/`), texte en Helvetica, et
l’accueil en deux colonnes, le texte à gauche et un grand iPhone à droite. Le vert forêt d’Arpente, éclairci
(`#8cc4a0`), sert d’accent : trait de surligneur du titre, halo derrière le téléphone, anneaux de focus.

## Pages

Trois langues : anglais (par défaut, `x-default`), français (`/fr/`) et espagnol (`/es/`). L’app, elle, n’existe
qu’en anglais et en français : les pages espagnoles le disent, et le JSON-LD de l’app sur `/es/` déclare `["en", "fr"]`.

| English | Français | Español |
| --- | --- | --- |
| `/` | `/fr/` | `/es/` |
| `/support/` | `/fr/assistance/` | `/es/soporte/` |
| `/privacy/` | `/fr/confidentialite/` | `/es/privacidad/` |
| `/strava-alternative/` | `/fr/alternative-strava/` | `/es/alternativa-strava/` |
| `/alltrails-alternative/` | `/fr/alternative-alltrails/` | `/es/alternativa-alltrails/` |
| `/komoot-alternative/` | `/fr/alternative-komoot/` | `/es/alternativa-komoot/` |
| `/gaia-gps-alternative/` | `/fr/alternative-gaia-gps/` | `/es/alternativa-gaia-gps/` |
| `/wikiloc-alternative/` | `/fr/alternative-wikiloc/` | `/es/alternativa-wikiloc/` |
| `/outdooractive-alternative/` | `/fr/alternative-outdooractive/` | `/es/alternativa-outdooractive/` |
| `/map-my-walk-alternative/` | `/fr/alternative-map-my-walk/` | `/es/alternativa-map-my-walk/` |
| `/relive-alternative/` | `/fr/alternative-relive/` | `/es/alternativa-relive/` |
| `/polarsteps-alternative/` | `/fr/alternative-polarsteps/` | `/es/alternativa-polarsteps/` |
| `/pacer-alternative/` | `/fr/alternative-pacer/` | `/es/alternativa-pacer/` |
| `/walking-journal/` | `/fr/journal-de-marche/` | `/es/diario-de-caminatas/` |
| `/private-hiking-tracker/` | `/fr/suivi-randonnee-sans-compte/` | `/es/seguimiento-senderismo-sin-cuenta/` |
| `/gpx-export/` | `/fr/export-gpx/` | `/es/exportar-gpx/` |
| `/free-walking-app/` | `/fr/application-marche-gratuite/` | `/es/app-caminar-gratis/` |
| `/quebec-hikes/` (+ `mont-albert/`, `acropole-des-draveurs/`, `sentier-de-la-statue/`) | `/fr/randonnees-quebec/` (mêmes fiches) | `/es/rutas-quebec/` (mêmes fiches) |
| `/montreal-walks/` (+ `lachine-canal/`, `mount-royal/`) | `/fr/marches-montreal/` (+ `canal-de-lachine/`, `mont-royal/`) | `/es/paseos-montreal/` (+ `canal-de-lachine/`, `mont-royal/`) |

Chaque page déclare ses trois équivalents (`hreflang`) et le pied de page mène aux deux autres langues. Les liens
sont relatifs ; seule `404.html` garde des liens depuis la racine. Le français est tutoyé (espaces insécables avant
`? ! : ;`), l’espagnol aussi (« tú »). Arpente est « une app » : on l’accorde au féminin.

Les guides (SEO) suivent le gabarit `.legal` de Reliure. Les fiches de randonnée ont une photo, les faits clés
(chiffres des parcs : Sépaq, Parcs Canada, Ville de Montréal), une carte et un profil d’altitude
(`assets/hikes/<id>/map.svg` et `profile.svg`) et une galerie. Le tracé des cartes est indicatif : calculé avec
BRouter sur les données OpenStreetMap (© contributeurs OpenStreetMap, ODbL), altitudes SRTM. Les photos viennent de
Wikimedia Commons, sous licence libre, avec le crédit sous chacune : garder ces crédits. Les comparatifs datent de
novembre 2026 : à revoir.

## Au quotidien

- **Styles** : modifier `assets/style.css`, puis `scripts/build-css.sh` pour produire `style.min.css`,
  que les pages chargent.
- **Alternatives** : les dix pages « meilleures alternatives à … » (Arpente en tête du classement, puis un tableau
  comparatif) ne s’éditent pas à la main. Le texte est dans `scripts/alternatives/{en,fr,es}.py` ; lancer
  `python3 scripts/make-alternatives.py` pour réécrire les 30 pages et leurs entrées dans `sitemap.xml` et `llms.txt`.
  Pas de prix précis pour les autres apps (ils changent selon le pays) : seulement le modèle (gratuite, abonnement…).
- **Script** : `assets/main.js` (le même que Reliure) affiche dans le téléphone l’écran de la section en cours de lecture
  (`data-screen`) et ajoute les points de navigation ; sans JavaScript, le premier écran reste affiché.
- **Images** : `python3 scripts/make-images.py` dessine l’icône et les favicons, les images Open Graph, les cinq
  écrans de la rangée et les deux cartes de la section « 2 km ou 18 km » (`icons`, `og`, `screens` ou `walks` pour
  n’en refaire qu’une partie). Il lui faut Google Chrome et `cwebp`.
- **Prévisualiser** : ouvrir `index.html`, ou `python3 -m http.server` à la racine puis http://localhost:8000.
- **Publier** : un push sur `main` déploie avec `.github/workflows/pages.yml`.

## Avant le lancement

- **Captures** : l’app n’existe pas encore (`../arpente-ios` est vide). Les écrans de la rangée sont des maquettes
  dessinées par `make-images.py`. Quand l’app tournera, les remplacer par de vraies captures du simulateur, comme
  `../porcom/scripts/capture-screens.sh`, et faire de même pour l’icône (`assets/icon.svg` est une proposition).
- **Fonctionnalités** : le texte suppose l’enregistrement GPS, Apple Plans pour les cartes, les notes et photos,
  la synchro iCloud et l’export GPX. Ajuster les pages, le JSON-LD, `llms.txt` et la politique de confidentialité
  si l’app diffère.
- **Domaine** : `CNAME` pointe vers `arpente.app`. À confirmer, et à remplacer partout si c’est un autre domaine.
- **App Store** : à la sortie, transformer « Coming soon to the App Store » / « Bientôt sur l’App Store » (en-tête,
  titre, appel à l’action) en lien vers l’App Store, régénérer le QR code (il mène à arpente.app pour l’instant)
  et ajouter `apple-itunes-app` et `installUrl` dans le JSON-LD.
