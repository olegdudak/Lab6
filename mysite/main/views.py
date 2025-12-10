from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django_otp.decorators import otp_required
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp import match_token
import qrcode
import io
import base64
import json
from django.http import JsonResponse
from django.db.models import Q
from .models import Article, News, ChatMessage

# Create your views here.

def index(request):
    latest_articles = Article.objects.all()[:3]
    return render(request, 'index.html', {'latest_articles': latest_articles})

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def blog(request):
    articles = Article.objects.all()
    return render(request, 'blog.html', {'articles': articles})

def article_detail(request, pk):
    article = Article.objects.get(pk=pk)
    return render(request, 'article_detail.html', {'article': article})

def news_list(request):
    news = News.objects.all()
    return render(request, 'news.html', {'news': news})

# 2FA Views
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            # Автоматично логінимо користувача після реєстрації
            login(request, user)
            messages.success(request, f'Ласкаво просимо, {username}! Налаштуйте 2FA для безпеки.')
            return redirect('index')  # Перенаправляємо на головну з модалкою
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def setup_2fa(request):
    user = request.user
    device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
    
    if not device:
        device = TOTPDevice.objects.create(user=user, name='default', confirmed=False)
    
    if request.method == 'POST':
        token = request.POST.get('token')
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            messages.success(request, '2FA успішно налаштовано!')
            return redirect('profile')
        else:
            messages.error(request, 'Невірний код. Спробуйте ще раз.')
    
    # Генеруємо QR код
    qr_url = device.config_url
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'registration/setup_2fa.html', {
        'qr_code': qr_code,
        'secret_key': device.key
    })

@login_required
def profile_view(request):
    devices = TOTPDevice.objects.filter(user=request.user, confirmed=True)
    has_2fa = devices.exists()
    backup_tokens = []
    if has_2fa:
        # Генеруємо або отримуємо резервні коди
        backup_tokens = list(range(1, 11))  # Приклад резервних кодів
    
    if request.method == 'POST' and 'disable_2fa' in request.POST:
        TOTPDevice.objects.filter(user=request.user).delete()
        messages.success(request, '2FA відключено!')
        return redirect('profile')
    
    return render(request, 'registration/profile.html', {
        'devices': devices,
        'has_2fa': has_2fa,
        'backup_tokens': backup_tokens
    })

@login_required
def disable_2fa(request):
    if request.method == 'POST':
        TOTPDevice.objects.filter(user=request.user).delete()
        messages.success(request, '2FA відключено!')
        return redirect('profile')
    return render(request, 'registration/disable_2fa.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Ви успішно вийшли з акаунта!')
    return redirect('index')

@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Пароль успішно змінено!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/password_change.html', {'form': form})

@login_required
def chatbot_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return JsonResponse({'error': 'Повідомлення не може бути порожнім'})
            
            # Пошук статей та новин
            search_results = search_content(user_message)
            
            # Формуємо текстову відповідь для збереження в БД
            if isinstance(search_results, list):
                text_response = ""
                for section in search_results:
                    text_response += f"{section['title']}\n"
                    for item in section['items']:
                        text_response += f"• {item['title']}\n"
                    text_response += "\n"
            else:
                text_response = search_results
            
            # Зберігаємо повідомлення в базі даних
            chat_message = ChatMessage.objects.create(
                user=request.user,
                message=user_message,
                response=text_response
            )
            
            return JsonResponse({
                'results': search_results,
                'timestamp': chat_message.timestamp.strftime('%H:%M')
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Невірний формат даних'})
    
    # GET запит - показуємо історію чату
    chat_history = ChatMessage.objects.filter(user=request.user)[:10]
    return render(request, 'chatbot.html', {'chat_history': chat_history})

def search_content(query):
    """
    Функція пошуку контенту для чат-бота з розумним пошуком слів
    """
    # Розбиваємо запит на окремі слова
    query_words = query.lower().split()
    
    # Створюємо Q об'єкти для кожного слова
    article_queries = Q()
    news_queries = Q()
    
    for word in query_words:
        # Для кожного слова шукаємо часткові збіги
        article_queries |= (
            Q(title__icontains=word) | 
            Q(content__icontains=word)
        )
        news_queries |= (
            Q(title__icontains=word) | 
            Q(content__icontains=word)
        )
    
    # Пошук в статтях
    articles = Article.objects.filter(article_queries).distinct()[:10]
    
    # Пошук в новинах
    news = News.objects.filter(news_queries).distinct()[:5]
    
    results = []
    
    if articles:
        results.append({
            'type': 'articles',
            'title': '📝 Знайдені статті:',
            'items': [{'id': article.id, 'title': article.title, 'date': article.date} for article in articles]
        })
    
    if news:
        results.append({
            'type': 'news', 
            'title': '📰 Новини:',
            'items': [{'id': item.id, 'title': item.title, 'date': item.date, 'author': item.author} for item in news]
        })
    
    if not articles and not news:
        # Якщо нічого не знайдено, пропонуємо популярні статті
        popular_articles = Article.objects.all()[:5]
        if popular_articles:
            results.append({
                'type': 'articles',
                'title': f'😔 Не знайдено результатів за запитом "{query}". Ось популярні статті:',
                'items': [{'id': article.id, 'title': article.title, 'date': article.date} for article in popular_articles]
            })
        else:
            return "😔 На жаль, не знайдено результатів. Спробуйте інший запит."
    
    return results

def get_search_suggestions(query):
    """
    Генерує пропозиції на основі популярних тем
    """
    suggestions = []
    
    keywords = {
        'мем': ['мем', 'меми', 'смішно', 'гумор'],
        'інтернет': ['інтернет', 'онлайн', 'web'],
        'технології': ['технології', 'IT', 'програмування'],
        'новини': ['новини', 'події', 'актуальне']
    }
    
    for category, words in keywords.items():
        if any(word in query for word in words):
            # Знаходимо статті цієї категорії
            category_articles = Article.objects.filter(
                Q(title__icontains=category) | Q(content__icontains=category)
            )[:3]
            
            for article in category_articles:
                suggestions.append(article.title)
    
    return suggestions[:5]

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Перевіряємо чи є у користувача 2FA
                has_2fa = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
                
                if has_2fa:
                    otp_token = request.POST.get('otp_token')
                    if otp_token:
                        # Перевіряємо 2FA код
                        if match_token(user, otp_token):
                            login(request, user)
                            messages.success(request, f'Ласкаво просимо, {user.username}!')
                            return redirect('index')
                        else:
                            messages.error(request, 'Невірний код 2FA!')
                            return render(request, 'registration/login.html', {
                                'form': form, 
                                'show_2fa_field': True
                            })
                    else:
                        # Показуємо форму з полем для 2FA
                        messages.info(request, 'Введіть код з додатку автентифікації')
                        return render(request, 'registration/login.html', {
                            'form': form, 
                            'show_2fa_field': True
                        })
                else:
                    # Користувач без 2FA - входимо і перенаправляємо на налаштування
                    login(request, user)
                    messages.warning(request, 'Налаштуйте 2FA для безпеки акаунта')
                    return redirect('setup_2fa')
            else:
                messages.error(request, 'Невірні дані для входу!')
        else:
            messages.error(request, 'Помилка у формі!')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {
        'form': form,
        'show_2fa_field': False
    })
