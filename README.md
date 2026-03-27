# IPTV Afrika — Premium Streaming Landing Pages

Landing pages pour **IPTV Afrika**, service de streaming TV avec 22,000+ chaînes et 120,000+ films en Afrique.

3 designs distinctifs. Pure HTML/CSS/JS. Aucun build tool requis.

---

## Aperçu des 3 Designs

### V1 — Minimalist Cinema (`templates/index.html`)

| | |
|---|---|
| **Font** | Inter (mono-famille) |
| **Style** | Noir profond, espace négatif extrême, boutons sharp |
| **Accent** | Orange africain `#E67E22` |
| **Ambiance** | Apple TV / Netflix — sobre, cinématique |

### V2 — Maximalist Luxury (`templates/index-v2.html`)

| | |
|---|---|
| **Fonts** | Cormorant (serif) + Montserrat (sans) |
| **Style** | Or africain, textures grain, séparateurs ornementaux |
| **Accents** | Gold `#D4A574` + Orange `#E67E22` |
| **Ambiance** | Rolls Royce — opulent, décoratif, layered |

### V3 — Kinetic Brutalist (`templates/index-v3.html`)

| | |
|---|---|
| **Fonts** | Space Grotesk (display) + Inter (body) |
| **Style** | Zéro border-radius, bordures épaisses, TOUT en majuscules |
| **Accent** | Orange `#E67E22` sur noir `#09090B` |
| **Ambiance** | Zine underground — brut, agressif, marquee infini |

---

## Structure du Projet

```
IPTV-Afrika-New/
├── templates/
│   ├── index.html          # V1 — Minimalist Cinema
│   ├── index-v2.html       # V2 — Maximalist Luxury
│   ├── index-v3.html       # V3 — Kinetic Brutalist
│   └── channel-list.html   # Page catalogue chaînes
├── statics/
│   ├── css/style.css       # Styles partagés
│   ├── js/script.js        # Animations & interactions
│   └── img/                # 122 images + 1 vidéo hero (9.5 MB)
├── CONTENT.md              # Documentation complète du contenu
└── README.md               # Ce fichier
```

## Sections (communes aux 3 versions)

- **Navigation** — Header flottant glassmorphique (sticky)
- **Hero** — Vidéo plein écran avec overlay
- **Stats** — Chiffres clés (22K chaînes, 120K films, 4K, 0 pub)
- **Features** — 3 avantages avec icônes SVG
- **How It Works** — 3 étapes (Choisir → Recevoir → Regarder)
- **Pricing** — 3 forfaits (Basique 2,990 / Pro 5,990 / Premium 9,990 FCFA)
- **FAQ** — 5 questions avec accordion JS
- **Footer** — Navigation, contact, légal

## Stack Technique

| Tech | Usage |
|------|-------|
| **HTML5** | Structure sémantique |
| **Tailwind CSS** | CDN, pas de build |
| **CSS Variables** | Design system par version |
| **Vanilla JS** | IntersectionObserver, FAQ accordion |
| **Google Fonts** | Inter, Cormorant, Montserrat, Space Grotesk |
| **SVG Icons** | Inline, pas d'emojis |

## Lancer en Local

Ouvrir directement dans le navigateur :

```bash
# Depuis le dossier du projet
open templates/index.html      # V1
open templates/index-v2.html   # V2
open templates/index-v3.html   # V3
```

Ou avec un serveur local :

```bash
python -m http.server 8080
# → http://localhost:8080/templates/index.html
```

## Tarification

| Plan | Prix | Qualité | Écrans |
|------|------|---------|--------|
| **Basique** | 2,990 FCFA/mois | HD | 1 |
| **Pro** | 5,990 FCFA/mois | 4K Ultra HD | 4 |
| **Premium** | 9,990 FCFA/mois | 4K Ultra HD | Illimité |

---

**IPTV Afrika** — L'Afrique regarde autrement.

Built by [MOA Digital Agency](https://github.com/moa-digitalagency)