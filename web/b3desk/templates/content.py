from flask_babel import lazy_gettext as _

FAQ_CONTENT = [
    {
        "title": _(
            """Quelles sont les conditions d’accès pour accéder aux services ?"""
        ),
        "description": _(
            """Cette plateforme offre une solution complète et puissante, adaptée à de nombreux types d’événements en ligne, jusqu’à 350 participants (Séminaire, formation, table ronde, ateliers collaboratifs…)

Pour qui ?

L’accès à ce service est dédié aux agents de l’État et à leurs interlocuteurs (suivant le nom de domaine autorisé, demande sur contact@webinaire.numerique.gouv.fr) depuis un poste de travail sur site ou en télétravail ou un appareil mobile personnel ou professionnel.
L’accès au Webinaire de L’Etat n’est pas ouvert aux collectivités territoriales, ni aux Universités et établissements d'enseignements du Ministère de l’enseignement supérieur.

Par quel moyen ?

• Sur site :
Depuis votre ordinateur de travail en utilisant les navigateurs préconisés : Edge, Chromium, Chrome, et aussi Firefox pour l'éducation nationale

• En télétravail :
Depuis votre ordinateur de travail (VPN activé ou désactivé) les navigateurs préconisés sont : Edge, Chromium, Chrome, et aussi Firefox pour l'éducation nationale ou ordinateur personnel (Navigateurs Edge, Chrome, Chromium, Firefox)

• Depuis vos appareils mobiles :
- Téléphone portable ou tablette  (sans application, un lien participant ou modérateur suffit).
- Sur IOS, le navigateur Safari est recommandé pour les iphone et ipad (IOS 12.2+)
- Sur Android, utiliser le navigateur Chrome par défaut (Android 6.0+)
"""
        ),
    },
    {
        "title": _("""Quel est le matériel nécessaire ?"""),
        "description": _(
            """Pour utiliser l’outil Webinaire de l’État, il vous suffit de disposer du matériel suivant :

    • un ordinateur connecté à Internet
    • un navigateur web (pas d’application à télécharger et à installer). Il est recommandé d’utiliser la dernière version de Microsoft Edge (Chromium), Chromium ou Google Chrome.
    • une webcam,
    • un micro et des haut-parleurs, ou, de préférence, un casque avec micro intégré.
    • Le webinaire de l’Etat fonctionne également sur les appareils mobiles (sans application). Le navigateur Safari est recommandé pour les iphone et ipad (IOS 12.2+). Sur Android, utiliser le navigateur chrome par défaut (Android 6.0+)
    • Pour rejoindre un webinaire, vous devez juste cliquer sur le lien envoyé par l’organisateur/modérateur depuis votre smartphone ou tablette sous Android ou iOS, la caméra et le micro sont activables suivant le contexte d’intervention."""
        ),
    },
    {
        "title": _(
            """Puis-je utiliser mon smartphone ou ma tablette pour me connecter ?"""
        ),
        "description": _(
            """Le Webinaire de l’Etat fonctionne également sur les appareils mobiles par un simple lien (sans application) sur le portail ou dans le séminaire. Sur les iphone et ipad (IOS 12.2+) le navigateur Safari est recommandé. Sur Android, utiliser le navigateur chrome par défaut (Android 6.0+).
"""
        ),
    },
    {
        "title": _("""Comment créer un séminaire ?"""),
        "description": _(
            """Si vous êtes un agent de l’état, vous pouvez :
- Créer des séminaires immédiatement en renseignant votre courriel professionnel sur .gouv.fr et suivant les noms de domaines autorisés.
- Créer un compte pour créer et configurer des séminaires que vous pourrez retrouver facilement dans votre espace ainsi que les liens de connexions, les replays des enregistrements…
- Pour les personnels du MENJS vous devez utiliser le bouton « HUB d'authentification Éducation, Jeunesse et Sports. »

Si votre nom de domaine n’est pas reconnu, et que vous pensez être éligible au service, envoyez un mail à contact@webinaire.numerique.gouv.fr
"""
        ),
    },
    {
        "title": _("""Comment créer un compte ?"""),
        "description": _(
            """En tant qu’agent de l’État, si vous organisez régulièrement des séminaires vous pouvez créer un compte pour organiser et conserver facilement vos séminaires sur mesure.

Vous avez la possibilité créer une ou plusieurs salles de séminaire et les configurer suivant le type de dispositifs adaptés (ex : Séminaire, Formation, classe virtuelle, Conférence interactive, Plénière, Table ronde, Assemblée générale, Ateliers collaboratifs ou d’idéation, Comités en grand nombre, …etc.)."""
        ),
    },
    {
        "title": _("""Comment inviter les participants/ modérateurs"""),
        "description": _(
            """L’organisateur qui a créé le séminaire peut partager le lien :
« Participants » qu’ils soient de l’administration ou de l’extérieur (partenaires, prestataires, entreprises, citoyens…)
« Organisateurs/modérateurs » qui géreront avec vous le séminaire."""
        ),
    },
    {
        "title": _("""Rejoindre un Webinaire en appel téléphonique ?"""),
        "description": _(
            """Une fois dans le séminaire, il est possible d’utiliser aussi son téléphone fixe ou mobile pour suivre le séminaire.
Les informations sont visibles dans le séminaire sur discussion publique. Vous pouvez transmettre ses informations composées du numéro d’appel et du code du séminaire :

Pour rejoindre cette conférence par téléphone, composez-le :
+33 1 XX XX XX XX
Puis entrez le code d’accès XXXXX suivi de la touche #.
Une fois dans la conférence, appuyez sur la touche « 0 » de votre téléphone afin d’activer ou de désactiver votre microphone."""
        ),
    },
    {
        "title": _("""J'ai des perturbations audio ou vidéo ?"""),
        "description": _(
            """
Pour l’audio, rapprochez-vous de votre borne wifi, ou/et coupez votre caméra
Nous vous invitons à utiliser un casque pour une meilleure écoute et pour que les bruits de fond autour de vous ne perturbent pas les autres participants.

Pour la vidéo, baisser la résolution de votre caméra lors de votre connexion sur le Webinaire

La fonctionnalité partage d’écran est la plus consommatrice de bande passante devant la vidéo. Si vous êtes organisateur et que votre bande passante est faible, elle peut dégrader la qualité de votre séminaire.

Pour utiliser moins de bande passante et profiter du service dans les meilleures conditions, avec beaucoup de participants, nous recommandons de vous connecter hors VPN.
"""
        ),
    },
    {
        "title": _("""Besoin de contacter l'équipe du Webinaire de l’Etat ?"""),
        "description": _("""contact@webinaire.numerique.gouv.fr"""),
    },
    {
        "title": _(
            """Besoin de contacter l'équipe du ministére de l'Éducation nationale ?"""
        ),
        "description": _(
            """Rendez-vous sur votre portail d'assistance académique https://www.education.gouv.fr/la-messagerie-professionnelle-3446 ou sur Apps.education.fr"""
        ),
    },
]
