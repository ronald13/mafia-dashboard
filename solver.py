from dash import Dash
import pandas as pd
import json
from pandas import json_normalize
from loguru import logger
import plotly.graph_objects as go

def merge_two_dicts(x, y):
    z = x.copy()   # start with keys and values of x
    z.update(y)    # modifies z with keys and values of y
    return z
def count_number(list, num):
    """
    counts the number of values in list from 1 to num
    """
    new_l=[]
    for i in range(1, num+1):
        list.count(i)
        new_l.append(list.count(i))
    return new_l

def df_firstshot_with_hit_rate(df, all_games_number):
    """
    Сalculate the shooting rate according to the FIIM formula
    The value B = 0.4 * number of all games in the tournament and rounded to the nearest integer.
    """

    B = round(0.4 * all_games_number)
    if df['number_shot'] <= B:
        df['Ci'] = round(((df['number_shot'] * 0.4 / B) * df['shot_and_lose']), 2)
    else:
        df['Ci'] = round((0.4 * df['shot_and_lose']), 2)
    return df


class Mafia(object):

    def __init__(self, games, teams, first_shot, referee, GAME_NUMBER=14):
        self.games = games
        self.teams = teams
        self.referee = referee
        self.first_shot = first_shot

        self.games_number = GAME_NUMBER
        self.font_family = "Open Sans"
        self.font_size = 14
        self.role = self.get_role()
        self.fulldata = self.get_info_about_all_games()

    def get_role(self):
        role = pd.DataFrame( [{'role_id':1,'role_name':'Мирный'}, {'role_id':2,'role_name':'Мафия'}, {'role_id':3,'role_name':'Дон'}, {'role_id':4,'role_name':'Шериф'} ])
        return role

    def teams_list(self):
        return self.teams['team_name'].unique()

    def get_all_players(self):
        """
        create df with info about players with player_name
        """
        df_players = self.games[['player_id', 'player_name']].drop_duplicates()
        df_players = df_players.merge(self.teams[['player_id', 'team_id', 'team_name']], how='left', on='player_id')
        return df_players

    def get_info_about_all_games(self):
        '''
        get the final table (full_data) which has the information for all charts on the dashboard
        As a result we get dataframe with 10 * all_games_number rows.
        '''
        full_data = self.games

        full_data = pd.merge(full_data, self.get_role(), how="left", on="role_id")
        full_data = pd.merge(full_data, self.get_all_players()[['player_id', 'team_id', 'team_name']], how="left",
                             on="player_id")
        full_data = full_data.rename(
            columns={'table': 'table_number', 'number': 'round_number', 'boxNumber': 'box_number',
                     'PlayerName': 'player_name', 'role_name_y': 'role_name', 'WinnerName': 'winner'})

        # change type score to float
        full_data['round_number'] = full_data['round_number'].astype('int')
        full_data['table_number'] = full_data['table_number'].astype('int')
        full_data['score'] = full_data['score'].astype('float')
        full_data['score'] = full_data['score'].astype('float')
        full_data['score'] = full_data['score'].astype('float')
        full_data['score_dop'] = full_data['score_dop'].astype('float')
        full_data['score_minus'] = full_data['score_minus'].astype('float')
        logger.info('Full data table successfully created!')

        return full_data

    def get_table_distribution(self):
        """
        create df with info about distribution of players on the tables. df is used for spider chart
        """
        table_distribution =  self.fulldata.groupby(['team_name', 'player_name'])['table_number'].apply(list).reset_index()
        table_distribution['table_number_count'] = table_distribution['table_number'].apply(count_number, args=(int(self.games.shape[0] / self.games_number / 10),))
        return table_distribution

    def get_box_distribution(self):
        """
        create df with info about distribution of players on the boxes. df is used for spider chart (box)
        """
        box_distribution = self.fulldata.groupby(['team_name', 'player_name', 'box_number'])['player_id'].count().unstack().fillna(
            0).reset_index()
        return box_distribution

    def make_firstshot_table(self):
        """
        create information about first shot and calculate hit rate for every game
        """
        # logger.info('Calculating firstshot table...')
        first_shot = self.first_shot

        col = ['table', 'number', 'winner_id', 'gamefirstshot.player_id',
               'gamefirstshot.boxNumber', 'gamefirstshot.score']
        firstshot_df = first_shot[col].rename(
            columns={'number': 'game_number', 'winner_id': 'who_win', 'gamefirstshot.player_id': 'player_id',
                     'gamefirstshot.boxNumber': 'boxNumber', 'gamefirstshot.score': 'score'})

        firstshot_df['score'] = firstshot_df['score'].astype('float')

        firstshot_df = pd.merge(firstshot_df, self.get_all_players()[['player_id', 'player_name', "team_name"]],
                                how="left",
                                on="player_id").rename(columns={'score': 'score_firstshot'})


        number_first_shot = firstshot_df.groupby(['player_name', "team_name"]).agg(
            {'score_firstshot': 'sum', 'player_id': 'count', 'who_win': 'sum'}).sort_values(by='player_id',
                                                                                            ascending=False).reset_index().rename(
            columns={'player_id': 'number_shot', 'who_win': 'shot_and_lose'})
        number_first_shot = number_first_shot.apply(df_firstshot_with_hit_rate, axis=1, args=(14,))
        logger.info('First-Shot table has been created!')
        return number_first_shot
    def get_total_score_table(self):
        """
        the final table that can be used to display the results
        """

        total_result_players = self.fulldata.groupby(['team_name', 'player_name']).agg({'score': 'sum', 'score_dop': 'sum', 'score_minus': 'sum'}).reset_index()
        # merge with first short
        total_result_players = pd.merge(total_result_players, self.make_firstshot_table()[['score_firstshot', 'Ci',  'player_name']], how="left", on="player_name")

        total_result_players['score_firstshot'] = total_result_players['score_firstshot'].fillna(0)
        total_result_players['Ci'] = total_result_players['Ci'].fillna(0)

        total_result_players['total']  = total_result_players['score'] + total_result_players['score_dop'] + total_result_players['score_firstshot'] + total_result_players['score_minus'] + total_result_players['Ci']
        total_result = total_result_players.sort_values(by='total', ascending=False)
        return total_result

    def team_metrics(self):
        number_shots = self.make_firstshot_table().groupby('team_name').agg({'number_shot': 'sum'}).reset_index()
        agregate_total_score_table = self.get_total_score_table().groupby('team_name').agg(
            {'score': 'sum', 'score_dop': 'sum', 'score_minus': 'sum', 'score_firstshot': 'sum', 'Ci': 'sum'})
        result = pd.merge(agregate_total_score_table, number_shots, how='left', on='team_name')
        result['number_shot'] = result['number_shot'].fillna(0)
        return result
    def team_winners(self):
        """
        get the top three winners in the team standings competition
        """
        # logger.info('Calculating table with all team winners...')
        team_winners = self.get_total_score_table().groupby('team_name')['total'].sum().reset_index().sort_values(by='total', ascending=False)['team_name'].iloc[0:3].to_list()
        return team_winners

    def personal_winners(self):
        """
        get the top three winners in the individual competition
        """
        personal_winners = self.get_total_score_table()['player_name'].iloc[0:3].to_list()
        return personal_winners
    def win_by_round(self):
        """
        get a table with information about the winnings of the team in the context of the round
        """
        df_temp = self.get_info_about_all_games().groupby(['team_name', 'round_number'])[['score', 'score_dop', 'score_minus']].sum().reset_index()
        df_temp['cum_score'] = df_temp.groupby('team_name')['score'].cumsum()
        df_temp['cum_score_dop'] = df_temp.groupby('team_name')['score_dop'].cumsum()
        df_temp['cum_score_minus'] = df_temp.groupby('team_name')['score_minus'].cumsum()
        df_temp['total_score'] = df_temp['cum_score'] + df_temp['cum_score_dop'] + df_temp['cum_score_minus']
        result = pd.pivot_table(df_temp,
                                index='team_name',
                                columns='round_number',
                                values='total_score').reset_index()
        return result
    def wind_by_round_referee(self):
        """
        get a dataframe with information about the team's win on each table (each referee)
        result: double list
        """
        logger.info('Calculation wind_by_round_referee')

        win_by_round = self.fulldata.groupby(['team_name', 'round_number', 'table_number'])['score'].sum().reset_index()
        win_by_round = win_by_round.groupby(['team_name']).apply(
            lambda x: pd.pivot_table(data=x,
                                     values="score",
                                     index="table_number",
                                     columns="round_number",
                                     aggfunc='mean').fillna(0).values).reset_index(name='win_list')
        return win_by_round
    def referee_score(self):
        """
        the number of  score awarded by the referee
        """
        referee_score = self.get_info_about_all_games().groupby('table_number').agg({'score_dop':'sum', 'score_minus':'sum'}).reset_index()
        referee_score = pd.merge(referee_score, self.referee[['table_number', 'referee_name']], how="left", on="table_number")

        return referee_score
    def win_lose(self):
        """
        percentage of mafia and civilian wins
        result: [mafia,citizen]
        """
        win_lose = self.get_info_about_all_games()['winner'].value_counts(normalize=True).round(2).reset_index()['winner'].to_list()
        return win_lose

    def game_results(self, normalize=True):
        """

        :param normalize:
        :return:
        """
        df = self.games[['game_id', 'table', 'winner_id', 'WinnerName']].rename(
            columns={'table': 'table_number', 'WinnerName': 'winner'})
        df = df.groupby('table_number')['winner'].value_counts(normalize=normalize).round(2).reset_index(name="value")
        df = df.groupby('table_number')['value'].apply(list).reset_index()
        return df
    def death_leader(self):
        """
        most killed player: [nick, number]
        """
        return [self.make_firstshot_table().iloc[0]['player_name'], self.make_firstshot_table().iloc[0]['number_shot']]

    def full_best_score(self):
        return self.make_firstshot_table().loc[self.make_firstshot_table()['score_firstshot'] == 0.4][
            'player_name'].to_list()
    def get_team_name(self, player_name):
        if player_name in self.get_all_players()['player_name'].values:
            return self.get_all_players().loc[self.get_all_players()['player_name'] == player_name]['team_name'].values[0]
        else:
            return 'Игрок не принимал участие в турнире'
    def save_df(self,year):
        """
        saving all df for file
        """
        self.get_role().to_csv(f'year/role.csv')
        self.get_all_players().to_csv(f'year/players.csv')