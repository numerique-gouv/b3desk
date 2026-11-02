## Sécurité

- Les vérifications de codes de réunion sont limitées côté serveur par IP et utilisateur, y compris sans cookie ({issue}`423`).

## Configuration

- `VISIO_CODE_RATE_LIMIT` (120) et `VISIO_CODE_RATE_WINDOW` (60 secondes) règlent la limite ; un cache Redis partagé et une IP client fiable sont nécessaires.
