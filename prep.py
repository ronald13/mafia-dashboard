import plotly.graph_objects as go
import plotly.express as px
import math
import pandas as pd
import numpy as np
from dash import  dash_table
from plotly.subplots import make_subplots
from styling import color_list
template = 'plotly_dark'
# from dashboard import marker_color_full
marker_color_full = ['#C0D8C0', '#F5EEDC','#3D0C11', '#DD4A48', '#ECB390', '#05668D', '#4B5842', '#387780', '#756D54', '#587792']


color1 = ['#2A0944', '#3FA796', '#FEC260', '#A10035']
marker_color = ['#C0D8C0', '#F5EEDC', '#DD4A48', '#ECB390']

def create_tornado(df, team1, team2, marker_color=marker_color):
    #transpose df and change header and reindex
    df = df.T
    df.columns = df.iloc[0]
    df = df.drop(df.index[0]).reset_index().rename(columns={'index': 'team_name'})
    df.reset_index(drop=True, inplace=True)
    df = df.replace({'score': 'Победы', 'score_dop': 'Доп баллы', 'score_minus': 'Штрафы', 'score_firstshot': 'ЛХ',
                     'number_shot': 'Отстрелы', 'Ci': 'Ci коэф'}).reindex([4, 3, 2, 1, 5, 0])

    # create subplots

    fig = make_subplots(rows=1, cols=2, specs=[[{}, {}]], shared_xaxes=False,
                        shared_yaxes=True, horizontal_spacing=0)

    fig.add_trace(go.Bar(x=df[team1],
                            y=df['team_name'],
                            text='    ' + df[team1].map('{:,.1f}'.format),
                            # Display the numbers with thousands separators in hover-over tooltip
                            textposition='inside',
                            hovertemplate='<b>' + df['team_name']+ ' :</b>'+ '%{text}'+'<extra></extra>',
                            orientation='h',
                            width=0.7,
                            showlegend=False,
                            marker_color=marker_color[0]),
                     1, 1)  # 1,1 represents row 1 column 1 in the plot grid

    fig.add_trace(go.Bar(x=df[team2],
                            y=df['team_name'],
                            text=df[team2].map('{:,.0f}'.format) + '     ',
                            textposition='inside',
                            hovertemplate='<b>' + df['team_name'] + ' :</b>'+ '%{text}'+'<extra></extra>',
                            orientation='h',
                            width=0.7,
                            showlegend=False,
                            marker_color=marker_color[2]),
                     1, 2)  # 1,2 represents row 1 column 2 in the plot grid

    fig.update_xaxes(showticklabels=False, title_text=team1, row=1, col=1, range=[30,0 ], showgrid=False)
    fig.update_xaxes(showticklabels=False, title_text=team2, row=1, col=2, showgrid=False)

    fig.update_layout(
        template=template,
        margin=dict(l=0, r=10, t=0, pad=20),
        height=400,
        xaxis1={'side': 'top'},
        xaxis2={'side': 'top'},)

    return fig

def simple_bar(df, inputheight=200):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df['value'][::-1].values,  y=df['referee_name'][::-1].values, marker=dict(color=color_list[len(df)]),  orientation="h", textfont=dict(color='black')))

    fig.update_layout(height=inputheight,
                      template=template,
                      margin={'t': 20, 'r': 0, 'l': 0, 'b': 20},)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False )
    fig.update_traces(hoverlabel_bgcolor='#ffffff',  hovertemplate='<b>%{y}</b><br>' + '%{x:.1f}' +'%' + '<extra></extra>', textfont=dict(color='#313844'), texttemplate='<b>%{x:.1f}' +'% </b>', marker=dict(line=dict(width=0)))
    fig.update_yaxes(titlefont_size=15, color='black', showgrid=False, ticklabelposition='inside')

    return fig
def stacked_bar(x_left, x_right, y,  inputheight, chart='DB'):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_left,
                         y=y,
                         orientation='h',
                         name='Мирные',
                         customdata=x_left,
                         # hovertemplate = "<b>%{y}</b><br>Score:%{customdata}<extra></extra>",
                         marker_color='#DD4A48',
                         # textfont=dict(color='black')
                         ))
    fig.add_trace(go.Bar(x=x_right ,
                         y =y,
                         orientation='h',
                         name='Мафия',
                         # hovertemplate="<b>%{y}</b><br>Score:%{x}<extra></extra>",
                         marker_color='#C0D8C0',
                         # textfont=dict(color='black')
                         ),
                         )

    fig.update_layout(barmode='relative',
                      height=inputheight,
                      margin={'t': 30, 'r': 0, 'l': 0, 'b': 20, 'pad':10},
                      template='plotly_white',
                      yaxis_autorange='reversed',
                      bargap=0.2,
                      legend_orientation ='h',
                      legend_x=0.1, legend_y=0,
                      showlegend=False,
                      font=dict(
                          color="#fff"
                      ),
                      # legend=dict( xanchor="right",),
                        yaxis = dict(color="#fff")
                      )

    if chart == 'DB':

        fig.update_xaxes(title='<b>ДБ</b>', showgrid=False, showticklabels=False, zeroline=False, color='#fff')
        fig.update_traces( hoverlabel_bgcolor='#ffffff',  hovertemplate='<b>%{y}</b><br>' + '%{x:.1f}' +' балл' + '<extra></extra>',
                           textfont=dict(color='#313844'),
                           texttemplate='<b>%{x:.1f}</b>', marker=dict(line=dict(width=0)))
        fig.update_yaxes(titlefont_size=15, color="red", showgrid=False, ticklabelposition='inside')
    elif chart == 'win/lose' :
        fig.update_layout(showlegend=True)
        fig.update_xaxes(title='<b>Победы</b>', showgrid=False, showticklabels=False, zeroline=False, color='#fff')
        fig.update_traces(hoverlabel_bgcolor='#ffffff',
                          hovertemplate='<b>%{y}</b><br>' + '%{x:.0f}' + '<extra></extra>',
                          textfont=dict(color='#313844'),
                          texttemplate='<b>%{x:.0f}</b>',
                          textangle=0, marker=dict(line=dict(width=0)))

    return fig
def simple_pie(colors= ['red', 'black'], title='WIN', values=[40, 60]):
    fig = go.Figure()
    fig.add_trace(
        go.Pie(values=values,
               labels=['мирный', 'мафия'], hole=0.5,
               marker_colors=colors))

    fig.update_traces(hoverinfo='label+percent',
                       textinfo='percent', textfont_size=10)
    fig.update_layout(
        template=template,
        margin={'t': 0, 'r': 0, 'l': 0, 'b': 0},
        height=80,
        width=100,
        showlegend=False,
    )
    fig.add_annotation(x=0.5, y=0.5,
                        text=title,
                        font=dict(size=10, family='Open sans',
                                  color='#f7f7f7'),
                        showarrow=False)
    return fig

def draw_pie(df):
    fig = go.Figure()
    fig.add_trace(
        go.Pie(labels=df['state'].to_list(),
               values=df['sum'].to_list(),
               pull=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0.2],
               hole=0.5,
               marker_colors=marker_color_full,
               ))

    fig.update_traces(hoverinfo='label+percent',
                       textinfo='percent', textfont_size=10)
    fig.update_layout(
        template=template,
        margin={'t': 0, 'r': 0, 'l': 0, 'b': 0},
        height=370,
        width=370,
        showlegend=False,
    )
    fig.add_annotation(x=0.5, y=0.5,
                        text='<b>Смета</b>',
                        font=dict(size=14, family='Open sans',
                                  color='#f7f7f7'),
                        showarrow=False)
    return fig

def make_spider(values, param=['Title','#C0D8C0']):
    fig = go.Figure(
        go.Scatterpolar(
            r=values,
            theta=[f'Стол {table}' for table in range(1, len(values)+1)],
            fill='toself',
            # mode="lines",
            marker_color=param[1],
            hovertemplate='%{theta}' + '<br>' +
                          '<b>Сыграно: ' + '%{r}'+
                          '<extra></extra>',
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
            visible=True,
            range=[0, 8],
            ),

        ),


        margin={'t': 40, 'r': 45, 'l': 45, 'b': 0, 'pad': 10},
        template=template,
        showlegend=False,
        title=param[0],
        title_x=0.5,
        title_font_color=param[1],
    )
    return fig

def text_fig(text=''):
    figure = go.Figure()
    figure.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[
                 {
                "text": text,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {
                    "size": 24,
                    "color": "#fff",
                }
            }
        ]
    )
    return figure


def create_box_bars(values, param='#dsdss'):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], y=values,
                         marker_color=param,
                         name='expenses',
                         hovertemplate='Бокс: ' + '<b>%{x}</b>' + '<br>' +
                                       'Сыграно: ' + '<b>%{y}</b>' +
                                       '<extra></extra>',
                         ))
    fig.update_traces(texttemplate=['%{y}' if x > 0 else '' for x in values],
                      textposition='outside')
    fig.update_yaxes(visible=False,
                     range=[0, 10])
    fig.update_xaxes(
                     range=[0.5, 10.5],
                     zeroline=False,
                     # visible=False,
                     showgrid=False,
                     linecolor='grey', linewidth=2,
                     tickfont_size=10,
                     tickmode="array", tickvals=np.arange(1, 11, 1), ticktext=[str(x) for x in range(1, 11)],
                     fixedrange=True, tickangle=0)
    fig.update_layout(
        autosize=True,
        template=template,
        height=160,
        margin={'t': 0, 'r': 10, 'l': 10, 'b': 10, 'pad': 0},
        showlegend=False,
    )
    return fig

def create_heatmap(df):
    """
    Создает компактную тепловую карту средних оценок игрок-судья
    """

    means = df.pivot_table(values='score_dop', index='player_name', columns='referee_name', aggfunc='sum')
    counts = df.pivot_table(values='score_dop', index='player_name', columns='referee_name', aggfunc='count').fillna(0)

    fig = go.Figure(data=go.Heatmap(
        z=means,
        x=means.columns,
        y=means.index,
        colorscale='Greys',
        text=means.round(2).astype(str) + '<br>(' + counts.astype(int).astype(str) + ' игр-а)',
        texttemplate='%{text}',
        xgap= 10,
        ygap= 10,
        textfont={"size": 10},
        hovertemplate='%{y} - %{x}<br>Сумма ДБ: %{z:.2f}<extra></extra>',
        showscale=False
    ))

    fig.update_layout(
        title=None,
        width=700,
        # height=600,
        xaxis={'side': 'top', 'showline': False},
        yaxis={ 'showline': False},
        margin=dict(l=10, r=10, t=20, b=10, pad=10)


    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)

    return fig