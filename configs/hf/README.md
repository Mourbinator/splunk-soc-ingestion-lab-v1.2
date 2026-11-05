# Heavy Forwarder (référence — optionnel)

Un **Heavy Forwarder (HF)** est une instance Splunk Enterprise complète (avec Splunk Web et le parsing) qui ne stocke pas
les données (`indexAndForward = false`) mais les transforme puis les envoie ailleurs. Il se justifie pour :
- router/filtrer/masquer **avant** l'indexeur ;
- exécuter des inputs modulaires (API, DB Connect) ;
- relier des segments réseau.

Ces fichiers sont des **références** : le lab fonctionne sans HF (le PC Windows fait indexeur + parsing).
Pour l'essayer : installer une 2ᵉ instance Splunk Enterprise sur la VM Ubuntu (tarball), y placer ces fichiers dans une app,
faire pointer l'UF vers elle (`9997`) et observer le routage `_TCP_ROUTING` (voir `modules/M7-routage.md`, partie C).
