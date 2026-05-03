with apps as (
    select * from {{ ref('stg_itunes_apps') }}
),

dim_cat as (
    select * from {{ ref('dim_category') }}
),

dim_sel as (
    select * from {{ ref('dim_seller') }}
),

final as (
    select
        a.app_id,
        a.app_name,
        c.category_id,
        s.seller_id,
        a.price,
        a.currency,
        a.rating,
        a.rating_count,
        a.content_rating,
        a.release_date,
        a.version,
        a.loaded_at,
        case when a.price = 0 then 'Free' else 'Paid' end as price_tier,
        case
            when a.rating >= 4.5 then 'Excellent'
            when a.rating >= 4.0 then 'Good'
            when a.rating >= 3.0 then 'Average'
            else 'Below Average'
        end as rating_bucket
    from apps a
    left join dim_cat c on a.category = c.category_name
    left join dim_sel s on a.seller_name = s.seller_name
)

select * from final
