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
 'ru': {'population':'Этнический состав','population_sub':'Население Казахстана · 2026','dpi_sub':'Ресурсы по этносам ↗','platform_sub':'Распределение по платформам ↗','idae_sub':'Ресурсов на 10 000 человек ↗','links_sub':'Методология связей ↗','content':'Контент-анализ','content_sub':'Анализ публикаций ↗','click':'Нажмите, чтобы открыть аналитику'},
 'kk': {'population':'Этностық құрам','population_sub':'Қазақстан халқы · 2026','dpi_sub':'Этностар бойынша ресурстар ↗','platform_sub':'Платформалар үлесі ↗','idae_sub':'10 000 адамға шаққандағы ресурстар ↗','links_sub':'Байланыстар әдіснамасы ↗','content':'Контент-талдау','content_sub':'Жарияланымдарды талдау ↗','click':'Аналитиканы ашу үшін басыңыз'},
 'en': {'population':'Ethnic composition','population_sub':'Kazakhstan population · 2026','dpi_sub':'Resources by ethnic group ↗','platform_sub':'Platform distribution ↗','idae_sub':'Resources per 10,000 people ↗','links_sub':'Connection methodology ↗','content':'Content analysis','content_sub':'Analyse publications ↗','click':'Click to open analytics'}
}

st.session_state.setdefault('derk_language','en')
lang_cols = st.columns([6, 1.5])
with lang_cols[1]:
    st.selectbox('Language / Тіл / Язык', ['en','kk','ru'], format_func=lambda v: {'ru':'РУС','kk':'ҚАЗ','en':'ENG'}[v], key='derk_language')
L = LANGS[st.session_state.derk_language]

# Rhythmic electronic synthesizer. The browser may block audible autoplay; user can enable it.
# Kept outside the map so the control also appears on Analytics and Research pages.
import json as _derk_json
_ambient_labels = {
    'en': ['♫ Ambient sound: on', '♫ Ambient sound: off', '♫ Enable sound (browser permission required)'],
    'kk': ['♫ Фондық дыбыс: қосулы', '♫ Фондық дыбыс: өшірулі', '♫ Дыбысты қосу (браузер рұқсаты қажет)'],
    'ru': ['♫ Фоновый звук: включён', '♫ Фоновый звук: выключен', '♫ Включить звук (требуется разрешение браузера)'],
}
_ambient_html = r'''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>body{margin:0;background:transparent;font-family:Inter,system-ui,Arial,sans-serif;color:#bdefff}
button{background:#102b46;color:#c9f1ff;border:1px solid #3b7797;border-radius:999px;padding:9px 15px;cursor:pointer;font-size:12px;min-height:39px}
button:hover{border-color:#6fe8fa}small{color:#94b6cc;margin-left:8px;font-size:11px}</style></head>
<body><button id="ambientToggle" type="button" aria-pressed="false"></button><small id="ambientStatus"></small>
<script>(()=>{
const labels=__LABELS__,button=document.getElementById('ambientToggle'),status=document.getElementById('ambientStatus');
let desired=true,playing=false,ctx=null,master=null,delay=null,feedback=null,filter=null;
let timer=null,nextNote=0,step=0;
try{const saved=localStorage.getItem('derk_ambient_enabled');if(saved==='false')desired=false}catch(e){}
const Audio=window.AudioContext||window.webkitAudioContext;
const BPM=106,STEP=60/BPM/2;
// A melodic electronic score: minor-key arpeggios, warm bass and restrained synth percussion.
// All sounds are generated locally in Web Audio; no external audio files or downloads.
const arp=[0,7,12,15,12,7,3,7,0,7,10,15,19,15,10,7,3,10,15,19,15,10,7,10,0,7,12,19,15,12,7,3];
const bass=[0,0,3,3,8,8,7,7];
const hz=n=>440*Math.pow(2,(n-69)/12);
function paint(){button.textContent=!desired?labels[1]:(playing?labels[0]:labels[2]);button.setAttribute('aria-pressed',String(playing));}
function makeAudio(){
 if(!Audio)return false;
 if(ctx)return true;
 ctx=new Audio();
 master=ctx.createGain();master.gain.value=0;
 const compressor=ctx.createDynamicsCompressor();compressor.threshold.value=-25;compressor.ratio.value=3;
 filter=ctx.createBiquadFilter();filter.type='lowpass';filter.frequency.value=2300;
 master.connect(filter);filter.connect(compressor);compressor.connect(ctx.destination);
 delay=ctx.createDelay(1);delay.delayTime.value=STEP*1.5;
 feedback=ctx.createGain();feedback.gain.value=.22;
 const wet=ctx.createGain();wet.gain.value=.18;
 master.connect(delay);delay.connect(feedback);feedback.connect(delay);delay.connect(wet);wet.connect(compressor);
 return true;
}
function tone(midi,when,duration,kind='arp',velocity=1){
 const osc=ctx.createOscillator(),gain=ctx.createGain();
 const f=hz(midi);
 osc.type=kind==='bass'?'sawtooth':kind==='pad'?'triangle':'square';
 osc.frequency.setValueAtTime(f,when);
 const peak=(kind==='bass'?.09:kind==='pad'?.018:.023)*velocity;
 const attack=kind==='pad'?.45:.012;
 gain.gain.setValueAtTime(.0001,when);
 gain.gain.exponentialRampToValueAtTime(peak,when+attack);
 gain.gain.exponentialRampToValueAtTime(.0001,when+duration);
 if(kind==='bass'){
  const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=340;osc.connect(lp);lp.connect(gain);
 }else{osc.connect(gain)}
 gain.connect(master);osc.start(when);osc.stop(when+duration+.04);
}
function kick(when){
 const o=ctx.createOscillator(),g=ctx.createGain();o.type='sine';
 o.frequency.setValueAtTime(120,when);o.frequency.exponentialRampToValueAtTime(45,when+.15);
 g.gain.setValueAtTime(.075,when);g.gain.exponentialRampToValueAtTime(.0001,when+.2);
 o.connect(g);g.connect(master);o.start(when);o.stop(when+.21);
}
function tick(when){
 const o=ctx.createOscillator(),g=ctx.createGain(),hp=ctx.createBiquadFilter();
 o.type='triangle';o.frequency.value=3800;hp.type='highpass';hp.frequency.value=2400;
 g.gain.setValueAtTime(.0001,when);g.gain.linearRampToValueAtTime(.007,when+.003);g.gain.exponentialRampToValueAtTime(.0001,when+.045);
 o.connect(hp);hp.connect(g);g.connect(master);o.start(when);o.stop(when+.05);
}
function schedule(){
 if(!ctx||!desired||ctx.state!=='running')return;
 while(nextNote<ctx.currentTime+.22){
  const pos=step%32,bar=Math.floor(step/8)%8;
  tone(60+arp[pos],nextNote,STEP*.82,'arp',pos%4===0?1:.66);
  if(pos%2===0)tick(nextNote);
  if(pos%4===0){tone(36+bass[Math.floor(step/8)%8],nextNote,STEP*3.8,'bass');kick(nextNote)}
  if(pos===0){const root=48+bass[Math.floor(step/8)%8];[0,3,7,12].forEach(n=>tone(root+n,nextNote,STEP*7.6,'pad',.8))}
  nextNote+=STEP;step++;
 }
}
async function start(){
 if(!desired||!makeAudio()){paint();return}
 try{
  await ctx.resume();
  if(ctx.state!=='running'){playing=false;paint();return}
  master.gain.cancelScheduledValues(ctx.currentTime);
  master.gain.setTargetAtTime(.48,ctx.currentTime,.65);
  if(!timer){nextNote=ctx.currentTime+.06;timer=setInterval(schedule,60);schedule()}
  playing=true;status.textContent='';paint();
 }catch(e){playing=false;paint()}
}
function stop(){playing=false;if(ctx&&master){master.gain.cancelScheduledValues(ctx.currentTime);master.gain.setTargetAtTime(0,ctx.currentTime,.15)}if(timer){clearInterval(timer);timer=null}paint()}
button.addEventListener('click',()=>{
 // If autoplay was blocked, the first click should ENABLE audio, not disable it.
 if(desired&&!playing){start();return}
 desired=!desired;
 try{localStorage.setItem('derk_ambient_enabled',String(desired))}catch(e){}
 if(desired)start();else stop();
});
paint();
// Request audible playback immediately, as soon as the audio controller loads.
if(desired){start();}
// Retry on focus/visibility changes, useful when the tab is restored.
window.addEventListener('focus',()=>{if(desired&&!playing)start()});
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&desired&&!playing)start()});
document.addEventListener('keydown',()=>{if(desired&&!playing)start()},{capture:true});
// Browsers may allow sound only after a gesture. A click anywhere in the app can retry.
document.addEventListener('pointerdown',e=>{if(desired&&!playing&&e.target!==button)start()},{capture:true});
try{window.parent.document.addEventListener('pointerdown',()=>{if(desired&&!playing)start()},{capture:true})}catch(e){}
if(ctx)ctx.onstatechange=()=>{playing=ctx.state==='running'&&desired;paint()};
window.addEventListener('pagehide',()=>{stop();if(ctx)ctx.close().catch(()=>{})});
})();</script></body></html>'''
_ambient_html = _ambient_html.replace('__LABELS__',_derk_json.dumps(_ambient_labels[st.session_state.derk_language], ensure_ascii=False))
components.html(_ambient_html, height=53, scrolling=False)

st.title('Digital Ethnic Representation of Kazakhstan')
st.caption('DERK 3.7 · ' + L['subtitle'])
# The public view is a conceptual network, not a geographic population map.
requested_view = str(st.query_params.get('derk_view', ''))
nav_options = ['Публичная карта', 'Аналитика', 'Исследовательский кабинет', 'Контент-анализ']
nav_index = 1 if requested_view == 'analytics' else 3 if requested_view == 'content' else 0
mode = st.sidebar.radio(L['mode'], nav_options, index=nav_index, key='derk_mode',
                        
    format_func=lambda v: {
        'Публичная карта': L['map'],
        'Аналитика': L['analytics'],
        'Исследовательский кабинет': L['cabinet'],
        'Контент-анализ': PANEL_TRANSLATIONS[st.session_state.derk_language]['content']
    }[v])

if ((requested_view == 'analytics' and mode != 'Аналитика') or
        (requested_view == 'content' and mode != 'Контент-анализ')):
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
        # Kazakhs are a demographic reference mode, not a tenth research sample.
        ethnic_options = ['__all__', '__kazakhs__'] + sorted(
            x for x in source['ethnic_group'].dropna().astype(str).unique()
            if x.strip() and x.strip().casefold() not in ('казахи', 'қазақтар', 'kazakhs')
        )
        ethnic = st.selectbox(
            L['ethnic'], ethnic_options,
            format_func=lambda x: (L['all'] if x == '__all__' else
                {'en':'Kazakhs', 'kk':'Қазақтар', 'ru':'Казахи'}[st.session_state.derk_language]
                if x == '__kazakhs__' else x)
        )
        kazakh_reference_mode = ethnic == '__kazakhs__'
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
    group_count = len(all_verified[all_verified['ethnic_group'].eq(ethnic)]) if ethnic not in ('__all__', '__kazakhs__') else 0
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
    # The turquoise field is a conceptual reference visualization, not resource data.
    reference_info = {
        'en': {'name':'Kazakhs', 'label':'Official population · beginning of 2026',
               'people':'people', 'source':'Source: Bureau of National Statistics of Kazakhstan, table T-18-08-G.',
               'note':'Demographic reference only. Not included in the nine-group digital-resource indices.'},
        'kk': {'name':'Қазақтар', 'label':'Ресми халық саны · 2026 жылдың басы',
               'people':'адам', 'source':'Дереккөз: Қазақстан Республикасының Ұлттық статистика бюросы, Т-18-08-Г кестесі.',
               'note':'Тек демографиялық анықтама. Тоғыз этностың цифрлық индекстеріне қосылмайды.'},
        'ru': {'name':'Казахи', 'label':'Официальная численность · начало 2026 года',
               'people':'человек', 'source':'Источник: Бюро национальной статистики РК, таблица Т-18-08-Г.',
               'note':'Только демографическая справка. Не входит в индексы девяти исследуемых этносов.'},
    }[st.session_state.derk_language]
    reference_json = json.dumps(reference_info, ensure_ascii=False).replace('<','\u003c').replace('>','\u003e')
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

    links_json = json.dumps({**json.loads(links_json), 'content': app_base_url + '?derk_view=content'}, ensure_ascii=False)

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
    .kazakh-reference{display:none;position:absolute;z-index:4;top:51%;left:50%;transform:translate(-50%,-50%);width:min(350px,37%);text-align:center;background:rgba(5,29,44,.90);border:1px solid #49e3e3;border-radius:18px;padding:20px 17px;box-shadow:0 0 45px #0ccad43d, inset 0 0 28px #0ccad412;backdrop-filter:blur(10px)}
    .kazakh-reference .k-name{font-size:22px;font-weight:800;color:#c7ffff}.kazakh-reference .k-count{font-size:clamp(24px,3vw,35px);font-weight:800;color:#6af9f3;letter-spacing:.02em;margin:9px 0}.kazakh-reference .k-small{font-size:11px;color:#a6d7df;line-height:1.5}.kazakh-reference .k-note{margin-top:9px;color:#d2eff1;font-size:11px;line-height:1.5}
    .shell.kazakh-mode .kazakh-reference{display:block}.shell.kazakh-mode .network{filter:drop-shadow(0 0 18px #13ddd67a)}
    @media(max-width:680px){.shell{min-height:755px}.head{padding:14px}.head strong{font-size:11px}.head span{display:none}.network{top:235px;height:300px}.panel{min-width:0;width:calc(50% - 20px);max-width:none;padding:10px;backdrop-filter:none}.panel .value{font-size:19px}.tc{top:155px;left:50%;width:calc(100% - 24px);max-width:none;min-width:0;transform:translateX(-50%)}.tc:hover,.tc:focus-visible{transform:translate(-50%,-3px)}.tl{top:52px;left:12px}.tr{top:52px;right:12px}.bl{bottom:68px;left:12px}.br{bottom:68px;right:12px}.footer{left:15px;right:15px;bottom:8px}.tip{max-width:min(260px,calc(100% - 24px));font-size:14px;padding:14px}.tip a{padding:11px 14px;min-height:44px}.kazakh-reference{top:51%;width:calc(100% - 45px);max-width:360px;padding:14px 12px}.kazakh-reference .k-name{font-size:18px}.kazakh-reference .k-count{font-size:26px}.kazakh-reference .k-small,.kazakh-reference .k-note{font-size:10px}}
    </style>
    <div class="shell" id="shell"><div class="head"><strong>DERK</strong></div>
      <svg class="network" id="network" viewBox="0 0 1000 570" xmlns="http://www.w3.org/2000/svg" aria-label="Interactive digital resource network">
      <defs><pattern id="grid" width="42" height="42" patternUnits="userSpaceOnUse"><path d="M42 0H0V42" fill="none" stroke="#286182" stroke-width=".6" opacity=".24"/></pattern><radialGradient id="glow"><stop stop-color="#164867" stop-opacity=".35"/><stop offset="1" stop-color="#164867" stop-opacity="0"/></radialGradient></defs>
      <rect width="1000" height="570" fill="url(#grid)"/><ellipse cx="500" cy="285" rx="440" ry="270" fill="url(#glow)"/><g id="world"></g></svg>
      <a class="panel tl" id="linkDpi" target="_blank" rel="noopener noreferrer"><div class="label" id="dpiLabel"></div><div class="value" id="nCount"></div><div class="sub" id="nGroups"></div></a>
      <a class="panel tr" id="linkPlatforms" target="_blank" rel="noopener noreferrer"><div class="label" id="platformLabel"></div><div class="value" id="pValue"></div><div class="sub" id="pSub"></div></a>
      <a class="panel bl" id="linkIdae" target="_blank" rel="noopener noreferrer"><div class="label" id="idaeLabel"></div><div class="value">IDAE</div><div class="sub" id="idaeSub"></div></a>
      <a class="panel br" id="linkContent" target="_blank" rel="noopener noreferrer"><div class="label" id="contentLabel"></div><div class="value">DERK CI</div><div class="sub" id="contentSub"></div></a>
      <a class="panel tc" id="linkPopulation" target="_blank" rel="noopener noreferrer"><div class="label" id="populationLabel"></div><div class="value">20 499 822</div><div class="sub" id="populationSub"></div></a>
      <div class="kazakh-reference" id="kazakhReference" role="status" aria-live="polite"><div class="k-name" id="kazakhName"></div><div class="k-small" id="kazakhLabel"></div><div class="k-count">14 664 202</div><div class="k-small" id="kazakhPeople"></div><div class="k-note" id="kazakhSource"></div><div class="k-note" id="kazakhNote"></div></div>
      <div class="tip" id="tip"></div><div class="footer" id="explain"></div>
    </div>
    <script>
    (()=>{
      const kazakhMode=__KAZAKH_MODE__, kazakh=__KAZAKH_INFO__, links=__LINKS__, data=__NODES__, t=__STRINGS__, shell=document.getElementById('shell'), svg=document.getElementById('network'), world=document.getElementById('world'), tip=document.getElementById('tip');
      const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
      const set=(id,v)=>document.getElementById(id).textContent=v;
      set('dpiLabel',t.dpi);set('platformLabel',t.platforms);set('idaeLabel',t.idae);set('contentLabel',t.content);set('contentSub',t.content_sub);set('explain',t.explain);
      set('populationLabel',t.population);set('populationSub',t.population_sub);
       [['linkPopulation','population'],['linkDpi','dpi'],['linkPlatforms','platforms'],['linkIdae','idae'],['linkContent','content']].forEach(([id,key])=>document.getElementById(id).href=links[key]);
       set('nCount',__COUNT__);set('nGroups',__GROUPS__);set('pValue',__TOP_PLATFORM__);set('pSub',__TOP_PCT__+' · ↗');set('idaeSub',t.idae_sub);
      if(kazakhMode){
        shell.classList.add('kazakh-mode');
        set('kazakhName',kazakh.name);set('kazakhLabel',kazakh.label);
        set('kazakhPeople',kazakh.people);set('kazakhSource',kazakh.source);set('kazakhNote',kazakh.note);
        set('explain',kazakh.note);
      }
      const NS='http://www.w3.org/2000/svg';const make=(name,attrs)=>{const e=document.createElementNS(NS,name);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));return e};
      if(kazakhMode){
        // Turquoise glow is a decorative full-field reference, not synthetic data nodes.
        const defs=svg.querySelector('defs');
        const grad=make('radialGradient',{id:'kazakhTurquoiseGlow',cx:'50%',cy:'50%',r:'70%'});
        [['0%','#28fff1','.46'],['55%','#0bc1c9','.25'],['100%','#071426','.04']].forEach(([offset,color,opacity])=>grad.appendChild(make('stop',{offset,'stop-color':color,'stop-opacity':opacity})));
        defs.appendChild(grad);
        world.appendChild(make('rect',{x:0,y:0,width:1000,height:570,fill:'url(#kazakhTurquoiseGlow)'}));
        for(let i=0;i<110;i++){
          const x=(i*179.39)%1000,y=(i*83.71)%570;
          world.appendChild(make('circle',{cx:x,cy:y,r:2+(i%4),fill:'#36f8ef',opacity:.12+(i%5)*.055}));
        }
      }
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
    panel_html = (panel_html.replace('__KAZAKH_MODE__',json.dumps(kazakh_reference_mode))
       .replace('__KAZAKH_INFO__',reference_json)
       .replace('__LINKS__',links_json).replace('__NODES__',data_json).replace('__STRINGS__',strings_json)
       .replace('__COUNT__',json.dumps(str(len(resources))))
       .replace('__GROUPS__',json.dumps(str(resources['ethnic_group'].nunique())+' '+L['groups'].lower()))
       .replace('__TOP_PLATFORM__',json.dumps(top_platform,ensure_ascii=False))
       .replace('__TOP_PCT__',json.dumps(f'{pct:.1f}%'))
)
    components.html(panel_html,height=780,scrolling=False)
    # Native Streamlit links work even when an embedded iframe blocks navigation.
    st.caption({'en':'Open an analytical indicator (also available from the five map monitors):',
                'kk':'Аналитикалық көрсеткішті ашу (картадағы бес панельден де қолжетімді):',
                'ru':'Открыть аналитический показатель (также доступен с пяти мониторов карты):'}[st.session_state.derk_language])
    _nav_labels = {
        'en':['Population','DPI','IDAE','Platforms','Connections'],
        'kk':['Халық саны','DPI','ИДАЭ','Платформалар','Байланыстар'],
        'ru':['Численность этносов','DPI','ИДАЭ','Платформы','Связи'],
    }[st.session_state.derk_language]
    _nav_sections = ['population','dpi','idae','platforms','connections']
    _nav_cols = st.columns(5)
    for _c, _label, _section in zip(_nav_cols, _nav_labels, _nav_sections):
        with _c:
            st.link_button(_label + ' ↗', links_json and app_base_url + '?derk_view=analytics&derk_section=' + _section, use_container_width=True)

    if not kazakh_reference_mode:
        st.subheader(L['resources'])
        st.caption(L['listnote'])
        if resources.empty: st.info(L['empty'])
    for _,item in (resources.iloc[0:0] if kazakh_reference_mode else resources).iterrows():
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

# DERK Content Intelligence — pilot. Interface strings follow the global DERK language selector.
CI_TRANSLATIONS = {
    'ru': {
        'heading': 'DERK Content Intelligence — анализ публикации',
        'note': 'Экспериментальный модуль. Данные Supabase не изменяются.',
        'url': 'Ссылка на публикацию',
        'button': 'Анализировать публикацию',
        'loading': 'Извлекаем текст публикации...',
        'success': 'Текст публикации получен',
        'title': 'Заголовок', 'date': 'Дата', 'author': 'Автор', 'language': 'Язык',
        'unknown_m': 'Не определён', 'unknown_f': 'Не определена',
        'text': 'Извлечённый текст', 'error': 'Не удалось обработать публикацию',
    },
    'kk': {
        'heading': 'DERK Content Intelligence — жарияланымды талдау',
        'note': 'Эксперименттік модуль. Supabase деректері өзгертілмейді.',
        'url': 'Жарияланымға сілтеме',
        'button': 'Жарияланымды талдау',
        'loading': 'Жарияланым мәтіні алынуда...',
        'success': 'Жарияланым мәтіні алынды',
        'title': 'Тақырып', 'date': 'Күні', 'author': 'Автор', 'language': 'Тілі',
        'unknown_m': 'Анықталмаған', 'unknown_f': 'Анықталмаған',
        'text': 'Алынған мәтін', 'error': 'Жарияланымды өңдеу мүмкін болмады',
    },
    'en': {
        'heading': 'DERK Content Intelligence — publication analysis',
        'note': 'Experimental module. Supabase data is not modified.',
        'url': 'Publication URL',
        'button': 'Analyse publication',
        'loading': 'Extracting publication text...',
        'success': 'Publication text extracted',
        'title': 'Title', 'date': 'Date', 'author': 'Author', 'language': 'Language',
        'unknown_m': 'Not identified', 'unknown_f': 'Not identified',
        'text': 'Extracted text', 'error': 'Unable to process publication',
    },
}


if mode == 'Контент-анализ':
    ci = CI_TRANSLATIONS[st.session_state.derk_language]

    st.markdown("""
    <style>
    .ci-hero {
        padding: 28px;
        border: 1px solid #37567b;
        border-radius: 22px;
        background: linear-gradient(120deg, #0b1c38, #171638, #102947);
        box-shadow: 0 0 35px #266bff16;
        margin-bottom: 22px;
    }
    .ci-eyebrow {
        color: #ffab54;
        font-size: 12px;
        letter-spacing: 3px;
        font-weight: 700;
    }
    .ci-heading {
        color: #f4f8ff;
        font-size: clamp(26px, 4vw, 40px);
        font-weight: 800;
        margin: 12px 0;
    }
    .ci-description {color: #afc5e4; font-size: 15px;}
    </style>
    <div class="ci-hero">
        <div class="ci-eyebrow">DERK / RESEARCH INTELLIGENCE</div>
        <div class="ci-heading">Content Intelligence</div>
        <div class="ci-description">
            Digital ethnic representation · Comparative content analysis
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Исследовательские показатели")

    community = st.selectbox(
        "Этническое сообщество",
        ["Немцы", "Русские", "Корейцы", "Уйгуры"],
        key="ci_community"
    )

    homelands = {
        "Немцы": "Германия",
        "Русские": "Россия",
        "Корейцы": "Корея",
        "Уйгуры": "Историческая родина — требует уточнения",
    }
    homeland = homelands[community]

    st.caption(
        "Пилотная модель: доля публикаций о Казахстане, "
        "доля публикаций об исторической родине и наличие "
        "казахоязычного контента."
    )

    uploaded_review = st.file_uploader(
        "Загрузить проверенную таблицу content_review.csv",
        type=["csv"],
        key="ci_review_upload"
    )

    result = None

    if uploaded_review is not None:
        try:
            review = pd.read_csv(
                uploaded_review,
                dtype=str,
                keep_default_na=False
            )            
            preliminary_columns = {
                "internal_agenda_preliminary": "kazakhstan_related",
                "origin_agenda_preliminary": "homeland_related",
            }

            for source, target in preliminary_columns.items():
                if source in review.columns and target not in review.columns:
                    review[target] = review[source]

            required = {
                "verified_article",
                "kazakhstan_related",
                "homeland_related",
                "language",
            }

            missing = required - set(review.columns)

            if missing:
                st.error(
                    "В таблице отсутствуют поля: "
                    + ", ".join(sorted(missing))
                )
            else:
                for field in required:
                    review[field] = (
                        review[field].astype(str).str.strip().str.lower()
                    )

                valid_labels = (
                    review["verified_article"].isin(["yes", "no"])
                    & review["kazakhstan_related"].isin(["yes", "no"])
                    & review["homeland_related"].isin(["yes", "no"])
                )

                verified = review[
                    valid_labels
                    & review["verified_article"].eq("yes")
                ].copy()

                total = len(verified)

                if total:
                    kaz = 100 * (
                        verified["kazakhstan_related"].eq("yes").sum()
                        / total
                    )
                    home = 100 * (
                        verified["homeland_related"].eq("yes").sum()
                        / total
                    )
                    kazakh = verified["language"].eq("kk").any()

                    result = {
                        "kazakhstan": round(kaz, 1),
                        "homeland": round(home, 1),
                        "kazakh": kazakh,
                        "total": total,
                    }

                st.caption(
                    f"Строк в файле: {len(review)} · "
                    f"Подтверждённых статей с полной разметкой: {total}"
                )

        except Exception as exc:
            st.error(f"Ошибка обработки CSV: {exc}")

    if result is None:
        st.info(
            "Ожидаются проверенные данные. "
            "Проценты не рассчитываются до подтверждения публикаций."
        )
    else:
        a, b, c = st.columns(3)

        with a:
            st.metric(
                "Связь с Казахстаном",
                f"{result['kazakhstan']}%"
            )
        with b:
            st.metric(
                f"Связь: {homeland}",
                f"{result['homeland']}%"
            )
        with c:
            st.metric(
                "Казахский язык",
                "Обнаружен" if result["kazakh"] else "Не обнаружен"
            )

        chart = pd.DataFrame({
            "Показатель": ["Казахстан", homeland],
            "Доля, %": [
                result["kazakhstan"],
                result["homeland"],
            ],
        })

        fig = px.bar(
            chart,
            x="Показатель",
            y="Доля, %",
            color="Показатель",
            color_discrete_sequence=["#38bdf8", "#ff963f"],
            text="Доля, %",
        )

        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
        )
        fig.update_layout(
            height=400,
            yaxis_range=[0, 110],
            showlegend=False,
            paper_bgcolor="#071426",
            plot_bgcolor="#071426",
            font_color="#e9f3ff",
            yaxis_title="Доля публикаций, %",
            xaxis_title="",
        )

        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            f"Основание расчёта: {result['total']} "
            "подтверждённых публикаций. "
            "Показатели могут пересекаться."
        )

    st.divider()

    with st.expander("Проверка отдельной публикации"):
        st.caption(ci["note"])

        article_url = st.text_input(
            ci["url"],
            value=(
                "https://wiedergeburt-kasachstan.de/"
                "gruppa-zdorovya-otkryvaem-astanu-s-novoj-storony/"
            ),
            key="derk_article_url_legacy",
        )

        if st.button(ci["button"], key="derk_analyse_article"):
            from content_intelligence.collector import collect_article

            try:
                with st.spinner(ci["loading"]):
                    article = collect_article(article_url)

                st.success(ci["success"])
                st.write(f"**{ci['title']}:**", article.get("title") or "—")
                st.write(f"**{ci['date']}:**", article.get("date") or "—")
                st.write(f"**{ci['author']}:**", article.get("author") or "—")
                st.write(
                    f"**{ci['language']}:**",
                    article.get("language") or "—"
                )
                st.text_area(
                    ci["text"],
                    article.get("text") or "",
                    height=350,
                )

            except Exception as exc:
                st.error(f"{ci['error']}: {exc}")

   
