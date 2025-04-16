from utils import *

# Streamlit UI
st.title("Visualizzazione dei dati campionati")

# Sidebar per navigazione
st.sidebar.title("Navigazione")
page = st.sidebar.radio("Vai a:", ["Campionati", "Gare Atleta", "Confronto Atleti","Dashboard Atleta"])

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


elif page == "Confronto Atleti":
    st.title("Confronto Gare tra Due Atleti")

    # Ottieni lista atleti
    all_athletes = get_all_athletes()

    # Usa session_state per mantenere il valore selezionato
    if 'atleta_1' not in st.session_state:
        st.session_state.atleta_1 = all_athletes[0]  # Default valore
    if 'atleta_2' not in st.session_state:
        st.session_state.atleta_2 = all_athletes[0]  # Default valore

    # Seleziona il primo atleta
    atleta_1 = st.selectbox("Seleziona il primo atleta", all_athletes, index=all_athletes.index(st.session_state.atleta_1))
    st.session_state.atleta_1 = atleta_1

    # Seleziona il secondo atleta
    atleta_2 = st.selectbox("Seleziona il secondo atleta", all_athletes, index=all_athletes.index(st.session_state.atleta_2))
    st.session_state.atleta_2 = atleta_2

    if atleta_1 and atleta_2:
        # Ottieni i dati per i due atleti
        data_1 = get_athlete_events(atleta_1)
        data_2 = get_athlete_events(atleta_2)

        st.subheader(f"📊 Confronto tra {atleta_1} e {atleta_2}")

        # Funzione per espandere i risultati in colonne
        def clean_results(df):
            result_expanded = df["Result"].apply(pd.Series)
            df = pd.concat([df.drop(columns=["Result"]), result_expanded], axis=1)
            return df

        # Pulisci i risultati prima di fare il merge
        data_1 = clean_results(data_1)
        data_2 = clean_results(data_2)

        campi_interessati = ["Year", "Event", "position", "time", "Championship"]

        # Mantieni solo i campi desiderati (se esistono nel DataFrame)
        data_1 = data_1[[col for col in campi_interessati if col in data_1.columns]]
        data_2 = data_2[[col for col in campi_interessati if col in data_2.columns]]

        # Mostra affiancati i risultati
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### {atleta_1}")
            st.dataframe(data_1)

        with col2:
            st.markdown(f"### {atleta_2}")
            st.dataframe(data_2)

        # Unisci i due dataframe sulle colonne comuni (Gara, Anno)
        comuni = pd.merge(
            data_1,
            data_2,
            on=["Year", "Championship", "Event"],
            suffixes=(f" - {atleta_1}", f" - {atleta_2}")
        )

        # 📊 Grafico di Confronto delle Posizioni
        if not comuni.empty:
            comuni["Gara"] = (
                comuni["Year"].astype(str) + " - " +
                comuni["Event"]
            )

            # Ordina le gare per anno
            comuni = comuni.sort_values("Year")
           # Verifica che le colonne "Position" esistano
            position_col_1 = f"position - {atleta_1}"
            position_col_2 = f"position - {atleta_2}"

            if position_col_1 in comuni.columns and position_col_2 in comuni.columns:
                comuni[position_col_1] = pd.to_numeric(comuni[position_col_1], errors="coerce")
                comuni[position_col_2] = pd.to_numeric(comuni[position_col_2], errors="coerce")
                comuni = comuni.dropna(subset=[position_col_1, position_col_2])

                # Crea il grafico
                fig, ax = plt.subplots(figsize=(14, 7))

                sns.set_style("whitegrid")  # Sfondo a griglia
                palette = sns.color_palette("Set2", 2)  # Palette colori carina

                sns.lineplot(
                    data=comuni, x="Gara", y=position_col_1,
                    marker='o', label=atleta_1, ax=ax, linewidth=2.5, color=palette[0]
                )
                sns.lineplot(
                    data=comuni, x="Gara", y=position_col_2,
                    marker='s', label=atleta_2, ax=ax, linewidth=2.5, color=palette[1]
                )

                # Etichette dei punti (opzionale, ma utile per pochi dati)
                for i, row in comuni.iterrows():
                    ax.text(row["Gara"], row[position_col_1] + 0.2, f"{int(row[position_col_1])}", color=palette[0], fontsize=8, ha='center')
                    ax.text(row["Gara"], row[position_col_2] - 0.3, f"{int(row[position_col_2])}", color=palette[1], fontsize=8, ha='center')

                ax.set_title(f"📈 Confronto Posizioni Classifica: {atleta_1} vs {atleta_2}", fontsize=16)
                ax.set_ylabel("Posizione (1° in basso)", fontsize=12)
                ax.set_xlabel("Gara", fontsize=12)
                ax.tick_params(axis='x', rotation=35)
                ax.invert_yaxis()
                ax.legend(title="Atleti", loc="upper right", fontsize=10)
                ax.grid(True, which='major', linestyle='--', alpha=0.5)
                ax.invert_yaxis()

                fig.tight_layout()
                st.pyplot(fig)
            else:
                st.warning("⚠️ Le colonne di posizione non sono presenti nei dati.")

        else:
            st.write("⚠️ Nessuna gara in comune trovata tra i due atleti.")


elif page == "Dashboard Atleta":
    st.title("📊 Dashboard Personalizzata Atleta")

    all_athletes = get_all_athletes()
    atleta = st.selectbox("Seleziona un atleta", all_athletes)

    if atleta:
        data = get_athlete_events(atleta)
        data = clean_results(data)  # funzione già definita per esplodere 'Result'

        st.subheader(f"🔍 Cosa vuoi visualizzare per {atleta}?")

        show_positions = st.checkbox("📈 Andamento delle Posizioni")
        show_medals = st.checkbox("🥇 Medagliere")
        show_records = st.checkbox("🏁 Migliori Prestazioni")

        if show_positions:
            st.markdown("### 📈 Posizioni nel tempo")
            show_positions_chart(data, atleta)

        if show_medals:
            st.markdown("### 🥇 Medagliere")
            show_medal_count(data)

        if show_records:
            st.markdown("### 🏁 Migliori Prestazioni")
            show_top_results(data)
