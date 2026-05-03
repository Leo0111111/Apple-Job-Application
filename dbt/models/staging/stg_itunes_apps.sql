with source as (
    select * from {{ source('raw', 'RAW_ITUNES_APPS') }}
),

renamed as (
    select
        app_id,
        app_name,
        seller_name,
        category,
        price,
        currency,
        rating,
        rating_count,
        content_rating,
        release_date,
        version,
        loaded_at
    from source
    where app_id is not null
      and app_name is not null
)

select * from renamed
