with apps as (
    select distinct seller_name from {{ ref('stg_itunes_apps') }}
    where seller_name is not null
),

final as (
    select
        md5(seller_name) as seller_id,
        seller_name
    from apps
)

select * from final
