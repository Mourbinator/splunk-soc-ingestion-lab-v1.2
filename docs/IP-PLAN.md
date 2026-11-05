# Plan IP (exemple uniquement)
| Hôte | IP proposée | Fonction |
|---|---|---|
| PC-SPLUNK | 10.50.0.10 | Splunk Enterprise (Windows) |
| UBUNTU-LAB | 10.50.0.40 | syslog-ng, UF, générateurs, poller, mock API |
| WIN-LAB | 10.50.0.50 | UF Windows (optionnel) |

- Adaptez à votre réseau hôte-privé / NAT. Les IP **dans les logs** (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) sont des adresses
  **réservées à la documentation** (RFC 5737) : elles ne sont jamais routées sur Internet.
- `localhost` dans une VM désigne **cette VM**, pas le PC Windows hôte. C'est l'erreur n°1 des débutants.
- Pour remplacer 10.50.0.10 partout : `grep -rn "10.50.0.10" configs/ docs/` puis adaptez.
