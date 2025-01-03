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

def df_firstshot_with_hit_rate(row, all_games_number):
    """
    Сalculate the shooting rate according to the FIIM formula
    The value B = 0.4 * number of all games in the tournament and rounded to the nearest integer.
    """

    B = round(0.4 * all_games_number) # 6
    if row['number_shot'] <= B:
        return round((row['shot_and_lose'] * 0.3 / B), 4)
    else:
        return 0.3


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

    def make_firstshot_table(self,  type='total'):
        """
        create information about first shot and calculate hit rate for every game
        type: str
            - total - return aggregated table with columns: team_name, team_name, score_firstshot, number_shot,  shot_and_lose, Ci
            - round  - return aggregated table with additional columns: game_id, round_number
        """
        # logger.info('Calculating firstshot table...')
        first_shot = self.first_shot

        col = ['id', 'table', 'number', 'winner_id', 'gamefirstshot.player_id',
               'gamefirstshot.boxNumber', 'gamefirstshot.score']
        firstshot_df = first_shot[col].rename(
            columns={'id': 'game_id', 'number': 'round_number', 'winner_id': 'who_win',
                     'gamefirstshot.player_id': 'player_id',
                     'gamefirstshot.boxNumber': 'boxNumber', 'gamefirstshot.score': 'score'})
        firstshot_df.dropna(subset=['game_id', 'player_id', 'round_number', 'score'], inplace=True)
        firstshot_df['score'] = firstshot_df['score'].astype('float')

        firstshot_df.dropna(subset=['game_id', 'player_id', 'round_number', 'score'], inplace=True)

        firstshot_df = pd.merge(firstshot_df, self.get_all_players()[['player_id', 'player_name', "team_name"]],
                                how="left",
                                on="player_id").rename(columns={'score': 'score_firstshot'})

        firstshot_df['number_shot_by_round'] = firstshot_df.groupby(['player_id', 'round_number'])[
            'score_firstshot'].transform('count')

        firstshot_df['shot_and_lose'] = firstshot_df.groupby('player_id')['who_win'].transform(
            lambda x: (x == 1).sum())  # the player was killed, and the team lost

        firstshot_df['number_shot'] = firstshot_df.groupby(['player_id', ])['round_number'].transform(
            'count')  # total player deaths

        # points for a kill on the first night (Ci) in the current round
        firstshot_df['Ci_by_round'] = firstshot_df.apply(df_firstshot_with_hit_rate, axis=1, args=(14,))
        firstshot_df['Ci_by_round'] = round(firstshot_df['Ci_by_round'] * firstshot_df['who_win'],4)

        firstshot_df['Ci_total'] = round(firstshot_df['Ci_by_round'] * firstshot_df['shot_and_lose'], 4)  # total points for a kill on the first night (Ci)
        firstshot_df['merge_id'] = firstshot_df['round_number'].astype('str') + firstshot_df['team_name']

        # print(firstshot_df[firstshot_df['player_name'] == 'Yesterday'])

        if type == 'total':
            return firstshot_df.groupby(['player_name', 'team_name']).agg(
                score_firstshot=('score_firstshot', 'sum'),
                number_shot=('number_shot_by_round', 'sum'),
                Ci=('Ci_by_round', 'sum'),
            ).reset_index().sort_values(by='number_shot', ascending=False)

        elif type == 'round':
            return firstshot_df

        else:
            logger.error('Calculation type not recognized!')
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
    def position_tracking(self, type='win'):
        """
        get a dataframe with information about the team's position tracking by each round
        result: dataframe
        """
        logger.info('Calculation position_tracking')
        df_temp = self.get_info_about_all_games().copy()
        df_temp['total_score'] = df_temp['score'] + df_temp['score_dop'] + df_temp['score_minus']
        df_temp = df_temp.groupby(['round_number', 'team_name']).agg(only_win=('score', 'sum'),
                                                               total_score=('total_score', 'sum'),
                                                               dop_plus=('score_dop', 'sum'),
                                                               dop_minus=('score_minus', 'sum')) \
            .reset_index()
        df_temp['merge_id'] = df_temp['round_number'].astype('str') + df_temp['team_name']

        firstshot_table = self.make_firstshot_table(type='round').groupby('merge_id').agg(
            score_firstshot=('score_firstshot', 'sum'),
            Ci_by_round=('Ci_by_round', 'sum')).reset_index()

        full_df = df_temp.merge(
            firstshot_table[['merge_id', 'score_firstshot', 'Ci_by_round']],
            how='left',
            on='merge_id'
        )
        full_df.fillna(0, inplace=True)


        # print(full_df.groupby('team_name').agg(only_win=('only_win', 'sum'),
        #                                        total_score=('total_score', 'sum'),
        #                                        # dop_plus=('score_dop', 'sum'),
        #                                        # dop_minus=('score_minus', 'sum'),
        #                                        score_firstshot=('score_firstshot', 'sum'),
        #                                        Ci=('Ci_by_round', 'sum')
        #
        #                                        ).sort_values(by='total_score', ascending=False))

        if type == 'win':
            full_df['cumulative_metric'] = full_df.groupby('team_name')['only_win'].cumsum()
        elif type == 'dops':
            full_df['win+dops'] = full_df['total_score']
            full_df['cumulative_metric'] = full_df.groupby('team_name')['win+dops'].cumsum()
        elif type == 'firstshot':
            full_df['win+firstshot'] = full_df['only_win'] + full_df['score_firstshot']
            full_df['cumulative_metric'] = full_df.groupby('team_name')['win+firstshot'].cumsum()
        elif type == 'dops+Ci':
            full_df['total_score+Ci'] = full_df['total_score'] + full_df['Ci_by_round']
            full_df['cumulative_metric'] = full_df.groupby('team_name')['total_score+Ci'].cumsum()
        elif type == 'win+firstshot':
            full_df['win+firstshot'] = full_df['only_win'] + full_df['score_firstshot']
            full_df['cumulative_metric'] = full_df.groupby('team_name')['win+firstshot'].cumsum()
        elif type == 'no_dops':
            full_df['no_dops'] = full_df['only_win'] + full_df['score_firstshot'] + full_df['Ci_by_round']
            full_df['cumulative_metric'] = full_df.groupby('team_name')['no_dops'].cumsum()
        elif type == 'total_score':
            full_df['total+firstshot+Ci'] = full_df['total_score'] + full_df['score_firstshot'] + full_df['Ci_by_round']
            full_df['cumulative_metric'] = full_df.groupby('team_name')['total+firstshot+Ci'].cumsum()


        elif type == 'Ci':
            full_df['win+ci'] = full_df['total_score'] + full_df['Ci_by_round']
            full_df['cumulative_metric'] = full_df.groupby('team_name')['win+ci'].cumsum()

        full_df['rank'] = full_df.groupby('round_number', group_keys=False).apply(
            lambda group: group.sort_values(by='cumulative_metric', ascending=False).assign(rank=range(1, len(group) + 1)))[
            'rank']
        print('=====After Cumulative Metrics=====')

        return full_df

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
        win_lose = self.get_info_about_all_games()['winner'].value_counts(normalize=True).round(2).reset_index()['proportion'].to_list()
        return win_lose

    def game_results(self):
        """

        :param normalize:
        :return:
        """
        df = self.games[['game_id', 'table', 'winner_id', 'WinnerName']].rename(
            columns={'table': 'table_number', 'WinnerName': 'winner'})
        df = df.groupby('table_number')['winner'].value_counts(normalize=False).round(2).reset_index(name="value")

        df_pivot = df.pivot(index="table_number", columns="winner", values="value").reset_index()

        df_pivot.columns.name = None
        df_pivot.rename(columns={
            "Победа мафии": "mafia_win (number)",
            "Победа мирных": "citizen_win (number)"
        }, inplace=True)

        df_pivot["mafia_win (number)"] = ( df_pivot["mafia_win (number)"] / 10).astype(int)
        df_pivot["citizen_win (number)"] = (df_pivot["citizen_win (number)"] / 10).astype(int)

        # Вычисление процентных значений с округлением
        df_pivot["mafia_win (%)"] = (df_pivot["mafia_win (number)"] /
                                        (df_pivot["mafia_win (number)"] + df_pivot[
                                            "citizen_win (number)"]) * 100).round(0)
        df_pivot["citizen_win (%)"] = (df_pivot["citizen_win (number)"] /
                                         (df_pivot["mafia_win (number)"] + df_pivot[
                                             "citizen_win (number)"]) * 100).round(0)

        return df_pivot
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