# catalyst
git clone https://github.com/kalpesh232/catalyst.git
cd catalyst
python -m venv django-environ
source django-environ/bin/activate  # On Windows: django-environ\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
redis-server
celery -A catalyst worker --loglevel=info
python manage.py runserver

