import io
import html
import hashlib
import math
from urllib.parse import urlsplit, urlunsplit
import streamlit.components.v1 as components
import uuid
from datetime import date
import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(page_title='DERK | Digital Ethnic Representation of Kazakhstan', page_icon='🗺️', layout='wide')
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)
BASE = Path(__file__).parent
REGIONS = pd.read_csv(BASE / "regions.csv")
COLS = ['record_id','ethnic_group','region','platform','community_name','public_url','language','topic','followers','observed_at','source_url','verification_status','methodology_comment']

@st.cache_data(ttl=60)
def load_data():
    response = supabase.table("observations").select("*").execute()
    return pd.DataFrame(response.data, columns=COLS).fillna("")

# DERK 2.2 visual theme — UI only; data, analytics, and Supabase remain unchanged.
st.markdown(r"""<style>
:root {color-scheme:dark;}
html, body, [data-testid="stApp"], .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {background:#071426 !important;color:#e9f3ff !important;}
[data-testid="stHeader"] {background:rgba(7,20,38,.92) !important;}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {background:#0d2039 !important;color:#e9f3ff !important;}
[data-testid="stSidebar"] * {color:#dcecff;}
[data-testid="stSidebarNav"] {background:transparent !important;}
.block-container {max-width:1440px;padding-top:2.2rem;padding-bottom:3rem;}
h1,h2,h3,h4,p,li,label,[data-testid="stMarkdownContainer"] {color:#e9f3ff;}
h1 {font-size:clamp(1.8rem,4vw,2.8rem)!important;letter-spacing:-.035em;color:#f5fbff!important;}
h2,h3 {color:#eff8ff!important;}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {color:#9fb6d1!important;}
[data-testid="stMetric"] {background:linear-gradient(145deg,#112944,#0d2139);border:1px solid #24445f;border-radius:16px;padding:14px 18px;min-height:100px;}
[data-testid="stMetricLabel"] * {color:#a9c3db!important;}
[data-testid="stMetricValue"] * {color:#f2fbff!important;}
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stFileUploader"] section {background:#122a47!important;color:#f1f8ff!important;border-color:#345674!important;border-radius:12px!important;}
[data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"], [data-baseweb="popover"] {background:#132b48!important;color:#fff!important;}
[role="option"] {background:#132b48!important;color:#fff!important;}
[role="option"]:hover {background:#245177!important;}
[data-testid="stSelectbox"] svg {fill:#9cdff1!important;}
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] button {background:#173e60!important;border:1px solid #32799b!important;color:#effcff!important;border-radius:12px!important;}
.stButton > button:hover, .stDownloadButton > button:hover {background:#205b7c!important;border-color:#5bdaf0!important;}
[data-testid="stAlert"] {background:#102c47!important;border:1px solid #285676!important;color:#d9f0ff!important;border-radius:12px!important;}
[data-testid="stDataFrame"], [data-testid="stDataEditor"], [data-testid="stForm"] {background:#0e233b!important;border-radius:14px;border:1px solid #28435d;}
hr {border-color:#25435e!important;}
.derk-title {color:#f5fbff!important;}
.derk-card {background:linear-gradient(115deg,#122b47,#0c213a)!important;border:1px solid #2a4b67!important;box-shadow:0 8px 24px #020b1940;}
.derk-name {color:#f6fbff!important;}
.derk-meta {color:#a6c0db!important;}
[data-testid="stRadio"] label, [data-testid="stSelectbox"] label {color:#c8ddf0!important;}
@media(max-width:700px){.block-container{padding:1.15rem .85rem 2rem!important;}[data-testid="stMetric"]{padding:10px 12px;min-height:90px;}[data-testid="stMetricValue"]{font-size:1.5rem!important;}h1{font-size:1.75rem!important;}}
</style>""", unsafe_allow_html=True)

LANGS = {
 'ru': {'subtitle':'Карта цифровой этнической репрезентации Казахстана','map':'Публичная карта','analytics':'Аналитика','cabinet':'Исследовательский кабинет','ethnic':'Этнос','platform':'Платформа','all':'Все','resources':'Цифровые ресурсы','filtered':'Ресурсов по фильтрам','groups':'Представленных этносов','share':'Доля этноса в базе','open':'Открыть ресурс ↗','empty':'По выбранным фильтрам нет подтверждённых ресурсов с корректными ссылками.','tip':'Наведите на узел или нажмите для просмотра ресурса','explain':'Узлы представляют уникальные подтверждённые ссылки. Положение условное; линии фона декоративные и не доказывают информационные связи.','listnote':'Список подтверждённых цифровых ресурсов по выбранным фильтрам','nodes':'ЦИФРОВАЯ НЕЙРОННАЯ КАРТА','dpi':'Цифровое присутствие','platforms':'Платформы','idae':'Индекс ИДАЭ','links':'Подтверждённые связи','links_empty':'Нет проверенных данных о связях','mode':'Разделы DERK'},
 'kk': {'subtitle':'Қазақстан этностарының цифрлық репрезентация картасы','map':'Қоғамдық карта','analytics':'Аналитика','cabinet':'Зерттеу кабинеті','ethnic':'Этнос','platform':'Платформа','all':'Барлығы','resources':'Цифрлық ресурстар','filtered':'Сүзгі бойынша ресурстар','groups':'Қамтылған этностар','share':'Дерекқордағы этнос үлесі','open':'Ресурсты ашу ↗','empty':'Таңдалған сүзгілер бойынша расталған ресурстар табылмады.','tip':'Ресурсты көру үшін түйінді таңдаңыз','explain':'Түйіндер — бірегей расталған сілтемелер. Орналасуы шартты, фондық сызықтар ақпараттық байланысты дәлелдемейді.','listnote':'Таңдалған сүзгілер бойынша расталған цифрлық ресурстар','nodes':'ЦИФРЛЫҚ НЕЙРОНДЫҚ КАРТА','dpi':'Цифрлық қатысу','platforms':'Платформалар','idae':'ИДАЭ индексі','links':'Расталған байланыстар','links_empty':'Расталған байланыс деректері жоқ','mode':'DERK бөлімдері'},
 'en': {'subtitle':'Digital Ethnic Representation of Kazakhstan','map':'Public map','analytics':'Analytics','cabinet':'Research workspace','ethnic':'Ethnic group','platform':'Platform','all':'All','resources':'Digital resources','filtered':'Filtered resources','groups':'Ethnic groups','share':'Ethnic share in dataset','open':'Open resource ↗','empty':'No verified resources with valid links match these filters.','tip':'Hover over or select a node to view its resource','explain':'Nodes are unique verified links. Positions are conceptual; background lines do not establish information relationships.','listnote':'Verified digital resources matching the selected filters','nodes':'DIGITAL NEURAL MAP','dpi':'Digital presence','platforms':'Platforms','idae':'IDAE index','links':'Verified connections','links_empty':'No verified connection data','mode':'DERK sections'}
}
PANEL_TRANSLATIONS = {
 'ru': {'population':'Этнический состав','population_sub':'Население Казахстана · 2026','dpi_sub':'Ресурсы по этносам ↗','platform_sub':'Распределение по платформам ↗','idae_sub':'Ресурсов на 10 000 человек ↗','links_sub':'Методология связей ↗','click':'Нажмите, чтобы открыть аналитику'},
 'kk': {'population':'Этностық құрам','population_sub':'Қазақстан халқы · 2026','dpi_sub':'Этностар бойынша ресурстар ↗','platform_sub':'Платформалар үлесі ↗','idae_sub':'10 000 адамға шаққандағы ресурстар ↗','links_sub':'Байланыстар әдіснамасы ↗','click':'Аналитиканы ашу үшін басыңыз'},
 'en': {'population':'Ethnic composition','population_sub':'Kazakhstan population · 2026','dpi_sub':'Resources by ethnic group ↗','platform_sub':'Platform distribution ↗','idae_sub':'Resources per 10,000 people ↗','links_sub':'Connection methodology ↗','click':'Click to open analytics'}
}

st.session_state.setdefault('derk_language','ru')
lang_cols = st.columns([6, 1.5])
with lang_cols[1]:
    st.selectbox('Language / Тіл / Язык', ['ru','kk','en'], format_func=lambda v: {'ru':'РУС','kk':'ҚАЗ','en':'ENG'}[v], key='derk_language')
L = LANGS[st.session_state.derk_language]

st.title('Digital Ethnic Representation of Kazakhstan')
st.caption('DERK 3.0 · ' + L['subtitle'])
# The public view is a conceptual network, not a geographic population map.
requested_view = str(st.query_params.get('derk_view', ''))
nav_options = ['Публичная карта', 'Аналитика', 'Исследовательский кабинет']
nav_index = 1 if requested_view == 'analytics' else 0
mode = st.sidebar.radio(L['mode'], nav_options, index=nav_index, key='derk_mode',
                        format_func=lambda v: {'Публичная карта':L['map'], 'Аналитика':L['analytics'], 'Исследовательский кабинет':L['cabinet']}[v])
if mode != 'Аналитика' and requested_view == 'analytics':
    st.query_params.clear()

data = load_data()
if 'working_data' not in st.session_state:
    st.session_state.working_data = data.copy()
data = st.session_state.working_data.copy()
verified = data[data['verification_status'].astype(str).str.lower().eq('verified')].copy()

if mode == 'Публичная карта':
    source = verified
elif mode == 'Исследовательский кабинет':
    st.subheader(L['cabinet'])
    st.caption('Предварительные записи доступны только в исследовательском режиме; публичная карта показывает только verified.')
    source = data


def canonical_url(value):
    try:
        u = urlsplit(str(value).strip())
        if u.scheme.lower() not in ('https', 'http') or not u.netloc:
            return ''
        return urlunsplit((u.scheme.lower(), u.netloc.lower(), u.path.rstrip('/') or '/', u.query, ''))
    except (ValueError, TypeError):
        return ''

if mode == 'Аналитика':
    st.header('📊 ' + L['analytics'] + ' DERK')
    target = str(st.query_params.get('derk_section', 'all'))
    if target not in ('all','population','dpi','idae','platforms','connections'):
        target = 'all'
    if target != 'all':
        if st.button({'ru':'← Вся аналитика','kk':'← Барлық аналитика','en':'← All analytics'}[st.session_state.derk_language]):
            st.query_params.clear()
            st.rerun()
    # Population figures retained from the existing DERK analytics source.
    total_population = 20499822

    ethnic_data = pd.DataFrame({
        'Этнос': [
            'Казахи',
            'Русские',
            'Узбеки',
            'Уйгуры',
            'Татары и башкиры',
            'Немцы',
            'Азербайджанцы',
            'Корейцы',
            'Турки',
            'Дунгане'
        ],
        'Численность': [
            14664202,
            2943022,
            695557,
            309164,
            238590,
            222890,
            157568,
            120821,
            93234,
            88165
        ]
    })

    other_population = total_population - ethnic_data['Численность'].sum()

    ethnic_data = pd.concat([
        ethnic_data,
        pd.DataFrame({
            'Этнос': ['Другие этносы'],
            'Численность': [other_population]
        })
    ], ignore_index=True)

    ethnic_data['Доля, %'] = (
        ethnic_data['Численность'] / total_population * 100
    ).round(2)


    def show_population():
        st.subheader({'ru':'Этнический состав населения Казахстана — 2026','kk':'Қазақстан халқының этностық құрамы — 2026','en':'Ethnic composition of Kazakhstan — 2026'}[st.session_state.derk_language])
        st.metric('Население Казахстана', f'{total_population:,}'.replace(',', ' '))

        scale = st.radio(
            'Масштаб диаграммы',
            ['Все категории', 'Увеличить малые группы'],
            horizontal=True
        )

        chart_data = ethnic_data.copy()

        if scale == 'Увеличить малые группы':
            chart_data['Значение для графика'] = (
                chart_data['Численность'] ** 0.5
            )
            axis_title = 'Квадратный корень численности (масштаб)'
        else:
            chart_data['Значение для графика'] = chart_data['Численность']
            axis_title = 'Численность населения, человек'

        chart_data = chart_data.sort_values(
            'Численность',
            ascending=True
        )

        fig = px.bar(
            chart_data,
            x='Значение для графика',
            y='Этнос',
            orientation='h',
            color='Этнос',
            color_discrete_sequence=px.colors.qualitative.Bold,
            custom_data=['Численность', 'Доля, %']
        )

        fig.update_traces(
            hovertemplate=(
                '<b>%{y}</b><br>'
                'Численность: %{customdata[0]:,.0f} человек<br>'
                'Доля населения: %{customdata[1]:.2f}%'
                '<extra></extra>'
            )
        )

        fig.update_layout(
            height=620,
            showlegend=False,
            xaxis_title=axis_title,
            yaxis_title='',
            margin=dict(l=10, r=20, t=20, b=40)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader('Статистические данные')
        st.dataframe(
            ethnic_data,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            'Источник: Бюро национальной статистики РК, '
            'таблица Т-18-08-Г (рус), лист «РК», '
            'на начало 2026 года.'
        )

        st.caption(
            'Татары и башкиры объединены для исследования DERK. '
            'Категория «Турки» соответствует официальной статистике; '
            'численность турок-ахыска отдельно не подтверждена. '
            '«Другие этносы» рассчитаны как разница между общей '
            'численностью населения и суммой десяти выбранных категорий.'
        )
        st.divider()
    def show_idae():
        st.subheader('📈 Индекс цифровой активности этноса (ИДАЭ)')

        st.caption(
            'Количество подтверждённых цифровых ресурсов '
            'на 10 000 представителей этнической группы.'
        )

        # Берём статистику из первой инфографики
        idae_data = ethnic_data[
            ethnic_data['Этнос'] != 'Другие этносы'
        ][['Этнос', 'Численность']].copy()

        # Берём подтверждённые ресурсы из Supabase
        resource_data = verified.copy()

        # Сопоставляем названия этносов
        ethnic_names = {
            'Казахи': 'Казахи',
            'Русские': 'Русские',
            'Узбеки': 'Узбеки',
            'Уйгуры': 'Уйгуры',
            'Татары': 'Татары и башкиры',
            'Башкиры': 'Татары и башкиры',
            'Татары и башкиры': 'Татары и башкиры',
            'Немцы': 'Немцы',
            'Азербайджанцы': 'Азербайджанцы',
            'Корейцы': 'Корейцы',
            'Турки': 'Турки',
            'Турки-ахыска': 'Турки',
            'Дунгане': 'Дунгане'
        }

        resource_data['Группа DERK'] = (
            resource_data['ethnic_group']
            .astype(str)
            .str.strip()
            .str.capitalize()
            .map(ethnic_names)
        )

        # Подсчитываем записи по каждой группе
        resource_counts = (
            resource_data
            .dropna(subset=['Группа DERK'])
            .groupby('Группа DERK')
            .size()
            .reset_index(name='Цифровые ресурсы')
        )

        idae_data = idae_data.merge(
            resource_counts,
            left_on='Этнос',
            right_on='Группа DERK',
            how='left'
        )

        idae_data['Цифровые ресурсы'] = (
            idae_data['Цифровые ресурсы'].fillna(0).astype(int)
        )

        # Автоматический расчёт индекса
        idae_data['ИДАЭ'] = (
            idae_data['Цифровые ресурсы']
            / idae_data['Численность']
            * 10000
        ).round(3)

        idae_data = idae_data.sort_values('ИДАЭ', ascending=True)

        fig_idae = px.bar(
            idae_data,
            x='ИДАЭ',
            y='Этнос',
            orientation='h',
            color='ИДАЭ',
            color_continuous_scale='Turbo',
            custom_data=['Цифровые ресурсы', 'Численность']
        )

        fig_idae.update_traces(
            hovertemplate=(
                '<b>%{y}</b><br>'
                'ИДАЭ: %{x:.3f}<br>'
                'Ресурсы: %{customdata[0]}<br>'
                'Население: %{customdata[1]:,.0f}'
                '<extra></extra>'
            )
        )

        fig_idae.update_layout(
            height=600,
            xaxis_title='Ресурсов на 10 000 человек',
            yaxis_title='',
            coloraxis_showscale=False
        )

        st.plotly_chart(fig_idae, use_container_width=True)

        st.dataframe(
            idae_data[
                ['Этнос', 'Численность', 'Цифровые ресурсы', 'ИДАЭ']
            ],
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            'Источник: статистика населения БНС РК за 2026 год '
            'и подтверждённые записи базы DERK (Supabase). '
            'ИДАЭ автоматически пересчитывается при обновлении данных.'
        )

        st.caption(
            'Показатель отражает выявленные цифровые ресурсы, '
            'а не интенсивность публикаций или активность пользователей. '
            'На данном этапе учитывается количество записей; '
            'проверка и исключение дубликатов ресурсов '
            'будут отдельным этапом методологии.'
        )
    def show_dpi():
        st.subheader({'ru':'Цифровая представленность этносов (DPI)','kk':'Этностардың цифрлық ұсынылуы (DPI)','en':'Digital presence by ethnic group (DPI)'}[st.session_state.derk_language])
        subset = verified.copy()
        subset['_canonical'] = subset['public_url'].apply(canonical_url)
        subset = subset[subset['_canonical'].ne('')].drop_duplicates(['ethnic_group','_canonical'])
        counts = subset.groupby('ethnic_group').size().sort_values(ascending=True)
        if counts.empty:
            st.info('Нет подтверждённых цифровых ресурсов.')
        else:
            fig = px.bar(x=counts.values, y=counts.index, orientation='h', color=counts.index,
                         color_discrete_sequence=px.colors.qualitative.Bold,
                         labels={'x':'Уникальных подтверждённых ресурсов','y':'Этнос'})
            fig.update_layout(showlegend=False, height=max(380, 38*len(counts)+110),
                              paper_bgcolor='#071426',plot_bgcolor='#071426',font_color='#e9f3ff')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(pd.DataFrame({'Этнос':counts.index,'Ресурсов':counts.values}), hide_index=True, use_container_width=True)
        st.caption('DPI здесь — число уникальных подтверждённых публичных ресурсов в выборке DERK, а не доля всего цифрового пространства Казахстана.')

    def show_platforms():
        st.subheader({'ru':'Структура цифровых платформ','kk':'Цифрлық платформалар құрылымы','en':'Digital platform distribution'}[st.session_state.derk_language])
        subset = verified.copy()
        subset['_canonical'] = subset['public_url'].apply(canonical_url)
        subset = subset[subset['_canonical'].ne('')].drop_duplicates(['ethnic_group','_canonical'])
        counts = subset['platform'].value_counts()
        if counts.empty:
            st.info('Нет подтверждённых ресурсов.')
        else:
            fig = px.pie(names=counts.index, values=counts.values, hole=.56,
                         color_discrete_sequence=px.colors.qualitative.Bold)
            fig.update_layout(paper_bgcolor='#071426',font_color='#e9f3ff',height=460)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(pd.DataFrame({'Платформа':counts.index,'Ресурсов':counts.values,
                                       'Доля, %':(counts.values/counts.sum()*100).round(1)}),
                         hide_index=True, use_container_width=True)
        st.caption('Распределение относится только к подтверждённым уникальным ресурсам в базе DERK.')

    def show_connections():
        st.subheader({'ru':'Трансграничные информационные связи','kk':'Трансшекаралық ақпараттық байланыстар','en':'Cross-border information connections'}[st.session_state.derk_language])
        st.info({'ru':'Подтверждённые связи пока не внесены в текущую модель данных. Этот раздел предназначен для документирования репостов, цитирований и перекрёстных ссылок.',
                 'kk':'Расталған байланыстар әзірше дерекқорға енгізілмеген. Бұл бөлім репосттарды, дәйексөздерді және өзара сілтемелерді тіркеуге арналған.',
                 'en':'Verified links are not yet recorded in the current data model. This section is reserved for documented reposts, citations and cross-links.'}[st.session_state.derk_language])

    sections = {'population':show_population,'dpi':show_dpi,'idae':show_idae,
                'platforms':show_platforms,'connections':show_connections}
    if target == 'all':
        for key, render in sections.items():
            render()
            st.divider()
    else:
        sections[target]()
    st.stop()

# DERK 2.0 — two public filters, abstract digital network inside Kazakhstan silhouette.
# Nodes denote verified unique URLs; faint lines are visual grouping only, NOT measured cross-platform ties.
st.markdown("""<style>
.derk-title {font-size:clamp(1.65rem,4vw,2.7rem);font-weight:800;letter-spacing:-.035em}
.derk-muted {color:#a5bcd7;font-size:.91rem}
.derk-card {border:1px solid rgba(80,150,200,.25);border-radius:16px;padding:15px;margin:8px 0;background:rgba(85,140,200,.055)}
.derk-name {font-weight:750;font-size:1.03rem;overflow-wrap:anywhere}
.derk-meta {font-size:.86rem;color:#8493a7;margin-top:5px}
@media(max-width:650px){.block-container{padding-left:1rem;padding-right:1rem}.derk-card{padding:12px}}
</style>""", unsafe_allow_html=True)

# Public map: only verified resources; two filters; research cabinet remains untouched.
if mode == 'Публичная карта':
    source = verified
    filters = st.columns(2)
    with filters[0]:
        ethnic_options = ['__all__'] + sorted(x for x in source['ethnic_group'].dropna().astype(str).unique() if x.strip())
        ethnic = st.selectbox(L['ethnic'], ethnic_options, format_func=lambda x: L['all'] if x == '__all__' else x)
    with filters[1]:
        platform_options = ['__all__'] + sorted(x for x in source['platform'].dropna().astype(str).unique() if x.strip())
        platform = st.selectbox(L['platform'], platform_options, format_func=lambda x: L['all'] if x == '__all__' else x)
    filtered = source.copy()
    if ethnic != '__all__': filtered = filtered[filtered['ethnic_group'].astype(str).eq(ethnic)]
    if platform != '__all__': filtered = filtered[filtered['platform'].astype(str).eq(platform)]

    resources = filtered.copy()
    resources['_url_key'] = resources['public_url'].apply(canonical_url)
    resources = resources[resources['_url_key'].ne('')].drop_duplicates(['ethnic_group','_url_key'])
    resources = resources.sort_values(['ethnic_group','platform','community_name'],kind='stable')
    all_verified = source.copy()
    all_verified['_url_key'] = all_verified['public_url'].apply(canonical_url)
    all_verified = all_verified[all_verified['_url_key'].ne('')].drop_duplicates(['ethnic_group','_url_key'])
    group_count = len(all_verified[all_verified['ethnic_group'].eq(ethnic)]) if ethnic != '__all__' else 0
    share = 100 * group_count / len(all_verified) if len(all_verified) else 0
    PALETTE = ['#39E0F5','#B299FF','#FFB765','#6EE7B7','#FB7185','#60A5FA','#F9A8D4','#FACC15','#2DD4BF']
    groups = sorted(source['ethnic_group'].dropna().astype(str).loc[lambda x:x.str.strip().ne('')].unique())
    colors = {g: PALETTE[i % len(PALETTE)] for i,g in enumerate(groups)}

    # Stable conceptual coordinates: deterministic clusters per ethnic group.
    # There are NO asserted cross-resource edges without verified link evidence.
    import json
    import collections
    import statistics
    import random
    import math
    group_indices = {g:i for i,g in enumerate(groups)}
    nodes = []
    for _, item in resources.iterrows():
        g = str(item['ethnic_group']); key = str(item['_url_key'])
        digest = hashlib.sha256((g+'|'+key).encode('utf-8')).digest()
        rng = random.Random(int.from_bytes(digest[:8], 'big'))
        i = group_indices[g]
        theta = 2*math.pi*i/max(len(groups),1) - math.pi/2
        # Larger radius for more groups; consistent group anchors across filtering.
        anchor_x = 500 + (240 if len(groups)>1 else 0)*math.cos(theta)
        anchor_y = 285 + (158 if len(groups)>1 else 0)*math.sin(theta)
        phi = rng.uniform(0, 2*math.pi)
        r = 12 + 74*math.sqrt(rng.random())
        x = max(38,min(962,anchor_x+r*math.cos(phi)))
        y = max(35,min(535,anchor_y+r*math.sin(phi)))
        nodes.append({'x':round(x,2),'y':round(y,2),'color':colors[g], 'name':str(item['community_name']), 'group':g, 'platform':str(item['platform']), 'language':str(item['language']), 'url':str(item['public_url'])})
    counts = resources['platform'].value_counts()
    top_platform = str(counts.index[0]) if len(counts) else '—'
    pct = (100*counts.iloc[0]/len(resources)) if len(resources) else 0
    data_json = json.dumps(nodes,ensure_ascii=False).replace('<','\u003c').replace('>','\u003e').replace('&','\u0026')
    strings_json = json.dumps({**{k:L[k] for k in ['tip','explain','nodes','dpi','platforms','idae','links','links_empty','open']},
                               **PANEL_TRANSLATIONS[st.session_state.derk_language]},ensure_ascii=False).replace('<','\u003c')
    try:
        app_base_url = str(st.context.url).split('?')[0].split('#')[0]
    except (AttributeError, RuntimeError):
        app_base_url = 'https://derk-dpi-test.streamlit.app/'
    if not app_base_url.startswith(('https://','http://')):
        app_base_url = 'https://derk-dpi-test.streamlit.app/'
    links_json = json.dumps({k:app_base_url+'?derk_view=analytics&derk_section='+k
                             for k in ['population','dpi','idae','platforms','connections']},ensure_ascii=False)

    # IDAE value intentionally not fabricated: no denominator is recomputed from partial records.
    panel_html = r'''<style>
    *{box-sizing:border-box}body{margin:0;background:#071426;color:#ecf7ff;font-family:Inter,system-ui,Arial,sans-serif}
    .shell{position:relative;min-height:635px;overflow:hidden;border:1px solid #234964;border-radius:20px;background:radial-gradient(ellipse at 52% 43%,#153456 0%,#0a1b31 50%,#071426 100%)}
    .head{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:18px 22px;position:relative;z-index:2}.head strong{letter-spacing:.12em;font-size:13px;color:#bceeff}.head span{color:#7bacc7;font-size:12px}.sound-btn{appearance:none;background:#102f4c;border:1px solid #397b9d;border-radius:999px;color:#c8efff;padding:9px 13px;font-size:12px;cursor:pointer;min-height:38px}.sound-btn:hover,.sound-btn:focus-visible{border-color:#68e3ff;background:#19415f;outline:2px solid #68e3ff44}.sound-btn:disabled{opacity:.65;cursor:default}
    .network{position:absolute;inset:30px 0 5px;width:100%;height:calc(100% - 35px);touch-action:pan-y;cursor:grab}.network:active{cursor:grabbing}
    .panel{position:absolute;z-index:3;background:rgba(9,27,47,.89);border:1px solid rgba(65,193,229,.35);box-shadow:0 8px 35px #0006,inset 0 0 22px #1c5a6a20;border-radius:13px;padding:12px 15px;min-width:160px;max-width:210px;backdrop-filter:blur(12px)}
    .panel{display:block;text-decoration:none;color:inherit;transition:transform .18s,border-color .18s,box-shadow .18s;cursor:pointer}.panel:hover,.panel:focus-visible{transform:translateY(-3px);border-color:#5de7ff;box-shadow:0 10px 34px #00172c,inset 0 0 25px #2eabc32a;outline:none}.panel .label{color:#8dbad0;font-size:11px;letter-spacing:.06em}.panel .value{font-size:24px;font-weight:750;margin-top:4px}.panel .sub{color:#94b5c8;font-size:11px;margin-top:3px;line-height:1.4}
    .tc{left:50%;top:70px;transform:translateX(-50%);text-align:center;min-width:205px}.tc:hover,.tc:focus-visible{transform:translate(-50%,-3px)}.tl{left:18px;top:70px}.tr{right:18px;top:70px}.bl{left:18px;bottom:25px}.br{right:18px;bottom:25px}
    .dot{cursor:pointer;outline:none}.dot .halo{opacity:.14;transition:opacity .2s,r .2s}.dot:hover .halo,.dot:focus .halo{opacity:.38}.dot .hit-area{pointer-events:all}
    .tip{display:none;position:absolute;z-index:8;max-width:265px;background:#102b47;color:#f4fbff;border:1px solid #4cbad8;border-radius:12px;padding:13px;box-shadow:0 12px 35px #000b;font-size:13px;line-height:1.5}.tip a{display:inline-block;margin-top:8px;background:#176488;color:white;text-decoration:none;border-radius:7px;padding:7px 10px}.tip small{color:#a3c5d6}
    .footer{position:absolute;z-index:2;left:22%;right:22%;bottom:13px;text-align:center;color:#7898aa;font-size:10px;pointer-events:none}
    @media(max-width:680px){.shell{min-height:755px}.head{padding:14px}.head strong{font-size:11px}.head span{display:none}.network{top:235px;height:300px}.panel{min-width:0;width:calc(50% - 20px);max-width:none;padding:10px;backdrop-filter:none}.panel .value{font-size:19px}.tc{top:155px;left:50%;width:calc(100% - 24px);max-width:none;min-width:0;transform:translateX(-50%)}.tc:hover,.tc:focus-visible{transform:translate(-50%,-3px)}.tl{top:52px;left:12px}.tr{top:52px;right:12px}.bl{bottom:68px;left:12px}.br{bottom:68px;right:12px}.footer{left:15px;right:15px;bottom:8px}.tip{max-width:min(260px,calc(100% - 24px));font-size:14px;padding:14px}.tip a{padding:11px 14px;min-height:44px}}
    </style>
    <div class="shell" id="shell"><div class="head"><strong>DERK</strong><button class="sound-btn" id="soundBtn" type="button" aria-label="Play DERK sound logo">▶ DERK SOUND · 10s</button></div>
      <svg class="network" id="network" viewBox="0 0 1000 570" xmlns="http://www.w3.org/2000/svg" aria-label="Interactive digital resource network">
      <defs><pattern id="grid" width="42" height="42" patternUnits="userSpaceOnUse"><path d="M42 0H0V42" fill="none" stroke="#286182" stroke-width=".6" opacity=".24"/></pattern><radialGradient id="glow"><stop stop-color="#164867" stop-opacity=".35"/><stop offset="1" stop-color="#164867" stop-opacity="0"/></radialGradient></defs>
      <rect width="1000" height="570" fill="url(#grid)"/><ellipse cx="500" cy="285" rx="440" ry="270" fill="url(#glow)"/><g id="world"></g></svg>
      <a class="panel tl" id="linkDpi" target="_top"><div class="label" id="dpiLabel"></div><div class="value" id="nCount"></div><div class="sub" id="nGroups"></div></a>
      <a class="panel tr" id="linkPlatforms" target="_top"><div class="label" id="platformLabel"></div><div class="value" id="pValue"></div><div class="sub" id="pSub"></div></a>
      <a class="panel bl" id="linkIdae" target="_top"><div class="label" id="idaeLabel"></div><div class="value">IDAE</div><div class="sub" id="idaeSub"></div></a>
      <a class="panel br" id="linkConnections" target="_top"><div class="label" id="linksLabel"></div><div class="value">—</div><div class="sub" id="linksSub"></div></a>
      <a class="panel tc" id="linkPopulation" target="_top"><div class="label" id="populationLabel"></div><div class="value">20 499 822</div><div class="sub" id="populationSub"></div></a><div class="tip" id="tip"></div><div class="footer" id="explain"></div>
    </div>
    <script>
    (()=>{
      const links=__LINKS__, data=__NODES__, t=__STRINGS__, shell=document.getElementById('shell'), svg=document.getElementById('network'), world=document.getElementById('world'), tip=document.getElementById('tip');
      const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
      const set=(id,v)=>document.getElementById(id).textContent=v;
      set('dpiLabel',t.dpi);set('platformLabel',t.platforms);set('idaeLabel',t.idae);set('linksLabel',t.links);set('linksSub',t.links_sub);set('explain',t.explain);
      set('populationLabel',t.population);set('populationSub',t.population_sub);
       [['linkPopulation','population'],['linkDpi','dpi'],['linkPlatforms','platforms'],['linkIdae','idae'],['linkConnections','connections']].forEach(([id,key])=>document.getElementById(id).href=links[key]);
       set('nCount',__COUNT__);set('nGroups',__GROUPS__);set('pValue',__TOP_PLATFORM__);set('pSub',__TOP_PCT__+' · ↗');set('idaeSub',t.idae_sub);
      // Optional 10-second synthesized sound logo; browsers require a user gesture.
      // No external audio, tracking, downloads, or automatic playback.
      const soundBtn=document.getElementById('soundBtn');
      const soundLabels={ru:['▶ ЗВУК DERK · 10 с','■ ОСТАНОВИТЬ','▶ ПОВТОРИТЬ'],kk:['▶ DERK ДЫБЫСЫ · 10 с','■ ТОҚТАТУ','▶ ҚАЙТАЛАУ'],en:['▶ DERK SOUND · 10s','■ STOP','▶ REPLAY']};
      const soundLang=__SOUND_LANG__;
      const soundText=soundLabels[soundLang]||soundLabels.ru;
      soundBtn.textContent=soundText[0];
      let audioCtx=null, soundActive=false, finishTimer=null, activeVoices=[];
      function stopSound(){
        if(finishTimer){clearTimeout(finishTimer);finishTimer=null;}
        activeVoices.forEach(v=>{try{v.gain.gain.cancelScheduledValues(audioCtx.currentTime);v.gain.gain.setTargetAtTime(0,audioCtx.currentTime,.035);v.osc.stop(audioCtx.currentTime+.2)}catch(e){}});
        activeVoices=[];soundActive=false;soundBtn.textContent=soundText[2];soundBtn.setAttribute('aria-pressed','false');
      }
      soundBtn.addEventListener('click',async()=>{
        if(soundActive){stopSound();return;}
        const AudioContextCtor=window.AudioContext||window.webkitAudioContext;
        if(!AudioContextCtor){soundBtn.textContent='Audio unavailable';return;}
        try{
          if(!audioCtx)audioCtx=new AudioContextCtor();
          await audioCtx.resume();
          const start=audioCtx.currentTime+.04;
          soundActive=true;soundBtn.textContent=soundText[1];soundBtn.setAttribute('aria-pressed','true');
          const master=audioCtx.createGain();master.gain.value=.28;master.connect(audioCtx.destination);
          const notes=[
            [0,110,4.5,'sine',.12],[0,164.81,5.0,'sine',.055],
            [1.2,329.63,2.4,'sine',.038],[2.6,392,2.6,'triangle',.022],
            [4.1,493.88,2.7,'sine',.032],[5.3,659.25,2.3,'sine',.028],
            [6.7,587.33,2.3,'sine',.025],[7.8,440,2.15,'sine',.02],
            [5.2,130.81,4.7,'sine',.065]
          ];
          notes.forEach(([offset,freq,duration,type,volume])=>{
            const osc=audioCtx.createOscillator(),gain=audioCtx.createGain();
            osc.type=type;osc.frequency.setValueAtTime(freq,start+offset);
            const a=start+offset,b=Math.min(start+10,a+duration);
            gain.gain.setValueAtTime(0,a);
            gain.gain.linearRampToValueAtTime(volume,a+.22);
            gain.gain.setValueAtTime(volume*.85,Math.max(a+.23,b-.75));
            gain.gain.exponentialRampToValueAtTime(.0001,b);
            osc.connect(gain);gain.connect(master);osc.start(a);osc.stop(b+.04);
            activeVoices.push({osc,gain});
          });
          finishTimer=setTimeout(()=>{soundActive=false;activeVoices=[];soundBtn.textContent=soundText[2];soundBtn.setAttribute('aria-pressed','false')},10050);
        }catch(e){soundActive=false;soundBtn.textContent=soundText[2]}
      });
      const NS='http://www.w3.org/2000/svg';const make=(name,attrs)=>{const e=document.createElementNS(NS,name);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));return e};
      // Faint decorative ambient points only; no resource-to-resource connections asserted.
      for(let i=0;i<85;i++){const x=(i*177.7)%1000,y=(i*97.31)%570;world.appendChild(make('circle',{cx:x,cy:y,r:'.9',fill:'#70a8c6',opacity:'.20'}))}
      let pinned=false;
      function card(d,node,pin){pinned=pin;tip.innerHTML='<strong>'+escape(d.name||d.url)+'</strong><div><small>'+escape(d.group)+' · '+escape(d.platform)+(d.language?' · '+escape(d.language):'')+'</small></div>'+(pin?'<a href="'+escape(d.url)+'" target="_blank" rel="noopener noreferrer">'+escape(t.open)+'</a>':'');tip.style.display='block';tip.style.pointerEvents=pin?'auto':'none';const r=shell.getBoundingClientRect(),n=node.getBoundingClientRect();tip.style.left=Math.max(8,Math.min(n.left-r.left+12,shell.clientWidth-230))+'px';tip.style.top=Math.max(8,Math.min(n.top-r.top-5,shell.clientHeight-130))+'px'}
      const mobileNodes=window.matchMedia('(max-width:680px)').matches;
      data.forEach(d=>{const g=make('g',{class:'dot',tabindex:'0',role:'button','aria-label':d.name||d.url});
        // Transparent hit area makes a node easier to tap on a narrow phone screen.
        g.appendChild(make('circle',{cx:d.x,cy:d.y,r:mobileNodes?60:19,fill:'transparent',class:'hit-area'}));
        g.appendChild(make('circle',{cx:d.x,cy:d.y,r:mobileNodes?25:12,fill:d.color,class:'halo','pointer-events':'none'}));
        g.appendChild(make('circle',{cx:d.x,cy:d.y,r:mobileNodes?12:4.4,fill:d.color,stroke:'#071426','stroke-width':mobileNodes?2:1.1,'pointer-events':'none'}));world.appendChild(g);g.addEventListener('mouseenter',()=>{if(!pinned)card(d,g,false)});g.addEventListener('mouseleave',()=>{if(!pinned)tip.style.display='none'});g.addEventListener('click',e=>{e.stopPropagation();card(d,g,true)});g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();card(d,g,true)}})});
      shell.addEventListener('click',e=>{if(!e.target.closest('.dot')&&!e.target.closest('.tip')){pinned=false;tip.style.display='none'}});
      // Wheel zoom and pointer drag, clamped for usability.
      let zoom=1,tx=0,ty=0,drag=null;
      function transform(){world.setAttribute('transform',`translate(${tx} ${ty}) scale(${zoom})`)}
      svg.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.min(3.5,Math.max(.7,zoom*(e.deltaY<0?1.12:.89)));transform()},{passive:false});
      svg.addEventListener('pointerdown',e=>{if(e.target.closest('.dot'))return;drag={x:e.clientX,y:e.clientY,tx,ty};svg.setPointerCapture(e.pointerId)});
      svg.addEventListener('pointermove',e=>{if(!drag)return;const r=svg.getBoundingClientRect();tx=drag.tx+(e.clientX-drag.x)*1000/r.width;ty=drag.ty+(e.clientY-drag.y)*570/r.height;transform()});
      svg.addEventListener('pointerup',()=>drag=null);svg.addEventListener('pointercancel',()=>drag=null);
    })();
    </script>'''
    panel_html = (panel_html.replace('__LINKS__',links_json).replace('__NODES__',data_json).replace('__STRINGS__',strings_json)
       .replace('__COUNT__',json.dumps(str(len(resources))))
       .replace('__GROUPS__',json.dumps(str(resources['ethnic_group'].nunique())+' '+L['groups'].lower()))
       .replace('__TOP_PLATFORM__',json.dumps(top_platform,ensure_ascii=False))
       .replace('__TOP_PCT__',json.dumps(f'{pct:.1f}%'))
       .replace('__SOUND_LANG__',json.dumps(st.session_state.derk_language)))
    components.html(panel_html,height=780,scrolling=False)
    st.subheader(L['resources'])
    st.caption(L['listnote'])
    if resources.empty: st.info(L['empty'])
    for _,item in resources.iterrows():
        group=html.escape(str(item['ethnic_group']));name=html.escape(str(item['community_name']) or str(item['public_url']))
        platform_name=html.escape(str(item['platform']));language=html.escape(str(item['language']))
        color=colors.get(str(item['ethnic_group']),'#36D9F5')
        st.markdown(f'<div class="derk-card" style="border-left:4px solid {color}"><div class="derk-name">{name}</div><div class="derk-meta">{group} · {platform_name}'+(f' · {language}' if language else '')+'</div></div>',unsafe_allow_html=True)
        st.link_button(L['open'],str(item['public_url']),use_container_width=True)

# Existing DPI and research editing functionality remain available.
if mode == 'Исследовательский кабинет':
    st.caption('В исследовательском кабинете отображаются также записи со статусами pending и rejected. Публичная карта показывает только verified.')
if mode == 'Исследовательский кабинет':
    st.divider()
    st.subheader('Добавить наблюдение вручную')
    st.caption('Запись сразу появится в рабочей базе текущей сессии. Для публичной карты требуется статус verified. Для долговременного хранения скачайте CSV; в облачной версии понадобится база данных.')
    with st.form('manual_observation', clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            group = st.text_input('Этнос / этнокультурная группа *')
            area = st.selectbox('Регион *', REGIONS['region'].tolist())
            site = st.selectbox('Платформа *', ['Facebook','Instagram','YouTube','TikTok','Telegram','VK','Сайт','Другое'])
            community = st.text_input('Название публичного ресурса *')
            url = st.text_input('Ссылка на ресурс (https://...) *')
            lang = st.text_input('Язык публикаций')
        with f2:
            topic = st.text_input('Тематика')
            followers = st.number_input('Аудитория (если известно)', min_value=0, step=1)
            observed = st.date_input('Дата наблюдения', value=date.today())
            evidence = st.text_input('Ссылка на подтверждающий источник')
            status = st.selectbox('Статус проверки', ['pending','verified','rejected'], help='По умолчанию pending. Verified устанавливайте после проверки источника.')
            note = st.text_area('Примечания / методологический комментарий')
        submitted = st.form_submit_button('Добавить запись в рабочую базу', type='primary')
    if submitted:
        errors = []
        if not group.strip() or not community.strip(): errors.append('Заполните этнос и название ресурса.')
        if not url.strip().startswith(('https://','http://')): errors.append('Укажите корректную ссылку http(s).')
        if errors:
            for error in errors: st.error(error)
        else:
            record = dict(zip(COLS, [str(uuid.uuid4()), group.strip(), area, site, community.strip(), url.strip(), lang.strip(), topic.strip(), int(followers), observed.isoformat(), evidence.strip(), status, note.strip()]))
            supabase.table("observations").insert(record).execute()
            st.success("Наблюдение сохранено в базе данных DERK Kazakhstan.")
            load_data.clear()
            st.session_state.pop("working_data", None)
            st.rerun()
    st.subheader('Редактирование и удаление записей')
    if not data.empty:
        st.caption('Измените значения в таблице и нажмите «Применить изменения». Удаление строк через редактор также применяется после нажатия.')
        edited = st.data_editor(data[COLS], num_rows='dynamic', use_container_width=True, hide_index=True, key='derk_editor')
        if st.button('Применить изменения таблицы'):
            edited = edited.fillna('')
            invalid = edited[~edited['region'].isin(REGIONS['region']) | ~edited['verification_status'].isin(['pending','verified','rejected']) | ~edited['public_url'].astype(str).str.startswith(('https://','http://'))]
            if len(invalid): st.error('Есть некорректные регионы, статусы или ссылки. Изменения не сохранены.')
            else:
                for _, row in edited.iterrows():
                    supabase.table("observations").update(row.drop("record_id").to_dict()).eq("record_id", row["record_id"]).execute()
                st.success('Изменения сохранены в Supabase.')
                load_data.clear()
                st.session_state.pop('working_data', None)
                st.rerun()
    st.subheader('Импорт и проверка данных')
    st.write('Загрузите CSV с колонками шаблона. Файл действует в текущей сессии и **не записывается на сервер**.')
    st.download_button('Скачать шаблон CSV', (BASE/ 'observations.csv').read_bytes(), 'derk_observations_template.csv', 'text/csv')
    uploaded = st.file_uploader('CSV наблюдений', type=['csv'])
    if uploaded:
        try:
            candidate = pd.read_csv(uploaded, dtype={'record_id':'string'}).fillna('')
            missing = set(COLS) - set(candidate.columns)
            if missing:
                st.error('Не хватает колонок: ' + ', '.join(sorted(missing)))
            else:
                candidate = candidate[COLS]
                statuses = {'verified','pending','rejected'}
                bad_status = ~candidate['verification_status'].astype(str).str.lower().isin(statuses)
                bad_region = ~candidate['region'].isin(REGIONS['region'])
                bad_url = ~candidate['public_url'].astype(str).str.match(r'^https?://', na=False)
                if bad_status.any() or bad_region.any() or bad_url.any():
                    st.error(f'Проверка не пройдена: статус {int(bad_status.sum())}, регион {int(bad_region.sum())}, URL {int(bad_url.sum())}.')
                else:
                    st.session_state.working_data = candidate
                    st.success('CSV загружен в сессию. Переключайте режимы и фильтры; для сохранения используйте экспорт.')
        except Exception as exc:
            st.error(f'Ошибка чтения CSV: {exc}')
    data = st.session_state.working_data.copy()
    st.subheader('Экспорт')
    st.download_button('Экспорт отфильтрованных данных CSV', data.to_csv(index=False).encode('utf-8-sig'), 'derk_filtered.csv', 'text/csv')
    st.download_button('Экспорт всей рабочей базы CSV', data.to_csv(index=False).encode('utf-8-sig'), 'derk_all_observations.csv', 'text/csv')
    if not data.empty:
        st.subheader('Статусы проверки')
        st.bar_chart(data['verification_status'].value_counts())
        st.subheader('Сводка по платформам')
        st.bar_chart(data['platform'].value_counts())

st.divider()
st.caption('Методология: единица наблюдения — публичный цифровой ресурс с зафиксированным этнокультурным позиционированием. Самоидентификация отдельных пользователей не устанавливается. Географические контуры не используются; расположение цифровых узлов условное и не обозначает географию.')
