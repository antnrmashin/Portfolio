
/* Проект первого модуля: анализ данных для агентства недвижимости
 * Часть 2. Решаем ad hoc задачи
 * 
 * Автор: Ромашин Антон
 * Дата: 27.11.2024
*/

-- Определим аномальные значения (выбросы) по значению перцентилей:
WITH limits AS (
    SELECT  
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY total_area) AS total_area_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY rooms) AS rooms_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY balcony) AS balcony_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_h,
        PERCENTILE_DISC(0.01) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_l
    FROM real_estate.flats     
),
-- Найдем id объявлений, которые не содержат выбросы:
filtered_id AS(
    SELECT id
    FROM real_estate.flats  
    WHERE 
        total_area < (SELECT total_area_limit FROM limits) 
        AND rooms < (SELECT rooms_limit FROM limits) 
        AND balcony < (SELECT balcony_limit FROM limits) 
        AND ceiling_height < (SELECT ceiling_height_limit_h FROM limits) 
        AND ceiling_height > (SELECT ceiling_height_limit_l FROM limits)
    )
-- Выведем объявления без выбросов:
SELECT *
FROM real_estate.flats
WHERE id IN (SELECT * FROM filtered_id);


-- Задача 1: Время активности объявлений
-- Результат запроса должен ответить на такие вопросы:
-- 1. Какие сегменты рынка недвижимости Санкт-Петербурга и городов Ленинградской области 
--    имеют наиболее короткие или длинные сроки активности объявлений?
-- 2. Какие характеристики недвижимости, включая площадь недвижимости, среднюю стоимость квадратного метра, 
--    количество комнат и балконов и другие параметры, влияют на время активности объявлений? 
--    Как эти зависимости варьируют между регионами?
-- 3. Есть ли различия между недвижимостью Санкт-Петербурга и Ленинградской области по полученным результатам?

-- Определим аномальные значения (выбросы) по значению перцентилей:
WITH limits AS (
    SELECT  
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY total_area) AS total_area_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY rooms) AS rooms_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY balcony) AS balcony_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_h,
        PERCENTILE_DISC(0.01) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_l
    FROM real_estate.flats     
),
-- Найдем id объявлений, которые не содержат выбросы:
filtered_id AS(
    SELECT id
    FROM real_estate.flats  
    WHERE 
        total_area < (SELECT total_area_limit FROM limits)
        AND (rooms < (SELECT rooms_limit FROM limits) OR rooms IS NULL)
        AND (balcony < (SELECT balcony_limit FROM limits) OR balcony IS NULL)
        AND ((ceiling_height < (SELECT ceiling_height_limit_h FROM limits)
        AND ceiling_height > (SELECT ceiling_height_limit_l FROM limits)) OR ceiling_height IS NULL)
    ),
-- категоризируем на населенные пункты и время активности    
t1 AS(
SELECT
*,
CASE
WHEN city = 'Санкт-Петербург' THEN 'Санкт-Петербург'
ELSE 'Города ЛенОбл'
END AS city_location, -- катеризируем по принадлежности к населенным пунктам
CASE 
    WHEN days_exposition BETWEEN 1 AND 31 THEN 'меньше месяца'
    WHEN days_exposition BETWEEN 32 AND 90 THEN 'меньше квартала'
    WHEN days_exposition BETWEEN 91 AND 180 THEN'меньше полугода'
    WHEN days_exposition IS NULL THEN 'незакрытые объявления'
    ELSE 'больше, чем полгода'
END AS group_of_day, -- категоризируем по времени активности
round(last_price::numeric/total_area::NUMERIC,2) AS cost_for_1_sq_m -- Средняя стоимость за 1 кв.м
FROM real_estate.flats AS f
INNER JOIN real_estate.city USING(city_id)
INNER JOIN real_estate.advertisement USING(id)
INNER JOIN real_estate.TYPE USING (type_id)
WHERE id IN (
SELECT id
FROM filtered_id) AND TYPE='город' -- фильтруем по Типу "ГОРОД" и исключаем аномальные выбросы
)
--Выводим необходимую информацию, создавая сводную таблицу
SELECT
city_location AS "Локация",
group_of_day AS "Время активности",
round(avg(cost_for_1_sq_m::NUMERIC),2)AS "Средняя стоимость за 1кв.м", -- средняя стоимость за 1кв.м по нас.пунктам и времени активности (чтобы не группировать, т.к. avg_cost_for_1_sq_m=cost_for_1_sq_m)
count(id) AS "Кол-во квартир(объявлений)", -- кол-во уникальных идентификаторов квартир
SUM (count(id)) OVER (PARTITION BY city_location) AS "Кол-во объявлений по Региону",
round(count(id)::NUMERIC/SUM (count(id)) OVER (PARTITION BY city_location),2) AS "Доля продаж", --доля продаж по региону и по времени активности
round(avg (total_area::NUMERIC),2) AS "Средняя площадь квартир", -- средняя площадь кв в объявлениях
PERCENTILE_DISC (0.5) WITHIN GROUP (ORDER BY rooms) AS "Медиана кол-ва комнат", -- медиана кол-ва комнат
PERCENTILE_DISC (0.5) WITHIN GROUP (ORDER BY balcony) AS "Медиана кол-ва балконов", -- медиана кол-ва балконов
PERCENTILE_DISC (0.5) WITHIN GROUP (ORDER BY floor) AS "Медиана этажности" -- медиана этажности квартир
--PERCENTILE_DISC (0.5) WITHIN GROUP (ORDER BY floors_total) AS "Медиана этажности дома" -- медиана этажности дома, в котором находится квартира
FROM t1
GROUP BY city_location, group_of_day
ORDER BY city_location, group_of_day ASC 


-- Задача 2: Сезонность объявлений
-- Результат запроса должен ответить на такие вопросы:
-- 1. В какие месяцы наблюдается наибольшая активность в публикации объявлений о продаже недвижимости? 
--    А в какие — по снятию? Это показывает динамику активности покупателей.
-- 2. Совпадают ли периоды активной публикации объявлений и периоды, 
--    когда происходит повышенная продажа недвижимости (по месяцам снятия объявлений)?
-- 3. Как сезонные колебания влияют на среднюю стоимость квадратного метра и среднюю площадь квартир? 
--    Что можно сказать о зависимости этих параметров от месяца?

/*--Задача 2.1 Публикация объявлений
WITH limits AS (
    SELECT  
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY total_area) AS total_area_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY rooms) AS rooms_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY balcony) AS balcony_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_h,
        PERCENTILE_DISC(0.01) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_l
    FROM real_estate.flats     
),
-- Найдем id объявлений, которые не содержат выбросы:
filtered_id AS(
    SELECT id
    FROM real_estate.flats  
    WHERE 
        total_area < (SELECT total_area_limit FROM limits)
        AND (rooms < (SELECT rooms_limit FROM limits) OR rooms IS NULL)
        AND (balcony < (SELECT balcony_limit FROM limits) OR balcony IS NULL)
        AND ((ceiling_height < (SELECT ceiling_height_limit_h FROM limits)
        AND ceiling_height > (SELECT ceiling_height_limit_l FROM limits)) OR ceiling_height IS NULL)
    )
SELECT
	--date_trunc('month', first_day_exposition) AS "Дата подачи объявлений",
	--COUNT (date_trunc('month', first_day_exposition)) AS "Кол-во объявлений",
	ROW_NUMBER () OVER (ORDER BY COUNT (date_trunc('month', first_day_exposition)) DESC )AS "Место по кол-ву подачи объявлений",
	EXTRACT(MONTH FROM first_day_exposition::DATE) AS "Месяц подачи объявлений",
	Count (EXTRACT(MONTH FROM first_day_exposition::DATE)) AS "Количество объявлений",
	round(avg (total_area::NUMERIC),2) AS "Средняя площадь квартир", -- средняя площадь кв в объявлениях
	round(avg(last_price)::NUMERIC/avg(total_area)::numeric,2) AS "Средняя стоимость за 1 кв.м" -- Средняя стоимость за 1 кв.м
FROM real_estate.advertisement a 
INNER JOIN real_estate.flats f USING (ID)
INNER JOIN real_estate.TYPE USING (type_id)
WHERE id IN (
	SELECT id
	FROM filtered_id) --AND days_exposition IS NOT NULL 
	AND TYPE='город' -- фильтруем выбросы и те объявления, которые не сняты с продаж, и выбираем только Города
GROUP BY "Месяц подачи объявлений" --,"Дата подачи объявлений"
ORDER BY "Средняя площадь квартир" DESC --,"Дата подачи объявлений" --"Место по кол-ву подачи объявлений";

--Задача 2.1 Снятие объявлений

WITH limits AS (
    SELECT  
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY total_area) AS total_area_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY rooms) AS rooms_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY balcony) AS balcony_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_h,
        PERCENTILE_DISC(0.01) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_l
    FROM real_estate.flats     
),
-- Найдем id объявлений, которые не содержат выбросы:
filtered_id AS(
    SELECT id
    FROM real_estate.flats  
    WHERE 
        total_area < (SELECT total_area_limit FROM limits)
        AND (rooms < (SELECT rooms_limit FROM limits) OR rooms IS NULL)
        AND (balcony < (SELECT balcony_limit FROM limits) OR balcony IS NULL)
        AND ((ceiling_height < (SELECT ceiling_height_limit_h FROM limits)
        AND ceiling_height > (SELECT ceiling_height_limit_l FROM limits)) OR ceiling_height IS NULL)
    )
SELECT 
	--date_trunc('month', first_day_exposition+days_exposition::integer) AS "Дата продаж",
	ROW_NUMBER () OVER (ORDER BY COUNT (date_trunc('month', first_day_exposition+days_exposition::integer)) DESC )AS "Место по кол-ву продаж",
	EXTRACT(MONTH FROM first_day_exposition::DATE+days_exposition::integer) AS "Месяц продажи",
	count (EXTRACT(MONTH FROM first_day_exposition::DATE+days_exposition::integer)) AS "Кол-во снятых объявлений",
	round(avg (total_area::NUMERIC),2) AS "Средняя площадь квартир",
	round(avg(last_price)::NUMERIC/avg(total_area)::numeric,2) AS "Средняя стоимость за 1 кв.м"
FROM real_estate.advertisement a
INNER JOIN real_estate.flats f USING (ID)
INNER JOIN real_estate.TYPE USING (type_id)
WHERE id IN (
	SELECT id
	FROM filtered_id) AND days_exposition IS NOT NULL 
	AND TYPE='город' -- фильтруем выбросы и те объявления, которые не сняты с продаж, и выбираем только Города
GROUP BY "Месяц продажи"--,group_of_day
ORDER BY "Средняя площадь квартир" DESC --,"Дата продаж" --"Место по кол-ву продаж";
*/





--Задача 2
WITH limits AS (
    SELECT  
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY total_area) AS total_area_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY rooms) AS rooms_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY balcony) AS balcony_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_h,
        PERCENTILE_DISC(0.01) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_l
    FROM real_estate.flats     
),
-- Найдем id объявлений, которые не содержат выбросы:
filtered_id AS(
    SELECT id
    FROM real_estate.flats  
    WHERE 
        total_area < (SELECT total_area_limit FROM limits)
        AND (rooms < (SELECT rooms_limit FROM limits) OR rooms IS NULL)
        AND (balcony < (SELECT balcony_limit FROM limits) OR balcony IS NULL)
        AND ((ceiling_height < (SELECT ceiling_height_limit_h FROM limits)
        AND ceiling_height > (SELECT ceiling_height_limit_l FROM limits)) OR ceiling_height IS NULL)
    ),
    t1 AS (
SELECT
	--date_trunc('month', first_day_exposition) AS "Дата подачи объявлений",
	--COUNT (date_trunc('month', first_day_exposition)) AS "Кол-во объявлений",
	ROW_NUMBER () OVER (ORDER BY COUNT (date_trunc('month', first_day_exposition)) DESC )AS "Место по кол-ву подачи объявлений",
	EXTRACT(MONTH FROM first_day_exposition::DATE) AS "Месяц подачи объявлений",
	Count (EXTRACT(MONTH FROM first_day_exposition::DATE)) AS "Количество объявлений",
	round(avg (total_area::NUMERIC),2) AS "Средняя площадь квартир", -- средняя площадь кв в объявлениях
	round(avg(last_price)::NUMERIC/avg(total_area)::numeric,2) AS "Средняя стоимость за 1 кв.м" -- Средняя стоимость за 1 кв.м
FROM real_estate.advertisement a 
INNER JOIN real_estate.flats f USING (ID)
INNER JOIN real_estate.TYPE USING (type_id)
WHERE id IN (
	SELECT id
	FROM filtered_id) AND days_exposition IS NOT NULL 
	AND TYPE='город' -- фильтруем выбросы и те объявления, которые не сняты с продаж, и выбираем только Города
GROUP BY "Месяц подачи объявлений" --,"Дата подачи объявлений"
ORDER BY "Средняя площадь квартир" DESC --,"Дата подачи объявлений" --"Место по кол-ву подачи объявлений";
),
	t2 AS (
	SELECT 
	--date_trunc('month', first_day_exposition+days_exposition::integer) AS "Дата продаж",
	ROW_NUMBER () OVER (ORDER BY COUNT (date_trunc('month', first_day_exposition+days_exposition::integer)) DESC )AS "Место по кол-ву продаж",
	EXTRACT(MONTH FROM first_day_exposition::DATE+days_exposition::integer) AS "Месяц продажи",
	count (EXTRACT(MONTH FROM first_day_exposition::DATE+days_exposition::integer)) AS "Кол-во снятых объявлений",
	round(avg (total_area::NUMERIC),2) AS "Средняя площадь квартир прод.",
	round(avg(last_price)::NUMERIC/avg(total_area)::numeric,2) AS "Средняя стоимость за 1 кв.м прод."
FROM real_estate.advertisement a
INNER JOIN real_estate.flats f USING (ID)
INNER JOIN real_estate.TYPE USING (type_id)
WHERE id IN (
	SELECT id
	FROM filtered_id) AND days_exposition IS NOT NULL 
	AND TYPE='город' -- фильтруем выбросы и те объявления, которые не сняты с продаж, и выбираем только Города
GROUP BY "Месяц продажи"--,group_of_day
ORDER BY "Средняя площадь квартир прод." DESC --,"Дата продаж" --"Место по кол-ву продаж";
)
SELECT 
"Место по кол-ву подачи объявлений",
"Месяц подачи объявлений",
"Количество объявлений",
"Средняя площадь квартир",
"Средняя стоимость за 1 кв.м",
"Место по кол-ву продаж",
"Месяц продажи",
"Кол-во снятых объявлений",
"Средняя площадь квартир прод.",
"Средняя стоимость за 1 кв.м прод."
FROM  t1
FULL JOIN t2 ON t1."Месяц подачи объявлений"=t2."Месяц продажи"
ORDER BY "Место по кол-ву подачи объявлений"  

	
-- Задача 3: Анализ рынка недвижимости Ленобласти
-- Результат запроса должен ответить на такие вопросы:
-- 1. В каких населённые пунктах Ленинградской области наиболее активно публикуют объявления о продаже недвижимости?
-- 2. В каких населённых пунктах Ленинградской области — самая высокая доля снятых с публикации объявлений? 
--    Это может указывать на высокую долю продажи недвижимости.
-- 3. Какова средняя стоимость одного квадратного метра и средняя площадь продаваемых квартир в различных населённых пунктах? 
--    Есть ли вариация значений по этим метрикам?
-- 4. Среди выделенных населённых пунктов какие пункты выделяются по продолжительности публикации объявлений? 
--    То есть где недвижимость продаётся быстрее, а где — медленнее.


WITH limits AS (
    SELECT  
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY total_area) AS total_area_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY rooms) AS rooms_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY balcony) AS balcony_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_h,
        PERCENTILE_DISC(0.01) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_l
    FROM real_estate.flats     
),
-- Найдем id объявлений, которые не содержат выбросы:
filtered_id AS(
    SELECT id
    FROM real_estate.flats  
    WHERE 
        total_area < (SELECT total_area_limit FROM limits)
        AND (rooms < (SELECT rooms_limit FROM limits) OR rooms IS NULL)
        AND (balcony < (SELECT balcony_limit FROM limits) OR balcony IS NULL)
        AND ((ceiling_height < (SELECT ceiling_height_limit_h FROM limits)
        AND ceiling_height > (SELECT ceiling_height_limit_l FROM limits)) OR ceiling_height IS NULL)
    ),
t1 AS (
SELECT
	TYPE AS "Тип нас.пункта",
	city AS "Имя нас.пункта",
	count(a.id) AS "Кол-во объявлений",
	round(avg (total_area::NUMERIC),2) AS "Средняя площадь квартир",
	round(avg(last_price)::NUMERIC/avg(total_area)::numeric,2) AS "Средняя стоимость за 1 кв.м",
	--SUM (count(a.id)) OVER ( ) AS "Общее кол-во объявлений", 
	round(avg(days_exposition)::NUMERIC,2) AS "Среднее время продажи кв в днях", -- среднее время нахождения объявлений в продаже
	COUNT(days_exposition) AS "Кол-во проданных кв.", -- Кол-во проданных квартир(считаются квартиры, где длительность нахождения объявления на сайте (в днях) не равно нулю, т.е. только проданные квартиры)
	SUM (COUNT(days_exposition)) OVER (PARTITION BY TYPE, city) AS "Общее кол-во проданных кв"
		FROM real_estate.flats AS f
INNER JOIN real_estate.city USING(city_id)
INNER JOIN real_estate.TYPE USING (type_id)
LEFT JOIN real_estate.advertisement a USING(id)
WHERE city <> 'Санкт-Петербург'
AND id IN (	SELECT id	FROM filtered_id) --AND days_exposition IS NOT NULL
GROUP BY city, type
ORDER BY  "Кол-во объявлений" DESC
)
SELECT 
"Тип нас.пункта",
"Имя нас.пункта",
--"Общее кол-во объявлений",
--"Общее кол-во проданных кв",
"Средняя площадь квартир",
"Средняя стоимость за 1 кв.м",
CASE 
    WHEN "Среднее время продажи кв в днях" BETWEEN 1 AND 31 THEN 'меньше месяца'
    WHEN "Среднее время продажи кв в днях" BETWEEN 32 AND 90 THEN 'меньше квартала'
    WHEN "Среднее время продажи кв в днях" BETWEEN 91 AND 180 THEN'меньше полугода'
    WHEN "Среднее время продажи кв в днях" IS NULL THEN 'незакрытые объявления'
    ELSE 'больше, чем полгода'
END AS "Время продажи",--group_of_day,
--"Среднее время продажи кв в днях",
"Кол-во объявлений",
"Кол-во проданных кв.",
round("Кол-во проданных кв."::NUMERIC/"Кол-во объявлений",2) AS "Доля проданных кв"
FROM t1
Where "Кол-во объявлений" > 50 -- Фильтрация по кол-ву объявлений ( на мой взгляд, это более показательно тем, что так мы исключаем мелкие посления)
ORDER BY "Доля проданных кв" DESC 



	
Проект первого модуля.sql
Проект первого модуля.sql. На экране.