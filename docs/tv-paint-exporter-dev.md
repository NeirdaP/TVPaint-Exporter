# TV Paint Exporter

Découvrons l'outil d'export de layers TV Paint à Supamonks du point de vue du département R&amp;D.

# Vue d’ensemble

L'outil d'export de layers TV Paint a été créé suite à la demande de la production WOF pour permettre aux artistes 2D à distance travaillant sur tablettes, et donc en dehors du réseau Supamonks, de publier leur travail directement sur le lecteur partagé M:/.

Le script connecte une machine distante au réseau Supa à l'aide d'un tunnel FTP, restitue tous les layers de tous les clips et scènes du projet TV Paint actuellement ouvert, ainsi qu'une compilation mp4 de tous les layers de la scène dans un dossier temporaire, copie le contenu de ce dossier dans un endroit prédéterminé sur le lecteur M, et publie enfin le mp4 avec un commentaire sur une tâche prédéterminée dans Kitsu.

<p class="callout danger">Le script ne fonctionne qu'avec TV Paint Pro</p>

# Requirements

Afin de bien utiliser le script, le package et le plugin PyTVPaint doivent être installés et le projet doit respecter certaines conventions de dénomination.

##### Plugin

La dernière version du DLL du plugin peut être téléchargée depuis: [https://github.com/brunchstudio/tvpaint-rpc/releases](https://github.com/brunchstudio/tvpaint-rpc/releases) et peut être directement copié dans le dossier des plugins, trouvé dans C:/Program Files/TVPaint Developpement/TVPaint Animation &lt;version&gt; Pro (64bits)/plugins.   
Le plugin lance un serveur de web socket dans TVPaint et reçoit les commandes George (le langage natif de TVPaint) du projet actuellement ouvert. Notez que si plusieurs projets sont ouverts dans une session TVPaint, seul le projet actuellement sélectionné/au premier plan sera traité. Parfois, nous avons rencontré des erreurs de connexion de socket qui sont généralement résolues en fermant et en rouvrant le projet.

#####   
Package

Le package PyTVPaint peut être installé à la main avec pip, mais ici il a été inclus dans l'exécutable fourni par PyInstaller, décrit ci-dessous.

#####   
File Naming

Le projet TVPaint doit se conformer à une convention de dénomination qui permet au script de déduire le chemin de sortie des layers. Pour TWOF, la convention des fichiers décidée suit le modèle : **WOF\_LAYOUT\_SH010\_01\_lb**

  
L'outil plantera s'il ne parvient pas à analyser les métadonnées nécessaires, notamment le nom du shot, à partir du nom du fichier. Si nécessaire, la logique de la convention de dénomination peut être modifiée pour les besoins de production dans les méthodes *parse\_tokens* et *get\_server\_output\_roots* de l'outil.

# FTP

L'outil utilise le module ftplib de Python afin d'établir une connexion avec le serveur FTP Supamonks, de se connecter et de transférer des fichiers. Les commandes notables incluent:  
  
**mkd** – ceci est similaire à mkdir et crée les dossiers nécessaires sur le serveur de destination, mais il échoue si les dossiers intermédiaires n'existent pas. Il faut donc l'utiliser avec prudence pour s'assurer que les structures de fichiers sont créées de manière séquentielle  
  
**prot\_p** – un appel requis pour sécuriser la connexion de données avec le serveur distant  
  
**storbinary** – cela prend un argument de descripteur de fichier et est responsable du transfert des bytes de la source à la destination  
  
La configuration du tunnel a présenté quelques défis. Premièrement, il existe un bug connu dans Python provoquant des erreurs de connexion de données lors de la tentative de transfert de fichiers. Suite aux informations contenues dans ce post, il a été nécessaire de sous-classer FTP\_TLS afin d' overrider la méthode ntransfercmd pour corriger le problème.  
  
Après cela, le script était capable d'écrire sur le serveur FTP en hors du réseau Supamonks, mais pas à l'intérieur. Cela a été corrigé en modifiant le numéro de port d'accès sur le serveur et en mettant à jour les fichiers host.ini côté client. Cette mise à jour a depuis été déployée sur toutes les postes à Supamonks afin que le script fonctionne à la fois à l'intérieur et à l'extérieur du réseau Supa.

<span style="background-color: transparent; color: rgb(34, 34, 34); white-space-collapse: preserve;">  
Enfin, il y avait un problème de déconnexions intermittentes du serveur lors des processus de copie. Bien que la cause sous-jacente des déconnexions n'ait pas été découverte, il a été possible de contourner ce problème comme indiqué dans ce fil en encapsulant la logique de transfert dans un try/except qui détecte ces erreurs et se reconnecte au serveur si nécessaire au long du processus d'exportation. Cela a été testé et n’a produit aucun comportement anormal côté serveur.</span>

# Déploiement

Le script d'exportation TVPaint peut facilement être regroupé dans un seul exécutable à l'aide de [PyInstaller](https://pyinstaller.org/en/stable/installation.html).

Une fois [l'environnement virtuel activé](https://supadocs.supamonks.com/books/tv-paint-exporter/page/developpement), accédez simplement au dossier du script et exécutez :

```
pyinstaller --distpath <dossier d'output> --onefile <nom du script>
```

PyInstaller analysera le script pour les imports et les dépendances et créera un seul fichier exécutable (comme précisé par --onefile) qui inclut toutes les dépendances. Par défaut, l'exécutable sera écrit dans un répertoire dist/ à côté du fichier python exporté. Les prints du programme doivent apparaître par défaut dans une console lorsque l'exécutable est lancé. Les utilisateurs peuvent désormais exécuter le script sans avoir besoin d'installer manuellement les dépendances, notamment python, gazu ou pytvpaint.

<p class="callout warning">Malheureusement, pour builder l'outil, il faut avoir une licence TV Paint Pro activée sur notre machine.</p>

<p class="callout info">Pour builder l'outil, il faut parfois désactiver la "Protection en temps réel" de Windows Defender</p>

# Développement

Pour développer ainsi que pour builder l'outil, on utilise un environnement virtuel et on installe les paquets situés dans *requirements.txt*.

<p class="callout danger">Le script ne fonctionne qu'avec TV Paint Pro.</p>