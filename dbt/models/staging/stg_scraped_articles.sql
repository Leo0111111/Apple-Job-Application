with source as (
    select * from {{ source('raw', 'RAW_SCRAPED_ARTICLES') }}
),

renamed as (
    select
        source_id,
        url,
        site,
        title,
        word_count,
        scraped_at
    from source
    where source_id is not null
      and title is not null
)

select * from renamed
