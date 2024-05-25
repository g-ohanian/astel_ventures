## Setup local development

- Make sure you have Python 3.12 installed;
- Run `pip install -r requirements.txt`;
- Run `python -m spacy download en_core_web_sm`;
- Run `python manage.py createsuperuser` and follow the instructions. Created user will be the authorized one;
- Run `python manage.py migrate`;
- Run `python manage.py collectstatic`;
- Create a copy of `.env-example` named `.env`;

## Running API locally

python manage.py runserver
