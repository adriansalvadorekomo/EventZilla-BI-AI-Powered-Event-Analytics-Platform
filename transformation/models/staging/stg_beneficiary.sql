-- Data minimisation: names, e-mails and phone numbers stay in raw; analytics needs none of them.
select
  {{ int_('id_beneficiary') }}                                  as beneficiary_id,
  {{ txt('email') }} is not null                                as has_email,
  lower(split_part({{ txt('email') }}, '@', 2))                 as email_domain
from {{ source('raw', 'beneficiary') }}
