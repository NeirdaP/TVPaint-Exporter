# TV Paint Exporter

## Installation  

*Les utilisateurs recevront un dossier contenant trois fichiers: le plugin PyTVPaint, (tvpaint-rpc-1.0.0.dll), l'exécutable de l'outil, tvpaint\_exporter.exe, ftp\_config.json*

### Installer le plugin

- copiez **tvpaint-rpc-1.0.0.dll** dans <span style="text-decoration: underline;">**C:/Program Files/TVPaint Developpement/TVPaint Animation &lt;version&gt; Pro (64bits)/plugins.** </span>
- copiez **les deux autres fichiers** *( ftp\_config.json, tvpaint\_exporter.exe )* sur le <span style="text-decoration: underline;">**Bureau** </span>
- Dans **ftp\_config.json**, chaque utilisateur doit remplir les champs "username" et "password" avec ses informations d'identification personnelles, qui peuvent être obtenues en demandant à l'IT. Voici un exemple ci-dessous:

```json
{
    "username":"lionel.jospin",
    "password":"j_assume_pleinement_la_responsabilité_de_cet_echec"
}
```


## Usage
Pour utiliser le script d'export, un projet TV Paint doit déjà être ouvert sur votre machine. Notez que si plusieurs projets sont ouverts dans une seule session, seul le projet actuellement sélectionné sera traité. De plus, le nom du projet doit respecter certaines conventions – pour la production PFLE, il est attendu que le nom de fichier suive le modèle :

PFLE2\_&lt;task&gt;\_SH010\_01  
  
Attention: si le nom du shot est absent du nom du fichier, l'outil ne pourra pas s'exécuter car il ne peut pas déterminer où sortir les layers.   
  
Une fois qu'un projet TVPaint correctement nommé est ouvert, il suffit de double-cliquez sur le raccourci tvpaint\_exporter.exe pour lancer l'outil. La progression de l'outil sera affichée dans une console. Seuls les calques actuellement visibles dans le projet seront traités par l'outil.