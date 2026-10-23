### Configuration

 - add `SESSION_COOKIE_SECURE`, `True` par défaut pour limiter les cookies en `https` ({pr}`455`, {issue}`416` et {user}`SbirLobo`)
 - add `SESSION_COOKIE_SAMESITE`, `Lax` par défaut pour la restrictions des cookies externes sauf lors d'une navigation directe ({pr}`455`, {issue}`416` et {user}`SbirLobo`)

### Sécurité

  - Ajout des en-têtes `Content-Security-Policy`, `Strict-Transport-Security` (2 ans) et `X-Frame-Options: SAMEORIGIN`, qui limitent les injections de scripts et l'intégration de B3Desk dans des sites tiers. Les ressources externes sont désormais bloquées par le navigateur (exceptions : Matomo, La Suite numérique, BigBlueButton, le sondage de satisfaction, podeduc et Nextcloud) ({pr}`455`, {issue}`416` et {user}`SbirLobo`).
