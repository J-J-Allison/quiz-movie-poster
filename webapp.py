import os
import random
import string
import time
from io import BytesIO

from PIL import Image, ImageFilter
import pandas as pd
import requests
import streamlit as st

# Configuration
MAX_ROUNDS = 8
API_KEY = "a0c122e9bafc4305d559ed48f3701bc5"
BASE_URL = "https://api.themoviedb.org/3"

st.set_page_config(page_title="🎬 Défi Cinéma",
                   page_icon="🎯",
                   layout="wide")

# Movie eras
ERA_CATEGORIES = {
    "Les 1990s": (1990, 2000),
    "Les 2000s": (2000, 2010),
    "Les 2010s": (2010, 2020),
    "Les 2020s": (2020, 2025)
}

# Initialize session state
for key, default in [
    ("score", 0),
    ("round", 1),
    ("current_movie", {}),
    ("feedback", ""),
    ("next_round", False),
    ("guess_value", ""),
    ("next_movie", None),
    ("poster", None),
    ("poster_full", None),
    ("points_to_gain", 10),
    ("game_history", []),
    ("start_time", 0.0),
    ("reaction_times", []),
    ("page", "game"),
    ("final_image_path", ""),
    ("final_phrase", ""),
    ("movie_sequence", []),
    ("main_hint", "")
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Genre mapping
GENRE_MAP = {
    "Action": 28,
    "Aventure": 12,
    "Animation": 16,
    "Comédie": 35,
    "Crime": 80,
    "Documentaire": 99,
    "Drame": 18,
    "Famille": 10751,
    "Fantastique": 14,
    "Histoire": 36,
    "Horreur": 27,
    "Musique": 10402,
    "Mystère": 9648,
    "Romance": 10749,
    "Science_Fiction": 878,
    "Téléfilm": 10770,
    "Thriller": 53,
    "Guerre": 10752,
    "Western": 37
}

GENRES_LIST = list(GENRE_MAP.keys())


# Utility functions
def remove_punctuation(text):
    """Remove punctuation and special characters from a string."""
    if not text:
        return ""
    punctuation_to_remove = string.punctuation + '’«»—'
    return text.translate(str.maketrans('', '', punctuation_to_remove))


def levenshtein_distance(s1, s2):
    """Compute Levenshtein distance between two strings."""
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min(
                    distances[i1], distances[i1 + 1], distances_[-1]
                ))
        distances = distances_
    return distances[-1]


# Fetch movies
@st.cache_data(show_spinner=False)
def fetch_movie_data(genre, year):
    """Fetch movies from the TMDB API."""
    try:
        response = requests.get(
            f"{BASE_URL}/discover/movie",
            params={
                "api_key": API_KEY,
                "with_genres": GENRE_MAP[genre],
                "primary_release_date.gte": f"{year}-01-01",
                "primary_release_date.lte": f"{year}-12-31",
                "vote_count.gte": 100,
                "sort_by": "popularity.desc",
            },
            timeout=8
        ).json()
        return response.get("results", [])
    except Exception:
        return []


def fetch_random_movie(era=None):
    """Fetch a random movie from a random or specific era."""
    for _ in range(5):
        genre = random.choice(GENRES_LIST)
        if era and era in ERA_CATEGORIES:
            start, end = ERA_CATEGORIES[era]
        else:
            era = random.choice(list(ERA_CATEGORIES.keys()))
            start, end = ERA_CATEGORIES[era]

        year = random.randint(start, end - 1)
        results = fetch_movie_data(genre, year)
        if results:
            movie = random.choice(results)
            if movie.get("title") and movie.get("poster_path"):
                movie["genre_name"] = genre
                movie["era"] = era
                return movie
    return None


@st.cache_data(show_spinner=False)
def get_movie_poster(poster_path, size="w200"):
    """Get movie poster image."""
    if poster_path:
        poster_url = f"https://image.tmdb.org/t/p/{size}{poster_path}"
        try:
            response = requests.get(poster_url, timeout=8)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception:
            pass
    return Image.new("RGB", (200, 300), color=(20, 20, 20))


def preload_next_movie():
    """Preload the next movie."""
    movie = fetch_random_movie()
    if movie:
        st.session_state.next_movie = movie


def generate_movie_sequence():
    """Generate a sequence of movies from all eras."""
    sequence = []
    for era in ERA_CATEGORIES.keys():
        for _ in range(2):
            movie = fetch_random_movie(era)
            if movie:
                sequence.append(movie)
    random.shuffle(sequence)
    st.session_state.movie_sequence = sequence


def start_new_round():
    """Start a new game round."""
    if st.session_state.round > MAX_ROUNDS:
        return
    if not st.session_state.movie_sequence:
        generate_movie_sequence()

    movie = st.session_state.movie_sequence[st.session_state.round - 1]
    st.session_state.current_movie = movie
    poster_full = get_movie_poster(movie.get("poster_path"))
    st.session_state.poster_full = poster_full
    st.session_state.poster = poster_full.filter(ImageFilter.GaussianBlur(15))
    overview = movie.get("overview", "Aucune description disponible")
    st.session_state.main_hint = (
        f"**Résumé :** *{overview}* | **Genre :** {movie['genre_name']}"
    )
    st.session_state.feedback = ""
    st.session_state.next_round = False
    st.session_state.guess_value = ""
    st.session_state.start_time = time.time()
    preload_next_movie()


def get_title_hint():
    """Return the first letter of the movie title as a hint."""
    title = remove_punctuation(
        st.session_state.current_movie.get("title", "Inconnu")
    )
    return f"**`{title[0]}{'_' * (len(title) - 1)}`**"


def submit_guess(guess):
    """Handle user movie title submission."""
    if st.session_state.next_round:
        return

    guess = guess.strip()
    if not guess:
        st.session_state.feedback = "⚠️ Veuillez entrer une proposition avant de soumettre."
        return

    reaction_time = round(time.time() - st.session_state.start_time, 2)
    st.session_state.reaction_times.append(reaction_time)

    correct_title = st.session_state.current_movie.get("title")
    clean_correct_title = remove_punctuation(correct_title)
    clean_guess = remove_punctuation(guess)
    normalized_correct = clean_correct_title.lower().replace(' ', '')
    normalized_guess = clean_guess.lower().replace(' ', '')

    distance = levenshtein_distance(normalized_correct, normalized_guess)
    max_dist = max(len(normalized_correct), len(normalized_guess))
    partial_factor = max(0.0, 1 - distance / max_dist)

    points_gained = int(st.session_state.points_to_gain * partial_factor)
    st.session_state.score += points_gained

    vote_count = st.session_state.current_movie.get("vote_count", 0)
    difficulte = round(10 - min(vote_count / 2000, 9), 1)
    difficulte = max(1.0, difficulte)

    if partial_factor == 1.0:
        feedback_msg = f"🎉 **Correct !** C'était **{correct_title}** !"
    elif partial_factor >= 0.5:
        feedback_msg = f"🤏 **Presque !** C'était **{correct_title}**."
    else:
        feedback_msg = f"❌ **Faux !** Le film était **{correct_title or 'Inconnu'}**."

    st.session_state.feedback = feedback_msg
    st.session_state.game_history.append({
        'manche': st.session_state.round,
        'titre': correct_title,
        'poster_path': st.session_state.current_movie.get('poster_path'),
        'proposition': guess,
        'points': points_gained,
        'points_max': st.session_state.points_to_gain,
        'temps_reaction': reaction_time,
        'difficulté': difficulte,
        'époque': st.session_state.current_movie.get('era', 'Inconnue')
    })

    st.session_state.poster = st.session_state.poster_full
    st.session_state.next_round = True

    if st.session_state.round == MAX_ROUNDS:
        df = pd.DataFrame(st.session_state.game_history)
        era_points = df.groupby('époque', as_index=False)['points'].sum()
        total_score = st.session_state.score
        total_possible = sum(
            [r['points_max'] for r in st.session_state.game_history]
        )

        if total_score == 0 or total_score < total_possible * 0.2:
            img_path = r"C:\Users\Suffy\Documents\Python\Projet\images\mauvais.jpg"
            phrase = "😬 Ouch... Aucun film trouvé ? Essaie encore !"
        else:
            era_stats = df.groupby('époque').agg({
                'points': 'sum',
                'temps_reaction': 'sum'
            }).reset_index()
            era_stats = era_stats.sort_values(
                by=['points', 'temps_reaction'],
                ascending=[False, True]
            ).reset_index(drop=True)
            best_era = era_stats.loc[0, 'époque']
            jokes = {
                "Les 1990s": (
                    r"C:\Users\Suffy\Documents\Python\Projet\images\Les 1990s.jpg",
                    "Ta meilleure catégorie: Les 1990s ! T'es un dinosaure ?"
                ),
                "Les 2000s": (
                    r"C:\Users\Suffy\Documents\Python\Projet\images\Les 2000s.jpg",
                    "Ta meilleure catégorie: Les 2000s! On se retrouve sur MSN"
                ),
                "Les 2010s": (
                    r"C:\Users\Suffy\Documents\Python\Projet\images\Les 2010s.jpg",
                    "Ta meilleure catégorie: Les 2010s! Tu as regardé tous ces films pendant le confinement ?"
                ),
                "Les 2020s": (
                    r"C:\Users\Suffy\Documents\Python\Projet\images\Les 2020s.jpg",
                    "Ta meilleure catégorie: Les 2020s! Les films sont trop longs pour toi. Reste sur TikTok !"
                )
            }
            img_path, phrase = jokes[best_era]

        st.session_state.final_image_path = img_path
        st.session_state.final_phrase = phrase

    st.rerun()


# Game UI
st.title("🎬 Movie Match Challenge")

if st.session_state.page == "game" and st.session_state.poster is None:
    start_new_round()

if st.session_state.page == "game":
    st.markdown(
        f"### Score : {st.session_state.score} | Manche : "
        f"{st.session_state.round} sur {MAX_ROUNDS}"
    )
    st.markdown("---")

    col_poster, col_game = st.columns([1, 3])
    with col_poster:
        if st.session_state.poster is not None:
            st.image(
                st.session_state.poster,
                caption="Devinez le titre du film !",
                width=250
            )
        else:
            placeholder_img = Image.new("RGB", (250, 375), color=(30, 30, 30))
            st.image(
                placeholder_img,
                caption="Chargement de l’affiche...",
                width=250
            )

    with col_game:
        st.markdown("⏳ Manche en cours…")
        st.markdown(st.session_state.main_hint)
        st.markdown("---")
        with st.form("guess_form"):
            st.write(f"💰 Points potentiels : **{st.session_state.points_to_gain}**")
            st.write(f"✨ Indice de titre : {get_title_hint()}")
            guess_input = st.text_input(
                "Entrez le titre du film",
                value=st.session_state.guess_value,
                disabled=st.session_state.next_round
            )
            submitted = st.form_submit_button(
                "Entrer", disabled=st.session_state.next_round
            )

    if submitted:
        submit_guess(guess_input)

    if st.session_state.next_round:
        st.markdown(st.session_state.feedback)
        if st.button("➡️ Manche suivante"):
            if st.session_state.round < MAX_ROUNDS:
                st.session_state.round += 1
                start_new_round()
                st.rerun()
            else:
                st.session_state.page = "result"
                st.rerun()

if st.session_state.page == "result":
    if os.path.exists(st.session_state.final_image_path):
        img = Image.open(st.session_state.final_image_path)
    else:
        img = Image.new("RGB", (800, 600), color=(20, 20, 20))
    st.image(img, width="stretch")
    st.markdown(f"## {st.session_state.final_phrase}")
    if st.button("➡️ Voir le tableau de bord"):
        st.session_state.page = "dashboard"
        st.rerun()

elif st.session_state.page == "dashboard":
    st.title("🏁 Tableau de bord")
    total_score = st.session_state.score
    total_possible = sum(
        [r['points_max'] for r in st.session_state.game_history]
    )
    st.markdown(f"### 🎯 Score total : {total_score} / {total_possible}")

    df = pd.DataFrame(st.session_state.game_history)
    df_display = df[
        ['manche', 'titre', 'proposition', 'points',
         'temps_reaction', 'difficulté', 'époque']
    ]
    st.dataframe(df_display, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📈 Performance par manche")
        st.line_chart(
            df_display[['points', 'temps_reaction', 'difficulté']]
            .set_index(df_display['manche'])
        )
    with col2:
        st.markdown("### 📊 Points par époque")
        era_points = df.groupby('époque', as_index=False)['points'].sum()
        st.bar_chart(era_points.set_index('époque'))

    if st.button("🔄 Rejouer"):
        st.session_state.score = 0
        st.session_state.round = 1
        st.session_state.current_movie = {}
        st.session_state.next_movie = None
        st.session_state.poster = None
        st.session_state.poster_full = None
        st.session_state.feedback = ""
        st.session_state.guess_value = ""
        st.session_state.next_round = False
        st.session_state.game_history = []
        st.session_state.reaction_times = []
        st.session_state.page = "game"
        st.session_state.movie_sequence = []
        start_new_round()
        st.rerun()