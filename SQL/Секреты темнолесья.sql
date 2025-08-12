/* Проект «Секреты Тёмнолесья»
 * Цель проекта: изучить влияние характеристик игроков и их игровых персонажей 
 * на покупку внутриигровой валюты «райские лепестки», а также оценить 
 * активность игроков при совершении внутриигровых покупок
 * 
 * Автор: Ромашин Антон Игоревич
 * Дата: 10.11.2024
*/

-- Часть 1. Исследовательский анализ данных
-- Задача 1. Исследование доли платящих игроков


-- 1.1. Доля платящих пользователей по всем данным:

-- Вычисляем долю платящих игроков от общего кол-ва пользователей
SELECT 
    COUNT(id) AS total_players, -- считаем кол-во игроков
    --COUNT(CASE WHEN payer = '1' THEN 1 END) AS paying_players, -- считаем платящих игроков 
    SUM (payer) AS paying_players, -- считаем платящих игроков -- так действительно проще (что-то я усложнил =))
    Round(SUM (payer) / COUNT(id)::NUMERIC, 4) AS share_of_paying_players --считаем долю платящих игроков
FROM 
    fantasy.users;

-- 1.2. Доля платящих пользователей в разрезе расы персонажа:


SELECT 
	r.race, -- выводим названия рас
	SUM (u.payer) AS payer_gamer, --считаем платящих игроков по расе (используем просто SUM по рекомендации Ревьювера (да, так проще =)))
	--SUM(CASE WHEN u.payer=1 THEN 1 ELSE 0 END) AS payer_gamer, --считаем платящих игроков по расе
	COUNT(id) AS total_players, -- общее кол-во зарегистрированных игроков по каждой расе
	Round(AVG (u.payer)::NUMERIC,4) AS share_of_paying_players_1 -- доля платящих игроков от общего количества пользователей, зарегистрированных в игре в разрезе каждой расы персонажа (используем AVG по рекомендации ревьювера)
	--Round(SUM(CASE WHEN u.payer=1 THEN 1 ELSE 0 END)  / COUNT(u.id)::NUMERIC, 4) AS share_of_paying_players -- доля платящих игроков от общего количества пользователей, зарегистрированных в игре в разрезе каждой расы персонажа
FROM fantasy.users u
LEFT JOIN fantasy.race r ON u.race_id = r.race_id 
GROUP BY r.race
--ORDER BY share_of_paying_players_1  -- сортируем по доле платящих игроков
ORDER BY total_players DESC 

-- Задача 2. Исследование внутриигровых покупок
-- 2.1. Статистические показатели по полю amount:
SELECT 
	COUNT (amount)::NUMERIC AS count_amount, -- общее кол-во покупок
	SUM (amount)::NUMERIC AS sum_amount, -- сумма стоимости всех покупок
	MIN (amount)::NUMERIC AS min_amount, -- минимальная стоимость покупки
	MAX (amount)::NUMERIC AS max_amount, -- максимальная стоимость покупки
	AVG (amount)::NUMERIC(10, 2) AS avg_amount, -- средняя стоимость покупки
	percentile_disc (0.5) WITHIN GROUP (ORDER BY amount)::NUMERIC(10, 2) AS median_amount, -- медиана стоимости покупки
	STDDEV (amount)::NUMERIC(10, 2) AS st_deviation_amount -- стандартное отклонение стоимости покупки
FROM fantasy.events
WHERE amount <> 0; -- исключаем нулевые покупки (по рекомендации Ревьювера это помогает лучше понять, какова реально была минимальная стоимость внутриигровой покупки)


-- 2.2: Аномальные нулевые покупки:
SELECT 	
	COUNT (amount)::NUMERIC AS count_amount, -- общее кол-во покупок
	COUNT(transaction_id) FILTER (WHERE amount = 0) AS not_paying_players,  -- кол-во покупок  за нулевую стоимость. (Ревьювер посоветовал использовать данную функцию, так как она помогает проще читать код (Отличная функция FILTER, надо почиать про неё побольше))
	--COUNT (CASE WHEN amount = 0 THEN 1 END) AS not_paying_players, -- кол-во покупок  за нулевую стоимость 
	ROUND(COUNT (CASE WHEN amount = 0 THEN 1 END) / COUNT (amount)::NUMERIC,4) AS share_of_not_paying_players -- доля покупок за 0 стоимость 
	FROM fantasy.events

-- 2.3: Сравнительный анализ активности платящих и неплатящих игроков: 
/* -- убрал в коментарии чтобы попробовать  подход который посоветовал Ревьювер
    WITH t1 AS (
	SELECT 
		u.payer,
        e.id AS payer_id,
		COUNT(e.transaction_id) AS count_trans, -- считаем кол-во покупок
        SUM(e.amount) AS total_amount -- считаем сумму всех покупок
	FROM fantasy.users AS u
	NATURAL JOIN fantasy.events AS e-- ON u.id = e.id
	WHERE e.amount <> 0 -- фильтруем, чтобы покупки не были равны 0
	GROUP BY  u.payer, e.id -- группируем по id игроков
	)
	SELECT 
	CASE WHEN t1.payer= 0 THEN 'не платящий'
            WHEN t1.payer=1 THEN 'платящий'
            END AS Meaning,
            COUNT( t1.payer_id) AS player_count, -- общее кол-во игроков по категории платящий/не платящий (убрал DISTINCT в соответствии с рекомндацией Ревьювера)
	ROUND (SUM(t1.count_trans)/COUNT( t1.payer_id)::NUMERIC, 4) AS avg_count_transon_1_player, -- среднее количество покупок на 1 игрока
	ROUND (SUM(t1.total_amount)::NUMERIC/COUNT( t1.payer_id)::NUMERIC, 4) AS avg_total_amount -- средняя суммарная стоимость покупок на 1 игрока
	FROM t1
	GROUP BY t1.payer;
*/	

SELECT 
race,
CASE WHEN payer= 0 THEN 'не платящий'
            WHEN payer=1 THEN 'платящий'
            END AS Meaning,
COUNT(DISTINCT e.id) AS player_count, -- общее кол-во игроков по категории платящий/не платящий
round (COUNT(transaction_id)::NUMERIC / COUNT(DISTINCT e.id),4) AS avg_count_transon_1_player, -- среднее количество покупок на 1 игрока
ROUND (SUM(e.amount)::NUMERIC/COUNT(DISTINCT u.id)::NUMERIC, 4) AS avg_total_amount -- средняя суммарная стоимость покупок на 1 игрока
FROM fantasy.users AS u
	NATURAL JOIN fantasy.events AS e
	NATURAL JOIN fantasy.race AS r
WHERE e.amount <> 0 -- фильтруем, чтобы покупки не были равны 0
GROUP BY race, payer


	
-- 2.4: Популярные эпические предметы:
WITH t1 AS (
	SELECT 
		count (DISTINCT e.id) AS id_1, -- считаем кол-во уникальных игроков, совершивших покупку хоть одного эпического предмета
		--SUM (count (DISTINCT id)) OVER () AS sum_count_id, -- считаем общее кол-во уникальныхз игроков, совершивших покупку эпик предмета
		game_items,
		SUM(amount)::NUMERIC AS sum_amount, -- стоимость покупок каждого эпического предмета
		SUM(SUM(amount)::NUMERIC) OVER () AS sum_all_amount, -- Сумма всех продаж (не очень понимаю, почему у меня здесь общая сумма получилась больше, чем отдельно в проверке моей по сумме всех продаж, с учетом нулевых продаж)
		count (amount) AS count_amount, -- 
		SUM (count(e.transaction_id)::NUMERIC) over() AS sum_count_trans, --сумма количества транзакций,
		count(e.transaction_id) AS count_transaction	-- абсолютное значение внутриигровых продаж без учета нулевых продаж
	FROM fantasy.items AS i 
	NATURAL JOIN fantasy.events AS e 
	WHERE e.amount <> 0 -- фильтруем, чтобы покупки не были равны 0
	GROUP BY game_items
	ORDER BY sum_amount desc),
	t2 AS (
	SELECT 
		count(DISTINCT id) AS id		
	FROM fantasy.events AS e
	WHERE e.amount <> 0 -- фильтруем, чтобы покупки не были равны 0
	)
SELECT 
	game_items,
	t1.sum_amount,
	t1.count_transaction,
	round (count_transaction/sum_count_trans, 4) AS  relative_value, -- относительная доля продаж без учета нулевых продаж 
	round(id_1::NUMERIC /id,4) AS relative_players -- доля игроков, которые хотя бы раз покупали предмет
FROM t1
NATURAL JOIN t2 
ORDER BY count_transaction DESC

/* ЧИСТО ДЛЯ ПРОВЕРКИ СЕБЯ
 * 
* -- проверяю общую сумму продаж
SELECT 	
	SUM(amount) AS s_a
FROM fantasy.events
*
*-- проверяю общее кол-во эпических предметов, с учетом нулевых продаж	
SELECT 
	count(game_items)
FROM fantasy.items
*
*
*--проверяю кол-во уникальных пользователей
SELECT 
	count (DISTINCT id)
FROM fantasy.events
*/

	

-- Часть 2. Решение ad hoc-задач
-- Задача 1. Зависимость активности игроков от расы персонажа:
	
	WITH t1 AS ( -- считаем общее кол-во зареганых игроков в разрезе рас 
				SELECT 
					r.race AS race,
       				COUNT(DISTINCT id) AS total_players  -- общее кол-во зарегистрированных игроков (по каждой расе)
    			FROM fantasy.users AS u
    			LEFT JOIN fantasy.race r ON u.race_id = r.race_id 
    			GROUP BY r.race -- разбиваем на рассы
    			ORDER BY r.race
),
	t2 AS ( --производим вычисления по платящим игрокам, считаем их кол-во, долю
			SELECT 
				r.race AS race,
				--count (DISTINCT e.id ) FILTER (WHERE u.payer =1) AS payer_gamer_1, -- выводил для себя чтобы визуально увидеть и провериь, что я вывел именно платящих(пока решил оставить для себя). По факту эту строчку можно удалить!
       			COUNT(DISTINCT e.id) AS count_id_trans, -- кол-во игороков которые сделали покупку внутри игры
       			SUM(CASE WHEN u.payer=1 THEN 1 END) AS payer_gamer, -- считаем платящих
       			round(COUNT(DISTINCT e.id)/COUNT(DISTINCT u.id)::NUMERIC,2) AS share_of_total_players, -- доля игроков, которые совершают внутриигровые покупки от общего кол-ва игроков
       			count(transaction_id) AS count_trans, -- считаем кол-во транзакций
       			round (count (DISTINCT e.id ) FILTER (WHERE u.payer =1)/COUNT(DISTINCT e.id)::NUMERIC,2) AS share_of_paying_players, -- доля платящих игроков, среди тех, кто вообще совершал покупки
       			round(count(transaction_id)/COUNT(DISTINCT e.id)::NUMERIC,2) AS avg_pur_per_player -- считаем среднее кол-во покупок на одного игрока(которые совершали покупки)
    		FROM fantasy.users AS u
    		LEFT JOIN fantasy.race r ON u.race_id = r.race_id 
    		LEFT JOIN fantasy.events e ON u.id = e.id
    		GROUP BY r.race
    		ORDER BY r.race
    	),
	t3 AS ( -- производим вычисления со стоимостями покупок 
				SELECT 
					r.race AS race, 
					count (DISTINCT u.id) AS count_id, -- кол-во покупателей
					count(e.transaction_id) AS count_trans, -- кол-во совершенных покупок в разрезе рас
					COUNT(CASE WHEN u.payer = '1' THEN 1 END) AS paying_players, -- считаем платящих игроков 
					round(AVG(e.amount)::NUMERIC,2)AS avg_order_amount, -- средняя стоимость покупок на одного игрока
					sum(e.amount) AS sum_amount,
					round(sum(e.amount)::NUMERIC/COUNT(DISTINCT e.id)::NUMERIC,2) AS avg_sum_amount -- средняя стоимость всех покупок на одного игрока	(которые сделали хоть одну покупку(не учитываем 0 стоимость))				
				FROM fantasy.users AS u
    			LEFT JOIN fantasy.race r ON u.race_id = r.race_id 
    			LEFT JOIN fantasy.events e ON u.id = e.id
    			WHERE amount <>0
				GROUP BY r.race
				ORDER BY r.race		
		)
		-- выводим всё, что надо
	SELECT 
		t1.race, -- названия рас
		t1.total_players, --общее количество зарегистрированных игроков 
		t2.count_id_trans, -- количество игроков, которые совершают внутриигровые покупки
		t2.share_of_total_players, -- доля игроков, которые совершают внутриигровые покупки от общего кол-ва игроков 
		t2.share_of_paying_players, --доля платящих игроков от количества игроков, которые совершили покупки    
		t2.avg_pur_per_player, --среднее количество покупок на одного игрока
		t3.avg_order_amount, --средняя стоимость одной покупки на одного игрока
		t3.avg_sum_amount --средняя суммарная стоимость всех покупок на одного игрока
		FROM t1
		JOIN t2 ON t1.race=t2.race
		JOIN t3 ON t1.race=t3.race
