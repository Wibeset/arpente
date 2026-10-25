# Travailler sur le site d’Arpente

Du HTML statique, une feuille de style et un petit script, publiés par GitHub Pages. La structure et le design
reprennent ceux de Porcom (`../porcom`) et de Reliure (`../reliure`), mais en mode clair seulement, aux couleurs
de l’app : vert forêt `#2d5a3d`, crème `#f4efe4` et noir charbon `#1e211f`.

## Pages

| English | Français |
| --- | --- |
| `/` | `/fr/` |
| `/support/` | `/fr/assistance/` |
| `/privacy/` | `/fr/confidentialite/` |

L’anglais est la langue par défaut (`x-default`). Chaque page déclare son équivalent (`hreflang`) et
le lien de langue mène à la même page dans l’autre langue. Les liens sont relatifs
(`../assets/…`), donc les pages s’ouvrent aussi bien depuis le disque que servies d’un sous-dossier ;
seule `404.html` garde des liens depuis la racine, puisque GitHub Pages la sert à n’importe quelle adresse. Le français est tutoyé, comme
l’app, avec des espaces insécables avant `? ! : ;` et dans les « guillemets ». Arpente est « une app » : on l’accorde au féminin.

## Au quotidien

- **Styles** : modifier `assets/style.css`, puis `scripts/build-css.sh` pour produire `style.min.css`,
  que les pages chargent.
- **Script** : `assets/main.js` fait apparaître les sections au défilement ; sans JavaScript, tout reste visible.
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
