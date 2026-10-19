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
    st.stop()

# DERK 2.0 — two public filters, abstract digital network inside Kazakhstan silhouette.
# Nodes denote verified unique URLs; faint lines are visual grouping only, NOT measured cross-platform ties.
st.markdown("""<style>
.derk-title {font-size:clamp(1.65rem,4vw,2.7rem);font-weight:800;letter-spacing:-.035em}
.derk-muted {color:#718096;font-size:.91rem}
.derk-card {border:1px solid rgba(80,150,200,.25);border-radius:16px;padding:15px;margin:8px 0;background:rgba(85,140,200,.055)}
.derk-name {font-weight:750;font-size:1.03rem;overflow-wrap:anywhere}
.derk-meta {font-size:.86rem;color:#8493a7;margin-top:5px}
@media(max-width:650px){.block-container{padding-left:1rem;padding-right:1rem}.derk-card{padding:12px}}
</style>""", unsafe_allow_html=True)

# Public map contains verified records only. Research cabinet retains its existing workflow.
if mode == 'Публичная карта':
    st.markdown('<div class="derk-title">Цифровая экосистема Казахстана</div>', unsafe_allow_html=True)
    st.caption('Контур страны — визуальная рамка цифрового пространства, а не карта распределения населения или ресурсов по территории.')

filter_cols = st.columns(2)
with filter_cols[0]:
    ethnic = st.selectbox('Этнос', ['Все'] + sorted(x for x in source['ethnic_group'].dropna().astype(str).unique() if x.strip()))
with filter_cols[1]:
    platform = st.selectbox('Платформа', ['Все'] + sorted(x for x in source['platform'].dropna().astype(str).unique() if x.strip()))

filtered = source.copy()
if ethnic != 'Все':
    filtered = filtered[filtered['ethnic_group'].astype(str) == ethnic]
if platform != 'Все':
    filtered = filtered[filtered['platform'].astype(str) == platform]

def canonical_url(value):
    raw = str(value).strip()
    try:
        parts = urlsplit(raw)
        if parts.scheme.lower() not in ('https', 'http') or not parts.netloc:
            return ''
        host = parts.netloc.lower()
        path = parts.path.rstrip('/') or '/'
        return urlunsplit((parts.scheme.lower(), host, path, parts.query, ''))
    except ValueError:
        return ''

resources = filtered.copy()
resources['_url_key'] = resources['public_url'].apply(canonical_url)
resources = resources[resources['_url_key'].ne('')].drop_duplicates(subset=['ethnic_group', '_url_key'])
resources = resources.sort_values(['ethnic_group', 'platform', 'community_name'], kind='stable')

# Stable color per ethnic group: the same group has the same color across filter changes.
PALETTE = ['#36D9F5','#A78BFA','#FB7185','#FBBF24','#34D399','#F472B6','#60A5FA','#F97316','#C4B5FD','#2DD4BF','#E879F9','#A3E635']
all_groups = sorted(source['ethnic_group'].dropna().astype(str).loc[lambda x:x.str.strip().ne('')].unique())
GROUP_COLORS = {g: PALETTE[i % len(PALETTE)] for i, g in enumerate(all_groups)}

# DPI counts distinct verified URLs per ethnic group; avoid counting multiple observation rows as multiple resources.
if mode == 'Публичная карта':
    all_verified = source.copy()
    all_verified['_url_key'] = all_verified['public_url'].apply(canonical_url)
    all_verified = all_verified[all_verified['_url_key'].ne('')].drop_duplicates(['ethnic_group', '_url_key'])
    total_unique = len(all_verified)
    group_unique = len(all_verified[all_verified['ethnic_group'] == ethnic]) if ethnic != 'Все' else 0
    share = 100 * group_unique / total_unique if total_unique else 0
    m1, m2, m3 = st.columns(3)
    m1.metric('Ресурсов по фильтрам', len(resources))
    m2.metric('Представленных этносов', resources['ethnic_group'].nunique())
    m3.metric('Доля этноса в базе', f'{share:.1f}%' if ethnic != 'Все' else '—', help='Доля уникальных подтверждённых URL выбранного этноса среди всех подтверждённых URL базы; фильтр платформы на знаменатель не влияет.')

# Stylized silhouette is a deliberate non-geographic design element; not an official boundary.
SILHOUETTE = [(22,123),(58,111),(87,77),(126,69),(151,49),(196,61),(224,43),(254,64),(289,57),(319,77),(367,67),(397,84),(443,86),(462,111),(430,129),(437,158),(406,178),(378,209),(340,212),(309,231),(267,218),(226,241),(185,211),(149,207),(117,183),(72,185),(60,155),(22,149)]

def inside_poly(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj-xi)*(y-yi)/(yj-yi+1e-12)+xi:
            inside = not inside
        j = i
    return inside

outline = ' '.join(f'{x},{y}' for x,y in SILHOUETTE)
node_svg = []
points = []
for _, item in resources.iterrows():
    url = str(item['public_url']).strip()
    key = str(item['_url_key'])
    group = str(item['ethnic_group'])
    color = GROUP_COLORS.get(group, '#36D9F5')
    # Hash placement keeps resource nodes stable as users switch filters.
    digest = hashlib.sha256((group+'|'+key).encode('utf-8')).digest()
    x = y = 0
    for attempt in range(80):
        hx = hashlib.sha256(digest + bytes([attempt]) + b'x').digest()
        hy = hashlib.sha256(digest + bytes([attempt]) + b'y').digest()
        xx = 34 + int.from_bytes(hx[:4], 'big') / 2**32 * 412
        yy = 55 + int.from_bytes(hy[:4], 'big') / 2**32 * 173
        if inside_poly(xx, yy, SILHOUETTE):
            x, y = xx, yy
            break
    if not x:
        x, y = 240, 135
    points.append((x, y, color, url, str(item['community_name']), group))

# Thin background strokes are decorative, not evidence of observed informational interactions.
for idx, (x,y,color,url,name,group) in enumerate(points):
    if idx % 3 == 0:
        node_svg.append(f'<path d="M {x:.1f},{y:.1f} Q 240,130 240,130" stroke="{color}" stroke-opacity=".13" fill="none" stroke-width=".7"/>')
for x,y,color,url,name,group in points:
    title = html.escape(f'{name} · {group}', quote=True)
    safe_url = html.escape(url, quote=True)
    node_svg.append(f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer"><title>{title} — открыть ресурс</title><circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{color}" fill-opacity=".12"/><circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="{color}" stroke="#07182D" stroke-width="1"/></a>')

svg_html = f"""<div style="background:linear-gradient(135deg,#07152B,#112E4B);border:1px solid #244968;border-radius:20px;padding:12px;overflow:hidden;color:white;font-family:system-ui">
<div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;padding:5px 9px"><strong>DERK · DIGITAL NETWORK</strong><span style="font-size:12px;color:#9FC9DB">Нажмите на узел для перехода ↗</span></div>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 485 280" style="width:100%;height:auto" role="img" aria-label="Схематический контур Казахстана с цифровыми ресурсами">
<polygon points="{outline}" fill="#123653" stroke="#4EE0F5" stroke-width="2.4" stroke-linejoin="round"/>
{''.join(node_svg)}
</svg>
<div style="padding:0 9px 9px;font-size:11px;color:#8FAEBF">Узлы — уникальные ссылки; расположение условное, линии декоративные. Это не географическая карта и не доказательство информационных связей.</div></div>"""
components.html(svg_html, height=350, scrolling=False)

st.subheader('Цифровые ресурсы')
if resources.empty:
    st.info('Для выбранных фильтров пока нет ресурсов с корректными ссылками.')
else:
    st.caption('Все найденные ресурсы показаны ниже. Нажмите «Открыть ресурс» для перехода на исходную площадку.')
    for _, item in resources.iterrows():
        group = html.escape(str(item['ethnic_group']))
        name = html.escape(str(item['community_name']) or 'Без названия')
        platform_label = html.escape(str(item['platform']))
        language_label = html.escape(str(item['language']))
        color = GROUP_COLORS.get(str(item['ethnic_group']), '#36D9F5')
        st.markdown(f'<div class="derk-card" style="border-left:4px solid {color}"><div class="derk-name">{name}</div><div class="derk-meta">{group} · {platform_label}' + (f' · {language_label}' if language_label else '') + '</div></div>', unsafe_allow_html=True)
        st.link_button('Открыть ресурс ↗', str(item['public_url']), use_container_width=True)

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
    st.download_button('Экспорт отфильтрованных данных CSV', filtered.to_csv(index=False).encode('utf-8-sig'), 'derk_filtered.csv', 'text/csv')
    st.download_button('Экспорт всей рабочей базы CSV', data.to_csv(index=False).encode('utf-8-sig'), 'derk_all_observations.csv', 'text/csv')
    if not data.empty:
        st.subheader('Статусы проверки')
        st.bar_chart(data['verification_status'].value_counts())
        st.subheader('Сводка по платформам')
        st.bar_chart(data['platform'].value_counts())

st.divider()
st.caption('Методология: единица наблюдения — публичный цифровой ресурс с зафиксированным этнокультурным позиционированием. Самоидентификация отдельных пользователей не устанавливается. Карта использует приближённые центры регионов, а не границы административных единиц.')
