# TV Paint Exporter

Découvrons l'outil d'export de layers TV Paint à Supamonks du point de vue du département R&amp;D.

## Vue d’ensemble

L'outil d'export de layers TV Paint a été créé suite à la demande de la production WOF pour permettre aux artistes 2D à distance travaillant sur tablettes, et donc en dehors du réseau Supamonks, de publier leur travail directement sur le lecteur partagé M:/.

Le script connecte une machine distante au réseau Supa à l'aide d'un tunnel FTP, restitue tous les layers de tous les clips et scènes du projet TV Paint actuellement ouvert, ainsi qu'une compilation mp4 de tous les layers de la scène dans un dossier temporaire, copie le contenu de ce dossier dans un endroit prédéterminé sur le lecteur M, et publie enfin le mp4 avec un commentaire sur une tâche prédéterminée dans Kitsu.

Plus tard, il a été complété pour qu'on puisse l'utiliser sans tunnel FTP et sans Kitsu (voir § Configuration)

## Prérequis

Afin de bien utiliser le script, la librairie PyTVPaint et le plugin TVPaint RPC doivent être installés et le projet doit respecter certaines conventions de dénomination.

### Plugin TVPaint RPC

Le plugin TVPaint RPC peut être téléchargée depuis: [https://github.com/brunchstudio/tvpaint-rpc/releases](https://github.com/brunchstudio/tvpaint-rpc/releases) et peut être directement copié dans le dossier des plugins, trouvé dans C:/Program Files/TVPaint Developpement/TVPaint Animation &lt;version&gt; Pro (64bits)/plugins.

Attention, il faut choisir la bonne version du plugin TVPaint RPC en fonction de la version de TVPaint que vous utilisez :

| TVPaint version | tvpaint-rpc version |
|-----------------|---------------------|
| TVPaint 11.X    | tvpaint-rpc v1.0.0  |
| TVPaint 12.0    | tvpaint-rpc v1.1.0  |
| TVPaint 12.1    | tvpaint-rpc v1.2.0  |

Le plugin lance un serveur de web socket dans TVPaint et reçoit les commandes George (le langage natif de TVPaint) du projet actuellement ouvert. Notez que si plusieurs projets sont ouverts dans une session TVPaint, seul le projet actuellement sélectionné/au premier plan sera traité. Parfois, nous avons rencontré des erreurs de connexion de socket qui sont généralement résolues en fermant et en rouvrant le projet.

### Library PyTVPaint

La librairie PyTVPaint peut être installé à la main avec pip, mais ici il a été inclus dans l'exécutable fourni par PyInstaller, décrit ci-dessous.

### TV Paint Pro

Le script ne fonctionne qu'avec TV Paint Pro.

## Configuration

Pour configurer l'outil, la plupart des options sont regroupés dans le dictionnaire `PROJECT_CONFIGURATION`
C'est ici qu'on va définir :
- les chemins de sortie des fichiers exportés (`server_output_templates`)
- la nomenclature attendue pour les fichiers de travail (`shot_regex`)
- l'utilisation ou non d'un VPN (`transfer_strategy`)
- l'utilisation ou non de Kitsu (`need_upload_to_kitsu`)
- les informations de connexion à Kitsu

## FTP

L'outil utilise le module ftplib de Python afin d'établir une connexion avec le serveur FTP Supamonks, de se connecter et de transférer des fichiers. Les commandes notables incluent:  
  
**mkd** – ceci est similaire à mkdir et crée les dossiers nécessaires sur le serveur de destination, mais il échoue si les dossiers intermédiaires n'existent pas. Il faut donc l'utiliser avec prudence pour s'assurer que les structures de fichiers sont créées de manière séquentielle  
  
**prot\_p** – un appel requis pour sécuriser la connexion de données avec le serveur distant  
  
**storbinary** – cela prend un argument de descripteur de fichier et est responsable du transfert des bytes de la source à la destination  
  
La configuration du tunnel a présenté quelques défis. Premièrement, il existe un bug connu dans Python provoquant des erreurs de connexion de données lors de la tentative de transfert de fichiers. Suite aux informations contenues dans ce post, il a été nécessaire de sous-classer FTP\_TLS afin d' overrider la méthode ntransfercmd pour corriger le problème.  
  
Après cela, le script était capable d'écrire sur le serveur FTP en hors du réseau Supamonks, mais pas à l'intérieur. Cela a été corrigé en modifiant le numéro de port d'accès sur le serveur et en mettant à jour les fichiers host.ini côté client. Cette mise à jour a depuis été déployée sur toutes les postes à Supamonks afin que le script fonctionne à la fois à l'intérieur et à l'extérieur du réseau Supa.

Enfin, il y avait un problème de déconnexions intermittentes du serveur lors des processus de copie. Bien que la cause sous-jacente des déconnexions n'ait pas été découverte, il a été possible de contourner ce problème comme indiqué dans ce fil en encapsulant la logique de transfert dans un try/except qui détecte ces erreurs et se reconnecte au serveur si nécessaire au long du processus d'exportation. Cela a été testé et n’a produit aucun comportement anormal côté serveur.

## Développement

Pour développer ainsi que pour builder l'outil, on utilise un environnement virtuel et on installe les paquets situés dans *requirements.txt*.

## Déploiement

Le script d'exportation TVPaint peut facilement être regroupé dans un seul exécutable à l'aide de [PyInstaller](https://pyinstaller.org/en/stable/installation.html).

Une fois l'environnement virtuel activé (cf: § Développement), accédez simplement au dossier du script et exécutez :

```
pyinstaller --distpath <dossier d'output> --onefile <nom du script>
```

PyInstaller analysera le script pour les imports et les dépendances et créera un seul fichier exécutable (comme précisé par --onefile) qui inclut toutes les dépendances. Par défaut, l'exécutable sera écrit dans un répertoire dist/ à côté du fichier python exporté. Les prints du programme doivent apparaître par défaut dans une console lorsque l'exécutable est lancé. Les utilisateurs peuvent désormais exécuter le script sans avoir besoin d'installer manuellement les dépendances, notamment python, gazu ou pytvpaint.

Malheureusement, pour builder l'outil, il faut avoir une licence TV Paint Pro activée sur notre machine.</p>

Pour builder l'outil, il faut parfois désactiver temporairement la "Protection en temps réel" de Windows Defender</p>

