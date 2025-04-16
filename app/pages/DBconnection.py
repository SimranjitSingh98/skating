'''
import streamlit as st
import pandas as pd



selezionaCategoria = st.selectbox(
    "Categoria",
    ("Senior M", "Senior F", "Junior M", "Junior F"),
    index=None,
    placeholder="Clicca qui per scegliere la categoria",
)
st.write("Categoria selezionata:", selezionaCategoria)

selezionaGara = st.selectbox(
    "Gare",
    ("Gare Corte", "Gare Lunghe", "Tutte le gare"),
    index=None,
    placeholder="Clicca qui per scegliere la gara",
)
st.write("Gara selezionata:", selezionaGara)

selezionaCampionato = st.selectbox(
    "Campionato",
    ("Indoor", "Strada", "Pista", "Maratona", "Tiezzi"),
    index=None,
    placeholder="Clicca qui per scegliere il campionato",
)
st.write("Campionato selezionato:", selezionaCampionato)


st.write("Risultati")
data=pd.read_csv("../data/Risultati.csv")
st.write(data)



# Carica il dataset

df = pd.read_csv("../data/Risultati.csv")

# Controlla se la colonna "categoria" esiste
if 'Categoria' in df.columns:
    # Aggiunge un'opzione "Tutte le categorie"
    opzioni_categorie = ['Tutte le categorie'] + list(df['Categoria'].unique())
    categoria_selezionata = st.selectbox("Seleziona una categoria", opzioni_categorie)

    # Filtra il dataset in base alla selezione
    if categoria_selezionata == 'Tutte le categorie':
        df_filtrato = df  # Mostra tutte le categorie
    else:
        df_filtrato = df[df['Categoria'] == categoria_selezionata]

    # Visualizza il dataset filtrato
    st.write(f"Righe trovate: {len(df_filtrato)}")
    st.dataframe(df_filtrato)
else:
    st.error("La colonna 'Categoria' non è presente nel dataset.")


'''

import streamlit as st
import pymongo
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns

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
    client = pymongo.MongoClient("mongodb+srv://sannys387:Xc7oetTs2Pv3kpGG@skatingcluster.n9nuu.mongodb.net/?retryWrites=true&w=majority&appName=SkatingCluster")
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

def get_all_athletes():
    db = connect_to_db()
    collection = db["years"]  # Sostituisci con il nome della tua collezione
    athletes = collection.aggregate([  
        {"$unwind": "$championships"},
        {"$unwind": "$championships.categories"},
        {"$unwind": "$championships.categories.events"},
        {"$unwind": "$championships.categories.events.results"},
        {"$project": {"athlete_name": "$championships.categories.events.results.athlete_name"}}
    ])
    
    athlete_names = set()
    
    for athlete in athletes:
        # Usa .get() per evitare KeyError
        athlete_name = athlete.get("athlete_name", None)
        
        if athlete_name:
            # Se athlete_name è una lista, prendi il primo nome
            if isinstance(athlete_name, list):
                athlete_name = athlete_name[0]  # Gestisci come preferisci
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

# Streamlit UI
st.title("Visualizzazione dei dati campionati")

# Sidebar per navigazione
st.sidebar.title("Navigazione")
page = st.sidebar.radio("Vai a:", ["Campionati", "Gare Atleta", "Confronto Atleti"])

# Verifica se i dati sono già stati caricati nella sessione
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.data = None
    st.session_state.df = None

# Carica i dati solo una volta
if st.button("Carica Dati da MongoDB", key="carica_dati_btn"):
    with st.spinner('Caricamento dei risultati...'):
        data = get_data_from_db()
        if data:
            st.session_state.data = data
            st.session_state.df = data_to_dataframe(data)
            st.session_state.data_loaded = True
            #st.write(f"Dati caricati con successo! Numero di documenti: {len(data)}")
        else:
            st.write("Nessun dato trovato nel database.")





if page == "Campionati":
    st.header("Visualizzazione Campionati")
    if st.session_state.data_loaded:
        df = st.session_state.df

        # Selezione dell'anno disponibile
        available_years = sorted({year_data.get('year') for year_data in st.session_state.data if 'year' in year_data})
        selected_year = st.selectbox("Seleziona un Anno", available_years) if available_years else None
        
        if selected_year:
            # Estrai i nomi dei campionati per l'anno selezionato
            championships = [champ.get('name') for year_data in st.session_state.data
                            if year_data.get('year') == selected_year
                            for champ in year_data.get('championships', [])]
            
            if championships:
                selected_championship = st.selectbox("Seleziona un Campionato", championships)
                
                if selected_championship:
                    # Filtra i dati del campionato selezionato
                    selected_data = [championship for year_data in st.session_state.data
                                    if year_data.get('year') == selected_year
                                    for championship in year_data.get('championships', [])
                                    if championship.get('name') == selected_championship]
                    
                    if selected_data:
                        championship = selected_data[0]
                        st.write(f"### Dettagli del campionato selezionato: {championship.get('name')}")
                        st.write(f"**Luogo e Date:** {championship.get('location_dates')}")
                        st.write(f"**Organizzatore:** {championship.get('organizer')}")
                        
                        # Selezione della categoria
                        categories = [category.get('category') for category in championship.get('categories', [])]
                        selected_category = st.selectbox("Seleziona una Categoria", categories) if categories else None
                        
                        if selected_category:
                            # Trova la categoria selezionata
                            category = next((cat for cat in championship.get('categories', [])
                                            if cat.get('category') == selected_category), None)
                            
                            if category:
                                st.write(f"### Categoria selezionata: {category.get('category')}")
                                
                                # Selezione della gara
                                events = [event.get('event') for event in category.get('events', [])]
                                selected_event = st.selectbox("Seleziona una Gara", events) if events else None
                                
                                if selected_event:
                                    event = next((ev for ev in category.get('events', [])
                                                if ev.get('event') == selected_event), None)
                                    
                                    if event:
                                        st.write(f"### Gara selezionata: {event.get('event')}")
                                        st.write("**Risultati:**")
                                        
                                        result_list = [
                                            {
                                                'Position': athlete_result.get('position'),
                                                'Athlete Name': athlete_result.get('athlete_name'),
                                                'Athlete number': athlete_result.get('id_number'),
                                                'Time': athlete_result.get('time'),
                                                'Points': athlete_result.get('points'),
                                                'Team': athlete_result.get('team', '')
                                            }
                                            for result in event.get('results', [])
                                            for athlete_result in result
                                        ]
                                        
                                        if result_list:
                                            result_df = pd.DataFrame(result_list)
                                            result_df['Time (seconds)'] = result_df['Time'].apply(convert_time_to_seconds)
                                            st.write(result_df.drop(columns=['Time (seconds)']))
                                            st.bar_chart(result_df.set_index('Athlete Name')['Time (seconds)'].astype(float))
                                        else:
                                            st.write("⚠️ Nessun risultato disponibile per questa gara.")
                                    else:
                                        st.write("⚠️ Gara non trovata.")
                            else:
                                st.write("⚠️ Categoria non trovata.")
                    else:
                        st.write("⚠️ Nessun dato trovato per il campionato selezionato.")
            else:
                st.write("⚠️ Nessun campionato disponibile per l'anno selezionato.")
        else:
            st.write("⚠️ Nessun anno disponibile.")



elif page == "Gare Atleta":
    st.header("Storico Gare Atleta")

    if st.session_state.data_loaded:
        athlete_names = get_all_athletes()
        selected_athlete = st.selectbox("Seleziona un Atleta", athlete_names)

        if selected_athlete:
            athlete_df = get_athlete_events(selected_athlete)

            if not athlete_df.empty:
                # Costruzione del DataFrame dei risultati
                results_list = []
                for _, row in athlete_df.iterrows():
                    result = row["Result"]
                    results_list.append({
                        "Year": row["Year"],
                        "Championship": row["Championship"],
                        "Event": row["Event"],
                        "Position": result.get("position"),
                        "Time": result.get("time"),
                        "Points": result.get("points"),
                        "Team": result.get("team", ""),
                        "Athlete number": result.get("id_number")
                    })

                result_df = pd.DataFrame(results_list)
                result_df["Time (seconds)"] = result_df["Time"].apply(convert_time_to_seconds)

                # 🔍 Filtro per anno e tipo gara
                available_years = sorted(result_df["Year"].unique())
                available_events = sorted(result_df["Event"].unique())

                selected_years = st.multiselect("Filtra per Anno", available_years, default=available_years)
                selected_events = st.multiselect("Filtra per Gara", available_events, default=available_events)

                filtered_df = result_df[
                    (result_df["Year"].isin(selected_years)) &
                    (result_df["Event"].isin(selected_events))
                ]

                st.write(f"### Gare filtrate di {selected_athlete}")
                st.dataframe(filtered_df.drop(columns=["Time (seconds)"]))

                
               
                # 📊 Grafico dell'andamento delle posizioni in classifica
                if not filtered_df.empty:
                    # Crea un'etichetta combinata per ogni gara
                    filtered_df["Gara"] = (
                        filtered_df["Year"].astype(str) + " - " +
                        #filtered_df["Championship"] + " - " +
                        filtered_df["Event"]
                    )

                    # Ordina le gare per anno
                    filtered_df = filtered_df.sort_values("Year")

                    # 🧼 Assicura che le posizioni siano numeri (interi)
                    filtered_df["Position"] = pd.to_numeric(filtered_df["Position"], errors="coerce")

                    # Rimuovi eventuali righe con Position non numerico
                    filtered_df = filtered_df.dropna(subset=["Position"])

                    # Crea il grafico
                    fig, ax = plt.subplots(figsize=(12, 6))
                    sns.lineplot(
                        data=filtered_df,
                        x="Gara",
                        y="Position",
                        marker='o',
                        ax=ax
                    )

                    # Imposta il titolo e le etichette degli assi
                    ax.set_title(f"Andamento delle posizioni in classifica di {selected_athlete}")
                    ax.set_ylabel("Posizione (1° in basso)")
                    ax.set_xlabel("Gara")

                    # 🔄 Se vuoi la posizione 1 in basso
                    # ax.invert_yaxis()  <-- lascialo fuori se 1 deve essere in basso

                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig)
                else:
                    st.write("⚠️ Nessun dato disponibile con i filtri selezionati.")





            else:
                st.write("⚠️ Nessuna gara trovata per questo atleta.")
    else:
        st.write("⚠️ Carica prima i dati dal database.")