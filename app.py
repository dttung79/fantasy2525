from flask import Flask, render_template, request, jsonify
from fantasy_util import extract_data, read_team_week
import math

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    return build_league_page('week_tpl.html', 32200)

@app.route('/week/<league_id>')
def week(league_id):
    return build_league_page('week_tpl.html', league_id)

# @app.route('/tml')
# def tml():
#     return build_page('tml_tpl.html')
# @app.route('/tml/save')
# def tmlsave():
#     # columns = ['Rank', 'Team', 'GW Points', 'Total Points', 'Hits']
#     data = extract_data(live_url, team_week_names)
#     if len(data) == 0:
#         return jsonify([])
#     # Convert data to dictionary where key is row[1] and value is row[3]
#     data = {row[1]: row[3] for row in data}

#     f =  open('week.csv', 'r', encoding='utf-8-sig')
#     lines = f.readlines()
#     last_column = lines[0].split(',')[-1].strip()
#     new_column = 'W' + str(int(last_column[1:]) + 1)
#     header = lines[0].strip() + ',' + new_column + '\n'

#     week_table = {}
#     for i in range(1, len(lines)):
#         team_name = lines[i].split(',')[0]
#         points = lines[i].strip('\n').split(',')[1:]
#         week_table[team_name] = ','.join(points) + ',' + str(data[team_name])
#         # add new data to week_table
#     f.close()
#     # convert week_table to list of lines
#     lines = [f'{key},{value}\n' for key, value in week_table.items()]
#     # remove \n from each line then split by comma
#     lines = [line.strip().split(',') for line in lines]
#     # insert header to the first row
#     lines.insert(0, header.strip().split(','))
#     # save lines to week_update.csv
#     f = open('week.csv', 'w')
#     for line in lines:
#         f.write(','.join(line) + '\n')
#     f.close()
#     return build_page('tml_tpl.html')

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
    print(lines)
    
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
        print('Season team:', season_team_names)
        print('Team week:', team_week_names)
        team_week_names = [team for team in team_week_names if team in season_team_names]
        print('Team week after removed:', team_week_names)
    
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
    
    print(output)
    return jsonify(output)


# ####### routes for a league #######
# # route to build league rounds page
# @app.route('/<league_name>')
# def league(league_name):
#     return build_league_page('league_tpl.html', league_name)


# # route to build league table page
# @app.route('/<league_name>/table')
# def league_table(league_name):
#     return build_league_page('league_table_tpl.html', league_name)

# # route api to get result of a week round in a league
# @app.route('/api/<league_name>/week/<int:week_no>')
# def league_week(league_name, week_no):
#     return jsonify(match_round(league_name, week_no))

# # route api to get all rounds in a league
# @app.route('/api/<league_name>/rounds')
# def league_rounds(league_name):
#     return jsonify(get_rounds(league_name))

# # route api to get live round result in a league
# @app.route('/api/live/<league_name>/<int:week_no>')
# def live(league_name, week_no):
#     return jsonify(live_round(live_url, league_name, week_no))

# # route api to get league table result
# @app.route('/api/<league_name>/table')
# def league_table_api(league_name):
#     return jsonify(get_league_table(league_name))

####### general build pages function #######
# def build_page(filename):    
#     head = render_template('header_tpl.html')
#     content = render_template(filename)
#     footer = render_template('footer_tpl.html')
#     return head + '\n' + content + '\n' + footer

def build_league_page(filename, league_id):
    head = render_template('header_tpl.html', league_id=league_id)
    content = render_template(filename, league_id=league_id)
    footer = render_template('footer_tpl.html')
    return head + '\n' + content + '\n' + footer

####### main function #######
if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0')