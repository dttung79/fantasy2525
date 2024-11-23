from flask import Flask, render_template, request, jsonify
from fantasy_util import extract_data, read_team_week
import os
import pandas as pd

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    return build_league_page('week_tpl.html', 32200)

@app.route('/week/<league_id>')
def week(league_id):
    return build_league_page('week_tpl.html', league_id)

@app.route('/week/<league_id>/save/<week_number>')
def save_week(league_id, week_number):
    csv_file = f"{league_id}_week.csv"

    # Read the first line to get the latest week
    if os.path.exists(csv_file):
        latest_week = pd.read_csv(csv_file, nrows=1).columns[-1]  # Get the last column name
        latest_week_number = int(latest_week[-1])  # Extract the week number from the column name

        if week_number == latest_week_number:
            return jsonify({"warning": "Week number is already the latest week."})

        # Fetch live data for the league
        live_url = f'https://www.livefpl.net/leagues/{league_id}'
        team_week_names = read_team_week(league_id)  # Get team names for the league
        live_data = extract_data(live_url, team_week_names)  # Fetch live data

        # Prepare to read existing CSV data
        df = pd.read_csv(csv_file)

        # Extract live points and hits from the live data
        live_points_hits = {}
        for row in live_data:
            team_name = row[1]  # Assuming team name is in the second column
            points = row[3]  # Assuming live points are in the fourth column
            hits = abs(row[4])  # Assuming hits are in the fifth column
            live_points_hits[team_name] = f"{points}:{hits}"  # Store points and hits

        # Add a new column for the current week with live points and hits
        new_column = f'W{latest_week_number + 1}'
        df[new_column] = df['Team'].map(live_points_hits)
        df.to_csv(csv_file, index=False)

        return jsonify({"message": "Week saved successfully."})
    else:
        return jsonify({"error": "CSV file does not exist."})

@app.route('/api/week/<league_id>')
def get_weeks_data(league_id):
    # columns = ['Rank', 'Team', 'GW Points', 'Total Points', 'Hits']
    live_url = f'https://www.livefpl.net/leagues/{league_id}'
    data = extract_data(live_url, read_team_week(league_id))
    if len(data) == 0:
        return jsonify([])
    # Convert data to dictionary where key is row[1] and value is row[3]
    data = {row[1]: f'{row[3]}:{abs(row[4])}' for row in data}

    f =  open(f'{league_id}_week.csv', 'r', encoding='utf-8-sig')
    lines = f.readlines()
    last_column = lines[0].split(',')[-1].strip()
    new_column = 'W' + str(int(last_column[1:]) + 1)
    header = lines[0].strip() + ',' + new_column + '\n'

    week_table = {}
    for i in range(1, len(lines)):
        team_name = lines[i].split(',')[0]
        points_hits = lines[i].strip('\n').split(',')[1:]
        week_table[team_name] = ','.join(points_hits) + ',' + str(data[team_name])
        # add new data to week_table
    f.close()
    # convert week_table to list of lines
    lines = [f'{key},{value}\n' for key, value in week_table.items()]
    # remove \n from each line then split by comma
    lines = [line.strip().split(',') for line in lines]
    # insert header to the first row
    lines.insert(0, header.strip().split(','))
    
    return jsonify(lines)

@app.route('/season/<league_id>')
def season(league_id):
    return build_league_page('season_tpl.html', league_id)

@app.route('/api/season/<league_id>')
def get_season_data(league_id):
    season_table = {}
    
    # Fetch live data for the league
    live_url = f'https://www.livefpl.net/leagues/{league_id}'
    team_week_names = read_team_week(league_id)  # Get team names for the league
    live_data = extract_data(live_url, team_week_names)  # Fetch live data

    # Open the CSV file for the league
    f = open(f'{league_id}_week.csv', 'r', encoding='utf-8-sig')
    lines = f.readlines()

    season_file = f'{league_id}_season.txt'
    # get team names from season file then remove team names that are not in the season file
    with open(f'{season_file}', 'r') as sf:
        season_team_names = sf.readlines()

        # Remove newline characters from team names
        season_team_names = [team_name.strip() for team_name in season_team_names]
        team_week_names = [team for team in team_week_names if team in season_team_names]
    
    # Initialize a dictionary to hold cumulative points for each team
    cumulative_points = {}
    
    # Process each line to calculate cumulative points from the CSV
    for i in range(1, len(lines)):
        team_name = lines[i].split(',')[0]
        if team_name not in season_team_names:  # Filter teams based on season_team_names
            continue
        points_hits = lines[i].strip('\n').split(',')[1:]
        
        # Initialize the team's cumulative points if not already done
        if team_name not in cumulative_points:
            cumulative_points[team_name] = 0
        
        # Store weekly points for the current team
        if team_name not in season_table:
            season_table[team_name] = []
        
        # Sum points and subtract hits for the current week
        for j in range(0, len(points_hits)):  # Assuming points and hits are in pairs
            points = int(points_hits[j].split(':')[0])  # GW Points
            hits = int(points_hits[j].split(':')[1])  # Hits
            cumulative_points[team_name] += points - hits
            season_table[team_name].append(f'{cumulative_points[team_name]}:{hits}')  # Store weekly points and hits

    # Process live data to update the season table
    if live_data:
        for row in live_data:
            team_name = row[1]  # Assuming team name is in the second column
            if team_name not in season_team_names:  # Filter teams based on season_team_names
                continue
            points = int(row[3])  # Assuming points are in the fourth column
            hits = abs(int(row[4]))  # Assuming hits are in the fifth column
            
            # Initialize the team's cumulative points if not already done
            if team_name not in cumulative_points:
                cumulative_points[team_name] = 0
            
            # Update cumulative points
            cumulative_points[team_name] += points - hits
            
            # Append the latest data to the season table
            if team_name not in season_table:
                season_table[team_name] = []
            season_table[team_name].append(f'{cumulative_points[team_name]}:{hits}')  # Store updated points and hits

    f.close()
    
    # Prepare the final output format
    header = ["Team", *[f'W{i+1}' for i in range(len(season_table[next(iter(season_table))]))]]
    output = [header]
    
    for team_name, weekly_data in season_table.items():
        output.append([team_name, *weekly_data])
    
    return jsonify(output)


def build_league_page(filename, league_id):
    head = render_template('header_tpl.html', league_id=league_id)
    content = render_template(filename, league_id=league_id)
    footer = render_template('footer_tpl.html')
    return head + '\n' + content + '\n' + footer

# cronjob to keep the server running
@app.route('/cronjob', methods=['GET'])
def cronjob():
    return jsonify({"message": "Cronjob is running"})

####### main function #######
if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0')