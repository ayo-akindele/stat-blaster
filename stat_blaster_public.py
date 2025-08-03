
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Weekend Stat Blaster", layout="wide")

# Title
st.title("⚽ Weekend Stat Blaster")
st.markdown("Get clean, high-confidence betting trends for each EPL fixture based on historical performance. Updated weekly.")

# Admin mode toggle (hidden by default)
with st.expander("🔐 Admin Upload (For Updating Data)"):
    is_admin = st.checkbox("Enable Admin Upload Mode")

if is_admin:
    st.subheader("1. Upload Latest Match Results")
    results_file = st.file_uploader("Upload updated results CSV", type="csv")

    st.subheader("2. Upload Upcoming Gameweek Fixtures")
    fixtures_file = st.file_uploader("Upload upcoming fixtures CSV", type="csv")

    if results_file and fixtures_file:
        st.session_state['results_df'] = pd.read_csv(results_file)
        st.session_state['fixtures_df'] = pd.read_csv(fixtures_file)
        st.success("✅ Files uploaded successfully! Use the dropdown below to preview predictions.")
else:
    st.markdown("👉 To upload or update data, enable **Admin Mode** from the panel above.")

# Load from session state or use placeholder
results_df = st.session_state.get('results_df', None)
fixtures_df = st.session_state.get('fixtures_df', None)

if results_df is not None and fixtures_df is not None:
    # Standardize column names
    results_df.columns = [col.strip().lower().replace(" ", "_") for col in results_df.columns]
    fixtures_df.columns = [col.strip().lower().replace(" ", "_") for col in fixtures_df.columns]

    st.subheader("📅 Select Gameweek")
    gameweek = st.selectbox("Gameweek", sorted(fixtures_df['round_number'].unique()))

    gw_fixtures = fixtures_df[fixtures_df['round_number'] == gameweek]

    def generate_stats(home, away):
        h2h = results_df[
            ((results_df['home_team'] == home) & (results_df['away_team'] == away)) |
            ((results_df['home_team'] == away) & (results_df['away_team'] == home))
        ].sort_values(by="match_date", ascending=False).head(5)

        if len(h2h) < 5:
            return []

        total = len(h2h)
        trends = []

        def stat_check(series, label):
            count = series.sum()
            if count / total >= 0.8:
                return f"{label} in {count}/{total} games"
            return None

        # Match winner
        team_wins = 0
        for _, row in h2h.iterrows():
            if row['home_team'] == home and row['home_score'] > row['away_score']:
                team_wins += 1
            elif row['away_team'] == home and row['away_score'] > row['home_score']:
                team_wins += 1
        if team_wins / total >= 0.8:
            trends.append(f"{home} won {team_wins}/{total} recent meetings")

        # Create derived fields if not already present
        if 'total_corners' in h2h.columns:
            h2h['Corners_Over_9.5'] = h2h['total_corners'] > 9.5
        if 'home_yellow_cards' in h2h.columns and 'away_yellow_cards' in h2h.columns:
            h2h['Bookings_Over_3.5'] = (h2h['home_yellow_cards'] + h2h['away_yellow_cards']) > 3.5
        if 'first_half_home' in h2h.columns and 'first_half_away' in h2h.columns:
            h2h['First_Half_Goal'] = (h2h['first_half_home'] + h2h['first_half_away']) > 0

        checks = {
            'both_teams_score': "Both teams scored",
            'over_2_5': "Over 2.5 goals",
            'Corners_Over_9.5': "Over 9.5 corners",
            'Bookings_Over_3.5': "Over 3.5 bookings",
            'First_Half_Goal': "First-half goals"
        }

        for col, label in checks.items():
            if col in h2h.columns:
                trend = stat_check(h2h[col], label)
                if trend:
                    trends.append(trend)

        return trends

    st.subheader("📊 Gameweek Stats")
    for _, row in gw_fixtures.iterrows():
        home = row['home_team']
        away = row['away_team']
        st.markdown(f"### {home} vs {away}")
        fixture_stats = generate_stats(home, away)
        if fixture_stats:
            for s in fixture_stats:
                st.markdown(f"- {s}")
        else:
            st.info("Not enough H2H data to generate trends.")
else:
    st.warning("Please upload both result and fixture files in Admin Mode to activate predictions.")
