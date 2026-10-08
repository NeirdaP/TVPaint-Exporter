# TV Paint Exporter

## Installation  

Les utilisateurs recoivent un dossier contenant trois fichiers:
- le plugin tvpaint-rpc (tvpaint-rpc-1.0.0.dll)
- l'exécutable de l'outil (tvpaint_exporter.exe)
- un fichier ftp_config.json (uniquement si le studio a mis en place un serveur FTP)

### Installer le plugin

- copiez **tvpaint-rpc-1.0.0.dll** dans **C:/Program Files/TVPaint Developpement/TVPaint Animation &lt;version&gt; Pro (64bits)/plugins.**
- copiez **les deux autres fichiers** *( ftp\_config.json, tvpaint\_exporter.exe )* sur le **Bureau**
- Dans **ftp\_config.json**, chaque utilisateur doit remplir les champs "username" et "password" avec ses informations d'identification personnelles, qui peuvent être obtenues en demandant à l'IT. Voici un exemple ci-dessous:

```json
{
    "username":"lionel.jospin",
    "password":"j_assume_pleinement_la_responsabilité_de_cet_echec"
}
```


## Usage
Pour utiliser le script d'export, un projet TV Paint doit déjà être ouvert sur votre machine. Notez que si plusieurs projets sont ouverts dans une seule session, seul le projet actuellement sélectionné sera traité. De plus, le nom du projet doit respecter certaines conventions – pour la production TWOK, il est attendu que le nom de fichier suive le modèle : 
`{CODE_PROJET}_{TACHE}_SH{NUMERO_PLAN_SUR_3_CARACTERES}_v{NUMERO_VERSION}`

Exemple : `TWOK_ANIM_SH010_v001`
  
Attention: si le nom du shot est absent du nom du fichier, l'outil ne pourra pas s'exécuter car il ne peut pas déterminer où sortir les layers.
  
Une fois qu'un projet TVPaint correctement nommé est ouvert, il suffit de double-cliquez sur le raccourci tvpaint\_exporter.exe pour lancer l'outil. La progression de l'outil sera affichée dans une console. Seuls les calques actuellement visibles dans le projet seront traités par l'outil.

### Fonctionalités 
Lorsque l'outil est lancé, 3 possibilités sont proposées :
- 1 - Render Layers as PNGs and Anim Movie
- 2 - Render Layers as PSDs and Anim Movie
- 3 - Render Anim Movie Only

