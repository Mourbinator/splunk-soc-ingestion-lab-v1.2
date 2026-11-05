# Matrice des ports

| Port | Proto | Usage | Hôte écoutant | Qui s'y connecte | Restriction |
|---:|---|---|---|---|---|
| 8000 | TCP | Splunk Web | PC Splunk | poste d'analyse | poste/lab uniquement |
| 8089 | TCP | Management (REST, Deployment Server) | PC Splunk | admin, UF clients du DS | admin / réseau lab |
| 9997 | TCP | Réception S2S (forwarders) | PC Splunk | UF Ubuntu/Windows | réseau privé |
| 8088 | TCP | HEC (HTTPS) | PC Splunk | poller, applications | réseau privé |
| 5514 | UDP+TCP | Syslog du lab | VM Ubuntu | générateurs / firewalls | réseau privé |
| 6514 | TCP | Syslog TLS (optionnel) | VM Ubuntu | émetteurs | réseau privé |
| 8081 | TCP | Mock API | VM Ubuntu | poller | localhost |
| 514 | UDP/TCP | Syslog « officiel » **non utilisé** (port privilégié < 1024) | — | — | — |

Contrôles :
```powershell
# Windows : ports en écoute
Get-NetTCPConnection -State Listen | Where-Object LocalPort -in 8000,8088,8089,9997
```
```bash
# Ubuntu : ports en écoute (TCP et UDP) et processus propriétaire
sudo ss -lntup | grep -E '5514|6514|8081'
```
