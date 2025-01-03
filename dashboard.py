import os
import pandas as pd
import numpy as np
import json
from dash import Dash, dcc, html, Input, Output, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
from prep import create_tornado, simple_bar, stacked_bar, simple_pie, draw_pie, make_spider, text_fig, create_box_bars, create_heatmap
from styling import template, marker_color, marker_color_full, color_list
from solver import Mafia, merge_two_dicts
from loguru import logger
import json



pd.options.mode.chained_assignment = None  # default='warn'

here = os.path.abspath(os.path.dirname(__file__))
prefix = os.environ.get("DASH_PREFIX", "/")

WINNER_ORDER = (1, 0, 2)
PLAYERS_IN_TEAM = 4
color_schemes = ['rgb(243,243,243)', 'rgb(206,217,216)', 'rgb(152,171,184)', 'rgb(125,148,163)', 'rgb(93,114,125)',
              'rgb(67,84,92)']
GAME_NUMBER = 14


# teams = teams.replace({'РБФ':'RBF', 'Mafia house 1': 'Mafia House I', 'Mafia house': 'Mafia House', 'Медуза 1': 'Медуза I'})
#

def get_data(year, games_number=GAME_NUMBER):
    current_dir = f"data/{year}/"
    with open(current_dir + 'teams.json') as f:
        teams = pd.json_normalize(data=json.load(f),
                                  record_path='tplayer',
                                  meta=['name']
                                  )
    teams.rename(columns={'name': 'team_name'}, inplace=True)

    with open(current_dir + 'tstata.json') as f:
        games = pd.json_normalize(data=json.load(f),
                                  record_path=['gameplayer'],
                                  meta=['date', 'table', 'number', 'winner_id', 'WinnerName']
                                  )
    games.rename(columns={'boxNumber': 'box_number',
                          'PlayerName': 'player_name'},
                 inplace=True)
    with open(current_dir + 'tstata.json') as f:
        firstshot = pd.json_normalize(data=json.load(f))

    referee = pd.read_csv(current_dir + 'referee.csv')

    logger.info("Data has been loaded")
    return games, teams, firstshot, referee

kchb_by_years = {2024: Mafia(*get_data(2024, GAME_NUMBER)),
                 2023: Mafia(*get_data(2023, GAME_NUMBER)), 2022: Mafia(*get_data(2022, GAME_NUMBER)),
                 2021: Mafia(*get_data(2021, GAME_NUMBER)), 2020: Mafia(*get_data(2020, GAME_NUMBER)),
                 2019: Mafia(*get_data(2019, GAME_NUMBER)), 2018: Mafia(*get_data(2018, GAME_NUMBER))
                 }

app = Dash(
    __name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
    url_base_pathname=prefix,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    assets_folder=os.path.join(here, "assets")

)

app.title = "КЧБ | Dashboard"
server = app.server


# DROPDOWN UPDATING
@app.callback(
    [
        # Output('round_win_multi_dropdown', 'options'),
     Output('round_win_referee_dropdown', 'options'),
     Output('table_setting_team_dropdown', 'options'),
     Output('tornado_team_dropdown_1', 'options'),
     Output('tornado_team_dropdown_2', 'options'),
     Output('heatmap_team_dropdown', 'options')],
     Input('YearSelector', 'value')
)
def update_dropdown_options(year):
    kchb = kchb_by_years.get(year)
    # if not kchb:
    #     return
    teams_list = kchb.teams_list()
    teams_list_options = [{'label': i, 'value': i} for i in teams_list]
    return teams_list_options, teams_list_options, teams_list_options, teams_list_options, teams_list_options

@app.callback(
    [
        # Output('round_win_multi_dropdown', 'value'),
     Output('round_win_referee_dropdown', 'value'),
     Output('table_setting_team_dropdown', 'value'),
     Output('tornado_team_dropdown_1', 'value'),
     Output('tornado_team_dropdown_2', 'value'),
     Output('heatmap_team_dropdown', 'value')
     ],
    [
        # Input('round_win_multi_dropdown', 'options'),
     Input('round_win_referee_dropdown', 'options'),
     Input('table_setting_team_dropdown', 'options'),
     Input('tornado_team_dropdown_1', 'options'),
     Input('tornado_team_dropdown_2', 'options'),
     Input('heatmap_team_dropdown', 'options')
     ],
)
def update_dropdown_values(
                           round_win_referee_dropdown,
                           table_setting_team_dropdown,
                           tornado_team_dropdown_1,
                           tornado_team_dropdown_2,
                           heatmap_team_dropdown
                           ):

    teams_list_value = [k['value'] for k in round_win_referee_dropdown][0]
    teams_list_value_2 = [k['value'] for k in round_win_referee_dropdown][1]
    multi_team_list = [k['value'] for k in round_win_referee_dropdown][0:3]
    return (teams_list_value, teams_list_value, teams_list_value, teams_list_value_2, teams_list_value
            )

# TEAM STATISTIC
@app.callback(
    [Output('top_winner', 'children'),
     Output('personal_winner', 'children'),
     Output('additional_awards', 'children')],
     Input('YearSelector', 'value')
)
def update_graph(year):
    kchb = kchb_by_years.get(year)
    # if not kchb:
    #     return
    top_team = kchb.team_winners()
    personal_winners = kchb.personal_winners()
    player_awards = pd.read_csv(f"data/{year}/" + 'player_awards.csv')
    team_players = kchb.get_all_players()
    playersTeam = [team_players[team_players['team_name'] == top_team[position]]['player_name'].to_list() for position in WINNER_ORDER]

    team_winner = html.Div(
        [
                    html.Div([
                        html.Img(src=f'assets/img/team_place_{position}.png', style={'width': '60px', 'margin-bottom': '20px', }),
                        html.P(top_team[position], className='name_team'),
                        html.P(element[0], className='pearson_team'),
                        html.P(element[1], className='pearson_team'),
                        html.P(element[2], className='pearson_team'),
                        html.P(element[3], className='pearson_team'),
                    ], style={'flex-basis': '33.33%', 'text-align': 'center'}) for position, element in zip(WINNER_ORDER, playersTeam)


        ], style={'display': 'flex', 'width':'100%'})

    personal_winner = html.Div(
        [
                    html.Div([
                        html.Img(src=f'assets/img/place_{position}.png', style={'width': '30px', 'margin': '20px 0 10px 0'}),
                        html.P(personal_winners[position], className='name_team'),
                        html.P(kchb.get_team_name(personal_winners[position]), className='pearson_team'),
                    ], style={'flex-basis': '33.33%', 'text-align': 'center'}) for position in WINNER_ORDER

        ], style={'display': 'flex', 'width': '100%'}),
    image_name_list =player_awards['image_name'].values
    add_awards = html.Div(
        [
                    html.Div([
                        html.Img(src=f'assets/img/{image_name_list[counter]}.png', style={'width': '30px', 'margin-right': '15px'}),
                        html.P(player_awards['award'].values[counter], className='name_team'),
                        html.P(player_awards['player_name'].values[counter], className='pearson_team_add'),
                    ], style={'display': 'flex', 'align-items': 'center', 'margin': ' 5px 0'})
                    for counter in range(0, len(player_awards))

        ])

    return team_winner, personal_winner, add_awards

# BOX STATISTIC
@app.callback(
    [Output('total_teams', 'children'),
     Output('total_games', 'children'),
     Output('win_lose', 'figure'),
     Output('best_score', 'children'),
     Output('most_killed', 'children'),
     Output('total_teams-mobile', 'children'),
     Output('total_games-mobile', 'children'),
     Output('win_lose-mobile', 'figure'),
     Output('best_score-mobile', 'children'),
     Output('most_killed-mobile', 'children')


     ],
     Input('YearSelector', 'value')
)
def update_graph(year):
    kchb = kchb_by_years.get(year)
    if not kchb:
        return
    total_teams = kchb.teams.shape[0]
    total_games = kchb.games.shape[0] / 10

    win_lose_figure = simple_pie(colors=['#E0DDAA', '#A27B5C'], title='', values=[el * 100 for el in kchb.win_lose()])
    most_killed = kchb.death_leader()
    best_score = kchb.full_best_score()
    best_score_layout = html.Div(
        [
            html.Div(
                [
                   html.Div(best_score[counter], className='indicator', style = {'font-size': '19px', 'margin-bottom': '10px'})
                    for counter in range(0, len(best_score))
                ], style={'text-align':'center'}),
        ], className=''),

    most_killed_layout = html.Div(
        [
            html.Div(most_killed[0], className='indicator', style={'font-size': '26px', 'margin-bottom': '10px'}),
            html.Div(most_killed[1], style={'color': '#757575', 'font-size': '14px', 'margin-bottom': '0', 'text-align': 'center' }),
        ], style={}, className=''),


    return (total_teams, total_games, win_lose_figure, best_score_layout,  most_killed_layout,
           total_teams, total_games, win_lose_figure, best_score_layout, most_killed_layout)

# REFEREE PART
@app.callback(
    [Output('best-referee_layout', 'children'),
     Output('referee-statistic', 'children')],
     Input('YearSelector', 'value'),
     Input('TypeRefereeChart', 'value')
)
def update_graph(year, type_chart):
    kchb = kchb_by_years.get(year)
    if not kchb:
        return
    referee_score = kchb.referee_score()


        # fig = stacked_bar(referee_score, inputheight=200)

    if year in [2023, 2022, 2020]:
        referee_voting = pd.read_csv(f"data/{year}/" + 'referee_voting.csv')
        layout = dcc.Graph(figure=simple_bar(referee_voting, inputheight=200), config={'displayModeBar': False},
                           style={'margin-bottom': '20px'}),
    else:
        layout = html.P("Голосование не проводилось",
                        style={'height': '200px', 'font-size': '20px', 'color': '#fff', 'display': 'flex',
                               'align-items': 'center', 'justify-content': 'center'})

    referee_results = kchb.game_results()
    referee_results = referee_results.merge(kchb.referee, how='left', on='table_number')
    referee_pie_layout = html.Div(
                                [
                                    dcc.Graph(figure=stacked_bar(referee_results['citizen_win (number)'],
                                                                 referee_results['mafia_win (number)'],
                                                                 referee_results['referee_name'],
                                                                 inputheight=200,
                                                                 chart='win/lose'
                                                                 ), config={'displayModeBar': False},
                                              style={'margin-bottom': '20px', 'width': 350}),

                                ], style={'display': 'flex', 'width': '100%',
                                          'justify-content': 'space-between',
                                          'flex-wrap': 'wrap'}),

    if 'show_score' not in type_chart:
        referee_pie_layout
    else:
        referee_pie_layout = dcc.Graph(figure=stacked_bar(referee_score['score_minus'], referee_score['score_dop'], referee_score['referee_name'],  inputheight=200), config={'displayModeBar': False},
                           style={'margin-bottom': '20px', 'width': 350}),



    return layout, referee_pie_layout


# SPIDER PLOT
@app.callback(
     Output('spider_layout', 'children'),
    [Input('table_setting_team_dropdown', 'value'),
     Input('YearSelector', 'value')],
)
def update_graph(team, year):
    kchb = kchb_by_years.get(year)
    if not kchb:
        return

    df_tables = kchb.get_table_distribution()
    df_boxes = kchb.get_box_distribution()

    df_tables = df_tables[df_tables['team_name'] == team]
    df_boxes = df_boxes[df_boxes['team_name'] == team]
    tables_list = df_tables['table_number_count'].to_list()
    boxes_list = df_boxes.iloc[:, 2:].values.flatten().reshape(4, 10).tolist()

    players = df_tables['player_name'].to_list()
    spider_layout = html.Div(
        [
            html.Div([
                dcc.Graph(figure=make_spider(tables_list[counter],
                                             param=[players[counter], color_list[len(df_tables)][counter]]),
                          config={'displayModeBar': False},
                          className='spider_plot',
                          style={}
                          ),
                dcc.Graph(figure=create_box_bars(values=boxes_list[counter], param=color_list[len(df_tables)][counter]),
                          config={'displayModeBar': False},
                          style={'marginTop': '-80px'}
                          )
            ], className="spider_plot", style={'flex-basis': '25%',})
            for counter in range(0, PLAYERS_IN_TEAM)


        ], style={'display': 'flex', 'width': '100%', 'flex-wrap': 'wrap'})

    return spider_layout


@app.callback(
    Output('player_referee_heatmap', 'figure'),
    Input('heatmap_team_dropdown', 'value'),
    Input('YearSelector', 'value')
)
def update_graph(team, year):
    kchb = kchb_by_years.get(year)
    if not kchb:
        return

    print(team)

    df = kchb.get_info_about_all_games().copy()

    # filter data with team_name
    df = df[df['team_name'] == team]

    df = df.groupby(['player_name', 'table_number'])['score_dop'].sum().reset_index()
    df = df.merge(kchb.referee, how='left', on='table_number')

    print(df)

    heatmap_data = df.pivot_table(
        values='score_dop',
        index='player_name',
        columns='referee_name',
        aggfunc='sum'
    )
    games_count = df.pivot_table(
        values='score_dop',
        index='player_name',
        columns='referee_name',
        aggfunc='count'
    ).fillna(0)


    fig = create_heatmap(df)

    return fig


@app.callback(
    Output('ranking_track', 'figure'),
    Input('ranking_track-checklist', 'value'),
    Input('YearSelector', 'value')
)
def update_graph(checklist, year):
    kchb = kchb_by_years.get(year)
    if not kchb:
        return

    if checklist == ['win']:
        type = 'win'
    elif sorted(checklist) == ['dops', 'win']:
        type = 'dops'
    elif sorted(checklist) == ['dops', 'firstshot', 'win']:
        type = 'firstshot'
    elif sorted(checklist) == ['Ci', 'win', ]:
        type = 'Ci'
    elif sorted(checklist) == ['firstshot', 'win']:
        type = 'win+firstshot'
    elif sorted(checklist) == ['Ci', 'dops', 'win']:
        type = 'dops+Ci'
    elif sorted(checklist) == ['Ci', 'firstshot', 'win']:
        type = 'no_dops'
    elif sorted(checklist) == ['Ci', 'dops', 'firstshot', 'win',]:
        type = 'total_score'
    else:
        type = None

    df_Active = kchb.position_tracking(type=type)


    def generate_colors(num_teams):
        """
        Генерирует цветовую палитру с яркими цветами для топ-3 и пастельными для остальных

        Args:
            num_teams (int): Общее количество команд

        Returns:
            list: Список цветов для графика
        """
        # Яркие цвета для топ-3
        bright_colors = [
            '#d4af37',  # Gold - 1 место
            '#cccccc',  # Silver - 2 место
            '#ff6600'  # Bronze - 3 место
        ]

        if num_teams <= 3:
            return bright_colors[:num_teams]

        return bright_colors + ['#757575'] * (num_teams - 3)

    teams_number = len(kchb.teams_list())
    colors = generate_colors(teams_number)
    rounds = ['Тур ' + str(x) for x in range(1, 14 + 1)]
    fig = go.Figure()

    # Сортируем команды по их рангу в первом туре
    team_order = df_Active[df_Active['round_number'] == 14].sort_values('rank')['team_name'].tolist()
    team_order1 = df_Active[df_Active['round_number'] ==1].sort_values('rank')['team_name'].tolist()
    top3_team = team_order[:3]

    for i, team in enumerate(top3_team):
        team_data = df_Active[df_Active['team_name'] == team]

        fig.add_trace(go.Scatter(
            x=team_data['round_number'],
            y=team_data['rank'],
            mode='lines+markers',
            name=team,
            line=dict(color=colors[i], width=5),
            marker=dict(size=8),
            text=[team] * len(team_data),
            customdata=np.stack(
                (team_data['rank'].astype('str'), team_data['cumulative_metric'].round(2).astype('str')),
                axis=-1),
            hovertemplate='<b>%{text}</b><br>'
                          '%{x} - %{customdata[0]} место <br><br>' +
                          '<b>%{customdata[1]}</b> баллов' +
                          '<extra></extra>',
        ))


    for i, team in enumerate(team_order[3:]):
        team_data = df_Active[df_Active['team_name'] == team]

        fig.add_trace(go.Scatter(
            x=team_data['round_number'],
            y=team_data['rank'],
            mode='lines+markers',
            name=team,
            line=dict(color='#757575', width=5),
            marker=dict(size=8),
            text=[team] * len(team_data),
            # custom data for hovertemplate with full scores
            customdata=np.stack(
                (team_data['rank'].astype('str'),
                 team_data['cumulative_metric'].round(2).astype('str')), axis=-1
            ),
            hovertemplate='<b>%{text}</b><br>'
                          '%{x} - %{customdata[0]} место <br><br>' +
                          '<b>%{customdata[1]}</b> баллов' +
                          '<extra></extra>',
        ))



    # Настройка макета с цветными метками
    fig.update_layout(
        autosize=True,
        margin=dict(l=5, r=10, t=20, pad=8),
        template=template,
        showlegend=False,
        xaxis_title='Номер тура',
        # yaxis_title='Место в турнире',
        yaxis=dict(
            autorange='reversed',  # Инверсия оси Y
            range=[teams_number, 1],  # Диапазон от 10 до 1 места
            tickmode='array',
            tickvals=list(range(1,teams_number + 1)),
            ticktext=team_order1,  # Подписи команд
            # tickfont=dict(color='red')
        ),
        xaxis=dict(
            range=[0.7, 15],
            tickmode = 'array',
            tickvals = list(range(1, 15)),
            ticktext = rounds,

        ),
        height=600,
    )

    fig.add_annotation(
        x=15,
        y=1,
        text="<b>1 место</b><br>",
        showarrow=False,
        xanchor="right",
        font_color='#d4af37',
    )
    fig.add_annotation(
        x=15,
        y=2,
        text="<b>2 место</b><br>",
        showarrow=False,
        xanchor="right",
        font_color='#cccccc',
    )
    fig.add_annotation(
        x=15,
        y=3,
        text="<b>3 место</b><br>",
        showarrow=False,
        xanchor="right",
        font_color='#ff6600',
    )

    return fig



@app.callback(
     Output('round_win_referee', 'figure'),
     [Input('round_win_referee_dropdown', 'value'),
     Input('YearSelector', 'value')],
)
def update_graph(team, year):
    kchb = kchb_by_years.get(year)
    if not kchb:
        return
    fig = go.Figure()
    rounds = ['Тур ' + str(x) for x in range(1, 14 + 1)]
    df_Active = kchb.wind_by_round_referee()
    df_Active = df_Active[df_Active['team_name'] == team]
    referee = kchb.referee['referee_name'].to_list()

    for i, ref in zip(range(0, len(referee)), referee):
        fig.add_traces(
            go.Bar(name=ref, x=rounds, y=df_Active['win_list'].values[0][i], width=0.95,
                   marker_color=marker_color_full[i],
                   hovertemplate='%{x}' + '<br>' +
                                 'Победа' + '<br>' +
                                 'Судья:' + '<b>' + ref + '</b>' + '<br>' +
                                 '<extra></extra>',
                   )
        )

    fig.update_layout(barmode='stack', legend_title_text='<b>Судьи: </b>',
                      template=template,
                      legend=dict(
                          x=0,
                          y=1.2,
                          orientation="h"),
                      )

    fig.update_xaxes(title='<b>Номер тура</b>')
    fig.update_yaxes(title='<b>Победы</b>')

    return fig

@app.callback(
    Output('tornado_graph', 'figure'),
    Input('tornado_team_dropdown_1', 'value'),
    Input('tornado_team_dropdown_2', 'value'),
    Input('YearSelector', 'value')
)
def update_Tornado(team1, team2, year):
    kchb = kchb_by_years.get(year)
    if not kchb:
        return
    tor_df = kchb.team_metrics()
    fig = create_tornado(tor_df, team1, team2, marker_color=marker_color)

    return fig

@app.callback(
    Output('ranking_track-checklist', 'value'),
    Input('ranking_track-checklist', 'value'),
)
def enforce_win_selection(selected_values):
    if 'win' not in selected_values:
        return selected_values + ['win']
    return selected_values


app.layout = html.Div([

    html.Div([
        html.H1('Командный чемпионат Беларуси', style={'line-height': '1.1', 'letter-spacing': '-0.81px', 'color': '#f99746',
                                              'font-family': 'Roboto Slab', 'font-size': '42px', 'font-weight': 'bold',
                                              'margin': '0 0 20px 0', 'text-transform': 'uppercase'}),

        html.P('#кчб2022 #брест #мафиянассвязала',
               style={'width': '350px', 'font-size': '14px', 'margin-bottom':'10px', 'font-weight':'bold', 'color':'#757575'}, className='header__text'),

        html.Div([
            html.Div([
                html.P('Турнирная статистика за года', className='title'),
                html.Div([
                    dcc.Dropdown(
                        id="YearSelector-mobile",
                        options=[
                             {'label': '2024', 'value': 2024},
                             {'label': '2023', 'value': 2023},
                             {'label': '2022', 'value': 2022},
                             {'label': '2021', 'value': 2021},
                             {'label': '2020', 'value': 2020},
                             {'label': '2019', 'value': 2019},
                             {'label': '2018', 'value': 2018},
                                 ],
                        className="",
                        # labelCheckedClassName="date-group-labels-checked",
                        # inline=True,
                        value=2024,
                        style={'width': '200px'}
                        # style={'margin': '0 20px 20px 0'}
                    ),
                ], style={'display': 'flex', 'flex-wrap': 'wrap'}),

            ], className='vrectangle'),
            html.Div([
                html.Div(
                    [
                        html.Div("Количество игроков", className='title'),
                        html.Div(id='total_teams-mobile', className='indicator'),
                    ], style={}, className='square'),

                html.Div(
                    [
                        html.Div("Сыграно игр", className='title', style={'margin-bottom': '25px'}),
                        html.Div(id='total_games-mobile', className='indicator'),
                    ], style={}, className='square'),
                html.Div(
                    [
                        html.Div("Всего фолов", className='title', style={'margin-bottom': '25px'}),
                        html.Div('644', className='indicator'),
                    ], style={}, className='square'),
                html.Div(
                    [
                        html.Div("Победы", className='title'),
                        html.Div([
                            dcc.Graph(id='win_lose-mobile', config={'displayModeBar': False}, style={}),
                        ]),
                    ], style={}, className='square'),

                html.Div(
                        [
                            html.Div("Полный ЛХ", className='title', style={'margin-bottom': '25px'}),
                            html.Div(id='best_score-mobile'),
                        ], style={},
                           className='square'),

                html.Div(
                    [
                        html.Div("Смертник", className='title', style={'margin-bottom': '25px'}),
                        html.Div(id='most_killed-mobile'),
                    ], style={},
                    className='square'),

            ], style={'margin-bottom': '20px'}, className='square__block'),
        ], className='year__selector-mobile'),

        html.Div([
            html.Div("Призеры турнира", className='title'),
            html.Div(id='top_winner', style={'display': 'flex', 'width':'100%'})


        ], className='vrectangle'),
        html.Div([
            html.Div("Личный зачет", className='title'),
            html.Div(id='personal_winner', style={'display': 'flex', 'width': '100%'})

        ], className='vrectangle'),
        html.Div([
                html.Div("Дополнительные номинации", className='title'),
                html.Div(id='additional_awards', style={'display': 'flex', 'width': '100%'})

        ], className='vrectangle'),


        html.Div([
            html.Div("Cудейская аналитика", className='title'),
            html.P('Статистика красных/черных',
                   style={'color': '#757575', 'font-size': '12px',  'margin-bottom': '0'}),
            dcc.Checklist(
                id='TypeRefereeChart',
                options=[
                    {'label': 'ДБ', 'value': 'show_score'},
                ],
                value=[''],
                labelStyle={'display': 'flex', 'align-items': 'center'} ,
                style={'position': 'absolute', 'top':'22px', 'right':'35px', 'color':'#fff', 'font-size':'10px'}
            ),
            html.Div(id ='referee-statistic')],
            className='vrectangle relative'
        ),
        html.Div([
            html.Div("Лучший судья турнира", className='title'),
            html.P('Голосование только среди участников турнира',
                   style={'color': '#757575', 'font-size': '12px',  'margin-bottom': '0'}),

            html.Div(id='best-referee_layout', style={'max-width':'100%', 'width':'100%'}),
            ],
            className='vrectangle relative'
        ),



        #     html.Div([
        #             html.Div("Смета турнира", className='title'),
        #             html.P('Полный файл будет прикреплен в группе ВК',
        #                    style={'color': '#757575', 'font-size': '12px',  'margin-bottom': '0'}),
        #             html.Div([
        #                     dcc.Graph(figure=draw_pie(smeta),  config={'displayModeBar': False}, style={}),
        #
        #             ], style={'display':'flex', 'width':'100%', 'justify-content':'space-between'}),
        # ],  style=merge_two_dicts(rectangle, {'flex-direction': 'column'})),
        #
        # html.Div(id='ringle'),
    ], style={'padding': '10px 20px', 'flex-basis':'25%'}),

    html.Div([
        html.Div([
            html.Div([
                    html.P('Турнирная статистика за года', className='title'),
                    html.Div([
                                dbc.RadioItems(
                                        id="YearSelector",
                                        options=[
                                             {'label': '2024', 'value': 2024},
                                             {'label': '2023', 'value':2023},
                                             {'label': '2022', 'value':2022},
                                             {'label': '2021', 'value':2021},
                                             {'label': '2020', 'value':2020},
                                             {'label': '2019', 'value':2019},
                                             {'label': '2018', 'value':2018},
                                                 ],
                                        labelClassName="date-group-labels",
                                        labelCheckedClassName="date-group-labels-checked",
                                        inline=True,
                                        value=2024,
                                        # style={'margin': '0 20px 20px 0'}
                                    ),
                            ], style={'display': 'flex', 'flex-wrap':'wrap'}),

                        ],  className='vrectangle'),
            html.Div([
                    html.Div(
                        [
                            html.Div("Количество игроков", className='title'),
                            dcc.Loading(
                                [
                                    html.Div(id='total_teams', className='indicator'),
                                ],
                                type="circle",
                                style={
                                    "position": "relative",
                                    "backgroundColor": "none",
                                },
                            ),

                        ], style={}, className='square'),

                    html.Div(
                        [
                            html.Div("Сыграно игр", className='title', style={'margin-bottom':'25px'}),
                            dcc.Loading(
                                    [
                                        html.Div(id='total_games', className='indicator'),
                                    ],
                                    type="circle",
                                    style={
                                        "position": "relative",
                                        "backgroundColor": "none",
                                    },
                                ),

                        ],  style={}, className='square'),
                    html.Div(
                        [
                            html.Div("Всего фолов", className='title', style={'margin-bottom': '25px'}),
                            dcc.Loading(
                                [
                                    html.Div('644', className='indicator'),
                                ],
                                type="circle",
                                style={
                                    "position": "relative",
                                    "backgroundColor": "none",
                                },
                            ),

                        ], style={}, className='square'),
                    html.Div(
                        [
                            html.Div("Победы", className='title'),
                            dcc.Loading(
                                    [
                                        dcc.Graph(id="win_lose",
                                                config={'displayModeBar': False},
                                       )],
                                    type="circle",
                                    style={
                                        "position": "relative",
                                        "backgroundColor": "none",
                                    },

                                ),

                        ], style={ }, className='square'
                    ),
                    html.Div(
                        [
                            html.Div("Полный ЛХ", className='title', style={'margin-bottom': '25px'}),
                            dcc.Loading(
                                [
                                    html.Div(id='best_score'),
                                ],
                                type="circle",
                                style={
                                    "position": "relative",
                                    "backgroundColor": "none",
                                },
                             ),

                        ], style={}, className='square'),

                    html.Div(
                        [
                            html.Div("Смертник", className='title', style={'margin-bottom': '25px'}),
                            dcc.Loading(
                                [
                                    html.Div(id='most_killed'),
                                ],
                                type="circle",
                                style={
                                    "position": "relative",
                                    "backgroundColor": "none",
                                },
                             ),

                        ], style={},  className='square'),


            ], style={'margin-bottom': '20px'},className='square__block'),
        ], className='year__selector-desktop'),



        html.Div([
            html.P('Дорожная карта команд', className='title'),
            html.P('Цветом выделены только первые три места. Для слежения за своим фаворитом - выбери его в дропдауне. ',
                   style={'color': '#757575', 'font-size': '12px',  'margin-bottom': '0',}),
            html.Div([
                    dcc.Checklist(
                        id='ranking_track-checklist',
                        options=[
                            {'label': html.Div([html.Span('only' ), html.Span(' WIN')], className='checklist_label' ), 'value': 'win'},
                            {'label': html.Div([html.Span('with' ), html.Span(' ДБ')], className='checklist_label' ), 'value': 'dops'},
                            {'label': html.Div([html.Span('with' ), html.Span(' ЛХ')], className='checklist_label' ), 'value': 'firstshot'},
                            {'label': html.Div([html.Span('with' ), html.Span(' Ci')], className='checklist_label' ), 'value': 'Ci'},
                        ],
                        value=['Ci', 'dops', 'firstshot', 'win' ],
                        inline=True,
                        style={'color': 'white', 'text-align':'left'},
                        className='checklist',
                    )
            ], style={'width':'100%',  'margin-top': '20px'}),
            dcc.Graph(id='ranking_track',
                      config={'displayModeBar': False},
                      style={'max-width': '100%', 'width': '100%'}),
        ], className='vrectangle heatmap__block'),

        html.Div([
            html.P('Количество побед по турам', className='title'),
            html.P('Выбрав интересующую команду, вы можете изучить победы команды по турам в зависимости от судьи',
                   style={'color': '#757575', 'font-size': '12px',  'margin-bottom': '0'}),
            dcc.Dropdown(
                        id='round_win_referee_dropdown',
                        options=[],
                        placeholder='Выбери команду',
                        style={'width': '250px', 'margin': '10px 0'},
                    ),
            dcc.Graph(id='round_win_referee', config={'displayModeBar': False}, style={'max-width': '100%', 'width': '100%'}),
        ], className='vrectangle'),

        #
        html.Div([
            html.P('Рассадка турнира', className='title'),
            html.P('Выбрав команду, вы можете изучить насколько плоха была наша рассадка',
                   style={'color': '#757575', 'font-size': '12px',  'margin-bottom': '0'}),
            dcc.Dropdown(
                        id='table_setting_team_dropdown',
                        options=[],
                        placeholder='Выбери команду',
                        style={'width': '250px', 'margin': '10px 0'},
                    ),
            html.Div(id='spider_layout', style={'display':'flex', 'width':'100%', 'flex-wrap':'wrap'})

        ], className='vrectangle'),

        #
        html.Div([
            html.P('Сравнительная характеристика ', className='title'),
            html.P('Выберите две команды показатели которых хотите сравнить',
                   style={'color': '#757575', 'font-size': '12px', 'margin-bottom': '20px'}),
            html.Div([
                    dcc.Dropdown(
                        id='tornado_team_dropdown_1',
                        options=[],
                        placeholder='Выбери команду',
                        style={'width':'200px', 'margin-bottom': '10px'},
                    ),
                    dcc.Dropdown(
                        id='tornado_team_dropdown_2',
                        options=[],
                        placeholder='Выбери команду',
                        style={'width': '200px', 'margin-bottom': '20px' },
                    ),
            ], style={'display': 'flex', 'justify-content': 'space-between', 'width': '100%', 'flex-wrap':'wrap'}),
            dcc.Graph(id='tornado_graph',  config={'displayModeBar': False}, style={'max-width': '100%', 'width': '100%'}),

        ], className='vrectangle'),

        html.Div([
            html.P('Анализ получения судейских ДБ ', className='title'),
            html.P('Статистика показывает суммарные ДБ по каждому игроку и судье',
                   style={'color': '#757575', 'font-size': '12px', 'margin-bottom': '20px'}),
            dcc.Dropdown(
                        id='heatmap_team_dropdown',
                        options=[],
                        placeholder='Выбери команду',
                        style={'width': '250px', 'margin': '10px 0'},
                    ),

            dcc.Graph(id='player_referee_heatmap',  config={'displayModeBar': False}, style={'max-width': '100%', 'width': '100%'}),



        ], className='vrectangle'),


        html.Div([
            html.Div([
                html.Img(src='assets/img/logo_white.png', style={'width': '80px'}),
                html.P('© 2018 ШIFFER Inc. Информация для забавы', style={'font-size':'15px', 'color': '#fff', 'margin':'0 10px'}),
                html.A("Перейти на сайт", href='https://statistics.shiffer.by/#/Turnir/41', target="_blank", className='link'),
            ], style={'margin-top': '10px', 'display': 'flex', 'flex-direction': 'row', 'align-items': 'center', 'font-size': '15px', 'text-decoration': 'underline' }, className='footer')

        ], className='vrectangle')

    ], style={'display': 'flex', 'flex-direction': 'column', 'padding': '10px 20px', 'flex-basis':'75%'}),
], style={'display': 'flex'}, className='app__wrapper')

# don't run when imported, only when standalone
if __name__ == '__main__':
    port = os.getenv("DASH_PORT", 8053)
    app.run_server(debug=True, port=port, host="0.0.0.0")