# Guide d'Utilisation ECT Technis

## Table des Matières
1. Introduction
2. Démarrage
3. Téléchargement des Fichiers
4. Configuration des Comparaisons
5. Lancement de la Comparaison
6. Analyse et Visualisation des Résultats
7. Génération et Export des Rapports
8. Module d'Analyse PHP
9. Dépannage
10. FAQ

---

## 1. Introduction

ECT Technis est un outil spécialisé pour comparer des fichiers Excel avec d'autres fichiers Excel. Il détecte les différences, les doublons et génère des rapports détaillés pour faciliter le suivi des modifications.

### Fonctionnalités principales

- Comparaison avancée de fichiers Excel
- Correspondance automatique par codes de site (ex : LE, BGL)
- Détection des modifications, ajouts, suppressions et doublons
- Génération de rapports exportables (Excel, CSV, PDF)
- Interface claire pour visualiser et filtrer les résultats
- **NOUVEAU**: Analyse complète des programmes de maintenance PHP

---

## 2. Démarrage

### Configuration requise

- Windows 10/11
- 4 Go de RAM minimum
- 50 Mo d'espace disque libre
- Python 3.9+ (si utilisation depuis le code source)

### Installation

#### Application autonome

1. Téléchargez la dernière version depuis la page des versions.
2. Exécutez le fichier `ECT_Technis_version.exe`.
3. Aucune installation supplémentaire n'est requise.

#### Depuis le code source

1. Installez Python 3.9 ou supérieur.
2. Clonez le dépôt du projet.
3. Installez les dépendances :  
   `pip install -r requirements.txt`
4. Lancez l'application :  
   `python src/backend/app.py`

---

## 3. Téléchargement des Fichiers

1. Lancez ECT Technis.
2. Accédez à la page "Télécharger des fichiers" via le menu latéral.
3. Importez votre fichier de base PREPA PHP.
4. Importez un ou plusieurs fichiers de comparaison.
5. Vérifiez la structure des feuilles détectées.

**Exigences :**
- Fichier de base : excel de base avec en-têtes à la ligne 3 ou détectées dynamiquement.
- Fichiers de comparaison : Excel avec en-têtes à la ligne 8 ou détectées dynamiquement.
- Formats acceptés : `.xlsx`, `.xls`.

---

## 4. Configuration des Comparaisons

1. Sélectionnez les feuilles du fichier de base à comparer.
2. Configurez la correspondance des codes de site (ex : "LE" → "lens").
3. Vérifiez la normalisation automatique des identifiants de locomotive (insensible à la casse, préfixes conservés).

---

## 5. Lancement de la Comparaison

1. Cliquez sur "Démarrer la comparaison".
2. Patientez pendant le traitement (la durée dépend du volume de données).
3. À la fin, accédez à la page de comparaison pour consulter les résultats.

---

## 6. Analyse et Visualisation des Résultats

Après la comparaison, la page "Comparaison" affiche :

### a. Statistiques de résumé

- Nombre de feuilles comparées
- Nombre total de différences
- Nombre total de doublons
- Taux de correspondance (%)
- Temps de traitement

### b. Tableau des différences

- Affiche les modifications, ajouts et suppressions détectées.
- Pour chaque différence :
  - Clé composite (ex : Locomotive_CodeOp)
  - Colonne concernée
  - Valeur dans le fichier de base
  - Valeur dans le fichier de comparaison
- Les lignes modifiées sont listées avec leur statut ("Modifiée", "Ajoutée", "Supprimée").

### c. Tableau des doublons

- Affiche les enregistrements présents plusieurs fois dans un même fichier.
- Permet d'identifier rapidement les anomalies de saisie ou de duplication.

### d. Navigation et ergonomie

- Les tableaux sont paginés et scrollables horizontalement.
- Les valeurs vides ou non pertinentes (NaT, NaN) sont automatiquement nettoyées pour une meilleure lisibilité.
- Vous pouvez filtrer et trier les résultats pour cibler vos recherches.

---

## 7. Génération et Export des Rapports

1. Rendez-vous sur la page "Rapports".
2. Sélectionnez le rapport à exporter.
3. Choisissez le format souhaité : Excel (.xlsx), CSV ou PDF.
4. Spécifiez un nom de fichier personnalisé (optionnel).
5. Cliquez sur "Exporter" puis téléchargez le fichier généré.

**Formats disponibles :**

### Excel (.xlsx)
- **Structure améliorée** : Feuilles organisées avec des titres clairs et une mise en forme professionnelle
- **Mise en forme visuelle** : Lignes en couleur selon leur statut (vert pour ajouts, jaune pour modifications, rouge pour suppressions)
- **Onglets distincts** : Séparation entre les différences et les doublons pour faciliter l'analyse
- **Résumé exécutif** : Première feuille avec toutes les statistiques et informations clés
- **Données enrichies** : Icônes emoji (📊 📁 ➕ ➖ ✏️) et formatage adapté pour une meilleure lisibilité
- **Statistiques précises** : Comptage exact des entrées ajoutées, modifiées et supprimées

### CSV
- **Format classique** : Structure tabulaire simple compatible avec tous les logiciels
- **Encodage optimisé** : UTF-8 avec BOM pour compatibilité Excel européenne
- **Délimiteur point-virgule** : Adapté aux paramètres régionaux français
- **Limitation à 100 lignes** : Par feuille pour garantir des performances optimales
- **Structure claire** : Colonnes standards (Feuille, Fichier, Ligne, Statut, Key, Column, Base Value, Comparison Value)
- **Sans formatage** : Format brut idéal pour l'import dans d'autres outils d'analyse

### PDF
- **Présentation professionnelle** : Mise en page soignée avec en-têtes et filigrane
- **Visualisation graphique** : Graphiques à barres illustrant la répartition des différences par catégorie
- **Résumé exécutif** : Synthèse claire avec statistiques précises
- **Tables formatées** : Présentation des différences avec code couleur par catégorie
- **Regroupement par type** : Différences regroupées par statut (Ajoutées, Supprimées, Modifiées)
- **Comptage précis** : Statistiques corrigées montrant le nombre exact d'entrées par catégorie

**Conseils d'utilisation :**
- **Pour l'analyse détaillée** : Utilisez le format Excel qui offre la meilleure organisation visuelle et l'accès à toutes les données
- **Pour l'import dans d'autres outils** : Le format CSV est idéal avec sa structure simple et standardisée
- **Pour les présentations et l'archivage** : Le format PDF offre une présentation claire et non modifiable
- **Pour les grands volumes** : Notez que le format CSV limite à 100 lignes par feuille pour des raisons de performance

---

## 8. Module d'Analyse PHP

### a. Présentation du module

Le module d'analyse PHP permet d'analyser en profondeur les programmes de maintenance en calculant avec précision :
- Les jours d'immobilisation par engin
- La validité des rendez-vous de maintenance
- La charge de travail par semaine
- Les conflits et anomalies dans les données

### b. Accès au module d'analyse PHP

1. Accédez à la page "Analyse PHP" via le menu latéral.
2. Importez votre fichier PREPA PHP (formats acceptés : `.xlsx`, `.xls`).
3. Sélectionnez la feuille correspondant au site à analyser (ex : "lens", "bgl").
4. Choisissez une semaine spécifique pour filtrer les données ou "Tout" pour analyser l'ensemble.
5. Cliquez sur "Démarrer l'analyse" pour lancer le traitement.

### c. Interprétation des métriques

Les résultats affichent plusieurs métriques clés :

**Métriques de résumé :**
- **Total RDV** : Nombre total de rendez-vous de maintenance planifiés
- **Total Clients** : Nombre de clients uniques identifiés
- **Total de Séries** : Nombre de séries d'engins différentes
- **Total Heures** : Somme des heures d'immobilisation de tous les engins
- **Jours avec RDV** : Nombre de jours calendaires où le site a au moins un engin en maintenance
- **Conflits** : Nombre d'anomalies détectées dans les données

**Métriques par engin :**
- **RDV Total** : Nombre total de rendez-vous pour l'engin
- **RDV Valides/Invalides** : Les RDV invalides ont des dates manquantes ou incorrectes
- **Jours d'immobilisation** : Nombre de jours calendaires distincts où l'engin est immobilisé
- **Heures d'immobilisation** : Jours d'immobilisation × 24h
- **Durée moyenne** : Heures totales ÷ Nombre de RDV valides
- **Opérations** : Nombre d'opérations distinctes planifiées
- **Clients** : Nombre de clients distincts concernés

### d. Principe de calcul important

**Pour éviter les comptages en double :**
Si plusieurs opérations sont effectuées en parallèle sur un même engin le même jour, ce jour n'est compté qu'une seule fois dans le calcul des jours d'immobilisation.

**Exemple :**
Si un engin BB75000 a trois opérations distinctes prévues le 20/05/2025, l'analyse :
- Compte 3 RDV distincts
- Mais compte seulement 1 jour d'immobilisation (soit 24h)

### e. Données concaténées et filtrage

L'onglet "Données concaténées" permet de :
- Visualiser tous les rendez-vous dans un format standardisé
- Filtrer par client, série d'engin ou date
- Afficher les durées calculées pour chaque rendez-vous
- Identifier les RDV appartenant à un même groupe d'opérations

Format de concaténation : `Site_Client_Engin_DateDébut_DateFin_Opération`

### f. Détection des conflits

Le système détecte automatiquement plusieurs types d'anomalies :
- **Date début manquante** : L'engin n'est peut-être pas encore sur site
- **Date fin manquante** : L'entretien n'est peut-être pas encore défini
- **Inversion de dates** : La date de fin est antérieure à la date de début
- **Immobilisation excessive** : Période d'immobilisation anormalement longue (>1000 jours)

Les conflits sont regroupés par type et par engin pour une meilleure lisibilité.

### g. Export des résultats d'analyse

1. Après l'analyse, cliquez sur "Exporter les résultats".
2. Choisissez le format Excel.
3. Le fichier généré contient plusieurs onglets :
   - Résumé global
   - Analyse par engin
   - Analyse par semaine
   - Données concaténées
   - Liste des conflits détectés

---

## 9. Dépannage

### Problèmes courants

- **Différences inattendues** : Vérifiez la sélection des feuilles et la correspondance des codes de site.
- **Identifiants de locomotive non reconnus** : Contrôlez la colonne "Locomotive" dans vos fichiers.
- **Application ne démarre pas** : Vérifiez l'installation de Python et des dépendances, ou relancez l'application autonome.
- **Problèmes de dates dans l'analyse PHP** : Vérifiez le format des dates dans votre fichier d'entrée. Le système prend en charge plusieurs formats mais certains formats inhabituels peuvent nécessiter un prétraitement.

---

## 10. FAQ

**Q : Puis-je comparer plusieurs fichiers à la fois ?**  
R : Oui, vous pouvez importer un fichier de base et plusieurs fichiers de comparaison.

**Q : Comment l'outil gère-t-il les différences de format d'identifiant de locomotive ?**  
R : Les identifiants sont normalisés automatiquement, en préservant les préfixes de lettres.

**Q : L'outil modifie-t-il mes fichiers Excel d'origine ?**  
R : Non, l'outil ne fait que lire vos fichiers, ils ne sont jamais modifiés.

**Q : Comment retrouver une ligne dans le fichier d'origine ?**  
R : Les colonnes "Base Row" et "Comp Row" dans les exports indiquent la ligne d'origine dans chaque fichier.

**Q : Comment l'outil détermine-t-il qu'une ligne a été modifiée ?**  
R : Il compare les lignes présentes dans les deux fichiers à l'aide d'une clé composite (Locomotive_CodeOp).

**Q : Comment sont calculés les jours d'immobilisation dans le module d'analyse PHP ?**  
R : Les jours d'immobilisation représentent le nombre de jours calendaires uniques pendant lesquels un engin est en maintenance. Si plusieurs opérations sont effectuées le même jour sur le même engin, ce jour n'est compté qu'une seule fois.

**Q : Que signifie "RDV invalide" dans l'analyse PHP ?**  
R : Un RDV est considéré comme invalide lorsqu'il manque une date de début ou de fin, ou lorsque ces dates sont dans un format non reconnu. Ces RDV sont exclus des calculs de durée mais restent visibles dans les tableaux.

**Q : Comment filtrer les données par semaine dans l'analyse PHP ?**  
R : Lors du lancement de l'analyse, vous pouvez sélectionner une semaine spécifique dans le menu déroulant (format "S21", "S22", etc.) pour ne voir que les RDV de cette semaine.

---

Pour toute question ou problème, consultez la section Dépannage ou contactez le gestionnaire de l'application.