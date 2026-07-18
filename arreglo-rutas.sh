#!/bin/bash
# Arregla el 500 en subrutas: el docroot del subdominio vive dentro de
# public_html (WordPress) y hereda sus reglas de RewriteRule, que mandan
# toda URL "no-archivo" a un index.php inexistente. Desactivar el rewrite
# en el docroot del subdominio corta esa herencia; Passenger no lo necesita.
DOCROOT="$HOME/public_html/calculadora.petermanncapitalgroup.cl"

if [ ! -f "$DOCROOT/.htaccess" ]; then
    echo "ERROR: no existe $DOCROOT/.htaccess"
    exit 1
fi

if grep -q "RewriteEngine Off" "$DOCROOT/.htaccess"; then
    echo "El arreglo ya estaba aplicado."
else
    printf '\n# Evita heredar las reglas de WordPress del public_html padre\nRewriteEngine Off\n' >> "$DOCROOT/.htaccess"
    echo "Arreglo aplicado."
fi

echo "--- Contenido actual del .htaccess del subdominio ---"
cat "$DOCROOT/.htaccess"
