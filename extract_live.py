from fantasy_util import extract_data


if __name__ == "__main__":
    url = "https://www.livefpl.net/leagues/1704871"
    

    team_names = ['savapain', 'PhiHung50', 'Nani29', 'Onion XXL', 'Galaticos 2.0 FC']
    data = extract_data(url, team_names)
    for row in data:
        print(row)
