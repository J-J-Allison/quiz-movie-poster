# Défi Cinéma

Un jeu interactif en Python avec Streamlit pour tester vos connaissances cinématographiques à travers les époques et les genres. Devinez le titre des films à partir d’un poster flouté.  
Ce projet utilise l'API de TMDb (The Movie Database) pour récupérer les informations sur les films.

## Objectif du projet

L’objectif est de créer un quiz de films où les utilisateurs peuvent :  

- Découvrir des films de différentes époques (1990s, 2000s, 2010s, 2020s).  
- Tester leur connaissance des films par genre.  
- Obtenir un score basé sur l’exactitude et la rapidité de leurs réponses.  

## Principales fonctionnalités

- Jeu interactif en Streamlit avec affichage de posters floutés.  
- Système de scoring dynamique selon la précision de la réponse.  
- Indices : premier caractère du titre et résumé du film.  
- Support pour plusieurs époques et genres de films.  
- Dashboard présentant les données du jeu : graphiques et tableau. Classement par époque, difficulté, points accumulés, temps de réaction et titres.  

## Configuration

1. Copier les fichiers `webapp.py`, `requirements.txt` et le dossier `images` dans votre projet.  
2. Ouvrir le projet dans un environnement de développement (ex. VSCode).  
3. Installer les dépendances :  
   ```bash
   pip install -r requirements.txt
4. Lancer le jeu dans le terminal :  
   ```bash
   streamlit run webapp.py

- Les images de fin de partie doivent être placées dans un dossier local, et le chemin dans le code doit être mis à jour en conséquence. Modifier les lignes 276, 290, 294, 298, 302
Par exemple : img_path = r"C:\chemin\vers\vos\images\mauvais.jpg"
- Le jeu fonctionne même si ces images ne sont pas présentes. 
   
