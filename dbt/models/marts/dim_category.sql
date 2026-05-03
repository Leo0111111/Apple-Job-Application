with apps as (
    select distinct category from {{ ref('stg_itunes_apps') }}
    where category is not null
),

final as (
    select
        md5(category) as category_id,
        category as category_name
    from apps
)

select * from final
