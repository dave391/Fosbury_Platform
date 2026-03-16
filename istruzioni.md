Due problemi residui nel caricamento della pagina:

Font: il link Google Fonts in base.html carica pesi non usati e un font
(IBM Plex Mono) che serve solo come fallback. Inoltre mancano i tag preconnect.
Immagini: logo_dark.png è 143KB e 1917×2350px, ma viene visualizzato a
60×60px (classe .sidebar-logo). logo.png è 57KB e 2000×2424px, usato solo
come favicon. Totale: 200KB di immagini enormi per un logo di 60px.

OBIETTIVO
Ridurre il peso dei font e delle immagini senza cambiare l'aspetto visivo.
COSA FARE
A. Ottimizzare i font in base.html
Ho verificato nella codebase quali font e pesi sono effettivamente usati:
Inter (font principale):

weight 400: usato (testo base)
weight 600: usato (font-semibold, font-weight:600 in styles.css)
weight 700: usato (font-bold, font-weight:700 in styles.css)
weight 300: NON usato → rimuovere
weight 500: NON usato → rimuovere

IBM Plex Mono: referenziato SOLO come fallback nel body font-family in styles.css:
font-family: "Inter", "IBM Plex Mono", monospace;
Non è mai usato direttamente. monospace copre già il caso fallback.
→ Rimuovere dal Google Fonts.
→ Aggiornare font-family in styles.css a: font-family: "Inter", sans-serif;
Merriweather: usato tramite la classe .font-editorial che appare in vari template.

weight 300: NON usato (.font-editorial non imposta un weight, il default è 400)
weight 400: usato
weight 700: verificare se combinato con font-bold su un elemento .font-editorial.
Se non sicuro, tenerlo per sicurezza.

Modificare base.html:

AGGIUNGERE prima del link ai font:

html   <link rel="preconnect" href="https://fonts.googleapis.com">
   <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

SOSTITUIRE il link Google Fonts attuale con:

html   <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Merriweather:wght@400;700&display=swap" rel="stylesheet">

In app/static/styles.css, modificare il body font-family:

css   font-family: "Inter", sans-serif;
B. Ottimizzare le immagini logo
logo_dark.png (navbar): 1917×2350px, 143KB.
Viene visualizzato a 60×60px (.sidebar-logo: width 3.75rem; height 3.75rem).
Per retina display serve 2× = 120×120px. L'immagine è ~20 volte più grande del necessario.
logo.png (favicon): 2000×2424px, 57KB. I favicon non hanno bisogno di più di 192×192px.
Cosa fare:

Con Python + Pillow (pip install Pillow — solo per la conversione, NON come
dipendenza runtime):

python   from PIL import Image

   # logo_dark: ridimensiona a 120x120 (2× retina) e converti in WebP
   img = Image.open("app/static/logo_dark.png")
   # Mantieni l'aspect ratio, ridimensiona al lato più corto = 120
   img.thumbnail((120, 120), Image.LANCZOS)
   img.save("app/static/logo_dark.webp", "webp", quality=90)

   # logo: ridimensiona a 192x192 per favicon
   img = Image.open("app/static/logo.png")
   img.thumbnail((192, 192), Image.LANCZOS)
   img.save("app/static/logo.png", "png", optimize=True)

In base.html, per la navbar sostituire:

html   <img src="/static/logo_dark.png" ...>
con:
html   <picture>
     <source srcset="/static/logo_dark.webp" type="image/webp">
     <img src="/static/logo_dark.png" alt="Fosbury Platform" class="sidebar-logo">
   </picture>

TENERE anche i PNG originali nel repo (come fallback per browser vecchi).
Ma i file originali vanno RIDIMENSIONATI — non ha senso servire un PNG di
1917×2350px come fallback per un logo di 60px:

python   # Ridimensiona anche il PNG fallback
   img = Image.open("app/static/logo_dark.png")
   img.thumbnail((120, 120), Image.LANCZOS)
   img.save("app/static/logo_dark.png", "png", optimize=True)

NON convertire il favicon in WebP (non tutti i browser supportano favicon WebP).

VINCOLI

Non aggiungere Pillow come dipendenza runtime (solo per la conversione una tantum)
Le immagini devono apparire identiche a prima nel browser
Non cambiare le classi CSS o le dimensioni di visualizzazione
Non rompere il layout della navbar

TEST DI VERIFICA

Le pagine hanno lo stesso aspetto visivo di prima
Il logo nella navbar è nitido (non sfocato o pixelato)
Il favicon funziona
Il link Google Fonts non include IBM Plex Mono, Inter 300, Inter 500
I tag preconnect sono presenti nel <head>
Il peso totale delle immagini logo è ridotto significativamente
(da ~200KB a ~5-10KB)
Il font-family nel body usa "Inter", sans-serif