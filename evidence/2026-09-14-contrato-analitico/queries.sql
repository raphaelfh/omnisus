-- snapshots_before
SELECT snapshot_id,
            snapshot_time::VARCHAR AS snapshot_time, changes::VARCHAR AS changes
            FROM ducklake_snapshots('lake') ORDER BY snapshot_id;

-- publications
SELECT publication_id,
            dataset, scope_json, source_sha256, parser_version, run_id, batch_id,
            published_at, rows, active, managed, source_uri
            FROM lake._omnisus_publications ORDER BY dataset, scope_json, publication_id;

-- sim_obitos.schema
DESCRIBE SELECT * FROM "lake"."sim_obitos";

-- sim_obitos.scopes
SELECT uf, ano,
                 _source_release, count(*) AS n
                FROM "lake"."sim_obitos" GROUP BY ALL ORDER BY ALL;

-- sim_obitos.total
SELECT count(*) AS n FROM "lake"."sim_obitos";

-- sim_obitos.units
SELECT substr(trim(idade),1,1) AS unit,
                min(idade) AS raw_min, max(idade) AS raw_max, count(*) AS n
                FROM "lake"."sim_obitos" GROUP BY ALL ORDER BY ALL;

-- sim_obitos.sex
SELECT sexo, count(*) AS n
                FROM "lake"."sim_obitos" GROUP BY ALL ORDER BY ALL;

-- sim_obitos.reference_bands
WITH decoded AS
                (SELECT CASE WHEN regexp_full_match(trim(idade), '[0-9]{3}')
          AND trim(idade) <> '000' THEN CASE
            WHEN substr(trim(idade),1,1) IN ('0','1','2','3') THEN 0
            WHEN substr(trim(idade),1,1) = '4' THEN try_cast(substr(idade,2) AS INTEGER)
            WHEN substr(trim(idade),1,1) = '5' THEN 100 + try_cast(substr(idade,2) AS INTEGER)
          END END AS age FROM "lake"."sim_obitos")
                SELECT CASE WHEN age IS NULL THEN 'Desconhecida'
       WHEN age < 5 THEN '0-4' WHEN age < 15 THEN '5-14'
       WHEN age < 25 THEN '15-24' WHEN age < 35 THEN '25-34'
       WHEN age < 45 THEN '35-44' WHEN age < 55 THEN '45-54'
       WHEN age < 65 THEN '55-64' WHEN age < 75 THEN '65-74'
       ELSE '75+' END AS band, count(*) AS n
                FROM decoded GROUP BY ALL ORDER BY min(age) NULLS LAST;

-- sim_obitos.dates.dtnasc
SELECT
                    count(*) AS total,
                    count(*) FILTER (WHERE "dtnasc" IS NULL OR trim("dtnasc") = '') AS missing,
                    count(*) FILTER (WHERE "dtnasc" IS NOT NULL AND trim("dtnasc") <> ''
                      AND (NOT regexp_full_match("dtnasc", '[0-9]{8}')
                      OR try_strptime("dtnasc", '%d%m%Y') IS NULL)) AS invalid,
                    count(*) FILTER (WHERE regexp_full_match("dtnasc", '[0-9]{8}')
                      AND try_strptime("dtnasc", '%d%m%Y') IS NOT NULL) AS valid
                    FROM "lake"."sim_obitos";

-- sim_obitos.dates.dtobito
SELECT
                    count(*) AS total,
                    count(*) FILTER (WHERE "dtobito" IS NULL OR trim("dtobito") = '') AS missing,
                    count(*) FILTER (WHERE "dtobito" IS NOT NULL AND trim("dtobito") <> ''
                      AND (NOT regexp_full_match("dtobito", '[0-9]{8}')
                      OR try_strptime("dtobito", '%d%m%Y') IS NULL)) AS invalid,
                    count(*) FILTER (WHERE regexp_full_match("dtobito", '[0-9]{8}')
                      AND try_strptime("dtobito", '%d%m%Y') IS NOT NULL) AS valid
                    FROM "lake"."sim_obitos";

-- sim_obitos.sentinels
SELECT
                    count(*) FILTER (WHERE idade = '000') AS code_000,
                    count(*) FILTER (WHERE idade = '400') AS code_400,
                    count(*) FILTER (WHERE idade LIKE '9%') AS code_9xx,
                    count(*) FILTER (WHERE idade LIKE '%99') AS suffix_99
                    FROM "lake"."sim_obitos";

-- sim_obitos.domain_exceptions
SELECT idade, count(*) AS n
                    FROM "lake"."sim_obitos" WHERE idade IN ('100','200','300')
                    OR (substr(idade,1,1) = '0' AND try_cast(substr(idade,2) AS INT) > 59)
                    OR (substr(idade,1,1) = '1' AND try_cast(substr(idade,2) AS INT) > 23)
                    OR (substr(idade,1,1) = '2' AND try_cast(substr(idade,2) AS INT) > 29)
                    OR (substr(idade,1,1) = '3' AND try_cast(substr(idade,2) AS INT) > 11)
                    GROUP BY ALL ORDER BY ALL;

-- sim_obitos.suffix99
SELECT idade,
                    count(*) AS n FROM "lake"."sim_obitos" WHERE idade LIKE '%99'
                    GROUP BY ALL ORDER BY ALL;

-- sih_aih_reduzida.schema
DESCRIBE SELECT * FROM "lake"."sih_aih_reduzida";

-- sih_aih_reduzida.scopes
SELECT uf, ano,
                mes, _source_release, count(*) AS n
                FROM "lake"."sih_aih_reduzida" GROUP BY ALL ORDER BY ALL;

-- sih_aih_reduzida.total
SELECT count(*) AS n FROM "lake"."sih_aih_reduzida";

-- sih_aih_reduzida.units
SELECT cod_idade AS unit,
                min(idade) AS raw_min, max(idade) AS raw_max, count(*) AS n
                FROM "lake"."sih_aih_reduzida" GROUP BY ALL ORDER BY ALL;

-- sih_aih_reduzida.sex
SELECT sexo, count(*) AS n
                FROM "lake"."sih_aih_reduzida" GROUP BY ALL ORDER BY ALL;

-- sih_aih_reduzida.reference_bands
WITH decoded AS
                (SELECT CASE WHEN try_cast(idade AS INTEGER) BETWEEN 0 AND 99 THEN CASE
        WHEN trim(cod_idade) IN ('2','3') THEN 0
        WHEN trim(cod_idade) = '4' THEN try_cast(idade AS INTEGER)
        WHEN trim(cod_idade) = '5' THEN 100 + try_cast(idade AS INTEGER)
      END END AS age FROM "lake"."sih_aih_reduzida")
                SELECT CASE WHEN age IS NULL THEN 'Desconhecida'
       WHEN age < 5 THEN '0-4' WHEN age < 15 THEN '5-14'
       WHEN age < 25 THEN '15-24' WHEN age < 35 THEN '25-34'
       WHEN age < 45 THEN '35-44' WHEN age < 55 THEN '45-54'
       WHEN age < 65 THEN '55-64' WHEN age < 75 THEN '65-74'
       ELSE '75+' END AS band, count(*) AS n
                FROM decoded GROUP BY ALL ORDER BY min(age) NULLS LAST;

-- sih_aih_reduzida.dates.nasc
SELECT
                    count(*) AS total,
                    count(*) FILTER (WHERE "nasc" IS NULL OR trim("nasc") = '') AS missing,
                    count(*) FILTER (WHERE "nasc" IS NOT NULL AND trim("nasc") <> ''
                      AND (NOT regexp_full_match("nasc", '[0-9]{8}')
                      OR try_strptime("nasc", '%Y%m%d') IS NULL)) AS invalid,
                    count(*) FILTER (WHERE regexp_full_match("nasc", '[0-9]{8}')
                      AND try_strptime("nasc", '%Y%m%d') IS NOT NULL) AS valid
                    FROM "lake"."sih_aih_reduzida";

-- sih_aih_reduzida.dates.dt_inter
SELECT
                    count(*) AS total,
                    count(*) FILTER (WHERE "dt_inter" IS NULL OR trim("dt_inter") = '') AS missing,
                    count(*) FILTER (WHERE "dt_inter" IS NOT NULL AND trim("dt_inter") <> ''
                      AND (NOT regexp_full_match("dt_inter", '[0-9]{8}')
                      OR try_strptime("dt_inter", '%Y%m%d') IS NULL)) AS invalid,
                    count(*) FILTER (WHERE regexp_full_match("dt_inter", '[0-9]{8}')
                      AND try_strptime("dt_inter", '%Y%m%d') IS NOT NULL) AS valid
                    FROM "lake"."sih_aih_reduzida";

-- sih_aih_reduzida.dates.dt_saida
SELECT
                    count(*) AS total,
                    count(*) FILTER (WHERE "dt_saida" IS NULL OR trim("dt_saida") = '') AS missing,
                    count(*) FILTER (WHERE "dt_saida" IS NOT NULL AND trim("dt_saida") <> ''
                      AND (NOT regexp_full_match("dt_saida", '[0-9]{8}')
                      OR try_strptime("dt_saida", '%Y%m%d') IS NULL)) AS invalid,
                    count(*) FILTER (WHERE regexp_full_match("dt_saida", '[0-9]{8}')
                      AND try_strptime("dt_saida", '%Y%m%d') IS NOT NULL) AS valid
                    FROM "lake"."sih_aih_reduzida";

-- sih_aih_reduzida.dates.gestor_dt
SELECT
                    count(*) AS total,
                    count(*) FILTER (WHERE "gestor_dt" IS NULL OR trim("gestor_dt") = '') AS missing,
                    count(*) FILTER (WHERE "gestor_dt" IS NOT NULL AND trim("gestor_dt") <> ''
                      AND (NOT regexp_full_match("gestor_dt", '[0-9]{8}')
                      OR try_strptime("gestor_dt", '%Y%m%d') IS NULL)) AS invalid,
                    count(*) FILTER (WHERE regexp_full_match("gestor_dt", '[0-9]{8}')
                      AND try_strptime("gestor_dt", '%Y%m%d') IS NOT NULL) AS valid
                    FROM "lake"."sih_aih_reduzida";

-- sih_aih_reduzida.sentinel999
SELECT
                    cod_idade, count(*) AS total,
                    count(*) FILTER (WHERE idade = 999) AS value_999
                    FROM "lake"."sih_aih_reduzida" GROUP BY ALL ORDER BY ALL;

-- sih_aih_reduzida.birth_consistency

                    WITH parsed AS (SELECT cod_idade, idade, CASE WHEN try_cast(idade AS INTEGER) BETWEEN 0 AND 99 THEN CASE
        WHEN trim(cod_idade) IN ('2','3') THEN 0
        WHEN trim(cod_idade) = '4' THEN try_cast(idade AS INTEGER)
        WHEN trim(cod_idade) = '5' THEN 100 + try_cast(idade AS INTEGER)
      END END AS age,
                    try_strptime(nasc, '%Y%m%d') AS birth,
                    try_strptime(dt_inter, '%Y%m%d') AS admission,
                    try_strptime(dt_saida, '%Y%m%d') AS discharge FROM "lake"."sih_aih_reduzida")
                    SELECT cod_idade, count(*) AS total,
                    count(*) FILTER (WHERE birth IS NULL OR admission IS NULL) AS invalid_dates,
                    count(*) FILTER (WHERE birth > admission) AS birth_after_admission,
                    count(*) FILTER (WHERE age = date_part('year', age(admission,birth)))
                      AS matches_completed_years,
                    count(*) FILTER (WHERE age = date_part('year', age(discharge,birth)))
                      AS matches_completed_years_at_discharge,
                    min(date_part('year', age(admission,birth)) - idade) AS min_years_minus_raw,
                    max(date_part('year', age(admission,birth)) - idade) AS max_years_minus_raw
                    FROM parsed GROUP BY ALL ORDER BY ALL;

-- snapshots_after
SELECT snapshot_id,
            snapshot_time::VARCHAR AS snapshot_time, changes::VARCHAR AS changes
            FROM ducklake_snapshots('lake') ORDER BY snapshot_id;
