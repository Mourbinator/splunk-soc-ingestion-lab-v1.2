# Glossaire (A→Z)

| Terme | Définition simple |
|---|---|
| **ACK (indexer acknowledgment)** | Confirmation que l'indexeur a bien écrit les données ; l'UF les garde tant qu'il ne l'a pas reçue (`useACK=true`). |
| **Backoff** | Attendre de plus en plus longtemps entre deux tentatives (1 s, 2 s, 4 s…) pour ne pas aggraver une panne. |
| **Bucket** | Dossier de stockage d'un index : *hot* (écriture) → *warm* → *cold* → *frozen* (supprimé/archivé). |
| **btool** | Outil CLI qui affiche la configuration **effective** et le fichier d'où vient chaque ligne. |
| **Checkpoint** | Marque de progression (où j'en suis) conservée par un agent ou un poller pour reprendre sans perte ni doublon. |
| **CIM** | Common Information Model : noms de champs et modèles de données communs à toutes les sources. |
| **Collecteur** | Service qui reçoit des données (syslog-ng, HEC) et les rend disponibles pour la suite. |
| **Eventtype / Tag** | Étiquettes search-time qui font reconnaître un événement par un modèle CIM. |
| **Fishbucket** | Base interne de l'UF qui mémorise la position de lecture de chaque fichier. |
| **Forwarder (UF/HF)** | Programme qui envoie des données vers un indexeur. UF = léger, sans parsing ; HF = Splunk complet qui parse. |
| **HEC** | HTTP Event Collector : API HTTPS de Splunk pour recevoir des événements avec un token. |
| **Index-time / Search-time** | Réglage appliqué **à l'écriture** (irréversible pour les données déjà écrites) ou **à la recherche** (rétroactif). |
| **Indexeur** | Composant qui parse (si besoin), route et écrit les événements sur disque. |
| **Lookup** | Table (CSV…) qui ajoute des champs à des événements selon une clé. |
| **Normalisation** | Renommer/convertir les champs et valeurs vers un vocabulaire commun (ex. `src_ip` → `src`, `deny` → `blocked`). |
| **nullQueue** | « Poubelle » Splunk : un événement routé ici est supprimé avant indexation. |
| **Parsing** | Découper en événements, trouver l'horodatage, extraire des champs. |
| **Pipeline / Queue** | Étapes internes de traitement d'un indexeur, séparées par des files d'attente (`parsingQueue`, `indexQueue`…). |
| **Poller** | Programme qui interroge régulièrement une API (contrairement à un webhook qui pousse). |
| **RFC 5424** | Format moderne du Syslog : `<PRI>1 TIMESTAMP HOST APP PROCID MSGID SD MSG`. |
| **S2S** | Splunk-to-Splunk : protocole des forwarders (port 9997). |
| **SA / TA** | Supporting / Technical Add-on : paquet de configuration (enrichissement / parsing+normalisation). |
| **Sourcetype** | Étiquette de **format** d'un événement ; elle déclenche les règles `props.conf`. |
| **SLO** | Objectif de niveau de service mesurable (ex. 95 % des événements en < 120 s). |
| **UF** | Universal Forwarder : agent léger de collecte de fichiers/journaux. |
