import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import requests
import os

from dotenv import load_dotenv

load_dotenv()

RAPID_API_KEY = os.getenv("RAPID_API_KEY")

st.set_page_config(layout="wide")



live_url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
recent_url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/recent"
series_url = "https://cricbuzz-cricket.p.rapidapi.com/series/{match_id}/international"
scorecard_over_url = "https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/%7BmatchId%7D/overs"
scorecard_url = "https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}/scard"
player_search_url = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/search"
player_bowling_url = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}/bowling"
player_batting_url = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}/batting"
player_stats_url = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}"


RAPID_API_KEY =os.getenv("RAPID_API_KEY")

HEADERS = {
	"X-RapidAPI-Key": RAPID_API_KEY,
	"X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
}


@st.cache_resource
def get_connection():
    conn=psycopg2.connect(
        host="localhost",
        dbname="project",
        user="postgres",
        password=os.getenv("DB_PASSWORD")
        )

    conn.autocommit=True
    return conn

#For live fetching from API


def show_live_matches():

    # ----------------------------------
    # Fetch Live Matches
    # ----------------------------------
    response = requests.get(live_url, headers=HEADERS)
    data = response.json()

    matches = []

    for match_type in data.get("typeMatches", []):
        for series in match_type.get("seriesMatches", []):

            wrapper = series.get("seriesAdWrapper")
            if not wrapper:
                continue

            for match in wrapper.get("matches", []):

                info = match.get("matchInfo", {})

                match_data = {
                    "match_id": info.get("matchId"),
                    "team1": info.get("team1", {}).get("teamName"),
                    "team2": info.get("team2", {}).get("teamName"),
                    "state": info.get("state"),
                    "status": info.get("status"),
                    "format": info.get("matchFormat"),
                    "venue": info.get("venueInfo", {}).get("ground"),
                    "city": info.get("venueInfo", {}).get("city"),
                    "match_date": info.get("startDate")
                }

                matches.append(match_data)

    # ----------------------------------
    # STEP 3 — SELECT MATCH
    # ----------------------------------
    st.header("⚡ Choose a Match")

    if not matches:
        st.warning("No matches available")
        return

    live_matches = [m for m in matches if m["state"] != "Complete"]
    completed_matches = [m for m in matches if m["state"] == "Complete"]

    match_options = {}

    # LIVE
    for m in live_matches:
        label = f"🔴 LIVE | {m['team1']} vs {m['team2']} ({m['format']})"
        match_options[label] = m

    # COMPLETED
    for m in completed_matches:
        label = f"✅ COMPLETED | {m['team1']} vs {m['team2']} ({m['format']})"
        match_options[label] = m

    selected_label = st.selectbox(
        "Choose a Match",
        list(match_options.keys())
    )

    selected_match = match_options[selected_label]

    team1 = selected_match["team1"]
    team2 = selected_match["team2"]

    # ----------------------------------
    # MATCH DETAILS UI ✅ (UPGRADED)
    # ----------------------------------
    st.markdown("---")
    st.subheader("📋 Match Details")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"🏏 *Teams:* {selected_match['team1']} vs {selected_match['team2']}")
        st.markdown(f"🎯 *Format:* {selected_match['format']}")
        st.markdown(f"📡 *State:* {selected_match['state']}")

    with col2:
        st.markdown(f"🏟️ *Venue:* {selected_match['venue']}")
        st.markdown(f"🌆 *City:* {selected_match['city']}")
        

    st.info(f"🧾 Status: {selected_match['status']}")

    # IMPORTANT FOR NEXT STEP (Scorecard)
    selected_match_id = selected_match["match_id"]

    
    #return selected_match_id  #correct

    # =====================================
# STEP 5 — Scorecard API Check
# =====================================



# Create final scorecard URL
    final_scorecard_url = scorecard_url.format(
    match_id=selected_match_id
)

# API Call
    response = requests.get(final_scorecard_url, headers=HEADERS)

    if response.status_code != 200:
        st.error("Scorecard API Failed")
        return

    scorecard_data = response.json()




    # =====================================
# STEP 6 — Extract Innings
# =====================================


# Get innings list safely
    innings_list = scorecard_data.get("scorecard", [])

    if not innings_list:
        st.warning("Scorecard not available yet — Match innings not started")
        return


# -----------------------------
# Innings 1
# -----------------------------
    innings_1 = innings_list[0] if len(innings_list) > 0 else {}

    batting_1 = innings_1.get("batsman", [])
    bowling_1 = innings_1.get("bowler", [])


# -----------------------------
# Innings 2
# -----------------------------
    innings_2 = innings_list[1] if len(innings_list) > 1 else {}

    batting_2 = innings_2.get("batsman", [])
    bowling_2 = innings_2.get("bowler", [])


# =====================================
# STEP 7 — Innings 1 Batting Table
# =====================================

    st.header("📝 Scorecard")

    innings1_batting_team = team1
    innings1_bowling_team = team2

    innings2_batting_team = team2
    innings2_bowling_team = team1

    tab1,tab2=st.tabs([  "🔥First Innings ",
    "🔥Second Innings "])

    with tab1:
     
        st.markdown(
    f"""
    <div style="font-size:26px; font-weight:600;">
        🏏 {innings1_batting_team.upper()} — Batting
    </div>

    <div style="font-size:20px; font-weight:700; margin-top:6px;">
        ⚡ {innings1_bowling_team} Bowling
    </div>
    """,
    unsafe_allow_html=True

)
        
        st.subheader("🏏 Batting")
        if batting_1:

            batting_df_1 = pd.DataFrame(batting_1)

    # Select important columns
            batting_df_1 = batting_df_1[
        [
            "name",
            "runs",
            "balls",
            "fours",
            "sixes",
            "strkrate",
            "outdec"
        ]
    ]

            batting_df_1.columns = [
        "Batter",
        "Runs",
        "Balls",
        "4s",
        "6s",
        "Strike Rate",
        "Dismissal"
    ]

            st.dataframe(
        batting_df_1,
        use_container_width=True
    )

        else:
            st.info("Innings 1 batting not available yet")



        st.subheader("🏐 Bowling")

        if bowling_1:

            bowling_df_1 = pd.DataFrame(bowling_1)

            bowling_df_1 = bowling_df_1[
        [
            "name",
            "overs",
            "maidens",
            "runs",
            "wickets",
            "economy"
        ]
    ]

            bowling_df_1.columns = [
        "Bowler",
        "Overs",
        "Maidens",
        "Runs",
        "Wickets",
        "Economy"
    ]

            st.dataframe(
        bowling_df_1,
        use_container_width=True
    )

        else:
            st.info("Innings 1 bowling not available yet")

     
# STEP 9 — Innings 2 Batting
# =====================================
    with tab2:
        
        st.markdown(
    f"""
    <div style="font-size:26px; font-weight:600;">
        🏏 {innings2_batting_team.upper()} — Batting
    </div>

    <div style="font-size:20px; font-weight:700; margin-top:6px;">
        ⚡ {innings2_bowling_team} Bowling
    </div>
    """,
    unsafe_allow_html=True
)
        st.subheader("🏏 Batting")

        if batting_2:

            batting_df_2 = pd.DataFrame(batting_2)

            batting_df_2 = batting_df_2[
        [
            "name",
            "runs",
            "balls",
            "fours",
            "sixes",
            "strkrate",
            "outdec"
        ]
    ]

            batting_df_2.columns = [
        "Batter",
        "Runs",
        "Balls",
        "4s",
        "6s",
        "Strike Rate",
        "Dismissal"
    ]

            st.dataframe(
        batting_df_2,
        use_container_width=True
    )

        else:
            st.info("Innings 2 batting not available yet")

        st.subheader("🏐 Bowling")

        if bowling_2:

            bowling_df_2 = pd.DataFrame(bowling_2)

            bowling_df_2 = bowling_df_2[
        [
            "name",
            "overs",
            "maidens",
            "runs",
            "wickets",
            "economy"
        ]
    ]

            bowling_df_2.columns = [
        "Bowler",
        "Overs",
        "Maidens",
        "Runs",
        "Wickets",
        "Economy"
    ]

            st.dataframe(
        bowling_df_2,
        use_container_width=True
    )

        else:
            st.info("Innings 2 bowling not available yet")

######################################################

def fetch_player_stats(player_id):

    url = player_stats_url.format(player_id=player_id)

    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        st.error("Player profile fetch failed")
        return pd.DataFrame()

    data = response.json()

    player_info = {
        "Name": data.get("name"),
        "Role": data.get("role"),
        "Batting Style": data.get("bat"),
        "Bowling Style": data.get("bowl"),
        "Country": data.get("intlTeam"),
        "DOB": data.get("DoB"),
        "Birth Place": data.get("birthPlace")
    }

    return pd.DataFrame([player_info])



def fetch_player_batting(player_id):

    try:
        url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}/batting"

        response = requests.get(url, headers=HEADERS)
        data = response.json()

        rows = []

        # Cricbuzz structure parsing
        for block in data.get("values", []):
            vals = block.get("values", [])

            if len(vals) >= 5:
                rows.append(vals[:5])

        if not rows:
            return pd.DataFrame()

        batting_df = pd.DataFrame(
            rows,
            columns=["Stat", "Test", "ODI", "T20", "IPL"]
        )

        return batting_df

    except Exception as e:
        print("Batting Fetch Error:", e)
        return pd.DataFrame()


def fetch_player_bowling(player_id):

    try:
        url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}/bowling"

        response = requests.get(url, headers=HEADERS)
        data = response.json()

        rows = []

        for block in data.get("values", []):
            vals = block.get("values", [])

            if len(vals) >= 5:
                rows.append(vals[:5])

        if not rows:
            return pd.DataFrame()

        bowling_df = pd.DataFrame(
            rows,
            columns=["Stat", "Test", "ODI", "T20", "IPL"]
        )

        return bowling_df

    except Exception as e:
        print("Bowling Fetch Error:", e)
        return pd.DataFrame()
    

def batting_summary(df):

    try:
        df = df.copy()

        # Ensure first column is Stat
        if "Stat" not in df.columns:
            df.rename(columns={df.columns[0]: "Stat"}, inplace=True)

        df.set_index("Stat", inplace=True)

        # ✅ Convert API strings → numbers
        df = df.apply(pd.to_numeric, errors="coerce")

        summary = {
            "Matches": int(df.loc["Matches"].sum()),
            "Runs": int(df.loc["Runs"].sum()),
            "Average": round(df.loc["Average"].mean(), 2),
            "Strike Rate": round(df.loc["SR"].mean(), 2)
        }

        return summary

    except Exception as e:
        print("Batting Summary Error:", e)
        return None
    



def bowling_summary(df):

    try:
        if df is None or df.empty:
            return None

        df = df.copy()

        # Ensure Stat column exists
        if "Stat" not in df.columns:
            df.rename(columns={df.columns[0]: "Stat"}, inplace=True)

        df.set_index("Stat", inplace=True)

        # Convert numeric safely
        df = df.apply(pd.to_numeric, errors="coerce")

        summary = {
            "Matches": int(df.loc["Matches"].sum()) if "Matches" in df.index else 0,
            "Wickets": int(df.loc["Wickets"].sum()) if "Wickets" in df.index else 0,
            "Average": round(df.loc["Average"].mean(), 2) if "Average" in df.index else 0,
            "Economy": round(df.loc["Econ"].mean(), 2) if "Econ" in df.index else 0
        }

        return summary

    except Exception as e:
        print("Bowling Summary Error:", e)
        return None
    


def fetch_matches():
    conn=get_connection()
    cur=conn.cursor()
    
    quer="""select name,batting_style,bowling_style from indian_team_players;"""
    cur.execute(quer)
    row=cur.fetchall()

    columns=[desc[0] for desc in cur.description]

    cur.close()
    return pd.DataFrame(row,columns=columns)





def fetch_match_1():
    conn=get_connection()
    cur=conn.cursor()

    quer_2="""select * from recent_matches;"""
    cur.execute(quer_2)
    rows_2=cur.fetchall()

    columns=[desc[0] for desc in cur.description]

    cur.close()
    return pd.DataFrame(rows_2,columns=columns)



def fetch_matches_3():
    conn=get_connection()
    cur=conn.cursor()

    quer_3="""select player_name,matches,innings,runs,average from odi_top_10_q3;"""
    cur.execute(quer_3)
    row_3=cur.fetchall()

    columns=[desc[0] for desc in cur.description]

    cur.close()
    return pd.DataFrame(row_3,columns=columns)



def fetch_matches_4():
    conn=get_connection()
    cur=conn.cursor()

    quer_4="""select * from venue_dets_q4 order by Capacity desc;"""
    cur.execute(quer_4)
    row_4=cur.fetchall()

    columns=[desc[0] for desc in cur.description]

    cur.close()
    return pd.DataFrame(row_4,columns=columns)


def fetch_matches_5():
    conn=get_connection()
    cur=conn.cursor()

    quer_5="""select * from points_table_q5;"""
    cur.execute(quer_5)
    row_5=cur.fetchall()

    columns=[desc[0] for desc in cur.description]

    cur.close()
    return pd.DataFrame(row_5,columns=columns)


def fetch_matches_6():
    conn=get_connection()
    cur=conn.cursor()

    quer_6="""select Role, count(*) from each_prole_q6 group by Role;"""
    cur.execute(quer_6)
    row_6=cur.fetchall()

    columns=[desc[0] for desc in cur.description]

    cur.close()
    return pd.DataFrame(row_6,columns=columns)


def fetch_matches_7():

    conn = get_connection()
    cur = conn.cursor()

    query_test = """
    SELECT * FROM batting_scores_q7
    WHERE Match_format = 'Test';
    """

    query_odi = """
    SELECT * FROM batting_scores_q7
    WHERE Match_format = 'ODI';
    """

    query_t20 = """
    SELECT * FROM batting_scores_q7
    WHERE Match_format = 'T20';
    """

    
    cur.execute(query_test)
    test_rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    df_test = pd.DataFrame(test_rows, columns=columns)

    cur.execute(query_odi)
    odi_rows = cur.fetchall()
    df_odi = pd.DataFrame(odi_rows, columns=columns)


    cur.execute(query_t20)
    t20_rows = cur.fetchall()
    df_t20 = pd.DataFrame(t20_rows, columns=columns)

    cur.close()

    return df_test, df_odi, df_t20


def fetch_matches_8():
    conn=get_connection()
    cur=conn.cursor()

    quer_8="""select *, count(*) over (partition by series_name)as total_matches from series_2024_q9;"""
    cur.execute(quer_8)
    row_8=cur.fetchall()

    columns=[desc[0] for desc in cur.description]

    cur.close()
    return pd.DataFrame(row_8,columns=columns)


def fetch_matches_9():
    conn=get_connection()
    cur=conn.cursor()

    quer_9="""select s.player_name,s.Format,s.total_wickets,m.total_runs from (select player_name,Format, sum(Wickets) as total_wickets from allrounder_q9 group by player_name,Format)s left join (select player_name,Format,sum(runs) as total_runs from allrounder_bat_q9 group by player_name,Format)m on s.player_name=m.player_name and s.Format=m.Format order by player_name;"""

    cur.execute(quer_9)
    row_9=cur.fetchall()  

    columns=[desc[0] for desc in cur.description]

    cur.close()
    return pd.DataFrame(row_9,columns=columns)





def Recent_10():
    conn=get_connection()
    cur=conn.cursor()

    quer_9="""select * from Recent_20_matches order by start_date desc limit 20; """

    cur.execute(quer_9)
    row_9=cur.fetchall()  

    columns=[desc[0] for desc in cur.description]

    cur.close()
    return pd.DataFrame(row_9,columns=columns)

def fetch_player_format_comparison():

    conn = get_connection()
    cur = conn.cursor()

    query = """
    WITH filtered AS (
        SELECT
            player_id,
            format,
            runs,
            average
        FROM players_batt_q11
        WHERE format IN ('Test','ODI','T20')
    ),

    multi_format_players AS (
        SELECT player_id
        FROM filtered
        GROUP BY player_id
        HAVING COUNT(DISTINCT format) >= 2
    )

    SELECT
        f.player_id,

        SUM(CASE WHEN format='Test' THEN runs END) AS test_runs,
        AVG(CASE WHEN format='Test' THEN average END) AS test_avg,

        SUM(CASE WHEN format='ODI' THEN runs END) AS odi_runs,
        AVG(CASE WHEN format='ODI' THEN average END) AS odi_avg,

        SUM(CASE WHEN format='T20' THEN runs END) AS t20_runs,
        AVG(CASE WHEN format='T20' THEN average END) AS t20_avg,

        ROUND(AVG(average),2) AS overall_avg

    FROM filtered f
    JOIN multi_format_players m
        ON f.player_id = m.player_id

    GROUP BY f.player_id
    ORDER BY overall_avg DESC;
    """

    cur.execute(query)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    df = pd.DataFrame(rows, columns=cols)

    return df


def fetch_matches_table():

    conn = get_connection()
    cur = conn.cursor()

    query_121 = """
    SELECT *
    FROM away_q12;
    """

    cur.execute(query_121)

    rows_121 = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    cur.close()

    return pd.DataFrame(rows_121, columns=columns)


def fetch_away_wins():

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT COUNT(*)
        FROM away_q12
        WHERE results ILIKE 'india won%'
    """

    cur.execute(query)

    wins = cur.fetchone()[0]

    cur.close()

    return wins


def fetch_home_table():

    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM home_q12"

    cur.execute(query)

    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    cur.close()

    return pd.DataFrame(rows, columns=columns)

def fetch_home_wins():

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT COUNT(*)
        FROM home_q12
        WHERE results ILIKE 'india won%'
    """

    cur.execute(query)

    wins = cur.fetchone()[0]

    cur.close()

    return wins


def fetch_scorecard_13():

    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM partnership_13"

    cur.execute(query)

    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    cur.close()

    return pd.DataFrame(rows, columns=columns)








def fetch_partnership_100():

    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT *
    FROM (
        SELECT
            innings,
            player_name AS batter_1,

            LEAD(player_name) OVER (
                PARTITION BY innings
                ORDER BY rn
            ) AS batter_2,

            runs_scored +
            LEAD(runs_scored) OVER (
                PARTITION BY innings
                ORDER BY rn
            ) AS partnership_runs

        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY innings
                       ORDER BY innings
                   ) AS rn
            FROM partnership_13
        ) ordered_players
    ) t
    WHERE partnership_runs >= 100;
    """

    cur.execute(query)

    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    cur.close()

    return pd.DataFrame(rows, columns=columns)



def bowlers_14():

    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM question_14"

    cur.execute(query)

    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    cur.close()

    return pd.DataFrame(rows, columns=columns)


def analytics_14(df):

    result = (
        df[df["overs"] >= 4]
        .groupby("player_name")
        .agg(
            total_wickets=("wickets_taken", "sum"),
            avg_economy=("economy_rate", "mean"),
            total_matches=("venue", "count")
        )
        .reset_index()
    )

    return result[result["total_matches"] >= 3]


def get_match_scorecard(match_id):

    query = f"""
    SELECT
        player_name,
        team_name,
        innings,
        runs_scored
    FROM SA_match1
    WHERE Match_id = '{match_id}'
    ORDER BY innings, team_name;
    """

    conn = get_connection()
    df = pd.read_sql(query, conn)

    return df

def get_top_performers(match_id):

    query = f"""
    SELECT
        player_name,
        team_name,
        runs_scored,
        CASE
            WHEN LOWER(TRIM(team_name)) =
                 LOWER(TRIM(
                    (SELECT winner
                     FROM sa_match1
                     WHERE match_id = '{match_id}'
                     LIMIT 1)
                 ))
            THEN 1
            ELSE 0
        END AS match_result
    FROM sa_match1
    WHERE match_id = '{match_id}'
    ORDER BY runs_scored DESC
    LIMIT 5;
    """

    conn = get_connection()
    df = pd.read_sql(query, conn)

    return df


def get_match_teams(match_id):

    query = f"""
        SELECT DISTINCT team_name
        FROM sa_match1
        WHERE match_id = '{match_id}'
    """

    conn = get_connection()
    df = pd.read_sql(query, conn)

    return df["team_name"].tolist()


def get_match_result(match_id):

    query = f"""
        SELECT DISTINCT match_status
        FROM sa_match1
        WHERE match_id = '{match_id}'
        LIMIT 1
    """

    conn = get_connection()
    df = pd.read_sql(query, conn)

    return df.iloc[0]["match_status"]



def get_player_avg_runs():
    
    query = """
        SELECT
            player_name,
            year,
            COUNT(*) AS matches_played,
            ROUND(AVG(runs_scored),2) AS avg_runs
        FROM batters_per_q16_new
        GROUP BY player_name, year
        HAVING COUNT(*) >= 5
        ORDER BY player_name, year
    """

    conn = get_connection()
    df = pd.read_sql(query, conn)

    return df


def fetch_q17_full_table():

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT
            team_01,
            team_02,
            series_name,
            toss_status,
            match_status
        FROM winners_q17
        ORDER BY series_name;
    """

    cur.execute(query)

    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    cur.close()

    return pd.DataFrame(rows, columns=columns)


def fetch_q17():
    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT
        toss_decision,
        COUNT(*) AS total_matches,

        SUM(
            CASE
                WHEN toss_winner = match_winner THEN 1
                ELSE 0
            END
        ) AS toss_winner_wins,

        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN toss_winner = match_winner THEN 1
                    ELSE 0
                END
            ) / COUNT(*),2
        ) AS win_percentage

    FROM (
        SELECT
            split_part(toss_status,' opt',1) AS toss_winner,

            CASE
                WHEN match_status LIKE 'IND%' THEN 'India'
                WHEN match_status LIKE 'NZ%' THEN 'New Zealand'
                WHEN match_status LIKE 'RSA%' THEN 'South Africa'
                WHEN match_status LIKE 'AUS%' THEN 'Australia'
                WHEN match_status LIKE 'AFG%' THEN 'Afghanistan'
                WHEN match_status LIKE 'PAK%' THEN 'Pakistan'
                WHEN match_status LIKE 'BAN%' THEN 'Bangladesh'
                WHEN match_status LIKE 'ENG%' THEN 'England'
            END AS match_winner,

            CASE
                WHEN toss_status ILIKE '%bat%' THEN 'Bat First'
                WHEN toss_status ILIKE '%bowl%' THEN 'Bowl First'
            END AS toss_decision

        FROM winners_q17
    ) t

    GROUP BY toss_decision
    ORDER BY toss_decision;
    """

    cur.execute(query)
    rows = cur.fetchall()

    columns = [desc[0] for desc in cur.description]
    cur.close()

    return pd.DataFrame(rows, columns=columns)



def get_economical_bowlers():

    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT
        player_name,
        match_format,
        COUNT(*) AS matches_played,
        ROUND(AVG(overs),2) AS avg_overs,
        ROUND(AVG(economy),2) AS economy_rate,
        SUM(wickets) AS total_wickets
    FROM bow_18
    WHERE match_format IN ('ODI','T20')
    GROUP BY player_name, match_format
    HAVING COUNT(*) >= 5
       AND AVG(overs) >= 2
    ORDER BY economy_rate ASC;
    """

    cur.execute(query)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    df = pd.DataFrame(rows, columns=cols)

    cur.close()

    return df


def get_consistent_batsmen():

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT
            player_name,
            ROUND(AVG(runs_score),2) AS avg_runs,
            ROUND(STDDEV(runs_score),2) AS runs_std_dev
        FROM batters_q19
        GROUP BY player_name
        ORDER BY runs_std_dev ASC;
    """

    cur.execute(query)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    df = pd.DataFrame(rows, columns=cols)

    cur.close()

    return df


def get_yearly_consistency():

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT
            player_name,
            year,
            ROUND(STDDEV(runs_score),2) AS runs_std_dev
        FROM batters_q19
        GROUP BY player_name, year
        ORDER BY player_name, year;
    """

    cur.execute(query)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    df = pd.DataFrame(rows, columns=cols)

    cur.close()

    return df



def get_player_format_analysis():

    conn = get_connection()
    cur = conn.cursor()

    query = """ 
    SELECT
        player_name,
        player_id,

        MAX(CASE WHEN categories='Matches' THEN Test END) AS test_matches,
        MAX(CASE WHEN categories='Matches' THEN ODI END)  AS odi_matches,
        MAX(CASE WHEN categories='Matches' THEN T20 END)  AS t20_matches,

        MAX(CASE WHEN categories='Average' THEN Test END) AS test_avg,
        MAX(CASE WHEN categories='Average' THEN ODI END)  AS odi_avg,
        MAX(CASE WHEN categories='Average' THEN T20 END)  AS t20_avg

    FROM question_20
    GROUP BY player_name, player_id
    HAVING
        (
            MAX(CASE WHEN categories='Matches' THEN Test END) +
            MAX(CASE WHEN categories='Matches' THEN ODI END) +
            MAX(CASE WHEN categories='Matches' THEN T20 END)
        ) >= 20
    ORDER BY player_name;
    """

    cur.execute(query)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    df = pd.DataFrame(rows, columns=cols)

    cur.close()
    return df


def get_t20_rankings():

    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT
        player_name,

        ROUND(
            (
                COALESCE(MAX(CASE WHEN categories='Runs' THEN t20 END),0) * 0.01 +
                COALESCE(MAX(CASE WHEN categories='Average' THEN t20 END),0) * 0.5 +
                COALESCE(MAX(CASE WHEN categories='SR' THEN t20 END),0) * 0.3
            )
            +
            (
                COALESCE(MAX(CASE WHEN categories='Wickets' THEN t20 END),0) * 2 +
                (50 - COALESCE(MAX(CASE WHEN categories='Avg' THEN t20 END),50)) * 0.5 +
                (6 - COALESCE(MAX(CASE WHEN categories='Eco' THEN t20 END),6)) * 2
            )
        ,2) AS score,

        RANK() OVER (
            ORDER BY
            ROUND(
                (
                    COALESCE(MAX(CASE WHEN categories='Runs' THEN t20 END),0) * 0.01 +
                    COALESCE(MAX(CASE WHEN categories='Average' THEN t20 END),0) * 0.5 +
                    COALESCE(MAX(CASE WHEN categories='SR' THEN t20 END),0) * 0.3
                )
                +
                (
                    COALESCE(MAX(CASE WHEN categories='Wickets' THEN t20 END),0) * 2 +
                    (50 - COALESCE(MAX(CASE WHEN categories='Avg' THEN t20 END),50)) * 0.5 +
                    (6 - COALESCE(MAX(CASE WHEN categories='Eco' THEN t20 END),6)) * 2
                )
            ,2) DESC
        ) AS rank

    FROM ranking_21
    GROUP BY player_name
    ORDER BY rank;
    """

    cur.execute(query)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    df = pd.DataFrame(rows, columns=cols)

    cur.close()
  
    return df


def get_odi_rankings():

    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT
        player_name,

        ROUND(
            (
                COALESCE(MAX(CASE WHEN categories='Runs' THEN odi END),0) * 0.01 +
                COALESCE(MAX(CASE WHEN categories='Average' THEN odi END),0) * 0.5 +
                COALESCE(MAX(CASE WHEN categories='SR' THEN odi END),0) * 0.3
            )
            +
            (
                COALESCE(MAX(CASE WHEN categories='Wickets' THEN odi END),0) * 2 +
                (50 - COALESCE(MAX(CASE WHEN categories='Avg' THEN odi END),50)) * 0.5 +
                (6 - COALESCE(MAX(CASE WHEN categories='Eco' THEN odi END),6)) * 2
            )
        ,2) AS score,

        RANK() OVER (
            ORDER BY
            ROUND(
                (
                    COALESCE(MAX(CASE WHEN categories='Runs' THEN odi END),0) * 0.01 +
                    COALESCE(MAX(CASE WHEN categories='Average' THEN odi END),0) * 0.5 +
                    COALESCE(MAX(CASE WHEN categories='SR' THEN odi END),0) * 0.3
                )
                +
                (
                    COALESCE(MAX(CASE WHEN categories='Wickets' THEN odi END),0) * 2 +
                    (50 - COALESCE(MAX(CASE WHEN categories='Avg' THEN odi END),50)) * 0.5 +
                    (6 - COALESCE(MAX(CASE WHEN categories='Eco' THEN odi END),6)) * 2
                )
            ,2) DESC
        ) AS rank

    FROM ranking_21
    GROUP BY player_name
    ORDER BY rank;
    """

    cur.execute(query)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    df = pd.DataFrame(rows, columns=cols)

    cur.close()
    

    return df

def get_test_rankings():

    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT
        player_name,

        ROUND(
            (
                COALESCE(MAX(CASE WHEN categories='Runs' THEN test END),0) * 0.01 +
                COALESCE(MAX(CASE WHEN categories='Average' THEN test END),0) * 0.5 +
                COALESCE(MAX(CASE WHEN categories='SR' THEN test END),0) * 0.3
            )
            +
            (
                COALESCE(MAX(CASE WHEN categories='Wickets' THEN test END),0) * 2 +
                (50 - COALESCE(MAX(CASE WHEN categories='Avg' THEN test END),50)) * 0.5 +
                (6 - COALESCE(MAX(CASE WHEN categories='Eco' THEN test END),6)) * 2
            )
        ,2) AS score,

        RANK() OVER (
            ORDER BY
            ROUND(
                (
                    COALESCE(MAX(CASE WHEN categories='Runs' THEN test END),0) * 0.01 +
                    COALESCE(MAX(CASE WHEN categories='Average' THEN test END),0) * 0.5 +
                    COALESCE(MAX(CASE WHEN categories='SR' THEN test END),0) * 0.3
                )
                +
                (
                    COALESCE(MAX(CASE WHEN categories='Wickets' THEN test END),0) * 2 +
                    (50 - COALESCE(MAX(CASE WHEN categories='Avg' THEN test END),50)) * 0.5 +
                    (6 - COALESCE(MAX(CASE WHEN categories='Eco' THEN test END),6)) * 2
                )
            ,2) DESC
        ) AS rank

    FROM ranking_21
    GROUP BY player_name
    ORDER BY rank;
    """

    cur.execute(query)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    df = pd.DataFrame(rows, columns=cols)

    cur.close()

    return df

def fetch_head_to_head_prediction():

    conn = get_connection()
    cur = conn.cursor()

    query = """
    WITH base AS (

        SELECT
            team_1,
            team_2,
            venue_info,
            toss_status,
            match_result_t1,

            CAST(
                REGEXP_REPLACE(winning_margin,'[^0-9]','','g')
                AS INTEGER
            ) AS win_margin,

            CASE
                WHEN LOWER(match_result_t1) LIKE '%gujarat%'
                     OR LOWER(match_result_t1) LIKE '%gt%'
                THEN 'Gujarat Titans'

                WHEN LOWER(match_result_t1) LIKE '%mumbai%'
                     OR LOWER(match_result_t1) LIKE '%mi%'
                THEN 'Mumbai Indians'
            END AS winner

        FROM question_22
    ),

    pair_matches AS (
        SELECT
            LEAST(team_1,team_2) AS team_a,
            GREATEST(team_1,team_2) AS team_b,
            *
        FROM base
    ),

    filtered_pairs AS (
        SELECT team_a,team_b
        FROM pair_matches
        GROUP BY team_a,team_b
        HAVING COUNT(*) >= 1
    )

    SELECT
        p.team_a,
        p.team_b,

        COUNT(*) AS total_matches,

        SUM(CASE WHEN p.winner=p.team_a THEN 1 ELSE 0 END)
            AS team_a_wins,

        SUM(CASE WHEN p.winner=p.team_b THEN 1 ELSE 0 END)
            AS team_b_wins,

        ROUND(
            100.0 *
            SUM(CASE WHEN p.winner=p.team_a THEN 1 ELSE 0 END)
            / COUNT(*),2
        ) AS team_a_win_pct,

        ROUND(
            100.0 *
            SUM(CASE WHEN p.winner=p.team_b THEN 1 ELSE 0 END)
            / COUNT(*),2
        ) AS team_b_win_pct,

        AVG(
            CASE WHEN p.winner=p.team_a
            THEN p.win_margin END
        ) AS team_a_avg_margin,

        AVG(
            CASE WHEN p.winner=p.team_b
            THEN p.win_margin END
        ) AS team_b_avg_margin,

        SUM(
            CASE
                WHEN LOWER(p.toss_status) LIKE '%bat%'
                     AND p.winner IS NOT NULL
                THEN 1 ELSE 0
            END
        ) AS bat_first_wins,

        SUM(
            CASE
                WHEN LOWER(p.toss_status) LIKE '%bowl%'
                     AND p.winner IS NOT NULL
                THEN 1 ELSE 0
            END
        ) AS bowl_first_wins

    FROM pair_matches p
    JOIN filtered_pairs f
        ON p.team_a=f.team_a
       AND p.team_b=f.team_b

    GROUP BY p.team_a,p.team_b
    ORDER BY total_matches DESC;
    """

    cur.execute(query)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    df = pd.DataFrame(rows, columns=cols)

    return df

def get_player_form():

    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT 
        batters_name,

        ROUND(AVG(
            CASE WHEN match_id >= 6 
            THEN runs_scored END
        ),2) AS avg_last_5,

        ROUND(AVG(runs_scored),2) AS avg_last_10,

        ROUND(AVG(
            CASE WHEN match_id >= 6 
            THEN strike_rate END
        ),2) AS sr_last_5,

        ROUND(AVG(strike_rate),2) AS sr_last_10,

        ROUND(STDDEV(runs_scored),2) AS consistency_score,

        -- ✅ NEW REQUIREMENT
        SUM(
            CASE 
                WHEN runs_scored >= 50 THEN 1
                ELSE 0
            END
        ) AS fifties_last_10,

        CASE
            WHEN AVG(runs_scored) >= 50 
                 AND STDDEV(runs_scored) <= 15
                THEN 'Excellent Form'

            WHEN AVG(runs_scored) >= 35
                THEN 'Good Form'

            WHEN AVG(runs_scored) >= 20
                THEN 'Average Form'

            ELSE 'Poor Form'
        END AS player_form

    FROM q2324
    GROUP BY batters_name
    ORDER BY avg_last_5 DESC;
    """

    cur.execute(query)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    df = pd.DataFrame(rows, columns=cols)

    cur.close()


    return df

def get_partnership_analysis():

    conn = get_connection()
    cur = conn.cursor()

    query = """
    WITH batting_order AS (

        SELECT
            match_id,
            batters_name,
            runs_scored,

            ROW_NUMBER() OVER(
                PARTITION BY match_id
                ORDER BY match_date, batters_name
            ) AS batting_pos

        FROM q2324
    ),

    partnerships AS (

        SELECT
            a.match_id,
            a.batters_name AS player_1,
            b.batters_name AS player_2,

            (a.runs_scored + b.runs_scored)
                AS partnership_runs

        FROM batting_order a
        JOIN batting_order b
          ON a.match_id = b.match_id
         AND a.batting_pos + 1 = b.batting_pos
    ),

    partnership_stats AS (

        SELECT
            player_1,
            player_2,

            COUNT(*) AS total_partnerships,

            ROUND(AVG(partnership_runs),2)
                AS avg_partnership_runs,

            MAX(partnership_runs)
                AS highest_partnership,

            COUNT(
                CASE WHEN partnership_runs >= 50
                THEN 1 END
            ) AS partnerships_above_50,

            ROUND(
                COUNT(
                    CASE WHEN partnership_runs >= 50
                    THEN 1 END
                ) * 100.0 / COUNT(*),
            2) AS success_rate

        FROM partnerships
        GROUP BY player_1, player_2
    )

    SELECT *,
           RANK() OVER(
                ORDER BY success_rate DESC,
                         avg_partnership_runs DESC
           ) AS partnership_rank

    FROM partnership_stats
    ORDER BY partnership_rank;
    """

    cur.execute(query)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    df = pd.DataFrame(rows, columns=cols)

    cur.close()

    return df


def fetch_player_time_series_analysis():

    conn = get_connection()
    cur = conn.cursor()

    query = """
    WITH quarterly_stats AS (
        SELECT
            batters_name,
            quarter,
            COUNT(DISTINCT match_id) AS matches_played,
            AVG(runs_scored) AS avg_runs,
            AVG(strike_rate) AS avg_strike_rate
        FROM question_25
        GROUP BY batters_name, quarter
    ),

    filtered_players AS (
        SELECT batters_name
        FROM quarterly_stats
        WHERE matches_played >= 3
        GROUP BY batters_name
        HAVING COUNT(DISTINCT quarter) >= 6
    ),

    player_trend AS (
        SELECT
            qs.batters_name,
            qs.quarter,
            qs.avg_runs,
            qs.avg_strike_rate,

            LAG(qs.avg_runs) OVER(
                PARTITION BY qs.batters_name
                ORDER BY qs.quarter
            ) AS prev_runs

        FROM quarterly_stats qs
        JOIN filtered_players fp
        ON qs.batters_name = fp.batters_name
    ),

    performance_change AS (
        SELECT *,
            CASE
                WHEN prev_runs IS NULL THEN 0
                ELSE avg_runs - prev_runs
            END AS run_change,

            CASE
                WHEN prev_runs IS NULL THEN 'Stable'
                WHEN avg_runs > prev_runs THEN 'Improving'
                WHEN avg_runs < prev_runs THEN 'Declining'
                ELSE 'Stable'
            END AS performance_status
        FROM player_trend
    ),

    career_phase AS (
        SELECT
            batters_name,
            CASE
                WHEN AVG(run_change) > 2
                    THEN 'Career Ascending'
                WHEN AVG(run_change) < -2
                    THEN 'Career Declining'
                ELSE 'Career Stable'
            END AS career_phase
        FROM performance_change
        GROUP BY batters_name
    )

    SELECT
        pc.batters_name,
        pc.quarter,
        ROUND(pc.avg_runs,2) AS avg_runs,
        ROUND(pc.avg_strike_rate,2) AS avg_strike_rate,
        pc.performance_status,
        cp.career_phase
    FROM performance_change pc
    JOIN career_phase cp
    ON pc.batters_name = cp.batters_name
    ORDER BY pc.batters_name, pc.quarter;
    """

    cur.execute(query)

    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    cur.close()
    

    return pd.DataFrame(rows, columns=columns)

def create_player(name, batting, bowling, role):

    conn = get_connection()
    cur = conn.cursor()

    query = """
        INSERT INTO indian_team_players
        (name, batting_style, bowling_style, role)
        VALUES (%s, %s, %s, %s)
    """

    cur.execute(query, (name, batting, bowling, role))

    cur.close()


def read_players():

    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM indian_team_players"

    cur.execute(query)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    cur.close()

    return pd.DataFrame(rows, columns=cols)


def update_player(player_id, batting, bowling):

    conn = get_connection()
    cur = conn.cursor()

    query = """
        UPDATE indian_team_players
        SET batting_style=%s,
            bowling_style=%s
        WHERE player_id=%s
    """

    cur.execute(query, (batting, bowling, player_id))

    cur.close()

def delete_player(player_id):

    conn = get_connection()
    cur = conn.cursor()

    query = """
        DELETE FROM indian_team_players
        WHERE player_id=%s
    """

    cur.execute(query, (player_id,))

    cur.close()


def indian_team_players_crud():

    st.header("🛠️ Indian Team Players - CRUD Operations")

    conn = get_connection()
    cur = conn.cursor()

    operation = st.selectbox(
        "Choose Operation",
        ["Create Player", "View Players", "Update Player", "Delete Player"]
    )

    # =====================================================
    # CREATE
    # =====================================================
    if operation == "Create Player":

        st.subheader("➕ Add New Player")

        name = st.text_input("Player Name")
        role = st.text_input("Role")
        bat_style = st.text_input("Batting Style")
        bowl_style = st.text_input("Bowling Style")

        if st.button("Add Player"):

            query = """
            INSERT INTO indian_team_players
            (player_name, role, batting_style, bowling_style)
            VALUES (%s,%s,%s,%s)
            """

            cur.execute(query, (name, role, bat_style, bowl_style))
            conn.commit()

            st.success("✅ Player Added Successfully")

    # =====================================================
    # READ
    # =====================================================
    elif operation == "View Players":

        st.subheader("📋 Indian Team Squad")

        query = "SELECT * FROM indian_team_players"

        cur.execute(query)

        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]

        df = pd.DataFrame(rows, columns=cols)

        st.dataframe(df, use_container_width=True)

    # =====================================================
    # UPDATE
    # =====================================================
    elif operation == "Update Player":

        st.subheader("✏️ Update Player Details")

        player = st.text_input("Player Name to Update")

        new_role = st.text_input("New Role")
        new_bat = st.text_input("New Batting Style")
        new_bowl = st.text_input("New Bowling Style")

        if st.button("Update Player"):

            query = """
            UPDATE indian_team_players
            SET role=%s,
                batting_style=%s,
                bowling_style=%s
            WHERE player_name=%s
            """

            cur.execute(
                query,
                (new_role, new_bat, new_bowl, player)
            )

            conn.commit()

            st.success("✅ Player Updated Successfully")

    # =====================================================
    # DELETE
    # =====================================================
    elif operation == "Delete Player":

        st.subheader("🗑️ Remove Player")

        player = st.text_input("Player Name")

        if st.button("Delete Player"):

            query = """
            DELETE FROM indian_team_players
            WHERE player_name=%s
            """

            cur.execute(query, (player,))
            conn.commit()

            st.warning("⚠️ Player Deleted")




st.sidebar.title("🧭 Navigation")


live_option=None
player_option=None

menu_options = {
    "🏠 Home": "home",
    "🏏 Live Scores": "live",
    "👤 Player Stats": "player",
    "📊 SQL Analytics": "sql",
    "🛠 CRUD Operations": "crud"
}

selected_menu = st.sidebar.radio(
    "Choose below ⬇️",
    list(menu_options.keys())
)

main_menu = menu_options[selected_menu]


if main_menu == "live":

    st.title("📡 Cricbuzz Live Match Dashboard")

    show_live_matches()

    


elif main_menu == "player":

    st.title("👤 Cricket Player Statistics")

    player_name = st.text_input("Enter player name")

    if st.button("🔎 Search Player"):

        if not player_name:
            st.warning("⚠ Please enter player name")

        else:
            # ================= PLAYER SEARCH =================
            search_response = requests.get(
                player_search_url,
                headers=HEADERS,
                params={"plrN": player_name}
            )

            results = search_response.json()

            if results.get("player"):

                player_id = results["player"][0]["id"]

                st.success(
                    f"✅ Player Found: {results['player'][0]['name']}"
                )

                # ================= FETCH DATA =================
                profile_df = fetch_player_stats(player_id)
                batting_df = fetch_player_batting(player_id)
                bowling_df = fetch_player_bowling(player_id)

                tab1, tab2, tab3 = st.tabs(
                    ["👤 Profile", "🏏 Batting Stats", "🎯 Bowling Stats"]
                )

# =========================================================
# 👤 PLAYER PROFILE
# =========================================================
                with tab1:

                    if not profile_df.empty:

                        info = profile_df.iloc[0]

                        st.subheader("👤 Player Profile")

                        col1, col2 = st.columns([2,2])

                        with col1:
                            st.markdown(f"""
### 🧑 {info.get('Name','N/A')}

🎭 *Role:* {info.get('Role','N/A')}  
🏏 *Batting:* {info.get('Batting Style','N/A')}  
🎯 *Bowling:* {info.get('Bowling Style','N/A')}
""")

                        with col2:
                            st.markdown(f"""
🌍 *Country:* {info.get('Country','N/A')}  
🎂 *DOB:* {info.get('DOB','N/A')}  
📍 *Birth Place:* {info.get('Birth Place','N/A')}
""")

                    # ---------- Career Snapshot ----------
                    bat_sum = batting_summary(batting_df)
                    bowl_sum = bowling_summary(bowling_df)

                    st.markdown("---")
                    st.subheader("📊 Career Snapshot")

                    c1,c2,c3,c4,c5,c6 = st.columns(6)

                    c1.metric("📅 Matches", bat_sum.get("Matches",0))
                    c2.metric("🔥 Runs", bat_sum.get("Runs",0))
                    c3.metric("📈 Avg", bat_sum.get("Average",0))
                    c4.metric("⚡ SR", bat_sum.get("Strike Rate",0))
                    c5.metric("🎯 Wickets", bowl_sum.get("Wickets",0))
                    c6.metric("💰 Economy", bowl_sum.get("Economy",0))

                    # ---------- Intelligence ----------
                    st.markdown("---")
                    st.subheader("🧠 Player Intelligence")

                    if bowl_sum.get("Wickets",0) > bat_sum.get("Runs",0)/50:
                        role = "Bowling Dominant 🎯"
                    elif bat_sum.get("Runs",0) > 5000:
                        role = "Batting Specialist 🏏"
                    else:
                        role = "Balanced All-Rounder ⚖️"

                    st.info(f"Playing Style Prediction: *{role}*")

# =========================================================
# 🏏 BATTING TAB (STACKED CLEAN ALIGNMENT)
# =========================================================
                with tab2:

                    st.subheader("🏏 Format-wise Batting Performance")

                    batting_df.set_index("Stat", inplace=True)
                    batting_df = batting_df.apply(pd.to_numeric, errors="coerce")

                    formats = ["Test","ODI","T20","IPL"]
                    emojis = ["🟥","🟦","🟩","🟨"]

                    for i,f in enumerate(formats):

                        st.markdown("---")
                        st.markdown(f"## {emojis[i]} {f}")

                        c1,c2,c3,c4 = st.columns(4)

                        c1.metric("📅 Matches",
                                  batting_df.at["Matches",f])

                        c2.metric("🔥 Runs",
                                  batting_df.at["Runs",f])

                        c3.metric("📈 Average",
                                  batting_df.at["Average",f])

                        c4.metric("⚡ Strike Rate",
                                  batting_df.at["SR",f])

                    st.markdown("---")
                    st.subheader("📈 Career Progression")

                    prog = batting_df.loc["Runs",formats]
                    st.line_chart(prog)

                    st.dataframe(batting_df)

# =========================================================
# 🎯 BOWLING TAB (STACKED CLEAN ALIGNMENT)
# =========================================================
                with tab3:

                    st.subheader("🎯 Format-wise Bowling Performance")

                    bowling_df.set_index("Stat", inplace=True)
                    bowling_df = bowling_df.apply(pd.to_numeric, errors="coerce")

                    formats = ["Test","ODI","T20","IPL"]
                    emojis = ["🟥","🟦","🟩","🟨"]

                    for i,f in enumerate(formats):

                        st.markdown("---")
                        st.markdown(f"## {emojis[i]} {f}")

                        b1,b2,b3,b4 = st.columns(4)

                        b1.metric("📅 Matches",
                                  bowling_df.at["Matches",f])

                        b2.metric("🎯 Wickets",
                                  bowling_df.at["Wickets",f])

                        b3.metric("📉 Average",
                                  bowling_df.at["Avg",f])

                        b4.metric("💰 Economy",
                                  bowling_df.at["Eco",f])

                    st.markdown("---")
                    st.subheader("📉 Bowling Impact Progression")

                    prog = pd.DataFrame({
                        "Wickets": bowling_df.loc["Wickets",formats],
                        "Economy": bowling_df.loc["Eco",formats]
                    })

                    st.line_chart(prog)

                    st.dataframe(bowling_df)








elif main_menu == "sql":



    Option = st.selectbox(
        "Choose below ⬇️",
    [
        "👥Indian Team Players",
        "📅 Recent Matches",
        "🎯 Top 10 Scorers in ODI",
        "🏟️ Venues over 25k Capacity",
        "🏆 IPL 2025 Points Table",
        "🚀 Indian Player's role",
        "🏅Top scorers of all Times",
        "📌Cricket Series 2024",
        "🌟 All-rounders over 1000 runs & 50 wickets",
        "💫Player Format Comparison",
        "📊 India's home vs away",
        "⚡Partnership comparasion",
        "🏐Bowler's analytics",
        "🌟Player Performance in Close Matches",
        "📈 Player Performance Over Years",
        "🏏Recent 20 Matches",
        "⚖️ Toss Impact Analysis",
        "💰 Most Economical Bowlers",
        "📊 Most Consistent Batsmen",
        "📈 Player Format Analysis",
        "🥇 Player Rankings by Format",
        "🤝 Head-to-Head Match Prediction",
        "☄️Player's Form & Momentum",
        "🤝 Batting Partnerships",
        "📈 Player Career Evolution Analysis"
        
    ]
)

    if Option == "👥Indian Team Players":

        st.header("👥Indian Team Players")

        df = fetch_matches()

        st.dataframe(df)


    elif Option == "📅 Recent Matches":

        st.header("📅 Recent Matches")

        df_2 = fetch_match_1()
        st.dataframe(df_2)


    elif Option == "🎯 Top 10 Scorers in ODI":

        st.header("🎯 Top 10 Scorers in ODI")

        df_3 = fetch_matches_3()
        st.dataframe(df_3)


    elif Option == "🏟️ Venues over 25k Capacity":

        st.header("🏟️ Venues over 25k Capacity")

        df_4 = fetch_matches_4()
        st.dataframe(df_4)



    elif Option == "🏆 IPL 2025 Points Table":

        st.header("🏆 IPL 2025 Points Table")

        df_5 = fetch_matches_5()
    
        col1, col2 = st.columns([2,3])

        with col1:
         st.dataframe(df_5, use_container_width=True)

    
        with col2:
         st.markdown("📈")
         st.bar_chart(
         df_5.set_index("team")["matches_won"]
    )



    elif Option == "🚀 Indian Player's role":

        st.header("🚀 Indian Player's role")

        df_6 = fetch_matches_6()

        col1, col2 = st.columns([2,3])

        with col1:
         st.dataframe(df_6, use_container_width=True)

    
    elif Option == "🏅Top scorers of all Times":

        st.header("🏅Top scorers of all Times")

        df_test, df_odi, df_t20= fetch_matches_7()
        df_test, df_odi, df_t20 = fetch_matches_7()

        tab1, tab2, tab3 = st.tabs(
    ["🏏 Test", "🏆 ODI", "⚡ T20"]
    )

        with tab1:
         st.dataframe(df_test)

        with tab2:
         st.dataframe(df_odi)

        with tab3:
         st.dataframe(df_t20)


    elif Option == "📌Cricket Series 2024":

        st.header(" 📌Cricket Series 2024")

        df_8 = fetch_matches_8()
        st.dataframe(df_8)


    elif Option == "🌟 All-rounders over 1000 runs & 50 wickets":

        st.header("🌟 All-rounders over 1000 runs & 50 wickets")

        df_9 = fetch_matches_9()


        wkts_pivot = df_9.pivot_table(
    index="player_name",
    columns="format",
    values="total_wickets",
    aggfunc="sum"
    )

        wkts_pivot["Total_Wickets"] = wkts_pivot.sum(axis=1)

# ---------------------------
# RUNS PIVOT
# ---------------------------
        runs_pivot = df_9.pivot_table(
    index="player_name",
    columns="format",
    values="total_runs",
    aggfunc="sum"
    )

        runs_pivot["Total_Runs"] = runs_pivot.sum(axis=1)

# ---------------------------
# COMBINE BOTH
# ---------------------------
        final_df = wkts_pivot.merge(
    runs_pivot,
    left_index=True,
    right_index=True
  )

# Reset index
        final_df.reset_index(inplace=True)

        st.subheader("📊 All-Rounder Performance Summary")
        st.dataframe(final_df, use_container_width=True)

        final_df.columns = [
    "Player",
    "Total Wickets","IPL","ODI","T20","Test",
    "Total Runs","IPL Runs","ODI Runs","T20 Runs","Test Runs"
     ]

    elif Option == "🏏Recent 20 Matches":

        st.header("🏏Recent 20 Matches")

        df_101 = Recent_10()
        st.dataframe(df_101)



    elif Option == "💫Player Format Comparison":

        st.subheader("🏏 Player Performance Across Formats")

        df = fetch_player_format_comparison()

        for _, row in df.iterrows():

          st.markdown(f"### 👤 {row['player_id']}")

          c1, c2, c3, c4 = st.columns(4)

          c1.metric(
            "🟩Test",
            f"{int(row['test_runs']) if pd.notna(row['test_runs']) else 0}",
            f"Avg {round(row['test_avg'],2) if pd.notna(row['test_avg']) else '-'}"
        )

          c2.metric(
            "🟨ODI",
            f"{int(row['odi_runs']) if pd.notna(row['odi_runs']) else 0}",
            f"Avg {round(row['odi_avg'],2) if pd.notna(row['odi_avg']) else '-'}"
        )

          c3.metric(
            "🟥T20",
            f"{int(row['t20_runs']) if pd.notna(row['t20_runs']) else 0}",
            f"Avg {round(row['t20_avg'],2) if pd.notna(row['t20_avg']) else '-'}"
        )

          c4.metric(
            "🌟Overall Avg",
            row['overall_avg']
        )

          st.divider()
    
    elif Option == "📊 India's home vs away":

        st.header("📊 India Home vs Away Performance")

        away_df=fetch_matches_table()
        away_wins=fetch_away_wins()

        col1,col2=st.columns([4,1])

        with col1:
          st.subheader("✈️ India's Playing Away")
          st.dataframe(away_df, use_container_width=True) 

        with col2:
          st.markdown(" 🏆 India wins away")
          st.metric(label="Matches won",value=away_wins)  

      
        home_df = fetch_home_table()
        home_wins = fetch_home_wins()

        st.divider()

        col3, col4 = st.columns([4, 1])

        with col3:
          st.subheader("🏠 India's Playing Home")
          st.dataframe(home_df, use_container_width=True)

        with col4:
          st.markdown("### 🏆 India Wins (Home)")
          st.metric(
          label="Matches Won",
          value=home_wins
     ) 
      
        st.divider()

        st.subheader("📊 Overall Win Comparison")
 
        col5, col6 = st.columns(2)

        with col5:
          st.metric(
        label="🏆Away Wins",
        value=away_wins
        )

        with col6:
          st.metric(
        label="🏆 Home Wins",
        value=home_wins
     )
        
    
    

    elif Option == "⚡Partnership comparasion":

        st.header(" ⚡Partnership comparasion")
        st.subheader("ICC Champions Tropy 🏆 - NZ vs PAK")

        df_13= fetch_scorecard_13()
        partnership_df = fetch_partnership_100()

        col1, col2 = st.columns(2)

        with col1:
          st.subheader("📋 Full Scorecard")
          st.dataframe(df_13, use_container_width=True)

        with col2:
          st.subheader("💯 100+ Run Partnerships")
          st.dataframe(partnership_df, use_container_width=True)


    elif Option == "🏐Bowler's analytics":

        st.header(" 🏐Bowler's analytics")
        df = bowlers_14()
        col1, col2 = st.columns(2)

        with col1:
          st.markdown("Data with venue - MI bowlers at Mumbai")
          st.dataframe(df)

        with col2:
          st.markdown("✅Bowlers over 2 matches and 4 overs")
          st.dataframe(analytics_14(df))

    elif Option == "🌟Player Performance in Close Matches":

        st.header("🌟Player Performance in Close Matches")

        conn = get_connection()

    # Match selector
        match_list = pd.read_sql(
        "SELECT DISTINCT match_id FROM SA_match1",
        conn
    )

        match_id = st.selectbox(
        "Select Match",
         match_list["match_id"]
    )

        scorecard_df = get_match_scorecard(match_id)
        performer_df = get_top_performers(match_id)
        teams=get_match_teams(match_id)
        match_info = get_match_result(match_id)

    # Layout
        col1, col2 = st.columns([3, 2])

        with col1:

          st.subheader(f"📋 Match Scorecard - {teams[0]} vs {teams[1]}")
    
          match_result=get_match_result(match_id)

          st.markdown(f"🏆 {match_result}")

          st.dataframe(scorecard_df, use_container_width=True)

        with col2:

          st.subheader("🏅 Top Performers")

          st.dataframe(performer_df, use_container_width=True)


    elif Option == "📈 Player Performance Over Years":

        st.header("📈 Player Batting Performance Since 2020")

        avg_runs_df = get_player_avg_runs()

        st.subheader("Average Runs Per Match")
        st.dataframe(avg_runs_df, use_container_width=True)


        st.subheader("Performance Trend Over Years")

        pivot_df = avg_runs_df.pivot(
        index="year",
        columns="player_name",
        values="avg_runs")

        st.line_chart(pivot_df)


    elif Option == "⚖️ Toss Impact Analysis":

        st.header("⚖️ Toss Impact Analysis")

    # =============================
    # FULL MATCH TABLE (TOP)
    # =============================
        st.subheader("📋 Match Results Dataset")

        df_full = fetch_q17_full_table()

        st.dataframe(df_full, use_container_width=True)


        st.divider()


    # =============================
    # ANALYSIS TABLE (BOTTOM)
    # =============================
        st.subheader("📊 Toss Decision Impact")

        df17 = fetch_q17()

        st.dataframe(df17, use_container_width=True)


        fig = px.bar(
        df17,
        x="win_percentage",
        y="toss_decision",
        orientation="h",
        text="win_percentage",
        title="📈Toss Decision Win Percentage Comparison"
        )

        fig.update_layout(
        xaxis_title="Win Percentage (%)",
       yaxis_title="Toss Decision",
       height=400
        )

        st.plotly_chart(fig, use_container_width=True)


    elif Option == "💰 Most Economical Bowlers":

        st.header("💰 Most Economical Bowlers")

        conn = get_connection()

        eco_df = get_economical_bowlers()

        st.dataframe(eco_df, use_container_width=True)

        st.subheader("⚡Economy Rate Comparison")

        fig = px.bar(
    eco_df,
    x="player_name",
    y="economy_rate",
    color="match_format",
    barmode="group",
    text="economy_rate",
    title="Most Economical Bowlers ⬇️"
    )

        fig.update_layout(
    xaxis_title="Player",
    yaxis_title="Economy Rate",
    height=450
    )

        st.plotly_chart(fig, use_container_width=True)


    elif Option == "📊 Most Consistent Batsmen":

        st.header("📊 Most Consistent Batsmen")

        df = get_consistent_batsmen()

        st.dataframe(df, use_container_width=True)


        fig = px.bar(
    df,
    x="player_name",
    y="runs_std_dev",
    text="runs_std_dev",
    title="Batting Consistency (Lower⬇️= Better✅)"
     )
        fig.update_traces(width=0.3
                      )
        st.plotly_chart(fig, use_container_width=True)


        year_df = get_yearly_consistency()

        fig_line = px.line(
    year_df,
    x="year",
    y="runs_std_dev",
    color="player_name",
    markers=True,
    title="Consistency Change Over Years"
    )

        fig_line.update_layout(
    yaxis_title="Runs Standard Deviation (Lower⬇️= Better✅)",
    xaxis_title="Year"
    )

        st.plotly_chart(fig_line, use_container_width=True)



    elif Option == "📈 Player Format Analysis":

        st.header("📈 Matches & Batting Average by Format")

        df = get_player_format_analysis()

        st.dataframe(df, use_container_width=True)

        df_long_matches = df.melt(
    id_vars="player_name",
    value_vars=["test_matches","odi_matches","t20_matches"],
    var_name="Format",
    value_name="Matches"
    )


        fig1 = px.bar(
    df_long_matches,
    x="player_name",
    y="Matches",
    color="Format",
    barmode="group",
    title="🏏Matches Played Across Formats"
    )

        st.plotly_chart(fig1, use_container_width=True)

        df_long_avg = df.melt(
    id_vars="player_name",
    value_vars=["test_avg","odi_avg","t20_avg"],
    var_name="Format",
    value_name="Average"
    )

        fig2 = px.line(
    df_long_avg,
    x="Format",
    y="Average",
    color="player_name",
    markers=True,
    title="⚡Batting Average Across Formats"
    )

        st.plotly_chart(fig2, use_container_width=True)


    elif Option == "🥇 Player Rankings by Format":

        st.subheader("🥇 Player Rankings by Format")

        tab1, tab2, tab3 = st.tabs(["🏏T20", "🏏ODI", "🏏Test"])

        with tab1:
          st.dataframe(get_t20_rankings(), use_container_width=True)

        with tab2:
          st.dataframe(get_odi_rankings(), use_container_width=True)

        with tab3:
          st.dataframe(get_test_rankings(), use_container_width=True)

    

    elif Option == "🤝 Head-to-Head Match Prediction":

        st.header("🤝 Head-to-Head Match Prediction Analysis")

        df = fetch_head_to_head_prediction()

        st.markdown("### 📊 Team Rivalry Insights")

        col1, col2, col3 = st.columns(3)

        col1.metric(
    "Total Matches",
    int(df["total_matches"].iloc[0])
)

        col2.metric(
    f"{df['team_a'].iloc[0]} Wins",
    int(df["team_a_wins"].iloc[0])
)

        col3.metric(
    f"{df['team_b'].iloc[0]} Wins",
    int(df["team_b_wins"].iloc[0])
)

        st.dataframe(
        df,
        use_container_width=True)

        win_df = {
    df["team_a"].iloc[0]: df["team_a_win_pct"].iloc[0],
    df["team_b"].iloc[0]: df["team_b_win_pct"].iloc[0]
}

        fig_win = px.bar(
    x=list(win_df.keys()),
    y=list(win_df.values()),
    text=list(win_df.values()),
    title="🏆 Head-to-Head Win Percentage"
)
        fig_win.update_layout(bargap=0.6)
        fig_win.update_traces(textposition="outside",width=0.35)
        

        st.plotly_chart(fig_win, use_container_width=True)

        toss_df = {
    "Bat First Wins": df["bat_first_wins"].iloc[0],
    "Bowl First Wins": df["bowl_first_wins"].iloc[0]
}

        fig_toss = px.bar(
    x=list(toss_df.keys()),
    y=list(toss_df.values()),
    text=list(toss_df.values()),
    title="🎯 Toss Decision Impact"
)

        fig_toss.update_traces(textposition="outside",width=0.35)
        fig_win.update_layout(bargap=0.6)

        st.plotly_chart(fig_toss, use_container_width=True)

    elif Option == "☄️Player's Form & Momentum":

        st.subheader("☄️Player's Form & Momentum")

        st.markdown("🏆 ICC T20 Championship - 2026")

        form_df = get_player_form()

        st.dataframe(form_df, use_container_width=True)


        plot_df = form_df.melt(
    id_vars="batters_name",
    value_vars=["avg_last_5", "avg_last_10"],
    var_name="Match_Type",
    value_name="Average_Runs"
    )

        fig = px.bar(
    plot_df,
    x="batters_name",
    y="Average_Runs",
    color="Match_Type",
    barmode="group",
    title="Recent Form Comparison (Last 5 vs Last 10 Matches)"
)

        st.plotly_chart(
    fig,
    config={"responsive": True}
)
    
    


    elif Option == "🤝 Batting Partnerships":

        st.subheader("🤝 Successful Batting Partnerships")

        df = get_partnership_analysis()

        st.dataframe(df, width="stretch")


        df["Batting partners"] = df["player_1"] + " & " + df["player_2"]

        fig = px.bar(
    df.head(10),
    x="avg_partnership_runs",
    y="Batting partners",
    orientation="h",
    title="🌟Top Batting Partnerships"
    )

        st.plotly_chart(fig,
                    config={"responsive": True})

    elif Option == "📈 Player Career Evolution Analysis":
        st.subheader("📈 Player Career Evolution Analysis")

# Fetch data from SQL
        df_q25 = fetch_player_time_series_analysis()

        if df_q25.empty:
            st.warning("No players meet minimum requirement of 6 quarters and 3 matches per quarter.")
        else:

    # ======================
    # FULL OUTPUT TABLE
    # ======================
            st.dataframe(
        df_q25,
        use_container_width=True,
        hide_index=True
    )

            st.markdown("---")

    # ======================
    # PLAYER SELECTION
    # ======================
            selected_player = st.selectbox(
        "Select Player to View Performance Trend",
        sorted(df_q25["batters_name"].unique())
    )

            player_df = df_q25[
        df_q25["batters_name"] == selected_player
    ].sort_values("quarter")

    # ======================
    # PLAYER METRICS
    # ======================
            col1, col2, col3 = st.columns(3)

            col1.metric(
        "Career Phase",
        player_df["career_phase"].iloc[0]
    )

            col2.metric(
        "Average Runs",
        round(player_df["avg_runs"].mean(), 2)
    )

            col3.metric(
        "Average Strike Rate",
        round(player_df["avg_strike_rate"].mean(), 2)
    )

    # ======================
    # TIME SERIES CHART
    # ======================
            st.line_chart(
        player_df.set_index("quarter")[["avg_runs", "avg_strike_rate"]],
        use_container_width=True
    )

    # ======================
    # PERFORMANCE STATUS
    # ======================
            st.dataframe(
        player_df[
            [
                "quarter",
                "avg_runs",
                "avg_strike_rate",
                "performance_status"
            ]
        ],
        hide_index=True,
        use_container_width=True
    )   
    
    
elif main_menu == "crud":
    indian_team_players_crud()

elif main_menu == "home":

    st.title("🏏 Cricket Analytics Dashboard")
    st.markdown("### Real-Time Data • SQL Analytics • Visualization • CRUD Operations")

    st.markdown("---")

    st.markdown("""
    ## 📌 Project Overview

    The *Cricket Analytics Dashboard* is a full-stack data application built using *Streamlit*.  
    It integrates live cricket data from the Cricbuzz RapidAPI with structured SQL analytics and 
    interactive visualizations.

    This project demonstrates how real-time API data, database management, 
    and analytics can be combined into a single modular web application.
    """)

    st.markdown("---")

    st.markdown("## 📂 Application Modules")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 1️⃣ Live Scores")
        st.markdown("""
        - Fetches real-time and recent matches  
        - Displays match details and scorecards  
        - Innings-wise batting & bowling tables  
        - REST API integration and JSON parsing  
        """)

        st.markdown("### 3️⃣ SQL Analytics")
        st.markdown("""
        - Executes analytical SQL queries  
        - Uses PostgreSQL for structured data storage  
        - Visualizes insights using Plotly  
        - Demonstrates database-driven analytics  
        """)

    with col2:
        st.markdown("### 2️⃣ Player Statistics")
        st.markdown("""
        - Player search functionality  
        - Batting and bowling performance analysis  
        - Format-wise career statistics  
        - Data transformation using pandas  
        """)

        st.markdown("### 4️⃣ CRUD Operations")
        st.markdown("""
        - Create, Read, Update, Delete records  
        - Form-based database interaction  
        - Real-world data manipulation workflow  
        """)

    st.markdown("---")

    st.markdown("## 🛠 Technologies Used")

    st.markdown("""
    *Programming & Framework*
    - Python  
    - Streamlit  

    *Data Handling & API*
    - Pandas  
    - Requests  
    - Cricbuzz RapidAPI  

    *Database & Analytics*
    - PostgreSQL  
    - psycopg2  
    - SQL Queries  

    *Visualization*
    - Plotly Express  
    """)

    st.markdown("---")

    st.markdown("""
    ## 🎯 Project Objective

    To design and develop a modular cricket analytics system that integrates:
    - Real-time sports data  
    - Structured SQL analytics  
    - Interactive dashboards  
    - Database CRUD operations  

    into a single scalable Streamlit application.
    """)

    st.success("✔ End-to-End Data Application | ✔ API + Database Integration | ✔ Analytical Dashboard")
