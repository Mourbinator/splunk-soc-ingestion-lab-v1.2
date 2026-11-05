# Sécurité du lab

## Règles
1. Réseau **isolé** (host-only, NAT ou VLAN privé). Ne jamais exposer 8089, 9997, 8088, 5514 sur Internet.
2. **HEC** : un token dédié par usage, index autorisés limités (`saas`, `lab_api`), token dans une variable d'environnement ou un fichier ignoré par Git. Un token publié = token à révoquer immédiatement.
3. Données **synthétiques** uniquement ; IP de documentation ; domaines `.invalid`.
4. Comptes de service au **minimum nécessaire** (l'UF lit des fichiers : droits de lecture seulement, groupe `adm`).
5. Les pannes se **provoquent uniquement** sur les flux de test (`lab_sandbox`, ports de lab).
6. TLS : le certificat HEC du lab est auto-signé ; `--insecure`/`curl -k` est toléré **en lab seulement**.

## Modèle de menaces de la collecte (à compléter en E0)
| Menace | Exemple | Contre-mesure |
|---|---|---|
| Usurpation (Spoofing) | un hôte envoie du faux Syslog en UDP | filtres source, TLS client, réseau segmenté |
| Altération (Tampering) | modification des logs en transit | TCP+TLS, signatures côté source |
| Répudiation | l'émetteur nie avoir envoyé | `event_id` unique, horodatage source, conservation |
| Fuite d'information | token HEC ou mot de passe dans un log | masquage (SEDCMD, M7), secrets hors Git |
| Déni de service | inondation UDP, disque plein | rate limiting, quotas disque, supervision des files |
| Élévation de privilèges | UF exécuté en root avec droits trop larges | utilisateur dédié, groupe de lecture |
| Perte silencieuse | UDP saturé, fichier non lisible | compteurs source/collecteur/Splunk, alertes de fraîcheur |
| Injection de logs | saut de ligne injecté pour forger un événement | validation du format, découpage strict |
