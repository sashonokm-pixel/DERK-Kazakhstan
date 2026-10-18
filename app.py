import io
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

st.title('Digital Ethnic Representation of Kazakhstan')
st.caption('DERK · Карта цифровой этнической репрезентации Казахстана · исследовательский прототип v0.1')
st.info('Карта показывает **наблюдения об открытых цифровых ресурсах**, а не этнический состав населения. Пустые регионы означают отсутствие записей в базе, а не отсутствие цифровой репрезентации.')
mode = st.sidebar.radio('Разделы DERK', ['Публичная карта', 'Аналитика', 'Исследовательский кабинет'])
data = load_data()
if 'working_data' not in st.session_state:
    st.session_state.working_data = data.copy()
data = st.session_state.working_data.copy()
verified = data[data['verification_status'].astype(str).str.lower().eq('verified')].copy()

if mode == 'Публичная карта':
    st.subheader('Публичная интерактивная карта')
    source = verified
elif mode == 'Исследовательский кабинет':
    st.subheader('Исследовательский кабинет')
    st.caption('Предварительные записи доступны только в исследовательском режиме; публичная карта показывает только verified.')
    source = data


if mode == 'Аналитика':
    st.header('📊 Аналитика DERK')
    st.subheader('Этнический состав населения Казахстана — 2026')

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
    st.stop()

left, middle, right = st.columns(3)
with left:
    ethnic = st.selectbox('Этнос', ['Все'] + sorted(x for x in source['ethnic_group'].dropna().unique() if str(x).strip()))
with middle:
    platform = st.selectbox('Платформа', ['Все'] + sorted(x for x in source['platform'].dropna().unique() if str(x).strip()))
with right:
    region = st.selectbox('Регион', ['Все'] + sorted(x for x in REGIONS['region'].unique()))
filtered = source.copy()
if ethnic != 'Все': filtered = filtered[filtered['ethnic_group'] == ethnic]
if platform != 'Все': filtered = filtered[filtered['platform'] == platform]
if region != 'Все': filtered = filtered[filtered['region'] == region]

counts = filtered.groupby('region').size().rename('observations').reset_index()
map_data = REGIONS.merge(counts, on='region', how='left')
map_data['observations'] = map_data['observations'].fillna(0).astype(int)
map_data['marker_size'] = map_data['observations'].clip(lower=1)
fig = px.scatter_map(map_data, lat='lat', lon='lon', size='marker_size', color='observations',
                     hover_name='region', hover_data={'lat':False,'lon':False,'marker_size':False,'observations':True},
                     color_continuous_scale='Blues', zoom=3.6, center={'lat':48.1,'lon':67.5},
                     map_style='open-street-map', height=520, size_max=34)
fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), coloraxis_colorbar_title='Записей')
st.plotly_chart(fig, use_container_width=True)
st.subheader("Индекс цифрового присутствия (DPI)")

dpi_data = (
        filtered[
            filtered["ethnic_group"].astype(str).str.strip().ne("")
            & filtered["public_url"].astype(str).str.strip().ne("")
        ]
        .groupby("ethnic_group")["public_url"]
        .nunique()
        .reset_index(name="dpi")
    )

if not dpi_data.empty:
        fig_dpi = px.pie(
            dpi_data,
            names="ethnic_group",
            values="dpi",
            hole=0.55,
            title="Цифровое присутствие этносов"
        )
        st.plotly_chart(fig_dpi, use_container_width=True)
else:
        st.info("Пока нет данных для расчёта DPI.")
a,b,c = st.columns(3)
a.metric('Записей по фильтрам', len(filtered))
b.metric('Представленных этносов', filtered['ethnic_group'].replace('',pd.NA).nunique())
c.metric('Регионов с наблюдениями', filtered['region'].replace('',pd.NA).nunique())
if filtered.empty:
    st.warning('Пока нет записей по выбранным фильтрам. Загрузите подтверждённые наблюдения в исследовательском кабинете.')
else:
    show = ['ethnic_group','region','platform','community_name','public_url','language','observed_at','source_url','verification_status']
    st.dataframe(
    filtered[show],
    hide_index=True,
    use_container_width=True,
    column_config={
        "public_url": st.column_config.LinkColumn(
            "Ссылка на ресурс",
            display_text="Открыть ↗️"
        )
    }
)
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
                st.success('Изменения применены в текущей сессии. Не забудьте экспортировать CSV.')
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
    st.download_button('Экспорт отфильтрованных данных CSV', filtered.to_csv(index=False).encode('utf-8-sig'), 'derk_filtered.csv', 'text/csv')
    st.download_button('Экспорт всей рабочей базы CSV', data.to_csv(index=False).encode('utf-8-sig'), 'derk_all_observations.csv', 'text/csv')
    if not data.empty:
        st.subheader('Статусы проверки')
        st.bar_chart(data['verification_status'].value_counts())
        st.subheader('Сводка по платформам')
        st.bar_chart(data['platform'].value_counts())

st.divider()
st.caption('Методология: единица наблюдения — публичный цифровой ресурс с зафиксированным этнокультурным позиционированием. Самоидентификация отдельных пользователей не устанавливается. Карта использует приближённые центры регионов, а не границы административных единиц.')
