
import streamlit as st
import pymongo
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
import os




# Funzione per convertire il formato 'hh.mm.ss.xxx' in secondi
def convert_time_to_seconds(time_str):
    try:
        # Separiamo le ore, minuti, secondi e millisecondi
        if time_str.count('.') == 2:  # formato con ore (hh.mm.ss.xxx)
            hours, remainder = time_str.split('.', 1)
            minutes, seconds = remainder.split('.', 1)
        elif time_str.count('.') == 1:  # formato senza ore (mm.ss.xxx)
            hours = 0
            minutes, seconds = time_str.split('.', 1)
        else:
            return None
        
        seconds, milliseconds = seconds[:2], seconds[2:]  # Estrae i millisecondi
        
        # Calcoliamo il totale in secondi
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
        return total_seconds
    except Exception as e:
        st.write(f"Errore nella conversione del tempo {time_str}: {e}")
        return None  # Se non riesce a convertire, ritorna None

# Funzione per connettersi a MongoDB
def connect_to_db():
    # Modifica questa stringa con i tuoi dettagli di connessione
   # Carica le variabili d'ambiente dal file .env
    load_dotenv()

    # Ottieni l'URI dal file .env
    mongodb_uri = os.getenv("MONGODB_URI")

    # Usa l'URI per connetterti a MongoDB
    client = pymongo.MongoClient(mongodb_uri)

    db = client["skating_database"]  # Sostituisci con il nome del tuo database
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    return db


def get_collections():
    db = connect_to_db()
    if db is not None:  # Modifica questa riga
        collections = db.list_collection_names()
        print(f"Collezioni nel database: {collections}")
        return collections
    else:
        print("Connessione al database non riuscita.")
        return []


# Funzione per ottenere i dati dal DB
def get_data_from_db():
    db = connect_to_db()
    collection = db["years"]  # Sostituisci con il nome della tua collezione
    data = list(collection.find())
    return data

# Funzione per trasformare i dati in DataFrame
def data_to_dataframe(data):
    # Appiattire la struttura dei dati JSON
    df_list = []
    
    for year_data in data:
        year = year_data.get('year')
        championships = year_data.get('championships', [])

        for championship in championships:
            championship_name = championship.get('name')
            location_dates = championship.get('location_dates')
            organizer = championship.get('organizer')
            categories = championship.get('categories', [])

            for category in categories:
                category_name = category.get('category')
                events = category.get('events', [])

                for event in events:
                    event_name = event.get('event')
                    results = event.get('results', [])

                    for result in results:
                        for athlete_result in result:
                            athlete_name = athlete_result.get('athlete_name')
                            time = athlete_result.get('time')
                            points = athlete_result.get('points')
                            team = athlete_result.get('team', '')
                            position = athlete_result.get('position')
                            id_number = athlete_result.get('id_number')
                            df_list.append({
                                'Year': year,
                                'Championship': championship_name,
                                'Location/Date': location_dates,
                                'Organizer': organizer,
                                'Category': category_name,
                                'Event': event_name,
                                'Athlete Name': athlete_name,
                                'Time': time,
                                'Points': points,
                                'Team': team,
                                'Position': position,
                                'Id_number': id_number
                            })
    
    df = pd.DataFrame(df_list)
    return df

'''
#funzione per ottenere tutti gli atleti
def get_all_athletes():
    db = connect_to_db()
    collection = db["years"]

    athletes = collection.aggregate([
        {"$unwind": "$championships"},
        {"$unwind": "$championships.categories"},
        {"$unwind": "$championships.categories.events"},
        {"$unwind": "$championships.categories.events.results"},
        {"$unwind": "$championships.categories.events.results"},  # <- nuovo livello
        {"$project": {
            "athlete_name": "$championships.categories.events.results.athlete_name"
        }}
    ])
    
    athlete_names = set()
    for athlete in athletes:
        athlete_name = athlete.get("athlete_name")
        if athlete_name:
            athlete_names.add(athlete_name)
    
    return list(athlete_names)
'''
def get_all_athletes():
    db = connect_to_db()
    collection = db["years"]

    athletes = collection.aggregate([
        {"$unwind": "$championships"},
        {"$unwind": "$championships.categories"},
        {"$unwind": "$championships.categories.events"},
        
        # Escludi eventi che contengono americana, americane, team, team sprint
        {"$match": {
            "championships.categories.events.event": {
                "$not": {
                    "$regex": "americana|americane|team|team sprint", 
                    "$options": "i"  # case-insensitive
                }
            }
        }},
        
        {"$unwind": "$championships.categories.events.results"},
        {"$unwind": "$championships.categories.events.results"},
        {"$project": {
            "athlete_name": "$championships.categories.events.results.athlete_name"
        }}
    ])
    
    athlete_names = set()
    for athlete in athletes:
        athlete_name = athlete.get("athlete_name")
        if athlete_name:
            athlete_names.add(athlete_name)
    
    return list(athlete_names)





# Funzione per cercare tutte le gare di un atleta
def get_athlete_events(athlete_name):
    db = connect_to_db()
    collection = db["years"]  # Sostituisci con il nome della tua collezione
    events = collection.aggregate([
        {"$unwind": "$championships"},
        {"$unwind": "$championships.categories"},
        {"$unwind": "$championships.categories.events"},
        {"$unwind": "$championships.categories.events.results"},
        {"$match": {"championships.categories.events.results.athlete_name": athlete_name}},
        {"$project": {
            "year": 1,
            "championship_name": "$championships.name",
            "event_name": "$championships.categories.events.event",
            "result": "$championships.categories.events.results"
        }}
    ])
    event_details = []
    for event in events:
        results = event.get("result", [])
        if isinstance(results, dict):
            results = [results]
        for result in results:
            if isinstance(result, dict) and result.get("athlete_name") == athlete_name:
                event_details.append({
                    "Year": event["year"],
                    "Championship": event["championship_name"],
                    "Event": event["event_name"],
                    "Result": result
                })
    return pd.DataFrame(event_details)



#dashboard atleta
def show_positions_chart(df, atleta):
    import seaborn as sns
    import matplotlib.pyplot as plt

    df["position"] = pd.to_numeric(df["position"], errors="coerce")
    df = df.dropna(subset=["position"])
    df = df.sort_values("Year")
    df["Gara"] = df["Year"].astype(str) + " - " + df["Event"]

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(data=df, x="Gara", y="position", marker='o', ax=ax, color='teal')
    ax.set_title(f"Andamento Posizioni: {atleta}")
    ax.set_ylabel("Posizione (1° in basso)")
    ax.invert_yaxis()
    plt.xticks(rotation=45)
    st.pyplot(fig)


def show_medal_count(df):
    medals = df["position"].dropna().astype(int)
    gold = (medals == 1).sum()
    silver = (medals == 2).sum()
    bronze = (medals == 3).sum()

    st.metric("🥇 Ori", gold)
    st.metric("🥈 Argenti", silver)
    st.metric("🥉 Bronzi", bronze)
