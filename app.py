from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import requests
import random
from datetime import datetime
import locale

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)

with app.app_context():  
    db.create_all()

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    total_points = get_user_score(user.id)

    weather = get_weather()

    return render_template('home.html', total_points=total_points, weather=weather)

@app.route('/weather')
def get_weather():
    city = request.args.get('city', 'Toruń')  

    api_key = "9db2ae009b5d4709b34110342241502"  
    
    locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')

    api_url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&days=3&lang=pl&q={city}"
    response = requests.get(api_url)
    data = response.json()
    
    try:
        data_forecast = data['forecast']['forecastday']
    
        forecasts = []
        for item in data_forecast:
            date_string = item['hour'][0]['time']
            date_object = datetime.strptime(date_string, '%Y-%m-%d %H:%M')
            day_name = date_object.strftime('%A')
            icon_url = item['day']['condition']['icon']
            temp_day = round(item['day']['maxtemp_c'])
            temp_night = round(item['hour'][0]['temp_c'])
            forecast = {
                'day_name': day_name,
                'temp_day': temp_day,
                'temp_night': temp_night,
                'icon_url': icon_url 
            }
            forecasts.append(forecast)
        weather = {
            'city': city,
            'forecasts': forecasts
        }

        return weather
    except KeyError:
        weather = {
            'error_message':"Brak prognozy pogody dla tego miasta. Spróbuj wpisać nazwę miasta po angielsku lub bez polskich znaków."
        }
        return weather

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return 'Nazwa użytkownika zajęta!'
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            return redirect(url_for('home'))
        return 'Nieprawidłowa nazwa użytkownika lub hasło!'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    if request.method == 'POST':
        answer = request.form['answer']
        question = request.form['question']
        correct_answer = request.form['correct_answer']
        if answer == correct_answer:
            score = Quiz(user_id=user.id, score=1)
            db.session.add(score)
            db.session.commit()
        return redirect(url_for('quiz'))
    score = get_user_score(user.id)
    question = get_random_question()
    return render_template('quiz.html', question=question, score=score)

def get_random_question():
    questions = [
        {'question': 'Co to jest sztuczna inteligencja?', 'options': ['Technologia, która pozwala komputerom na wykonywanie zadań, które normalnie wymagałyby ludzkiej inteligencji', 'Metoda szyfrowania danych', 'Rodzaj algorytmu sortującego', 'Specjalna technika kompresji danych'], 'answer': 'Technologia, która pozwala komputerom na wykonywanie zadań, które normalnie wymagałyby ludzkiej inteligencji'},
        {'question': 'Jakie popularne biblioteki są używane w programowaniu sztucznej inteligencji?', 'options': ['TensorFlow', 'PyTorch', 'scikit-learn', 'Keras'], 'answer': 'TensorFlow'},
        {'question': 'Czym różni się uczenie nadzorowane od nienadzorowanego?', 'options': ['W uczeniu nadzorowanym dane treningowe mają etykiety, w nienadzorowanym nie ma etykiet', 'W uczeniu nadzorowanym nie ma etykiet, w nienadzorowanym dane treningowe mają etykiety', 'Nie ma różnicy', 'Zależy od preferencji programisty'], 'answer': 'W uczeniu nadzorowanym dane treningowe mają etykiety, w nienadzorowanym nie ma etykiet'},
        {'question': 'Co to jest sieć neuronowa?', 'options': ['Matematyczny model inspirowany funkcjonowaniem mózgu, złożony z połączonych neuronów', 'Program komputerowy do analizy danych', 'Specjalny rodzaj algorytmu sortującego', 'Rodzaj interfejsu użytkownika'], 'answer': 'Matematyczny model inspirowany funkcjonowaniem mózgu, złożony z połączonych neuronów'},
        {'question': 'Czym jest algorytm genetyczny?', 'options': ['To heurystyczny algorytm inspirowany procesem ewolucji biologicznej', 'To algorytm do kompresji danych', 'To rodzaj algorytmu sortującego', 'To algorytm do rozwiązywania równań różniczkowych'], 'answer': 'To heurystyczny algorytm inspirowany procesem ewolucji biologicznej'},
        {'question': 'Jakie metody są używane w uczeniu ze wzmocnieniem?', 'options': ['Metoda Q-learning', 'Metoda k-średnich', 'Metoda najbliższego sąsiada', 'Metoda regresji liniowej'], 'answer': 'Metoda Q-learning'},
        {'question': 'Co to jest uczenie głębokie?', 'options': ['To podzbiór sztucznej inteligencji, który wykorzystuje sieci neuronowe o wielu warstwach', 'To rodzaj algorytmu sortującego', 'To technika kompresji danych', 'To metoda optymalizacji funkcji'], 'answer': 'To podzbiór sztucznej inteligencji, który wykorzystuje sieci neuronowe o wielu warstwach'},
        {'question': 'Który język programowania jest często używany w projektach związanych z sztuczną inteligencją?', 'options': ['Python', 'Java', 'C++', 'JavaScript'], 'answer': 'Python'},
        {'question': 'Jakie są główne kroki w procesie uczenia maszynowego?', 'options': ['Zbieranie danych, wybór modelu, trenowanie modelu, ocena modelu, dostosowywanie parametrów', 'Wybór modelu, ocena modelu, dostosowywanie parametrów, trenowanie modelu', 'Trenowanie modelu, dostosowywanie parametrów, ocena modelu', 'Zbieranie danych, trenowanie modelu, ocena modelu, dostosowywanie parametrów'], 'answer': 'Zbieranie danych, wybór modelu, trenowanie modelu, ocena modelu, dostosowywanie parametrów'},
        {'question': 'Czym jest przetwarzanie języka naturalnego?', 'options': ['To dziedzina sztucznej inteligencji zajmująca się komunikacją między ludźmi a komputerami w naturalnych językach', 'To metoda kompresji danych', 'To technika szyfrowania danych', 'To algorytm sortujący'], 'answer': 'To dziedzina sztucznej inteligencji zajmująca się komunikacją między ludźmi a komputerami w naturalnych językach'},
        {'question': 'Jakie są typowe zadania w przetwarzaniu języka naturalnego?', 'options': ['Analiza sentymentu, rozpoznawanie mowy, generowanie tekstu', 'Algorytmy sortujące, kompresja danych, szyfrowanie', 'Tworzenie baz danych, analiza finansowa, tworzenie grafik', 'Projektowanie interfejsów użytkownika, rozwój oprogramowania, testowanie oprogramowania'], 'answer': 'Analiza sentymentu, rozpoznawanie mowy, generowanie tekstu'},
        {'question': 'Czym jest uczenie nienadzorowane?', 'options': ['To rodzaj uczenia maszynowego, w którym dane treningowe nie mają etykiet', 'To rodzaj uczenia maszynowego, w którym wszystkie dane są etykietowane ręcznie', 'To specjalna metoda optymalizacji funkcji', 'To metoda szyfrowania danych'], 'answer': 'To rodzaj uczenia maszynowego, w którym dane treningowe nie mają etykiet'},
        {'question': 'Czym jest regresja liniowa?', 'options': ['To metoda statystyczna służąca do modelowania zależności między zmiennymi', 'To algorytm sortujący', 'To specjalna metoda kompresji danych', 'To algorytm szyfrujący'], 'answer': 'To metoda statystyczna służąca do modelowania zależności między zmiennymi'},
        {'question': 'Jakie są podstawowe typy sieci neuronowych?', 'options': ['Perceptron jednowarstwowy, sieć wielowarstwowa (MLP), sieć konwolucyjna (CNN), sieć rekurencyjna (RNN)', 'Algorytmy sortujące, algorytmy kompresji danych, algorytmy szyfrujące', 'Szybkie, wolne, średnie', 'Proste, złożone, zrównoważone'], 'answer': 'Perceptron jednowarstwowy, sieć wielowarstwowa (MLP), sieć konwolucyjna (CNN), sieć rekurencyjna (RNN)'},
        {'question': 'Jakie są korzyści z wykorzystania sztucznej inteligencji?', 'options': ['Automatyzacja procesów, lepsze podejmowanie decyzji, efektywniejsze wykorzystanie danych', 'Szybsze sortowanie danych, szybsza kompresja danych, szybsze szyfrowanie danych', 'Zwiększenie liczby błędów w analizie danych', 'Zmniejszenie możliwości optymalizacji procesów biznesowych'], 'answer': 'Automatyzacja procesów, lepsze podejmowanie decyzji, efektywniejsze wykorzystanie danych'},
        {'question': 'Czym jest sieć konwolucyjna (CNN)?', 'options': ['To typ sieci neuronowej, który efektywnie przetwarza dane przestrzenne, takie jak obrazy', 'To metoda szyfrowania danych', 'To specjalna metoda kompresji danych', 'To algorytm sortujący'], 'answer': 'To typ sieci neuronowej, który efektywnie przetwarza dane przestrzenne, takie jak obrazy'},
        {'question': 'Jakie są główne wyzwania związane z implementacją sztucznej inteligencji?', 'options': ['Brak danych, interpretowalność modeli, zabezpieczenia', 'Niskie koszty, dostępność sprzętu, szybkość obliczeń', 'Wysoka interpretowalność modeli, niskie koszty, brak danych', 'Brak wyzwań w implementacji'], 'answer': 'Brak danych, interpretowalność modeli, zabezpieczenia'},
        {'question': 'Czym jest funkcja kosztu (loss function) w kontekście uczenia maszynowego?', 'options': ['To funkcja, która mierzy, jak bardzo predykcje modelu różnią się od prawdziwych wartości', 'To funkcja służąca do sortowania danych', 'To specjalna metoda kompresji danych', 'To algorytm szyfrujący'], 'answer': 'To funkcja, która mierzy, jak bardzo predykcje modelu różnią się od prawdziwych wartości'},
        {'question': 'Czym jest algorytm K-średnich (K-means)?', 'options': ['To algorytm grupowania danych, który dzieli dane na K klastrów', 'To specjalna metoda optymalizacji funkcji', 'To rodzaj algorytmu sortującego', 'To algorytm szyfrujący'], 'answer': 'To algorytm grupowania danych, który dzieli dane na K klastrów'},
        {'question': 'Czym jest sieć rekurencyjna (RNN)?', 'options': ['To typ sieci neuronowej, który ma pamięć i jest użyteczny w analizie sekwencji danych', 'To rodzaj algorytmu sortującego', 'To specjalna metoda kompresji danych', 'To algorytm szyfrujący'], 'answer': 'To typ sieci neuronowej, który ma pamięć i jest użyteczny w analizie sekwencji danych'}
    ]

    return random.choice(questions)

def get_user_score(user_id):
    user_score = Quiz.query.filter_by(user_id=user_id).count()
    return user_score


@app.route('/quiz_results')
def quiz_results():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()


    user_score = get_user_score(user.id)


    users = User.query.all()
    user_scores = []
    for user in users:
        score = get_user_score(user.id)
        user_scores.append({'username': user.username, 'score': score})


    sorted_user_scores = sorted(user_scores, key=lambda x: x['score'], reverse=True)

    return render_template('quiz_results.html', user_score=user_score, user_scores=sorted_user_scores)

if __name__ == '__main__':
    app.run(debug=True)
