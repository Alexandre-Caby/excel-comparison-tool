# Guide d'Utilisation ECT Technis

## Table des Matières
1. [Introduction](#introduction)
2. [Démarrage](#démarrage)
3. [Téléchargement des Fichiers](#téléchargement-des-fichiers)
4. [Configuration des Comparaisons](#configuration-des-comparaisons)
5. [Visualisation des Résultats](#visualisation-des-résultats)
6. [Génération des Rapports](#génération-des-rapports)
7. [Dépannage](#dépannage)
8. [FAQ](#faq)

## Introduction

ECT Technis est un outil spécialisé conçu pour comparer les fichiers PREPA PHP avec d'autres sources Excel. L'outil identifie les modifications entre les fichiers et vous permet de générer des rapports détaillés des changements.

### Fonctionnalités Principales

- Comparaison des fichiers PREPA PHP avec des fichiers Excel
- Correspondance des données par codes de site (LE, BGL)
- Identification des modifications aux enregistrements existants
- Détection des doublons
- Génération de rapports Excel et CSV

## Démarrage

### Configuration Requise

- Windows 10/11
- 4 Go de RAM minimum
- 50 Mo d'espace disque libre

### Installation

#### Application Autonome

1. Téléchargez la dernière version depuis la page des versions
2. Exécutez simplement le fichier `ECT_Technis.exe`
3. Aucune installation requise

#### À partir du code source

1. Assurez-vous d'avoir Python 3.9+ installé
2. Clonez le dépôt
3. Installez les dépendances: `pip install -r requirements.txt`
4. Lancez l'application: `run_app.bat`

## Téléchargement des Fichiers

### Étapes pour télécharger des fichiers

1. Lancez ECT Technis
2. Accédez à la page "Télécharger des fichiers" depuis le menu latéral
3. Téléchargez votre fichier de base PREPA PHP
4. Téléchargez un ou plusieurs fichiers de comparaison
5. Une fois les fichiers téléchargés, vous verrez la structure des feuilles détectées

### Exigences des fichiers

- **Fichier de base**: Fichier PREPA PHP avec les en-têtes sur la ligne 3
- **Fichiers de comparaison**: Fichiers Excel avec les en-têtes sur la ligne 8
- Les fichiers doivent être au format `.xlsx` ou `.xls`
- Les colonnes importantes sont traitées de A à J:
  - **A**: Site (LE, BGL, etc.)
  - **C**: Locomotive (identifiant normalisé)
  - **D**: CodeOp (code d'opération)
  - **E-J**: Données à comparer (commentaires, dates, heures)

## Configuration des Comparaisons

Après avoir téléchargé vos fichiers, configurez la comparaison:

1. **Sélectionner des feuilles**: Choisissez les feuilles du fichier de base à comparer
2. **Configuration des codes de site**: Définissez comment les codes de site correspondent aux noms des feuilles
   - Par exemple: "LE" correspond à la feuille "lens"
   - Par exemple: "BGL" correspond à la feuille "bgl"
3. **Lancer la comparaison**: Cliquez sur le bouton "Démarrer la comparaison"

### Normalisation des identifiants de locomotive

L'outil normalise automatiquement les identifiants de locomotive pour correspondre correctement:
- Les identifiants comme "BB15030" et "15030" seront considérés comme identiques
- Les préfixes de lettres (BB, Z) sont préservés pour correspondre correctement
- Insensible à la casse pour les correspondances

## Visualisation des Résultats

Après avoir exécuté une comparaison, vous verrez:

1. **Statistiques de résumé**:
   - Feuilles comparées
   - Différences totales
   - Taux de correspondance
   - Temps de traitement
   
2. **Tableau des modifications**:
   - Affiche uniquement les modifications entre les fichiers (pas les ajouts/suppressions)
   - Pour chaque modification, montre la clé (Locomotive_CodeOp)
   - Affiche la valeur de base et la valeur de comparaison
   
3. **Tableau des doublons**:
   - Montre les enregistrements qui apparaissent plusieurs fois
   - Triés par locomotive et code d'opération

Vous pouvez filtrer et trier ces résultats pour vous concentrer sur des zones spécifiques.

## Génération des Rapports

Pour créer un rapport:

1. Accédez à la page "Rapports"
2. Sélectionnez le rapport que vous souhaitez exporter
3. Choisissez un format de rapport (Excel ou CSV)
4. Cliquez sur "Exporter"
5. Téléchargez le rapport à l'emplacement souhaité

### Types de rapport

- **Rapport Excel**: Rapport complet avec tous les onglets de différences
- **Rapport CSV**: Données brutes des différences pour un traitement externe

## Dépannage

### Problèmes courants

#### "La comparaison montre des différences inattendues"
- Vérifiez que les bonnes feuilles sont sélectionnées
- Assurez-vous que les correspondances de codes de site sont correctes

#### "Certains identifiants de locomotive ne correspondent pas"
- Vérifiez la colonne C (Locomotive) dans les deux fichiers
- Contactez le support si la normalisation des identifiants ne fonctionne pas correctement

#### "L'application ne démarre pas"
- Assurez-vous que toutes les dépendances sont installées
- Essayez de réinstaller l'application

## FAQ

**Q: Puis-je comparer plusieurs fichiers à la fois?**
R: Oui, vous pouvez télécharger un fichier de base et plusieurs fichiers de comparaison.

**Q: Comment l'outil gère-t-il les différences de format d'identifiant de locomotive?**
R: L'outil normalise automatiquement les identifiants en préservant les préfixes de lettres.

**Q: L'outil modifie-t-il mes fichiers Excel d'origine?**
R: Non, l'outil lit uniquement vos fichiers et ne modifie jamais les originaux.

**Q: Comment l'outil détermine-t-il qu'une ligne a été modifiée?**
R: Il compare uniquement les lignes qui existent dans les deux fichiers, en utilisant une clé composite (Locomotive_CodeOp).
