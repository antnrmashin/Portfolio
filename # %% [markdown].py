# %% [markdown]
# Анализ системы метрик приложения

# %% [markdown]
# К началу лета в приложении Procrastinate Pro+ появился новый вид контента — спортивный. С его помощью менеджеры стремятся расширить аудиторию, добавив в неё пользователей, которые увлекаются спортом и здоровым образом жизни.
# 
# К запуску нового контента была скорректирована маркетинговая стратегия привлечения пользователей. Согласно бизнес-модели продукта, привлечение должно окупиться за первые 28 дней (4 недели).
# 
# После запуска нового контента и изменения стратегии интерес к продукту в целом вырос, но выручка начала стагнировать. Нужно разобраться, почему это происходит.
# 
# Задачи:
# 
# провести анализ юнит-экономики продукта в динамике за первые 28 дней;
# разобраться в причинах стагнации выручки;
# определить, какие источники привлечения приносят прибыль, а какие не выходят на уровень окупаемости;
# дать рекомендации отделу маркетинга.

# %% [markdown]
# Данные
# В вашем распоряжении есть данные о посещениях приложения, покупках и расходах на маркетинг. Данные собраны в трёх датасетах.
# 
# Датасет ppro_visits.csv — информация о посещениях приложения пользователями, которые зарегистрировались с 1 апреля 2024 года по 30 ноября 2024 года:
# 
# user_id — уникальный идентификатор пользователя;
# region — страна пользователя;
# device — категория устройства пользователя;
# channel — идентификатор рекламного источника, из которого пришёл пользователь;
# session_start — дата и время начала сессии;
# session_end — дата и время окончания сессии.
# Датасет ppro_orders.csv — информация о покупках:
# 
# user_id — уникальный идентификатор пользователя, который сделал покупку;
# event_dt — дата и время покупки;
# revenue — выручка.
# Датасет ppro_costs.csv — информация о затратах на маркетинг:
# 
# dt — дата
# channel — идентификатор рекламного источника;
# costs — затраты на этот рекламный источник в этот день.

# %% [markdown]
# Загрузка и предобработка данных

# %%
# Загрузка библиотек
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# %% [markdown]
# Загрузка датафреймов

# %%
PATH = "https://code.s3.yandex.net/datasets/"

# %%
visits_df = pd.read_csv(PATH + 'ppro_visits.csv')

# %%
orders_df = pd.read_csv(PATH + 'ppro_orders.csv')

# %%
costs_df = pd.read_csv(PATH + 'ppro_costs.csv')

# %%
display(visits_df)

# %%
display(orders_df)

# %%
display(costs_df)

# %%
# Преобразуем даты в datetime
visits_df['session_start'] = pd.to_datetime(visits_df['session_start'])
visits_df['session_end'] = pd.to_datetime(visits_df['session_end'])
orders_df['event_dt'] = pd.to_datetime(orders_df['event_dt'])
costs_df['dt'] = pd.to_datetime(costs_df['dt'])

# %%
# Функция оптимизации памяти
def optimize_memory(df):
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    start_mem = df.memory_usage().sum() / 1024**2
    for col in df.columns:
        col_type = df[col].dtypes
        if col_type in numerics:
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
    end_mem = df.memory_usage().sum() / 1024**2
    print(f"Memory usage reduced from {start_mem:.2f} MB to {end_mem:.2f} MB ({100 * (start_mem - end_mem) / start_mem:.1f}% reduction)")
    return df

# Оптимизация
visits_df = optimize_memory(visits_df)
orders_df = optimize_memory(orders_df)
costs_df = optimize_memory(costs_df)

# Финальная проверка
print("visits_df:")
visits_df.info()
print("\norders_df:")
orders_df.info()
print("\ncosts_df:")
costs_df.info()

# %% [markdown]
# Посмотрим уникальные значения

# %%
print(visits_df['region'].unique())

# %%
print(visits_df['device'].unique())

# %%
print(visits_df['channel'].unique())

# %%
print(orders_df['revenue'].unique())

# %%
print(orders_df['revenue'].unique())

# %% [markdown]
# Проверим на пропуски

# %%
# Проверка на дубликаты
print(f"Дубликаты в visits: {visits_df.duplicated().sum()}")
print(f"Дубликаты в orders: {orders_df.duplicated().sum()}")
print(f"Дубликаты в costs: {costs_df.duplicated().sum()}")

# Удалим дубликаты
visits_df.drop_duplicates(inplace=True)
orders_df.drop_duplicates(inplace=True)
costs_df.drop_duplicates(inplace=True)

# Проверка на пропуски
print("Пропуски:")
print(visits_df.isna().sum())
print(orders_df.isna().sum())
print(costs_df.isna().sum())


# Проверка, все ли user_id из orders есть в visits
print("user_id в orders не найденные в visits:", orders_df[~orders_df['user_id'].isin(visits_df['user_id'])].shape[0])

# %% [markdown]
# Просмотрели все датафреймы. Увидели, что столбцы, хранящие дату и время хранятся в формате Object и преобразовали в datetime. Уменьшили с помощью функции формат числовых значений. Нулевых значений не обнаружено. Дубликатов нет.

# %% [markdown]
# Подготовка данных к когортному анализу

# %%
# Минимальная дата сессии (дата привлечения)
user_first_session = visits_df.groupby('user_id').agg(
    first_dt=('session_start', 'min'),
    first_channel=('channel', 'first')  
).reset_index()

# %%
# Количество привлечённых пользователей по каналам
user_counts = user_first_session.groupby('first_channel').size().reset_index(name='users')

# Суммарные затраты по каналам
channel_costs = costs_df.groupby('channel')['costs'].sum().reset_index()

# Объединим и посчитаем CAC
cac_df = channel_costs.merge(user_counts, left_on='channel', right_on='first_channel', how='left')
cac_df['cac'] = cac_df['costs'] / cac_df['users']

# Оставим нужные поля
cac_df = cac_df[['channel', 'cac']]

# %%
display(channel_costs)

# %%
# Собираем новую таблицу
profiles = (
    visits_df
    .groupby('user_id', as_index=False)
    .agg(
        first_dt      = ('session_start','min'),
        first_channel = ('channel','first')  # предполагаем, что channel отсортирован по времени
    )
)
profiles['first_date'] = profiles['first_dt'].dt.date

# %%
# 2. Считаем, сколько новых пользователей пришло в каждый день по каждому каналу
new_users = (
    profiles
    .groupby(['first_channel','first_date'], as_index=False)
    .agg(new_users=('user_id','nunique'))
)

# %%
# 3. Готовим расходы по дням–каналам
costs_df['cost_date'] = costs_df['dt'].dt.date
daily_costs = (
    costs_df
    .groupby(['channel','cost_date'], as_index=False)
    .agg(daily_costs=('costs','sum'))
)

# %%
# 4. Считаем CAC по «день,канал»
cac = (
    daily_costs
    .merge(new_users,
           left_on = ['channel','cost_date'],
           right_on= ['first_channel','first_date'],
           how     = 'left')
    .assign(cac = lambda df: df.daily_costs / df.new_users)
    [['first_channel','first_date','cac']]
)

# %%
# 5. Добавляем CAC в профиль
profiles = (
    profiles
    .merge(cac,
           left_on = ['first_channel','first_date'],
           right_on= ['first_channel','first_date'],
           how     = 'left')
)

# %%
for df, dtcol in [(visits_df,'session_start'), (orders_df,'event_dt')]:
    df = (
        df
        .merge(profiles[['user_id','first_dt','first_channel','cac']],
               on='user_id', how='left')
        .assign(lifetime_days = lambda d:
            (d[dtcol] - d['first_dt']).dt.days)
        )

    if dtcol == 'session_start':
        visits_df = df
    else:
        orders_df = df

# %%
display(profiles)

# %%
display(orders_df)

# %%
display(visits_df)

# %% [markdown]
# Анализ месячной динамики основных метрик продукта

# %% [markdown]
# Задача 1. Начать анализ данных с изучения динамики активности пользователей и их вовлечённости в продукт. Рассчитать по всем данным значения DAU, MAU и Stickiness и визуализировать их. Активными считать всех пользователей, которые взаимодействовали с приложением.
# 
# Задача 2. В разрезе каждого месяца привлечения новых пользователей рассчитать:
# 
# Среднюю стоимость привлечения пользователя (CAC).
# Значение LTV и ROI с учётом покупок, совершённых за 28 дней с момента привлечения.

# %%
# 1) Получаем ежедневные DAU
visits_df['date'] = visits_df['session_start'].dt.date
daily = (
    visits_df
    .groupby('date', as_index=False)
    .user_id.nunique()
    .rename(columns={'user_id':'DAU'})
)
# Привяжем к дате месяц
daily['month'] = pd.to_datetime(daily['date']).dt.to_period('M')

# 2) Усредняем DAU по месяцам
monthly_dau = daily.groupby('month')['DAU'].mean()

# 3) Считаем MAU правильно
visits_df['month'] = visits_df['session_start'].dt.to_period('M')
monthly_mau = (
    visits_df
    .groupby('month')
    .user_id.nunique()
    .rename('MAU')
)

# 4) Stickiness
stickiness = (monthly_dau / monthly_mau).rename('Stickiness')

# Соберём в один DataFrame
metrics = pd.concat([monthly_dau, monthly_mau, stickiness], axis=1).reset_index()
metrics

# %%
# Преобразуем Period в datetime для оси X
metrics['month_ts'] = metrics['month'].dt.to_timestamp()

fig, axes = plt.subplots(1, 3, figsize=(18,4))

# 1) DAU
sns.lineplot(
    x='month_ts', 
    y='DAU', 
    data=metrics, 
    marker='o', 
    ax=axes[0]
)
axes[0].set_title('Средний DAU')
axes[0].set_xlabel('')
axes[0].set_ylabel('DAU')

# 2) MAU
sns.lineplot(
    x='month_ts', 
    y='MAU', 
    data=metrics, 
    marker='o',
    ax=axes[1]
)
axes[1].set_title('MAU')
axes[1].set_xlabel('')
axes[1].set_ylabel('MAU')

# 3) Stickiness (вовлеченность)
sns.lineplot(
    x='month_ts', 
    y='Stickiness', 
    data=metrics, 
    marker='o', 
    ax=axes[2]
)
axes[2].set_title('Stickiness (DAU/MAU)')
axes[2].set_xlabel('')
axes[2].set_ylabel('Stickiness')

for ax in axes:
    ax.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()

# %% [markdown]
# Вместе эти метрики показывают, что проект не только привлекает больше пользователей, но и удерживает их: ежемесячная аудитория растёт быстрее, чем ежедневная, а доля активных в месяце пользователей тоже увеличивается. По графикам видно, что включение спортивного контента поспособстовало привлечению и удержанию пользователей. Что, в целом говорит нам что стратегия по привелчению сработала. Видно, что интерес и привлечение до внедрения спортивного контента было высоким в мае месяце(но к июне стало падать), но удержание пользователей стало падать(к июню же, наоброт возрастать). В июне же, при включении спортивного контента, все метрики стали расти, и это хорошо и соответствует целям.

# %%
# 1) Граница наличия данных по датам привлечения
max_acq_date = orders_df['first_dt'].max()
print("максимальная дата в orders_df:", max_acq_date)

# %%
# 2) Добавляем месяц к профилям и считаем для каждой когорты её самый поздний день
profiles['cohort_month'] = profiles['first_dt'].dt.to_period('M')
cohort_last_join = (
    profiles
    .groupby('cohort_month')['first_dt']
    .max()
    .rename('last_join_dt')
)

# %%
# 3) Оставляем только те когорты, чьё last_join_dt + 27 дней не выходит за рамки max_acq_date
valid_cohorts = (
    cohort_last_join[cohort_last_join + pd.Timedelta(days=27) <= max_acq_date]
    .index
    .tolist()
)
print("полноценные когорты:", valid_cohorts)

# %%
# 4) Считаем количество пользователей в каждой полной когорте
users_per_cohort = (
    profiles
    .query("cohort_month in @valid_cohorts")
    .groupby('cohort_month', as_index=False)
    .user_id.nunique()
    .rename(columns={'user_id':'users'})
)

# %%
# 5) Считаем суммарный revenue за первые 28 дней (lifetime_days <= 27)
orders_28 = orders_df.query('lifetime_days <= 27').copy()
orders_28['cohort_month'] = orders_28['first_dt'].dt.to_period('M')
rev_per_cohort = (
    orders_28
    .query("cohort_month in @valid_cohorts")
    .groupby('cohort_month', as_index=False)
    .revenue.sum()
    .rename(columns={'revenue':'revenue_sum'})
)

# %%
# 6) Считаем суммарные затраты на привлечение по когортам
costs_df['cohort_month'] = costs_df['dt'].dt.to_period('M')
cost_per_cohort = (
    costs_df
    .query("cohort_month in @valid_cohorts")
    .groupby('cohort_month', as_index=False)
    .costs.sum()
    .rename(columns={'costs':'cost_sum'})
)

# %%
# 7) Собираем матрицу метрик: users, revenue_sum, cost_sum, затем считаем LTV/CAC/ROI
metrics = (
    users_per_cohort
    .merge(rev_per_cohort,   on='cohort_month', how='left')
    .merge(cost_per_cohort,  on='cohort_month', how='left')
    .assign(
        ltv = lambda d: (d['revenue_sum'] / d['users']).round(2),
        cac = lambda d: (d['cost_sum']    / d['users']).round(2),
        roi = lambda d: (((d['ltv'] - d['cac']) / d['cac']) * 100).round(1),
        cm_str = lambda d: d['cohort_month'].astype(str)
    )
    .sort_values('cohort_month')
)

# %%
# 8) Посмотрим результат
display(metrics)

# %%
# 9) Визуализация LTV vs CAC
plt.figure(figsize=(10, 5))
sns.lineplot(data=metrics, x='cm_str', y='ltv', marker='o', label='LTV')
sns.lineplot(data=metrics, x='cm_str', y='cac', marker='o', label='CAC')
plt.xticks(rotation=45)
plt.title('LTV vs CAC по когортам')
plt.xlabel('Когорта (год-месяц)')
plt.ylabel('Сумма, ед.')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# %%
# 10) Визуализация ROI
plt.figure(figsize=(10, 5))
sns.barplot(data=metrics, x='cm_str', y='roi', color='steelblue')
plt.axhline(0, color='gray', linestyle='--')
plt.xticks(rotation=45)
plt.title('ROI по когортам (%)')
plt.xlabel('Когорта (год-месяц)')
plt.ylabel('ROI, %')
plt.grid(axis='y')
plt.tight_layout()
plt.show()

# %% [markdown]
# Промежуточный вывод: Видно, что после июня суммарная прибыль, которую приносит клиент выросла, но так же видно, что и затраты на привлечение клиента выросло. Собственно, график ROI хорошо отражает то, что в июне был перекос в отрицательную зону окупаемости ( что логично, так как мы потратились на новый канал), в июле мы вышли в плюс(опять таки, привлекли новых пользователей и наши затраты стали окупаться), но потом мы видим опять то, что окупаемость перешла в отрицательную зону. Это так же отражено на графике с LTV, пользователи стали меньше приносить прибыль. (В июле доход с пользователей был больше чем затраты на привлечение пользователей, но потом, затраты стали перевешивать)

# %% [markdown]
# Анализ метрик в разрезе источника привлечения

# %% [markdown]
# Теперь необходимо разобраться, какие источники привлечения перспективны, а какие за 28 дней не окупились.
# 
# Задача 1. Определить самые популярные источники привлечения:
# 
# Посчитать общее число привлечённых пользователей для каждого источника.
# Визуализировать динамику набора новых пользователей по дням в каждом источнике.
# Рассчитать и визуализировать динамику DAU, MAU и Stickiness по источникам привлечения.
# Задача 2. Изучить динамику изменения метрик на 28-й день в разрезе источника. Провести анализ с выделением недельных когорт по дате привлечения. Рассчитать и визуализировать:
# 
# Скользящее удержание на 14-й день с момента привлечения (за период с 14-го по 28-й день).
# Конверсию в покупку.

# %%
# 1) Граница данных
max_acq_date = orders_df['first_dt'].max()

# %%
# 2) Список «валидных» месячных когорт по каналу (чтобы имели => 28 дней данных)
profiles['cohort_month'] = profiles['first_dt'].dt.to_period('M')
cohort_last_join = (
    profiles
      .groupby(['first_channel','cohort_month'])['first_dt']
      .max()
      .rename('last_join_dt')
)
valid_cohorts = (
    cohort_last_join[cohort_last_join + pd.Timedelta(days=27) <= max_acq_date]
      .reset_index()[['first_channel','cohort_month']]
)

# %%
# 3) Распределение пользователей по каналам 
users_per_channel = (
    profiles
      .groupby('first_channel')['user_id']
      .nunique()
      .sort_values(ascending=False)
      .reset_index(name='users')
)
plt.figure(figsize=(8,4))
sns.barplot(data=users_per_channel, x='first_channel', y='users', palette='tab10')
plt.title('Распределение пользователей по каналам')
plt.xlabel('Канал')
plt.ylabel('Число пользователей')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# %% [markdown]
# На данном графике видно, что больше всего пользователей на канале FaceBoom. ПО сути, он самый популярный у пользователей

# %%
# 4. Ежедневный набор новых пользователей по каналу
new_daily = (
    profiles
      .assign(date=profiles['first_dt'].dt.date)
      .groupby(['date','first_channel'])['user_id']
      .nunique()
      .reset_index(name='new_users')
)
plt.figure(figsize=(12,4))
sns.lineplot(data=new_daily, x='date', y='new_users', hue='first_channel', estimator=None)
plt.title('Ежедневный набор новых пользователей по каналам')
plt.xlabel('Дата')
plt.ylabel('Новых пользователей')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# %% [markdown]
# Собственно, данный график подтверждает, что у пользователей самый популярный канал это FaceBoom. А так же, что после июня месяца, канал TipTop вырвался вперед, относительно двух других каналов(MediaTornado и RocketSuperAds)

# %%
# 5. DAU, MAU, Stickiness по каналам
vis = visits_df.copy()
vis['date'] = vis['session_start'].dt.date
vis['month'] = vis['session_start'].dt.to_period('M')

# DAU по каналу
dau_ch = (
    vis
      .groupby(['date','first_channel'])['user_id']
      .nunique()
      .reset_index(name='DAU')
)

# MAU по каналу
mau_ch = (
    vis
      .groupby(['month','first_channel'])['user_id']
      .nunique()
      .reset_index(name='MAU')
)

# Средний DAU в месяце
avg_dau_ch = (
    dau_ch
      .assign(month=dau_ch['date'].astype('datetime64[ns]').dt.to_period('M'))
      .groupby(['month','first_channel'])['DAU']
      .mean()
      .reset_index()
)

# Соединяем и вычисляем stickiness
ch_metrics = (
    avg_dau_ch
      .merge(mau_ch, on=['month','first_channel'])
      .assign(stickiness=lambda d: d['DAU']/d['MAU'])
)
# Визуализация
for metric in ['DAU','MAU','stickiness']:
    plt.figure(figsize=(10,4))
    sns.lineplot(
        data=ch_metrics,
        x=ch_metrics['month'].dt.to_timestamp(),
        y=metric,
        hue='first_channel',
        marker='o'
    )
    plt.title(f'{metric} по каналам (среднемесячно)')
    plt.xlabel('Месяц')
    plt.ylabel(metric)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# %% [markdown]
# На данных графиках видно, что кол-во уникальных пользователей что в DAU, что в MAU заметно растет на канале TipTop. Канал Faceboom растет умерено. Остальные же каналы держат привлеченных новых пользователей примерно на одном уровне. Что касается Возврата пользователей , то на графике видно, что к июню на канале TipTop этот показатель увеличился и держится примерно на одном уровне всё наше исследование. Остальные же каналы не особо показывают изменения. Разве что, MediaTornado немного потерял возвращающихся пользователей.

# %%
# 6. Retention 14–28 дней по каналам 
vis2 = visits_df[['user_id', 'session_start', 'session_end']].merge(
    profiles[['user_id','first_dt','first_channel']],
    on='user_id',
    how='inner'
)
vis2['lifetime_days']  = (vis2['session_start'] - vis2['first_dt']).dt.days
vis2['cohort_month']   = vis2['first_dt'].dt.to_period('M')


# total и retained
total = (
    vis2
      .query("lifetime_days==0")
      .groupby(['first_channel','cohort_month'], as_index=False)
      .user_id.nunique()
      .rename(columns={'user_id':'total_users'})
)
ret14_28 = (
    vis2[vis2.lifetime_days.between(14,28)]
      .groupby(['first_channel','cohort_month'], as_index=False)
      .user_id.nunique()
      .rename(columns={'user_id':'retained_users'})
)
ret_rate = (
    total
      .merge(ret14_28, on=['first_channel','cohort_month'], how='left')
      .fillna({'retained_users':0})
      .merge(valid_cohorts, on=['first_channel','cohort_month'])
      .assign(retention_14_28=lambda d: d['retained_users']/d['total_users'])
      .sort_values(['first_channel','cohort_month'])
)
ret_rate['cohort_month_str'] = ret_rate['cohort_month'].astype(str)

plt.figure(figsize=(10,5))
sns.lineplot(
    data=ret_rate,
    x='cohort_month_str',
    y='retention_14_28',
    hue='first_channel',
    marker='o'
)
plt.title('Retention 14–28 дней по каналам (валидные когорты)')
plt.xlabel('Месяц когорты')
plt.ylabel('Retention rate')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# %% [markdown]
# На данном графике видно, что доля вернувшихся пользователей больше всего у канала TipTop, остальные каналы не показали особых изменений в данном параметре

# %%
# 7. Недельная конверсия / CAC / LTV / ROI по каналам 
# 7.1. Отбираем «валидные» недельные когорты (first_dt + 27 <= max_acq_date)
profiles_min = (
    profiles[['user_id','first_dt','first_channel']]
      .copy()
      .assign(cohort_week=lambda d: 
          d['first_dt'].dt.to_period('W').dt.to_timestamp()
      )
)


# Группировка по profiles_min
week_last_join = (
    profiles_min
      .groupby(['first_channel','cohort_week'])['first_dt']
      .max()
      .rename('last_join_dt')
)


valid_weeks = (
    week_last_join[week_last_join + pd.Timedelta(days=27) <= max_acq_date]
      .reset_index()[['first_channel','cohort_week']]
)


print(valid_weeks.head())

# %%
# 7.2. Новые users и buyers
weekly_users = (
    profiles_min
      .merge(valid_weeks, on=['first_channel','cohort_week'])
      .groupby(['cohort_week','first_channel'], as_index=False)['user_id']
      .nunique()
      .rename(columns={'user_id':'new_users'})
)

orders_min = (
    orders_df
      .assign(lifetime_days=(orders_df['event_dt'] - orders_df['first_dt']).dt.days)
      [['user_id','revenue','lifetime_days']]
)

ord28 = (
    orders_min
      .query('lifetime_days <= 27')
      .merge(
          profiles_min[['user_id','first_channel','cohort_week']],
          on='user_id',
          how='inner'
      )
)

weekly_buyers = (
    ord28
      .groupby(['cohort_week','first_channel'], as_index=False)['user_id']
      .nunique()
      .rename(columns={'user_id':'buyers'})
)

weekly_conv = (
    weekly_users
      .merge(weekly_buyers, on=['cohort_week','first_channel'], how='left')
      .fillna({'buyers':0})
      .assign(
          conv=lambda d: d['buyers'] / d['new_users'],
          cohort_start=lambda d: d['cohort_week'].dt.date
      )
)


plt.figure(figsize=(12, 4))
sns.lineplot(
    data=weekly_conv,
    x='cohort_start',
    y='conv',
    hue='first_channel',
    marker='o'
)
plt.title('Конверсия в покупку по каналам (недельные когорты)')
plt.xlabel('Дата старта недели')
plt.ylabel('Conversion rate')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# %% [markdown]
# На данном графике видно, что конверсия в покупку после июня месяца показала рост у канала TipTop и немного у FaceBoom. Это говорит о том, что спортивный контент привлекает больше пользователей на канале TipTop, так как видно, что данный показатель после июня хоть и скачет, но остается примерно одинаковый. У FaceBoom, данный показатель начинает падать к августу и дальше, в целом, нормализуется. Остальные же каналы не показали сильных изменений

# %%
# 7.3. Недельный CAC/LTV/ROI
costs_min = (
    costs_df[
        ['channel',
         'dt',
         'costs']
    ]
    .rename(columns={'channel':'first_channel', 'dt':'date'}) 
    .assign(cohort_week=lambda d: d['date'].dt.to_period('W').dt.to_timestamp())
)

costs_week = (
    costs_min
      .merge(valid_weeks, on=['first_channel','cohort_week'], how='inner')
      .groupby(['cohort_week','first_channel'], as_index=False)
      .costs
      .sum()
      .rename(columns={'costs':'weekly_costs'})
)

cac_w = (
    costs_week
      .merge(weekly_users.rename(columns={'new_users':'users'}),
             on=['cohort_week','first_channel'])
      .assign(cac=lambda d: d['weekly_costs']/d['users'])
)
rev_w = (
    ord28
      .groupby(['cohort_week','first_channel'], as_index=False)
      .agg(weekly_revenue=('revenue','sum'),
           buyers=('user_id','nunique'))
      .merge(weekly_users.rename(columns={'new_users':'users'}),
             on=['cohort_week','first_channel'])
      .assign(ltv=lambda d: d['weekly_revenue']/d['users'])
)
roi_w = (
    cac_w
      .merge(rev_w[['cohort_week','first_channel','ltv']],
             on=['cohort_week','first_channel'])
      .assign(roi=lambda d: (d['ltv'] - d['cac'])/d['cac']*100)
)

for df, title, y in [(cac_w,'Недельный CAC по каналам','cac'),
                     (rev_w,'Недельный LTV по каналам','ltv'),
                     (roi_w,'Недельный ROI по каналам','roi')]:
    plt.figure(figsize=(10,5))
    sns.lineplot(
        data=df,
        x=df['cohort_week'].astype(str),
        y=y,
        hue='first_channel',
        marker='o'
    )
    if 'ROI' in title: plt.axhline(0,color='gray',linestyle='--')
    plt.title(title)
    plt.xlabel('Когорта (неделя)')
    plt.ylabel(title.split()[-1])
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# %% [markdown]
# По проделанной нами работе видно, что САС стал сильно расти у канала TipTop, и немного у канала FaceBoom. На остальных канал затраты на привлечени либо остались на прежнем уровне, либо даже немного падают (RocketSuperAds). Что касается прибыли, то так же видно, что у канала TipTop данный показатель растет. У канала RocketSuperAds данный показатель средний, но сильно подскакивает в октябре. У остальных же каналов он в среднем, на одном уровне. ROI же неплохо показывает, что в целом, окупились только два канала, это RocketSuperAds и MediaTornado(хоть данный канал и не окупился в предполагаемые нами сроки). Из всего этого можно сделать вывод, чтосильные вливания в привлечение пользователей по каналу TipTop не достигли положительного результата, и приносят убытки.

# %% [markdown]
# Анализ периода окупаемости маркетинговых вложений

# %%
# 1) Собираем df_orders с ключевыми полями
df_orders = (
    orders_df
    [['user_id','event_dt','revenue']]
    .merge(
        profiles[['user_id','first_dt','first_channel']],
        on='user_id',
        how='inner'
    )
    # первая неделя (когорта) и неделя события
    .assign(
        first_week = lambda d: d['first_dt'].dt.to_period('W').dt.to_timestamp(),
        order_week = lambda d: d['event_dt'].dt.to_period('W').dt.to_timestamp()
    )
    .assign(N_week = lambda d: ((d['order_week'] - d['first_week'])
                                .dt.days // 7 + 1))
    .query('N_week <= 10')
)
display(df_orders['N_week'].unique())

# %%
# 2) Считаем размер когорты: новых пользователей в каждой first_week, канал
cohort_size = (
    profiles
    .assign(first_week = lambda d: d['first_dt'].dt.to_period('W').dt.to_timestamp())
    .groupby(['first_channel','first_week'], as_index=False)
    .user_id.nunique()
    .rename(columns={'user_id':'cohort_users'})
)

# %%
# 3) Revenue и кумулятивная выручка по N_week
cohort_revenue = (
    df_orders
    .groupby(['first_channel','first_week','N_week'], as_index=False)
    .revenue.sum()
    .rename(columns={'revenue':'week_revenue'})
    .sort_values(['first_channel','first_week','N_week'])
)
cohort_revenue['cum_revenue'] = (
    cohort_revenue
    .groupby(['first_channel','first_week'])['week_revenue']
    .cumsum()
)

# %%
# 4) Собираем LTV = cum_revenue / cohort_users
df_cohort = (
    cohort_revenue
    .merge(cohort_size, on=['first_channel','first_week'], how='left')
    .assign(ltv = lambda d: d['cum_revenue'] / d['cohort_users'])
)

# %%
# 5) Готовим weekly cost. CAC = week_costs / cohort_users
costs_min = (
    costs_df[['channel','dt','costs']]
    .rename(columns={'channel':'first_channel','dt':'date'})
    .assign(first_week=lambda d: d['date'].dt.to_period('W').dt.to_timestamp())
)
costs_week = (
    costs_min
    .groupby(['first_channel','first_week'], as_index=False)
    .costs.sum()
    .rename(columns={'costs':'week_costs'})
)
df_cohort = (
    df_cohort
    .merge(costs_week, on=['first_channel','first_week'], how='left')
    .assign(cac = lambda d: d['week_costs'] / d['cohort_users'])
)

# %%
# 6) Считаем ROI
df_cohort['roi'] = (df_cohort['ltv'] - df_cohort['cac']) / df_cohort['cac']

# %%
# 7) Находим «плохие» каналы: ROI<0 на N_week=5 ( так как мы использовали код: 
# ".assign(N_week = lambda d: ((d['order_week'] - d['first_week'])", который отсчитывает нам не с 0, а с 1,
# то и берем мы именно с N_week=5(т.е. именно если на 4 недели не было оккупаемости, то и берем с 5))
bad_channels = df_cohort.query('N_week == 5 and roi < 0')['first_channel'].unique()

# %%
# 8) Данные для теплокарты: индекс = first_week, колонки = N_week, значения = roi
heatmap_data = (
    df_cohort[df_cohort['first_channel'].isin(bad_channels)]
    .pivot_table(
        index='first_week',
        columns='N_week',
        values='roi',
        aggfunc='mean'
    )
    .sort_index()
    .reindex(columns=range(1, 9), fill_value=np.nan)
)

# %%
# 9) Убираем время из индекса
heatmap_data.index = heatmap_data.index.strftime('%Y-%m-%d')

# %%
# 10) Визуализируем
plt.figure(figsize=(12, 8))
sns.heatmap(
    heatmap_data,
    annot=True,
    fmt='.2f',
    cmap='RdBu_r',
    center=0,
    linewidths=.5,
    cbar_kws={'label':'ROI'}
)
plt.title('ROI по N_week (1–8) для «плохих» каналов')
plt.xlabel('Неделя жизни (N_week)')
plt.ylabel('Когорта (first_week)')
plt.xticks(rotation=0)
plt.yticks(rotation=45)
plt.tight_layout()
plt.show()

# %%
# Список каналов, у которых ROI<0 на N_week=5 ( так как мы использовали код: 
# ".assign(N_week = lambda d: ((d['order_week'] - d['first_week'])", который отсчитывает нам не с 0, а с 1,
# то и берем мы именно с N_week=5(т.е. именно если на 4 недели не было оккупаемости, то выводим с 5))
                                
bad_channels = df_cohort.query('N_week == 5 and roi < 0')['first_channel'].unique()

for ch in bad_channels:
    # Фильтруем данные по каналу
    sub = (
        df_cohort[df_cohort['first_channel'] == ch]
        .pivot_table(
            index='first_week',
            columns='N_week',
            values='roi',
            aggfunc='mean'
        )
        .sort_index()
    )

    # Заменяем нули (если они есть) на NaN, чтобы не окрашивать их
    sub = sub.replace(0, np.nan)
    all_weeks = sorted(df_cohort['N_week'].unique())
    sub = sub.reindex(columns=all_weeks)
    
    # 2) Убираем время из индекса
    sub.index = sub.index.strftime('%Y-%m-%d')

    # Визуализируем
    plt.figure(figsize=(12, 8))
    sns.heatmap(
        sub,
        annot=True,
        fmt='.2f',
        cmap='RdBu_r',
        center=0,
        linewidths=.5,
        cbar_kws={'label':'ROI'}
    )
    plt.title(f'ROI по N_week (1–10) для канала «{ch}»')
    plt.xlabel('Неделя жизни (N_week)')
    plt.ylabel('Когорта (first_week)')
    plt.xticks(rotation=0)
    plt.yticks(rotation=45)
    plt.tight_layout()
    plt.show()

# %% [markdown]
# По проделанной работе становится видно, что прибыльным на 4 неделе остается только один канал, и это RocketSuperAds. Остальные каналы не выходят на окупаемость в запланированные нами сроки. Тем не менее, канал TipTop становится окупаемым к 5 и более окупаемым к 6 неделе. Канал FaceBoom показывает значения ROI, остающиеся ниже нуля на протяжении всех 10 недель жизни привлечённых когорт. Это говорит о том, что затраты на привлечение пользователей пока не окупаются за указанный период, и канал работает в убыточном режиме. Канал MediaTornado показывает что кагорты стартуют с отрицательной базовой точкой (например, значения от –0.59 до –0.01). Это указывает на то, что на первых этапах покупки пользователей канал несёт расходы, которые не восполняются доходом. Однако уже в первые недели после привлечения наблюдается заметный рост ROI. Многие когорты постепенно переходят от отрицательных значений к положительным, что демонстрирует, что пользователи начинают приносить доход со временем. Данный канал на 8 неделю выходит по всем когортам на окупаемость. У канала TipTop видно отрицательный ROI у большинства когорт в первые недели. Это свидетельствует о высокой начальной стоимости привлечения пользователей, когда затраты перевешивают доходы. Но видна тенденция, когда по мере прохождения времени некоторые когортные группы начинают смещаться в сторону менее отрицательных, а то даже положительных значений. Такая динамика говорит о том, что, несмотря на изначальные инвестиционные убытки, при правильной монетизации и удержании аудитории окупаемость может начаться с задержкой. В целом, данный канал полностью выходит на окупаемость только к 7 неделе.

# %% [markdown]
# Выводы и рекомендации

# %% [markdown]
# Результаты, выводы, рекомендации:
# 
# TipTop. Этот канал он дороже, но именно он даёт стабильных, платящих и возвращающихся пользователей.
# Проблемные каналы — MediaTornado и RocketSuperAds: низкая конверсия, плохая окупаемость.
# FaceBoom — что-то среднее: много пользователей, но требуется работа с продуктом, чтобы повысить вовлечение и покупки.
# Аудитория продукта:
# 
# После запуска спортивного контента в июне интерес к продукту заметно вырос: DAU, MAU и Stickiness улучшались вплоть до ноября.
# Пользователи стали чаще возвращаться и проводить больше времени в приложении.
# Основные метрики в динамике:
# 
# Средний CAC увеличился почти вдвое за полгода: рост затрат на фоне попыток расширить охват.
# При этом LTV рос недостаточно быстро, из-за чего ROI по многим каналам ушёл в минус.
# В июле зафиксирован пик эффективности (ROI > 0), но в дальнейшем — постепенное снижение окупаемости.
# Вывод по эффективности каналов:
# 
# TipTop — самый качественный трафик: лучшее удержание, высокая конверсия и положительный ROI на горизонте до 6 недель.
# FaceBoom — широкий охват, но нестабильный результат. Нужна работа над удержанием.
# RocketSuperAds и MediaTornado не окупаются в установленные сроки. Последний особенно убыточен на длительном горизонте.
# Рекомендации:
# 
# Сфокусироваться на TipTop как основном источнике трафика:
# масштабировать при условии сохранения текущей стоимости;
# протестировать сегменты аудитории.
# Перезапустить стратегию работы с FaceBoom:
# A/B-тестирование рекламных форматов;
# повысить вовлечение и первый платёж;
# попытаться разобраться и повысить ретеншн.
# Ограничить или приостановить инвестиции в MediaTornado и RocketSuperAds:
# стоит произвести отдельную диагностику поведения привлечённых пользователей;
# возможно, текущий спортивный контент не соответствуют ожиданиям аудитории.


