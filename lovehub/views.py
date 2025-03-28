from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from datetime import timedelta, date, datetime
import random
from django.contrib.auth.models import User
import json
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash
from django import forms

from .models import (
    UserProfile, DailyMood, DailyMessage, Moment, MomentComment, MomentLike,
    Event, WishItem, DateIdea, DateIdeaRating, GratitudeNote, DashboardWidget,
    AppTheme, LoveQuote, Note, Notification, NotificationSettings, PrivacySettings,
    UserWidget
)

@login_required
def dashboard(request):
    """داشبورد اصلی برنامه"""
    user = request.user
    
    # Get user's enabled widgets or create defaults if none exist
    widgets = DashboardWidget.objects.filter(user=user, is_enabled=True).order_by('position')
    if not widgets:
        # Create default widgets
        default_widgets = [
            ('counter', 1),
            ('upcoming_events', 2),
            ('this_day', 3),
            ('latest_moment', 4),
            ('love_quote', 5),
            ('daily_mood', 6),
            ('daily_message', 7),
        ]
        for widget_type, position in default_widgets:
            DashboardWidget.objects.create(
                user=user,
                widget_type=widget_type,
                position=position
            )
        widgets = DashboardWidget.objects.filter(user=user, is_enabled=True).order_by('position')
    
    # Get user profile or create it
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Calculate relationship days
    relationship_days = 0
    if profile.relationship_start_date:
        delta = timezone.now().date() - profile.relationship_start_date
        relationship_days = delta.days
    
    # Get partner
    partner = None
    if profile.partner:
        partner = profile.partner.user
    
    # Get statistics counts
    event_count = Event.objects.filter(created_by=user).count()
    moment_count = Moment.objects.filter(created_by=user).count()
    note_count = Note.objects.filter(created_by=user).count()
    
    # Get recent moods for chart
    recent_moods = DailyMood.objects.filter(user=user).order_by('-date')[:7]
    
    # Prepare mood data for chart
    mood_data = []
    if recent_moods:
        for mood in reversed(recent_moods):
            # Map mood emoji to numeric value for chart
            mood_value = 5  # Default value
            if mood.mood == 'happy':
                mood_value = 10
            elif mood.mood == 'loved':
                mood_value = 9
            elif mood.mood == 'excited':
                mood_value = 8
            elif mood.mood == 'neutral':
                mood_value = 6
            elif mood.mood == 'tired':
                mood_value = 5
            elif mood.mood == 'sad':
                mood_value = 3
            elif mood.mood == 'angry':
                mood_value = 2
            
            mood_data.append({
                'date': mood.date.strftime('%m/%d'),
                'value': mood_value
            })
            
    # Get upcoming events 
    today = timezone.now().date()
    thirty_days_later = today + timedelta(days=30)
    upcoming_events = Event.objects.filter(
        Q(created_by=user) | Q(created_by__profile__partner=profile),
        date__gte=today,
        date__lte=thirty_days_later
    ).order_by('date')[:5]
    
    # Add days_until property to each event
    for event in upcoming_events:
        event.days_until = (event.date - today).days
    
    # Get unread notifications count
    unread_notifications_count = Notification.objects.filter(user=user, is_read=False).count()
    
    # Prepare data for each widget
    widget_data = {}
    
    for widget in widgets:
        if widget.widget_type == 'counter':
            # Days counter since relationship start
            if profile.relationship_start_date:
                # استفاده از timezone.now().date() برای محاسبه دقیق تعداد روزها
                delta = timezone.now().date() - profile.relationship_start_date
                widget_data['counter'] = {
                    'days': delta.days,
                    'start_date': profile.relationship_start_date
                }
            else:
                # اگر تاریخ شروع رابطه تنظیم نشده بود، یک مقدار پیش‌فرض قرار بده
                today = timezone.now().date()
                widget_data['counter'] = {
                    'days': 0,
                    'start_date': today
                }
                
        elif widget.widget_type == 'upcoming_events':
            # Get upcoming events in next 30 days
            today = timezone.now().date()
            thirty_days_later = today + timedelta(days=30)
            events = Event.objects.filter(
                Q(created_by=user) | Q(created_by__profile__partner=profile),
                date__gte=today,
                date__lte=thirty_days_later
            ).order_by('date')[:5]
            
            # Add days_until property to each event
            for event in events:
                event.days_until = (event.date - today).days
                
            widget_data['upcoming_events'] = events
            
        elif widget.widget_type == 'this_day':
            # "On this day" - events or moments from previous years on this date
            today = timezone.now().date()
            this_day_events = Event.objects.filter(
                Q(created_by=user) | Q(created_by__profile__partner=profile),
                date__day=today.day,
                date__month=today.month,
                date__year__lt=today.year
            )
            this_day_moments = Moment.objects.filter(
                Q(created_by=user) | Q(created_by__profile__partner=profile),
                date__day=today.day,
                date__month=today.month,
                date__year__lt=today.year
            )
            widget_data['this_day'] = {
                'events': this_day_events,
                'moments': this_day_moments
            }
            
        elif widget.widget_type == 'latest_moment':
            # Latest recorded moment
            latest_moment = Moment.objects.filter(
                Q(created_by=user) | Q(created_by__profile__partner=profile)
            ).order_by('-date').first()
            widget_data['latest_moment'] = latest_moment
            
        elif widget.widget_type == 'love_quote':
            # Random love quote
            quotes = LoveQuote.objects.filter(is_active=True)
            if quotes.exists():
                random_quote = random.choice(quotes)
                widget_data['love_quote'] = random_quote
            else:
                # اگر نقل قول فعالی وجود نداشت، یک نقل قول پیش‌فرض قرار بده
                widget_data['love_quote'] = {
                    'text': 'عشق صبر می‌کند، باور می‌کند، همیشه امیدوار است و در همه شرایط پایدار می‌ماند.',
                    'author': 'نقل قول پیش‌فرض'
                }
                
        elif widget.widget_type == 'daily_mood':
            # Today's mood for both partners
            today = timezone.now().date()
            user_mood = DailyMood.objects.filter(user=user, date=today).first()
            partner_mood = None
            if profile.partner and profile.partner.user:
                partner_mood = DailyMood.objects.filter(
                    user=profile.partner.user, 
                    date=today
                ).first()
            
            # Get mood history for the past 7 days
            week_ago = today - timedelta(days=7)
            user_moods = DailyMood.objects.filter(
                user=user, 
                date__gte=week_ago,
                date__lte=today
            ).order_by('date')
            
            partner_moods = []
            if profile.partner and profile.partner.user:
                partner_moods = DailyMood.objects.filter(
                    user=profile.partner.user,
                    date__gte=week_ago,
                    date__lte=today
                ).order_by('date')
            
            widget_data['daily_mood'] = {
                'user_mood': user_mood,
                'partner_mood': partner_mood,
                'user_moods': user_moods,
                'partner_moods': partner_moods
            }
            
        elif widget.widget_type == 'daily_message':
            # Today's shared message
            today = timezone.now().date()
            user_message = DailyMessage.objects.filter(sender=user, date=today).first()
            partner_message = None
            if profile.partner and profile.partner.user:
                partner_message = DailyMessage.objects.filter(
                    sender=profile.partner.user,
                    date=today
                ).first()
                
            widget_data['daily_message'] = {
                'user_message': user_message,
                'partner_message': partner_message
            }
            
        elif widget.widget_type == 'daily_challenge':
            # Random relationship challenge
            challenges = [
                "امروز صبحانه را با هم آماده کنید",
                "امروز یک فیلم عاشقانه با هم تماشا کنید",
                "امروز سه چیزی که در مورد همدیگر دوست دارید را بنویسید",
                "امروز بدون موبایل با هم وقت بگذرانید",
                "امروز خاطرات اولین ملاقاتتان را مرور کنید",
                "امروز یک عکس جدید با هم بگیرید",
                "امروز به پیاده روی بروید",
                "امروز برای یکدیگر یک نامه کوتاه بنویسید",
                "امروز سورپرایز کوچکی برای یکدیگر آماده کنید"
            ]
            widget_data['daily_challenge'] = random.choice(challenges)
    
    # Get user's theme preference
    theme, _ = AppTheme.objects.get_or_create(user=user, defaults={'theme': 'default'})
    
    context = {
        'widgets': widgets,
        'widget_data': widget_data,
        'theme': theme.theme,
        'profile': profile,
        'partner': partner,
        'relationship_days': relationship_days,
        'event_count': event_count,
        'moment_count': moment_count,
        'note_count': note_count,
        'recent_moods': recent_moods,
        'mood_data': json.dumps(mood_data),
        'upcoming_events': upcoming_events,
        'unread_notifications_count': unread_notifications_count
    }
    
    return render(request, 'lovehub/dashboard.html', context)

@login_required
def update_daily_mood(request):
    """بروزرسانی حس و حال روزانه"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    today = timezone.now().date()
    
    # Get today's mood if exists
    user_mood = DailyMood.objects.filter(user=user, date=today).first()
    
    # Get partner's mood if exists
    partner_mood = None
    if profile.partner and profile.partner.user:
        partner_mood = DailyMood.objects.filter(
            user=profile.partner.user,
            date=today
        ).first()
    
    if request.method == 'POST':
        mood = request.POST.get('mood')
        note = request.POST.get('note')
        
        # Update or create mood for today
        user_mood, created = DailyMood.objects.update_or_create(
            user=user,
            date=today,
            defaults={
                'mood': mood,
                'note': note
            }
        )
        
        # Create notification for partner if they exist
        if profile.partner and profile.partner.user:
            partner = profile.partner.user
            # Check if notification settings allow for this
            partner_settings, created = NotificationSettings.objects.get_or_create(
                user=partner,
                defaults={
                    'enabled': True,
                    'notify_events': True,
                    'notify_moments': True,
                    'notify_wishes': True,
                    'notify_comments': True,
                    'notify_daily_messages': True
                }
            )
            
            if partner_settings.enabled:
                Notification.objects.create(
                    user=partner,
                    title="ثبت حال و هوای روزانه",
                    message=f"{user.get_full_name() or user.username} حال و هوای خود را {mood} ثبت کرده است.",
                    notification_type='system',
                    link="/mood/update/"
                )
        
        messages.success(request, 'حال و هوای روزانه با موفقیت ثبت شد')
        return redirect('dashboard')
    
    context = {
        'user_mood': user_mood,
        'partner_mood': partner_mood
    }
    
    return render(request, 'lovehub/update_mood.html', context)

@login_required
def update_daily_message(request):
    """بروزرسانی پیام روزانه"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    today = date.today()
    
    # Get today's message if exists
    user_message = DailyMessage.objects.filter(sender=user, date=today).first()
    
    # Get partner's message if exists
    partner_message = None
    if profile.partner and profile.partner.user:
        partner_message = DailyMessage.objects.filter(
            sender=profile.partner.user,
            date=today
        ).first()
    
    if request.method == 'POST':
        message = request.POST.get('message')
        
        if message:
            # Update or create message for today
            user_message, created = DailyMessage.objects.update_or_create(
                sender=user,
                date=today,
                defaults={'message': message}
            )
            
            # Create notification for partner if they exist
            if profile.partner and profile.partner.user:
                partner = profile.partner.user
                # Check if notification settings allow for this
                partner_settings, created = NotificationSettings.objects.get_or_create(
                    user=partner,
                    defaults={
                        'enabled': True,
                        'notify_events': True,
                        'notify_moments': True,
                        'notify_wishes': True,
                        'notify_comments': True,
                        'notify_daily_messages': True
                    }
                )
                
                if partner_settings.enabled and partner_settings.notify_daily_messages:
                    Notification.objects.create(
                        user=partner,
                        title="پیام روزانه جدید",
                        message=f"{user.get_full_name() or user.username} یک پیام روزانه جدید برای شما ارسال کرده است.",
                        notification_type='daily_message',
                        link="/message/update/"
                    )
            
            messages.success(request, 'پیام روزانه با موفقیت ثبت شد')
            return redirect('dashboard')
    
    context = {
        'user_message': user_message,
        'partner_message': partner_message
    }
    
    return render(request, 'lovehub/update_message.html', context)

@login_required
def moments_list(request):
    """نمایش لیست لحظات ثبت شده"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # Get moments from both user and partner
    if profile.partner and profile.partner.user:
        moments = Moment.objects.filter(
            Q(created_by=user) | Q(created_by=profile.partner.user)
        ).order_by('-date')
    else:
        moments = Moment.objects.filter(created_by=user).order_by('-date')
    
    # Handle filtering
    query = request.GET.get('q')
    filter_date_from = request.GET.get('date_from')
    filter_date_to = request.GET.get('date_to')
    filter_mood_tags = request.GET.getlist('mood_tags')
    filter_location = request.GET.get('location')
    sort_by = request.GET.get('sort', 'newest')
    
    # Apply text search filter
    if query:
        moments = moments.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(location_name__icontains=query)
        )
    
    # Apply date filters
    if filter_date_from:
        try:
            moments = moments.filter(date__date__gte=filter_date_from)
        except ValueError:
            messages.error(request, 'فرمت تاریخ شروع نامعتبر است')
    
    if filter_date_to:
        try:
            moments = moments.filter(date__date__lte=filter_date_to)
        except ValueError:
            messages.error(request, 'فرمت تاریخ پایان نامعتبر است')
    
    # Apply mood tags filter
    if filter_mood_tags:
        mood_queries = Q()
        for tag in filter_mood_tags:
            mood_queries |= Q(mood_tags__icontains=tag)
        moments = moments.filter(mood_queries)
    
    # Apply location filter
    if filter_location:
        moments = moments.filter(location_name__icontains=filter_location)
    
    # Apply sorting
    if sort_by == 'oldest':
        moments = moments.order_by('date')
    elif sort_by == 'most_liked':
        moments = moments.annotate(likes_count=models.Count('likes')).order_by('-likes_count')
    elif sort_by == 'most_commented':
        moments = moments.annotate(comments_count=models.Count('comments')).order_by('-comments_count')
    # Default is already newest (-date)
    
    context = {
        'moments': moments,
        'filter_applied': bool(query or filter_date_from or filter_date_to or filter_mood_tags or filter_location),
        'filter_mood_tags': filter_mood_tags,
    }
    
    return render(request, 'lovehub/moments_list.html', context)

@login_required
def add_moment(request):
    """افزودن لحظه جدید"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        mood_tags = request.POST.get('mood_tags')
        location_name = request.POST.get('location_name')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        date_str = request.POST.get('date')
        
        if not title or not description:
            messages.error(request, 'لطفاً عنوان و توضیحات لحظه را وارد کنید')
            return render(request, 'lovehub/add_moment.html')
        
        # تنظیم تاریخ
        if date_str:
            try:
                date_obj = timezone.make_aware(datetime.strptime(date_str, '%Y/%m/%d'))
            except ValueError:
                date_obj = timezone.now()
        else:
            date_obj = timezone.now()
        
        # ایجاد لحظه
        moment = Moment.objects.create(
            created_by=request.user,
            title=title,
            description=description,
            date=date_obj,
            mood_tags=mood_tags,
            location_name=location_name,
            latitude=latitude if latitude else None,
            longitude=longitude if longitude else None
        )
        
        # اضافه کردن تصویر
        if 'image' in request.FILES:
            moment.image = request.FILES['image']
            moment.save()
        
        # ایجاد اعلان برای همسر
        user = request.user
        profile = get_object_or_404(UserProfile, user=user)
        if profile.partner and profile.partner.user:
            partner = profile.partner.user
            # بررسی تنظیمات اعلان‌های همسر
            partner_settings, created = NotificationSettings.objects.get_or_create(
                user=partner,
                defaults={
                    'enabled': True,
                    'notify_moments': True
                }
            )
            
            if partner_settings.enabled and partner_settings.notify_moments:
                Notification.objects.create(
                    user=partner,
                    title="لحظه جدید ثبت شد",
                    message=f"{user.get_full_name() or user.username} لحظه جدیدی با عنوان '{title}' ثبت کرده است.",
                    notification_type='moment',
                    link=f'/moment/{moment.id}/',
                    related_object_id=moment.id
                )
        
        messages.success(request, 'لحظه جدید با موفقیت ایجاد شد')
        return redirect('moment_detail', pk=moment.pk)
    
    context = {}
    return render(request, 'lovehub/add_moment.html', context)

@login_required
def moment_detail(request, pk):
    """نمایش جزئیات یک لحظه"""
    moment = get_object_or_404(Moment, pk=pk)
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # Check if user is authorized to view this moment
    if moment.created_by != user and (not profile.partner or moment.created_by != profile.partner.user):
        messages.error(request, 'شما اجازه دسترسی به این لحظه را ندارید')
        return redirect('moments_list')
    
    # Handle adding comment
    if request.method == 'POST':
        comment_text = request.POST.get('comment')
        if comment_text:
            MomentComment.objects.create(
                moment=moment,
                user=user,
                text=comment_text
            )
            messages.success(request, 'دیدگاه با موفقیت ثبت شد')
            return redirect('moment_detail', pk=moment.pk)
    
    # Get comments
    comments = moment.comments.all()
    
    # Check if user liked this moment
    user_liked = moment.likes.filter(user=user).exists()
    
    context = {
        'moment': moment,
        'comments': comments,
        'user_liked': user_liked
    }
    
    return render(request, 'lovehub/moment_detail.html', context)

@login_required
def like_moment(request, pk):
    """لایک کردن یک لحظه"""
    moment = get_object_or_404(Moment, pk=pk)
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # Check if user is authorized to like this moment
    if moment.created_by != user and (not profile.partner or moment.created_by != profile.partner.user):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'شما اجازه لایک کردن این لحظه را ندارید'}, status=403)
        messages.error(request, 'شما اجازه لایک کردن این لحظه را ندارید')
        return redirect('moments_list')
    
    # Toggle like
    like, created = MomentLike.objects.get_or_create(moment=moment, user=user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    like_count = moment.likes.count()
    
    # For AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked, 
            'count': like_count,
            'message': 'لایک با موفقیت ثبت شد' if liked else 'لایک با موفقیت حذف شد'
        })
    
    return redirect('moment_detail', pk=moment.pk)

@login_required
def events_list(request):
    """نمایش لیست رویدادها"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # Base query - Get events from both user and partner
    if profile.partner and profile.partner.user:
        events = Event.objects.filter(
            Q(created_by=user) | Q(created_by=profile.partner.user)
        ).select_related('created_by')
    else:
        events = Event.objects.filter(created_by=user).select_related('created_by')
    
    # Apply filters
    event_type = request.GET.get('event_type')
    search = request.GET.get('search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    sort = request.GET.get('sort', 'all')
    include_recurring = request.GET.get('include_recurring') == 'on'
    
    # Track if any filters are applied
    is_filtered = False
    
    # Filter by event type
    if event_type and event_type != 'all':
        events = events.filter(event_type=event_type)
        is_filtered = True
    
    # Filter by search term
    if search:
        events = events.filter(Q(title__icontains=search) | Q(description__icontains=search))
        is_filtered = True
    
    # Filter by date range
    if date_from:
        try:
            # Handle date formats like YYYY/MM/DD
            if '/' in date_from:
                year, month, day = date_from.split('/')
                date_from_formatted = f"{year}-{month}-{day}"
            else:
                date_from_formatted = date_from
            
            events = events.filter(date__gte=date_from_formatted)
            is_filtered = True
        except (ValueError, TypeError):
            messages.error(request, 'فرمت تاریخ شروع نامعتبر است')
    
    if date_to:
        try:
            # Handle date formats like YYYY/MM/DD
            if '/' in date_to:
                year, month, day = date_to.split('/')
                date_to_formatted = f"{year}-{month}-{day}"
            else:
                date_to_formatted = date_to
            
            events = events.filter(date__lte=date_to_formatted)
            is_filtered = True
        except (ValueError, TypeError):
            messages.error(request, 'فرمت تاریخ پایان نامعتبر است')
    
    # Filter recurring events if not included
    if not include_recurring:
        events = events.filter(is_recurring=False)
        is_filtered = True
    
    # Apply sorting
    today = date.today()
    if sort == 'upcoming':
        events = events.filter(date__gte=today).order_by('date')
    elif sort == 'recent':
        events = events.order_by('-date')
    elif sort == 'past':
        events = events.filter(date__lt=today).order_by('-date')
    elif sort == 'title':
        events = events.order_by('title')
    else:  # Default sort - show all events by date
        events = events.order_by('date')
    
    # Get upcoming events for sidebar
    upcoming_events = Event.objects.filter(
        Q(created_by=user) | Q(created_by=profile.partner.user) if profile.partner and profile.partner.user else Q(created_by=user),
        date__gte=today
    ).order_by('date')[:5]
    
    # Calculate days until for each event
    for event in events:
        try:
            event.days_until = (event.date - today).days if event.date else 0
        except (TypeError, AttributeError):
            event.days_until = 0
    
    # Calculate days until for upcoming events in sidebar
    for event in upcoming_events:
        try:
            event.days_until = (event.date - today).days if event.date else 0
        except (TypeError, AttributeError):
            event.days_until = 0
    
    # Pagination
    paginator = Paginator(events, 6)  # 6 events per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'events': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'upcoming_events': upcoming_events,
        'is_filtered': is_filtered,
        'event_type': event_type,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'sort': sort,
        'include_recurring': include_recurring
    }
    
    return render(request, 'lovehub/events_list.html', context)

@login_required
def add_event(request):
    """افزودن رویداد جدید"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        event_type = request.POST.get('event_type')
        date_str = request.POST.get('date')
        is_recurring = request.POST.get('is_recurring') == 'on'
        
        # Get notification fields from form
        enable_notification = request.POST.get('enable_notification') == 'on'
        notification_days = request.POST.get('notification_days', 1)
        notification_method = request.POST.get('notification_method', 'app')
        notify_partner = request.POST.get('notify_partner') == 'on'
        
        print(f"DEBUG - Add Event POST data: title={title}, event_type={event_type}, date={date_str}, is_recurring={is_recurring}")
        print(f"DEBUG - Notification data: enable={enable_notification}, days={notification_days}, method={notification_method}, notify_partner={notify_partner}")
        
        # Convert date format from Y/m/d to YYYY-MM-DD
        if date_str and '/' in date_str:
            try:
                year, month, day = date_str.split('/')
                date_str = f"{year}-{month}-{day}"
                print(f"DEBUG - Converted date: {date_str}")
            except ValueError:
                print(f"DEBUG - Date conversion error for: {date_str}")
                messages.error(request, 'فرمت تاریخ نامعتبر است. لطفا به صورت YYYY/MM/DD وارد کنید.')
                return render(request, 'lovehub/add_event.html')
        
        try:
            event = Event.objects.create(
                created_by=request.user,
                title=title,
                description=description,
                event_type=event_type,
                date=date_str,
                is_recurring=is_recurring,
                # Add notification fields
                enable_notification=enable_notification,
                notification_days=notification_days,
                notification_method=notification_method,
                notify_partner=notify_partner
            )
            print(f"DEBUG - Event created successfully: {event.id}")
            
            # Create notification for partner if they exist
            user = request.user
            profile = get_object_or_404(UserProfile, user=user)
            if notify_partner and profile.partner and profile.partner.user:
                partner = profile.partner.user
                # Check if notification settings allow for this
                partner_settings, created = NotificationSettings.objects.get_or_create(
                    user=partner,
                    defaults={
                        'enabled': True,
                        'notify_events': True,
                        'notify_moments': True,
                        'notify_wishes': True,
                        'notify_comments': True,
                        'notify_daily_messages': True
                    }
                )
                
                if partner_settings.enabled and partner_settings.notify_events:
                    try:
                        # Convert to proper date format for notification message
                        if isinstance(event.date, str):
                            # If it's still a string, create a proper date object
                            from datetime import datetime
                            event_date = datetime.strptime(event.date, '%Y-%m-%d').strftime('%Y/%m/%d')
                        else:
                            # If it's already a date object, format it
                            event_date = event.date.strftime('%Y/%m/%d')
                    except Exception as e:
                        # Fallback if date formatting fails
                        print(f"DEBUG - Date formatting error: {str(e)}")
                        event_date = str(event.date)
                        
                    Notification.objects.create(
                        user=partner,
                        title="رویداد جدید ثبت شد",
                        message=f"{user.get_full_name() or user.username} رویداد جدیدی با عنوان '{title}' برای تاریخ {event_date} ثبت کرده است.",
                        notification_type='event',
                        related_object_id=event.id,
                        link=f"/events/{event.id}/"
                    )
            
            messages.success(request, 'رویداد با موفقیت ثبت شد')
            return redirect('events_list')
        except Exception as e:
            print(f"DEBUG - Error creating event: {str(e)}")
            messages.error(request, f'خطا در ایجاد رویداد: {str(e)}')
            return render(request, 'lovehub/add_event.html')
    
    print("DEBUG - Rendering add_event form (GET)")
    return render(request, 'lovehub/add_event.html')

@login_required
def wishes_list(request):
    # Get the user and their profile
    user = request.user
    partner = None
    
    # Safely get user profile and partner
    try:
        profile = UserProfile.objects.get(user=user)
        if profile.partner:
            partner = profile.partner.user
    except UserProfile.DoesNotExist:
        # Handle case where profile doesn't exist
        profile = None
    
    # Get all wishes - both user's and partner's
    if partner:
        wishes_queryset = WishItem.objects.filter(Q(created_by=user) | Q(created_by=partner))
    else:
        wishes_queryset = WishItem.objects.filter(created_by=user)
    
    # Get filter and sort parameters
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'newest')
    
    # Apply status filter
    if status_filter == 'completed':
        wishes_queryset = wishes_queryset.filter(is_completed=True)
    elif status_filter == 'pending':
        wishes_queryset = wishes_queryset.filter(is_completed=False)
    
    # Apply sorting
    if sort_by == 'oldest':
        wishes_queryset = wishes_queryset.order_by('created_at')
    elif sort_by == 'completed-first':
        wishes_queryset = wishes_queryset.order_by('-is_completed', '-created_at')
    elif sort_by == 'pending-first':
        wishes_queryset = wishes_queryset.order_by('is_completed', '-created_at')
    else:  # default to newest
        wishes_queryset = wishes_queryset.order_by('-created_at')
    
    # Calculate statistics
    total_wishes = wishes_queryset.count()
    completed_wishes = wishes_queryset.filter(is_completed=True).count()
    
    # Calculate completion percentage
    completion_percentage = (completed_wishes / total_wishes * 100) if total_wishes > 0 else 0
    
    # Determine if filters are applied
    is_filtered = bool(status_filter or sort_by != 'newest')
    
    context = {
        'wishes': wishes_queryset,
        'total_count': total_wishes,
        'completed_count': completed_wishes,
        'completion_percentage': completion_percentage,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'is_filtered': is_filtered,
    }
    
    return render(request, 'lovehub/wishes_list.html', context)

@login_required
def add_wish(request):
    """افزودن آرزوی جدید"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        is_important = request.POST.get('is_important') == 'on'
        
        if title:
            wish = WishItem.objects.create(
                created_by=request.user,
                title=title,
                description=description,
                is_important=is_important
            )
            
            # ایجاد اعلان برای همسر
            user = request.user
            profile = get_object_or_404(UserProfile, user=user)
            if profile.partner and profile.partner.user:
                partner = profile.partner.user
                # بررسی تنظیمات اعلان‌های همسر
                partner_settings, created = NotificationSettings.objects.get_or_create(
                    user=partner,
                    defaults={
                        'enabled': True,
                        'notify_wishes': True
                    }
                )
                
                if partner_settings.enabled and partner_settings.notify_wishes:
                    Notification.objects.create(
                        user=partner,
                        title="آرزوی جدید ثبت شد",
                        message=f"{user.get_full_name() or user.username} آرزوی جدیدی با عنوان '{title}' ثبت کرده است.",
                        notification_type='wish',
                        link=f'/wishes/',
                        related_object_id=wish.id
                    )
            
            messages.success(request, 'آرزو با موفقیت اضافه شد')
            return redirect('wishes_list')
        else:
            messages.error(request, 'لطفاً عنوان آرزو را وارد کنید')
    
    context = {}
    return render(request, 'lovehub/add_wish.html', context)

@login_required
def toggle_wish_completed(request, pk):
    """تغییر وضعیت انجام آرزو"""
    wish = get_object_or_404(WishItem, pk=pk)
    
    # Ensure user has permission
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    if wish.created_by != user and (not profile.partner or wish.created_by != profile.partner.user):
        messages.error(request, 'شما اجازه تغییر این آرزو را ندارید')
        return redirect('wishes_list')
    
    # Toggle completed status
    wish.is_completed = not wish.is_completed
    wish.save()
    
    status = 'انجام شده' if wish.is_completed else 'انجام نشده'
    messages.success(request, f'وضعیت آرزو به {status} تغییر کرد')
    
    return redirect('wishes_list')

@login_required
def date_ideas(request):
    """ایده‌های قرار"""
    user = request.user
    
    # Filter options
    budget = request.GET.get('budget')
    location = request.GET.get('location')
    mood = request.GET.get('mood')
    
    date_ideas = DateIdea.objects.all()
    
    if budget:
        date_ideas = date_ideas.filter(budget=budget)
    if location:
        date_ideas = date_ideas.filter(location=location)
    if mood:
        date_ideas = date_ideas.filter(mood=mood)
    
    # Get random idea if requested
    random_idea = None
    if 'random' in request.GET:
        if date_ideas.exists():
            random_idea = random.choice(date_ideas)
    
    # Collect user ratings for displaying in template
    user_ratings = {}
    if request.user.is_authenticated:
        ratings = DateIdeaRating.objects.filter(user=request.user)
        for rating in ratings:
            user_ratings[rating.date_idea.id] = rating.liked
    
    context = {
        'date_ideas': date_ideas,
        'random_idea': random_idea,
        'budget_choices': DateIdea.BUDGET_CHOICES,
        'location_choices': DateIdea.LOCATION_CHOICES,
        'mood_choices': DateIdea.MOOD_CHOICES,
        'user_ratings': user_ratings
    }
    
    return render(request, 'lovehub/date_ideas.html', context)

@login_required
def add_date_idea(request):
    """افزودن ایده قرار جدید"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        budget = request.POST.get('budget')
        location = request.POST.get('location')
        mood = request.POST.get('mood')
        
        idea = DateIdea.objects.create(
            created_by=request.user,
            title=title,
            description=description,
            budget=budget,
            location=location,
            mood=mood
        )
        
        messages.success(request, 'ایده قرار با موفقیت ثبت شد')
        return redirect('date_ideas')
        
    context = {
        'budget_choices': DateIdea.BUDGET_CHOICES,
        'location_choices': DateIdea.LOCATION_CHOICES,
        'mood_choices': DateIdea.MOOD_CHOICES
    }
    
    return render(request, 'lovehub/add_date_idea.html', context)

@login_required
def rate_date_idea(request, pk):
    """امتیازدهی به ایده قرار"""
    idea = get_object_or_404(DateIdea, pk=pk)
    user = request.user
    liked = request.POST.get('liked') == 'true'
    
    # Update or create rating
    rating, created = DateIdeaRating.objects.update_or_create(
        date_idea=idea,
        user=user,
        defaults={'liked': liked}
    )
    
    # For AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        like_count = DateIdeaRating.objects.filter(date_idea=idea, liked=True).count()
        return JsonResponse({'liked': liked, 'count': like_count})
    
    return redirect('date_ideas')

@login_required
def gratitude_notes(request):
    """یادداشت‌های قدردانی"""
    user = request.user
    notes = GratitudeNote.objects.filter(created_by=user).order_by('-created_at')
    
    if request.method == 'POST':
        text = request.POST.get('text')
        
        if text:
            GratitudeNote.objects.create(
                created_by=user,
                text=text
            )
            messages.success(request, 'یادداشت قدردانی با موفقیت ثبت شد')
            return redirect('gratitude_notes')
    
    # Get random note if requested
    random_note = None
    if 'random' in request.GET and notes.exists():
        random_note = random.choice(notes)
    
    context = {
        'notes': notes,
        'random_note': random_note
    }
    
    return render(request, 'lovehub/gratitude_notes.html', context)

@login_required
def widget_settings(request):
    """تنظیمات ویجت‌های داشبورد"""
    user = request.user
    widgets = DashboardWidget.objects.filter(user=user).order_by('position')
    
    if request.method == 'POST':
        # Handle saving widget settings
        for widget in widgets:
            widget_id = str(widget.id)
            enabled = request.POST.get(f'enabled_{widget_id}') == 'on'
            position = request.POST.get(f'position_{widget_id}')
            
            widget.is_enabled = enabled
            if position:
                widget.position = int(position)
            widget.save()
        
        messages.success(request, 'تنظیمات ویجت‌ها با موفقیت ذخیره شد')
        return redirect('dashboard')
    
    context = {
        'widgets': widgets
    }
    
    return render(request, 'lovehub/widget_settings.html', context)

@login_required
def app_settings(request):
    """تنظیمات برنامه"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    theme, created = AppTheme.objects.get_or_create(user=user, defaults={'theme': 'default'})
    
    # آماده‌سازی فرم‌ها با مقادیر پیش‌فرض
    account_form = AccountForm(initial={
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'username': user.username,
    })
    
    password_form = PasswordChangeForm()
    
    # دریافت یا ایجاد تنظیمات اعلان
    notification_settings, created_ns = NotificationSettings.objects.get_or_create(
        user=user,
        defaults={
            'enabled': True,
            'notify_events': True,
            'notify_moments': True,
            'notify_wishes': True,
            'notify_comments': True,
            'notification_method': 'app'
        }
    )
    
    notification_form = NotificationForm(initial={
        'enabled': notification_settings.enabled,
        'notify_events': notification_settings.notify_events,
        'notify_moments': notification_settings.notify_moments,
        'notify_wishes': notification_settings.notify_wishes,
        'notify_comments': notification_settings.notify_comments,
        'notification_method': notification_settings.notification_method
    })
    
    # فرم ظاهری
    appearance_form = AppearanceForm(initial={
        'theme': theme.theme,
        'color_palette': getattr(theme, 'color_palette', 'default'),
        'font_size': getattr(theme, 'font_size', 'medium')
    })
    
    # دریافت یا ایجاد تنظیمات حریم خصوصی
    privacy_settings, created_ps = PrivacySettings.objects.get_or_create(
        user=user,
        defaults={
            'activity_tracking': True,
            'data_sharing': True
        }
    )
    
    privacy_form = PrivacyForm(initial={
        'activity_tracking': privacy_settings.activity_tracking,
        'data_sharing': privacy_settings.data_sharing
    })
    
    # تنظیمات رابطه
    relationship_form = RelationshipForm(initial={
        'anniversary_date': profile.relationship_start_date,
        'partner_email': profile.partner.user.email if profile.partner else ''
    })
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'update_account':
            # پردازش فرم حساب کاربری
            account_form = AccountForm(request.POST)
            if account_form.is_valid():
                user.first_name = account_form.cleaned_data['first_name']
                user.last_name = account_form.cleaned_data['last_name']
                user.email = account_form.cleaned_data['email']
                username = account_form.cleaned_data['username']
                
                # بررسی یکتا بودن نام کاربری
                if username != user.username and User.objects.filter(username=username).exists():
                    messages.error(request, 'نام کاربری قبلاً استفاده شده است')
                else:
                    user.username = username
                    user.save()
                    messages.success(request, 'اطلاعات حساب کاربری با موفقیت به‌روزرسانی شد')
            
        elif action == 'change_password':
            # پردازش فرم تغییر رمز عبور
            password_form = PasswordChangeForm(request.POST)
            if password_form.is_valid():
                old_password = password_form.cleaned_data['old_password']
                new_password1 = password_form.cleaned_data['new_password1']
                new_password2 = password_form.cleaned_data['new_password2']
                
                # بررسی صحت رمز عبور فعلی
                if not user.check_password(old_password):
                    messages.error(request, 'رمز عبور فعلی اشتباه است')
                elif new_password1 != new_password2:
                    messages.error(request, 'رمزهای عبور جدید مطابقت ندارند')
                elif len(new_password1) < 8:
                    messages.error(request, 'رمز عبور باید حداقل ۸ کاراکتر باشد')
                else:
                    user.set_password(new_password1)
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, 'رمز عبور با موفقیت تغییر کرد')
                    
        elif action == 'update_notifications':
            # پردازش فرم تنظیمات اعلان‌ها
            notification_form = NotificationForm(request.POST)
            if notification_form.is_valid():
                notification_settings.enabled = notification_form.cleaned_data['enabled']
                notification_settings.notify_events = notification_form.cleaned_data['notify_events']
                notification_settings.notify_moments = notification_form.cleaned_data['notify_moments']
                notification_settings.notify_wishes = notification_form.cleaned_data['notify_wishes']
                notification_settings.notify_comments = notification_form.cleaned_data['notify_comments']
                notification_settings.notification_method = notification_form.cleaned_data['notification_method']
                notification_settings.save()
                messages.success(request, 'تنظیمات اعلان‌ها با موفقیت به‌روزرسانی شد')
                
        elif action == 'update_appearance':
            # پردازش فرم تنظیمات ظاهری
            appearance_form = AppearanceForm(request.POST)
            if appearance_form.is_valid():
                theme.theme = appearance_form.cleaned_data['theme']
                
                # اضافه کردن فیلدهای جدید به مدل اگر وجود نداشته باشد
                if hasattr(theme, 'color_palette'):
                    theme.color_palette = appearance_form.cleaned_data['color_palette']
                
                if hasattr(theme, 'font_size'):
                    theme.font_size = appearance_form.cleaned_data['font_size']
                
                theme.save()
                messages.success(request, 'تنظیمات ظاهری با موفقیت به‌روزرسانی شد')
                
        elif action == 'update_privacy':
            # پردازش فرم تنظیمات حریم خصوصی
            privacy_form = PrivacyForm(request.POST)
            if privacy_form.is_valid():
                privacy_settings.activity_tracking = privacy_form.cleaned_data['activity_tracking']
                privacy_settings.data_sharing = privacy_form.cleaned_data['data_sharing']
                privacy_settings.save()
                messages.success(request, 'تنظیمات حریم خصوصی با موفقیت به‌روزرسانی شد')
                
        elif action == 'update_relationship':
            # پردازش فرم تنظیمات رابطه
            relationship_form = RelationshipForm(request.POST)
            if relationship_form.is_valid():
                # ذخیره تنظیمات رابطه
                
                # تنظیم تاریخ رابطه
                anniversary_date = relationship_form.cleaned_data['anniversary_date']
                if anniversary_date:
                    try:
                        year, month, day = anniversary_date.split('/')
                        profile.relationship_start_date = f"{year}-{month}-{day}"
                    except ValueError:
                        messages.error(request, 'فرمت تاریخ شروع رابطه نامعتبر است')
                
                # تنظیم همسر
                partner_email = relationship_form.cleaned_data['partner_email']
                if partner_email and partner_email != user.email:
                    try:
                        partner_user = User.objects.get(email=partner_email)
                        partner_profile = UserProfile.objects.get(user=partner_user)
                        
                        profile.partner = partner_profile
                        profile.save()
                        
                        messages.success(request, 'تنظیمات رابطه با موفقیت به‌روزرسانی شد')
                    except (User.DoesNotExist, UserProfile.DoesNotExist):
                        messages.error(request, 'کاربری با این ایمیل یافت نشد')
                else:
                    profile.save()
                    messages.success(request, 'تنظیمات رابطه با موفقیت به‌روزرسانی شد')
                
        elif action == 'update_widgets':
            # پردازش فرم تنظیمات ویجت‌ها
            widget_form = WidgetForm(request.POST, available_widgets=available_widgets)
            if widget_form.is_valid():
                # غیرفعال کردن همه ویجت‌های کاربر
                UserWidget.objects.filter(user=user).update(is_active=False, order=0)
                
                # فعال کردن ویجت‌های انتخاب شده
                active_widget_ids = widget_form.cleaned_data['active_widgets']
                for widget_id in active_widget_ids:
                    try:
                        widget = DashboardWidget.objects.get(id=widget_id, user=user)
                        user_widget, created = UserWidget.objects.get_or_create(
                            user=user,
                            widget=widget,
                            defaults={'is_active': True}
                        )
                        if not created:
                            user_widget.is_active = True
                            user_widget.save()
                    except DashboardWidget.DoesNotExist:
                        pass
                
                # تنظیم ترتیب ویجت‌ها
                widget_order = widget_form.cleaned_data['widget_order']
                if widget_order:
                    order_ids = widget_order.split(',')
                    for i, widget_id in enumerate(order_ids):
                        try:
                            widget = DashboardWidget.objects.get(id=int(widget_id), user=user)
                            user_widget = UserWidget.objects.get(user=user, widget=widget)
                            user_widget.order = i + 1
                            user_widget.save()
                        except (DashboardWidget.DoesNotExist, UserWidget.DoesNotExist, ValueError):
                            pass
                
                messages.success(request, 'تنظیمات ویجت‌ها با موفقیت به‌روزرسانی شد')
        
        # بازگشت به صفحه تنظیمات
        return redirect('app_settings')
    
    # Format dates for display
    if profile.birth_date:
        profile.birth_date_display = profile.birth_date.strftime('%Y/%m/%d')
    
    if profile.relationship_start_date:
        profile.relationship_start_date_display = profile.relationship_start_date.strftime('%Y/%m/%d')
    
    # ویجت‌های کاربر
    available_widgets = DashboardWidget.objects.filter(user=user)
    
    # بررسی UserWidget برای کاربر
    active_widgets = []
    for widget in available_widgets:
        user_widget, created = UserWidget.objects.get_or_create(
            user=user,
            widget=widget,
            defaults={'is_active': False, 'order': 0}
        )
        if user_widget.is_active:
            active_widgets.append(widget)
    
    # مرتب‌سازی ویجت‌های فعال بر اساس ترتیب
    active_widgets.sort(key=lambda w: UserWidget.objects.get(user=user, widget=w).order)
    
    # فرم ویجت‌ها
    widget_form = WidgetForm(
        available_widgets=available_widgets,
        initial={
            'active_widgets': [widget.id for widget in active_widgets],
            'widget_order': ','.join(str(widget.id) for widget in active_widgets)
        }
    )
    
    context = {
        'profile': profile,
        'theme': theme,
        'theme_choices': AppTheme.THEME_CHOICES,
        'account_form': account_form,
        'password_form': password_form,
        'notification_form': notification_form,
        'appearance_form': appearance_form,
        'privacy_form': privacy_form,
        'relationship_form': relationship_form,
        'available_widgets': available_widgets,
        'active_widgets': active_widgets,
        'widget_form': widget_form,
    }
    
    return render(request, 'lovehub/settings.html', context)

@login_required
def map_view(request):
    """نمایش لحظات روی نقشه"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # Get moments that have location data
    if profile.partner and profile.partner.user:
        moments = Moment.objects.filter(
            Q(created_by=user) | Q(created_by=profile.partner.user),
            latitude__isnull=False,
            longitude__isnull=False
        ).order_by('-date')
    else:
        moments = Moment.objects.filter(
            created_by=user,
            latitude__isnull=False,
            longitude__isnull=False
        ).order_by('-date')
    
    context = {
        'moments': moments,
    }
    
    return render(request, 'lovehub/map_view.html', context)

@login_required
def calendar_view(request):
    """نمایش تقویم"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # Force cache refresh if coming from event deletion
    force_refresh = request.session.pop('calendar_refresh', False)
    
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)
    
    try:
        # Convert to integers
        year = int(year)
        month = int(month)
    except (ValueError, TypeError):
        # Default to current date if invalid
        year = timezone.now().year
        month = timezone.now().month
    
    # Get events for this month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # Get events and moments for calendar
    today = date.today()
    
    # Create a list to store valid event IDs
    valid_event_ids = []
    
    # First get all existing events from database
    all_events = Event.objects.all().values_list('id', flat=True)
    
    if profile.partner and profile.partner.user:
        # Get events that exist in the database
        events = Event.objects.filter(
            Q(created_by=user) | Q(created_by=profile.partner.user),
            date__gte=start_date,
            date__lte=end_date,
            id__in=all_events  # Only include events that still exist
        ).select_related('created_by')
        
        # Store event IDs
        valid_event_ids = list(events.values_list('id', flat=True))
        
        moments = Moment.objects.filter(
            Q(created_by=user) | Q(created_by=profile.partner.user),
            date__date__gte=start_date,
            date__date__lte=end_date
        ).select_related('created_by')
    else:
        events = Event.objects.filter(
            created_by=user,
            date__gte=start_date,
            date__lte=end_date,
            id__in=all_events  # Only include events that still exist
        ).select_related('created_by')
        
        # Store event IDs
        valid_event_ids = list(events.values_list('id', flat=True))
        
        moments = Moment.objects.filter(
            created_by=user,
            date__date__gte=start_date,
            date__date__lte=end_date
        ).select_related('created_by')
    
    # Get upcoming events for sidebar (next 30 days)
    upcoming_events = Event.objects.filter(
        Q(created_by=user) | Q(created_by=profile.partner.user) if profile.partner and profile.partner.user else Q(created_by=user),
        date__gte=today,
        date__lte=today + timedelta(days=30),
        id__in=all_events  # Only include events that still exist
    ).order_by('date')[:5]
    
    # Add upcoming events to valid IDs
    valid_event_ids.extend(list(upcoming_events.values_list('id', flat=True)))
    
    # Remove duplicates
    valid_event_ids = list(set(valid_event_ids))
    
    # Delete notifications for events that no longer exist
    Notification.objects.filter(
        user=user,
        notification_type='event'
    ).exclude(
        related_object_id__in=valid_event_ids
    ).delete()
    
    # Calculate days until for each event
    for event in events:
        try:
            event.days_until = (event.date - today).days if event.date else 0
        except (TypeError, AttributeError):
            event.days_until = 0
    
    # Calculate days until for upcoming events
    for event in upcoming_events:
        try:
            event.days_until = (event.date - today).days if event.date else 0
        except (TypeError, AttributeError):
            event.days_until = 0
    
    # Organize data by day
    calendar_data = {}
    for event in events:
        try:
            day = event.date.day
            if day not in calendar_data:
                calendar_data[day] = {'events': [], 'moments': []}
            calendar_data[day]['events'].append(event)
        except (AttributeError, TypeError):
            # Skip events with invalid dates
            continue
    
    for moment in moments:
        try:
            day = moment.date.date().day
            if day not in calendar_data:
                calendar_data[day] = {'events': [], 'moments': []}
            calendar_data[day]['moments'].append(moment)
        except (AttributeError, TypeError):
            # Skip moments with invalid dates
            continue
    
    context = {
        'calendar_data': calendar_data,
        'year': year,
        'month': month,
        'upcoming_events': upcoming_events,
        'force_refresh': force_refresh,
        'events': events,  # Pass events directly
        'moments': moments  # Pass moments directly
    }
    
    return render(request, 'lovehub/calendar_view.html', context)

@login_required
def notifications(request):
    """نمایش اعلان‌های کاربر"""
    user = request.user
    filter_type = request.GET.get('filter', 'all')
    
    # Filter notifications based on type
    if filter_type == 'unread':
        notifications_list = Notification.objects.filter(user=user, is_read=False)
    elif filter_type in ['event', 'moment', 'wish', 'comment', 'system', 'daily_message']:
        notifications_list = Notification.objects.filter(user=user, notification_type=filter_type)
    else:
        # Default to showing all notifications
        notifications_list = Notification.objects.filter(user=user)
    
    # Calculate notification statistics
    total_count = Notification.objects.filter(user=user).count()
    if total_count > 0:
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        unread_percent = int((unread_count / total_count) * 100) if total_count > 0 else 0
        
        event_count = Notification.objects.filter(user=user, notification_type='event').count()
        event_percent = int((event_count / total_count) * 100) if total_count > 0 else 0
        
        moment_count = Notification.objects.filter(user=user, notification_type='moment').count()
        moment_percent = int((moment_count / total_count) * 100) if total_count > 0 else 0
        
        wish_count = Notification.objects.filter(user=user, notification_type='wish').count()
        wish_percent = int((wish_count / total_count) * 100) if total_count > 0 else 0
        
        comment_count = Notification.objects.filter(user=user, notification_type='comment').count()
        comment_percent = int((comment_count / total_count) * 100) if total_count > 0 else 0
        
        system_count = Notification.objects.filter(user=user, notification_type='system').count()
        system_percent = int((system_count / total_count) * 100) if total_count > 0 else 0
        
        daily_message_count = Notification.objects.filter(user=user, notification_type='daily_message').count()
        daily_message_percent = int((daily_message_count / total_count) * 100) if total_count > 0 else 0
    else:
        unread_count = unread_percent = event_count = event_percent = 0
        moment_count = moment_percent = wish_count = wish_percent = 0 
        comment_count = comment_percent = system_count = system_percent = 0
        daily_message_count = daily_message_percent = 0
    
    # Paginate results
    paginator = Paginator(notifications_list, 10)  # 10 notifications per page
    page_number = request.GET.get('page')
    notifications = paginator.get_page(page_number)
    
    context = {
        'notifications': notifications,
        'filter': filter_type,
        'unread_count': unread_count,
        'unread_percent': unread_percent,
        'event_count': event_count,
        'event_percent': event_percent,
        'moment_count': moment_count,
        'moment_percent': moment_percent,
        'wish_count': wish_count,
        'wish_percent': wish_percent,
        'comment_count': comment_count,
        'comment_percent': comment_percent,
        'system_count': system_count,
        'system_percent': system_percent,
        'daily_message_count': daily_message_count,
        'daily_message_percent': daily_message_percent
    }
    
    return render(request, 'lovehub/notifications.html', context)

@login_required
def mark_all_read(request):
    """علامت گذاری همه اعلان‌ها به عنوان خوانده شده"""
    if request.method == 'POST':
        # Mark all unread notifications as read
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'همه اعلان‌ها به عنوان خوانده شده علامت‌گذاری شدند')
    
    return redirect('notifications')

@login_required
def mark_notification_read(request, notification_id):
    """علامت گذاری یک اعلان به عنوان خوانده شده"""
    if request.method == 'POST':
        # Mark specific notification as read
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        messages.success(request, 'اعلان به عنوان خوانده شده علامت‌گذاری شد')
    
    return redirect('notifications')

@login_required
def profile(request):
    """نمایش و ویرایش پروفایل کاربر"""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Handle profile update
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        birth_date = request.POST.get('birth_date')
        profile_image = request.FILES.get('profile_image')
        
        # Update user info
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.save()
        
        # Update profile info
        if birth_date:
            profile.birth_date = birth_date
        if profile_image:
            profile.avatar = profile_image
        profile.save()
        
        messages.success(request, 'پروفایل با موفقیت بروزرسانی شد')
        return redirect('profile')
    
    context = {
        'user': user,
        'profile': profile
    }
    
    return render(request, 'lovehub/profile.html', context)

@login_required
def edit_profile(request):
    """ویرایش پروفایل کاربر"""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Handle profile update
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        bio = request.POST.get('bio')
        birth_date_str = request.POST.get('birth_date')
        relationship_start_date_str = request.POST.get('relationship_start_date')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        interests = request.POST.get('interests')
        favorite_food = request.POST.get('favorite_food')
        favorite_color = request.POST.get('favorite_color')
        profile_image = request.FILES.get('profile_image')
        
        # Update user info
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if email:
            user.email = email
        user.save()
        
        # Update profile info
        if bio:
            profile.bio = bio
            
        # Handle date formats
        if birth_date_str:
            try:
                # تلاش برای تبدیل رشته به تاریخ با فرمت مناسب
                if '/' in birth_date_str:  # فرمت فارسی مثل 1402/01/15
                    year, month, day = map(int, birth_date_str.split('/'))
                    birth_date = date(year, month, day)
                else:  # فرمت میلادی مثل 2023-05-20
                    birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                profile.birth_date = birth_date
            except (ValueError, TypeError):
                messages.error(request, 'فرمت تاریخ تولد نامعتبر است. لطفاً از فرمت YYYY/MM/DD استفاده کنید.')
                
        if relationship_start_date_str:
            try:
                # تلاش برای تبدیل رشته به تاریخ با فرمت مناسب
                if '/' in relationship_start_date_str:  # فرمت فارسی مثل 1402/01/15
                    year, month, day = map(int, relationship_start_date_str.split('/'))
                    relationship_start_date = date(year, month, day)
                else:  # فرمت میلادی مثل 2023-05-20
                    relationship_start_date = datetime.strptime(relationship_start_date_str, '%Y-%m-%d').date()
                profile.relationship_start_date = relationship_start_date
            except (ValueError, TypeError):
                messages.error(request, 'فرمت تاریخ شروع رابطه نامعتبر است. لطفاً از فرمت YYYY/MM/DD استفاده کنید.')
            
        if phone:
            profile.phone = phone
        if address:
            profile.address = address
        if interests:
            profile.interests = interests
        if favorite_food:
            profile.favorite_food = favorite_food
        if favorite_color:
            profile.favorite_color = favorite_color
        if profile_image:
            profile.avatar = profile_image
        profile.save()
        
        messages.success(request, 'پروفایل با موفقیت بروزرسانی شد')
        return redirect('profile')
    
    context = {
        'user': user,
        'profile': profile
    }
    
    return render(request, 'lovehub/edit_profile.html', context)

@login_required
def invite_partner(request):
    """ارسال دعوت به همسر"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # Check if user already has a partner
    if profile.partner:
        messages.info(request, 'شما قبلا به یک همسر متصل شده‌اید')
        return redirect('dashboard')
    
    # Generate invitation code (this would be a UUID in production)
    invite_code = "INVITE-" + str(user.id) + "-" + str(int(timezone.now().timestamp()))
    
    # In a real app, save this code to a model
    # Here we're just passing it to the template
    
    context = {
        'invite_code': invite_code,
        'user': user,
        'profile': profile
    }
    
    return render(request, 'lovehub/invite_partner.html', context)

@login_required
def accept_invite(request, code=None):
    """پذیرش دعوت همسر"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # Check if user already has a partner
    if profile.partner:
        context = {
            'already_connected': True,
            'partner': profile.partner.user
        }
        return render(request, 'lovehub/accept_invite.html', context)
    
    # If the code was submitted via POST form instead of URL
    if request.method == 'POST':
        form_code = request.POST.get('invite_code')
        if form_code:
            code = form_code
    
    # In a real app, validate the invite code from a model
    # Here we're just checking the format
    if not code or not code.startswith("INVITE-"):
        context = {
            'invite_error': 'invalid'
        }
        return render(request, 'lovehub/accept_invite.html', context)
    
    # Extract the user ID from the invite code
    try:
        inviter_id = int(code.split('-')[1])
        inviter = get_object_or_404(User, id=inviter_id)
        inviter_profile = get_object_or_404(UserProfile, user=inviter)
    except (ValueError, IndexError):
        context = {
            'invite_error': 'invalid'
        }
        return render(request, 'lovehub/accept_invite.html', context)
    
    # Prevent self-invitation
    if inviter.id == user.id:
        context = {
            'invite_error': 'self'
        }
        return render(request, 'lovehub/accept_invite.html', context)
    
    # Handle POST request (accept invitation)
    if request.method == 'POST':
        # Connect the two profiles
        profile.partner = inviter_profile
        profile.save()
        
        inviter_profile.partner = profile
        inviter_profile.save()
        
        messages.success(request, f'شما و {inviter.get_full_name() or inviter.username} اکنون به هم متصل شده‌اید')
        return redirect('dashboard')
    
    # Display the invitation details
    context = {
        'inviter': inviter,
        'invite_code': code
    }
    
    return render(request, 'lovehub/accept_invite.html', context)

@login_required
def track_mood(request):
    """ثبت و پیگیری حال و هوا"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # Get today's mood if exists
    today = timezone.now().date()
    today_mood = DailyMood.objects.filter(user=user, date=today).first()
    
    # Get partner's mood if exists
    partner_mood = None
    if profile.partner and profile.partner.user:
        partner_mood = DailyMood.objects.filter(
            user=profile.partner.user,
            date=today
        ).first()
    
    # Get mood history for the past 14 days
    two_weeks_ago = today - timedelta(days=14)
    mood_history = DailyMood.objects.filter(
        user=user,
        date__gte=two_weeks_ago,
        date__lte=today
    ).order_by('date')
    
    partner_mood_history = []
    if profile.partner and profile.partner.user:
        partner_mood_history = DailyMood.objects.filter(
            user=profile.partner.user,
            date__gte=two_weeks_ago,
            date__lte=today
        ).order_by('date')
    
    if request.method == 'POST':
        mood = request.POST.get('mood')
        note = request.POST.get('note')
        
        if mood:
            # Create or update today's mood
            daily_mood, created = DailyMood.objects.update_or_create(
                user=user,
                date=today,
                defaults={
                    'mood': mood,
                    'note': note
                }
            )
            
            if created:
                messages.success(request, 'حال و هوای امروز شما با موفقیت ثبت شد')
            else:
                messages.success(request, 'حال و هوای امروز شما با موفقیت بروزرسانی شد')
                
            return redirect('track_mood')
    
    context = {
        'today_mood': today_mood,
        'partner_mood': partner_mood,
        'mood_history': mood_history,
        'partner_mood_history': partner_mood_history,
        'today': today,
        'profile': profile
    }
    
    return render(request, 'lovehub/track_mood.html', context)

@login_required
def notes_list(request):
    """نمایش لیست یادداشت‌ها"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # Filter parameters
    filter_type = request.GET.get('type', 'all')  # all, personal, shared, important
    sort_by = request.GET.get('sort', 'newest')  # newest, oldest, title
    
    # Start with all notes from the user
    notes = Note.objects.filter(created_by=user)
    
    # If user has a partner, also get shared notes from the partner
    if profile.partner and profile.partner.user and filter_type != 'personal':
        partner_notes = Note.objects.filter(
            created_by=profile.partner.user,
            is_shared=True
        )
        notes = notes | partner_notes
    
    # Apply filters
    if filter_type == 'personal':
        notes = notes.filter(created_by=user, is_shared=False)
    elif filter_type == 'shared':
        notes = notes.filter(is_shared=True)
    elif filter_type == 'important':
        notes = notes.filter(is_important=True)
    
    # Apply sorting
    if sort_by == 'newest':
        notes = notes.order_by('-created_at')
    elif sort_by == 'oldest':
        notes = notes.order_by('created_at')
    elif sort_by == 'title':
        notes = notes.order_by('title')
    
    context = {
        'notes': notes,
        'filter_type': filter_type,
        'sort_by': sort_by,
        'profile': profile
    }
    
    return render(request, 'lovehub/notes_list.html', context)

@login_required
def add_note(request):
    """افزودن یادداشت جدید"""
    user = request.user
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        is_shared = request.POST.get('is_shared') == 'on'
        is_important = request.POST.get('is_important') == 'on'
        
        note = Note.objects.create(
            created_by=user,
            title=title,
            content=content,
            is_shared=is_shared,
            is_important=is_important
        )
        
        messages.success(request, 'یادداشت با موفقیت ایجاد شد')
        return redirect('note_detail', pk=note.pk)
    
    context = {
        'is_editing': False
    }
    
    return render(request, 'lovehub/add_note.html', context)

@login_required
def note_detail(request, pk):
    """نمایش جزئیات یادداشت"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    note = get_object_or_404(Note, pk=pk)
    
    # Check if user is authorized to view this note
    if note.created_by != user and (not note.is_shared or not profile.partner or note.created_by != profile.partner.user):
        messages.error(request, 'شما دسترسی به این یادداشت ندارید')
        return redirect('notes_list')
    
    # Handle editing
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'edit':
            title = request.POST.get('title')
            content = request.POST.get('content')
            is_shared = request.POST.get('is_shared') == 'on'
            is_important = request.POST.get('is_important') == 'on'
            
            # Ensure only the creator can edit
            if note.created_by != user:
                messages.error(request, 'فقط سازنده یادداشت می‌تواند آن را ویرایش کند')
                return redirect('note_detail', pk=note.pk)
            
            note.title = title
            note.content = content
            note.is_shared = is_shared
            note.is_important = is_important
            note.save()
            
            messages.success(request, 'یادداشت با موفقیت بروزرسانی شد')
        
        elif action == 'delete':
            # Ensure only the creator can delete
            if note.created_by != user:
                messages.error(request, 'فقط سازنده یادداشت می‌تواند آن را حذف کند')
                return redirect('note_detail', pk=note.pk)
            
            note.delete()
            messages.success(request, 'یادداشت با موفقیت حذف شد')
            return redirect('notes_list')
    
    context = {
        'note': note,
        'is_creator': note.created_by == user
    }
    
    return render(request, 'lovehub/note_detail.html', context)

@login_required
def edit_note(request, pk):
    """ویرایش یادداشت"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    note = get_object_or_404(Note, pk=pk)
    
    # Check if user is authorized to edit this note
    if note.created_by != user:
        messages.error(request, 'شما اجازه ویرایش این یادداشت را ندارید')
        return redirect('notes_list')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        is_shared = 'is_shared' in request.POST
        is_important = 'is_important' in request.POST
        
        if title and content:
            note.title = title
            note.content = content
            note.is_shared = is_shared
            note.is_important = is_important
            note.updated_at = timezone.now()
            note.save()
            
            messages.success(request, 'یادداشت با موفقیت ویرایش شد')
            return redirect('note_detail', pk=note.pk)
    
    context = {
        'form': {
            'title': {'value': note.title},
            'content': {'value': note.content},
            'is_shared': {'value': note.is_shared},
            'is_important': {'value': note.is_important}
        },
        'note': note,
        'edit_mode': True
    }
    
    return render(request, 'lovehub/add_note.html', context)

@login_required
def send_invite_email(request):
    """ارسال دعوت‌نامه از طریق ایمیل"""
    if request.method == 'POST':
        email = request.POST.get('email')
        invite_code = request.POST.get('invite_code')
        
        if email and invite_code:
            # In a real app, you would send an email here
            # For now, we'll just show a success message
            
            messages.success(request, f'دعوت‌نامه به آدرس {email} ارسال شد')
            return redirect('invite_partner')
        else:
            messages.error(request, 'لطفاً آدرس ایمیل را وارد کنید')
            return redirect('invite_partner')
            
    return redirect('invite_partner')

@login_required
def generate_new_invite_code(request):
    """ایجاد کد دعوت جدید"""
    if request.method == 'POST':
        user = request.user
        
        # Generate a new invitation code
        invite_code = "INVITE-" + str(user.id) + "-" + str(int(timezone.now().timestamp()))
        
        # In a real app, update this code in the database
        
        messages.success(request, 'کد دعوت جدید با موفقیت ایجاد شد')
        return redirect('invite_partner')
        
    return redirect('invite_partner')

@login_required
def event_detail(request, pk):
    """نمایش جزئیات رویداد"""
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    event = get_object_or_404(Event, pk=pk)
    
    # Check if user is authorized to view this event
    if event.created_by != user and (not profile.partner or event.created_by != profile.partner.user):
        messages.error(request, 'شما دسترسی به این رویداد را ندارید')
        return redirect('events_list')
    
    # Calculate days until event
    today = date.today()
    days_until = (event.date - today).days
    
    # Calculate progress percentage for countdown
    if days_until > 0:
        if event.is_recurring and event.date.year > today.year:
            # For recurring events, calculate based on previous occurrence
            previous_date = date(today.year, event.date.month, event.date.day)
            if previous_date < today:
                next_date = date(today.year + 1, event.date.month, event.date.day)
            else:
                next_date = previous_date
                previous_date = date(today.year - 1, event.date.month, event.date.day)
            
            total_days = (next_date - previous_date).days
            days_passed = (today - previous_date).days
            progress_percentage = min(100, max(0, (days_passed / total_days) * 100))
        else:
            # For normal future events
            progress_percentage = 0
    else:
        # For past events
        progress_percentage = 100
    
    # Add event data to context
    event.days_until = days_until
    event.progress_percentage = progress_percentage
    
    context = {
        'event': event,
        'is_creator': event.created_by == user
    }
    
    return render(request, 'lovehub/event_detail.html', context)

@login_required
def edit_event(request, pk):
    """ویرایش رویداد"""
    user = request.user
    event = get_object_or_404(Event, pk=pk)
    
    # Check if user is authorized to edit this event
    if event.created_by != user:
        messages.error(request, 'فقط سازنده رویداد می‌تواند آن را ویرایش کند')
        return redirect('event_detail', pk=event.pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        event_type = request.POST.get('event_type')
        date_str = request.POST.get('date')
        is_recurring = request.POST.get('is_recurring') == 'on'
        
        # Convert date format from Y/m/d to YYYY-MM-DD
        if date_str and '/' in date_str:
            try:
                year, month, day = date_str.split('/')
                date_str = f"{year}-{month}-{day}"
            except ValueError:
                messages.error(request, 'فرمت تاریخ نامعتبر است. لطفا به صورت YYYY/MM/DD وارد کنید.')
                return render(request, 'lovehub/edit_event.html', {'event': event})
        
        # Update event
        event.title = title
        event.description = description
        event.event_type = event_type
        event.date = date_str
        event.is_recurring = is_recurring
        event.save()
        
        messages.success(request, 'رویداد با موفقیت بروزرسانی شد')
        return redirect('event_detail', pk=event.pk)
    
    # Format the date from YYYY-MM-DD to Y/m/d for display in the template
    date_display = event.date.strftime('%Y/%m/%d')
    event.date_display = date_display
    
    context = {
        'event': event,
        'is_editing': True
    }
    
    return render(request, 'lovehub/edit_event.html', context)

@login_required
def delete_event(request, pk):
    """حذف رویداد"""
    user = request.user
    event = get_object_or_404(Event, pk=pk)
    
    # Check if user is authorized to delete this event
    if event.created_by != user:
        messages.error(request, 'فقط سازنده رویداد می‌تواند آن را حذف کند')
        return redirect('event_detail', pk=event.pk)
    
    if request.method == 'POST':
        event_id = event.id  # Store ID before deletion
        event_date = event.date  # Store date for refresh
        
        # First delete any notifications related to this event
        Notification.objects.filter(notification_type='event', related_object_id=event.id).delete()
        
        # Now delete the event
        event.delete()
        
        # Force refresh of calendar if user navigates back to it
        request.session['calendar_refresh'] = True
        
        # Success message
        messages.success(request, 'رویداد با موفقیت حذف شد')
        
        # Decide where to redirect based on referrer
        referer = request.META.get('HTTP_REFERER', '')
        if 'calendar' in referer:
            return redirect('calendar_view')
        else:
            return redirect('events_list')
    
    return redirect('event_detail', pk=event.pk)

@login_required
def enable_notification(request, pk):
    """فعال/غیرفعال کردن اعلان برای یک رویداد"""
    user = request.user
    event = get_object_or_404(Event, pk=pk)
    
    # Check if user is authorized to modify this event's notifications
    profile = get_object_or_404(UserProfile, user=user)
    if event.created_by != user and (not profile.partner or event.created_by != profile.partner.user):
        messages.error(request, 'شما دسترسی به تنظیمات این رویداد را ندارید')
        return redirect('event_detail', pk=event.pk)
    
    if request.method == 'POST':
        # Get notification settings
        enable = request.POST.get('enable_notification') == 'on'
        try:
            days_before = int(request.POST.get('notification_days', 1))
        except ValueError:
            days_before = 1
        notify_method = request.POST.get('notification_method', 'app')
        notify_partner = request.POST.get('notify_partner') == 'on'
        
        # Update event notification settings directly in the Event model
        event.enable_notification = enable
        event.notification_days = days_before
        event.notification_method = notify_method
        event.notify_partner = notify_partner
        event.save()
        
        messages.success(request, 'تنظیمات اعلان با موفقیت ذخیره شد')
        return redirect('event_detail', pk=event.pk)
    
    # Display notification settings form
    context = {
        'event': event,
    }
    return render(request, 'lovehub/event_notification.html', context)

@login_required
def edit_moment(request, pk):
    """ویرایش لحظه"""
    user = request.user
    moment = get_object_or_404(Moment, pk=pk)
    
    # Check if user is authorized to edit this moment
    if moment.created_by != user:
        messages.error(request, 'فقط سازنده لحظه می‌تواند آن را ویرایش کند')
        return redirect('moment_detail', pk=moment.pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        location_name = request.POST.get('location_name')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        mood_tags = request.POST.get('mood_tags')
        
        # Update moment fields
        moment.title = title
        moment.description = description
        moment.location_name = location_name
        moment.mood_tags = mood_tags
        
        # Only update coordinates if both are provided
        if latitude and longitude:
            try:
                moment.latitude = float(latitude)
                moment.longitude = float(longitude)
            except ValueError:
                pass
                
        # Handle image upload if provided
        if 'image' in request.FILES:
            moment.image = request.FILES['image']
            
        # Handle audio upload if provided
        if 'audio' in request.FILES:
            moment.audio = request.FILES['audio']
            
        moment.save()
        messages.success(request, 'لحظه با موفقیت بروزرسانی شد')
        return redirect('moment_detail', pk=moment.pk)
    
    context = {
        'moment': moment,
        'is_editing': True
    }
    
    return render(request, 'lovehub/edit_moment.html', context)

@login_required
def delete_moment(request, pk):
    """حذف لحظه"""
    user = request.user
    moment = get_object_or_404(Moment, pk=pk)
    
    # Check if user is authorized to delete this moment
    if moment.created_by != user:
        messages.error(request, 'فقط سازنده لحظه می‌تواند آن را حذف کند')
        return redirect('moment_detail', pk=moment.pk)
    
    if request.method == 'POST':
        moment.delete()
        messages.success(request, 'لحظه با موفقیت حذف شد')
        return redirect('moments_list')
    
    return redirect('moment_detail', pk=moment.pk)

@login_required
def add_comment(request, pk):
    """افزودن نظر به لحظه"""
    moment = get_object_or_404(Moment, pk=pk)
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # Check if user is authorized to comment on this moment
    if moment.created_by != user and (not profile.partner or moment.created_by != profile.partner.user):
        messages.error(request, 'شما اجازه نظر دادن به این لحظه را ندارید')
        return redirect('moments_list')
    
    if request.method == 'POST':
        text = request.POST.get('text')
        
        if text:
            MomentComment.objects.create(
                moment=moment,
                user=user,
                text=text
            )
            messages.success(request, 'نظر شما با موفقیت ثبت شد')
        
    return redirect('moment_detail', pk=moment.pk)

@login_required
def date_idea_detail(request, pk):
    """نمایش جزئیات ایده قرار"""
    idea = get_object_or_404(DateIdea, pk=pk)
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # Check if user has rated this idea
    user_rating = DateIdeaRating.objects.filter(date_idea=idea, user=user).first()
    
    # Get all ratings
    like_count = DateIdeaRating.objects.filter(date_idea=idea, liked=True).count()
    dislike_count = DateIdeaRating.objects.filter(date_idea=idea, liked=False).count()
    
    context = {
        'idea': idea,
        'user_rating': user_rating,
        'like_count': like_count,
        'dislike_count': dislike_count,
        'is_creator': idea.created_by == user,
        'profile': profile
    }
    
    return render(request, 'lovehub/date_idea_detail.html', context)

@login_required
def edit_date_idea(request, pk):
    """ویرایش ایده قرار"""
    user = request.user
    idea = get_object_or_404(DateIdea, pk=pk)
    
    # Check if user is authorized to edit this idea
    if idea.created_by != user:
        messages.error(request, 'فقط سازنده ایده قرار می‌تواند آن را ویرایش کند')
        return redirect('date_idea_detail', pk=idea.pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        budget = request.POST.get('budget')
        location = request.POST.get('location')
        mood = request.POST.get('mood')
        
        if title and description:
            idea.title = title
            idea.description = description
            idea.budget = budget
            idea.location = location
            idea.mood = mood
            idea.save()
            
            messages.success(request, 'ایده قرار با موفقیت ویرایش شد')
            return redirect('date_idea_detail', pk=idea.pk)
        else:
            messages.error(request, 'لطفا عنوان و توضیحات را وارد کنید')
    
    context = {
        'idea': idea,
        'budget_choices': DateIdea.BUDGET_CHOICES,
        'location_choices': DateIdea.LOCATION_CHOICES,
        'mood_choices': DateIdea.MOOD_CHOICES,
        'edit_mode': True
    }
    
    return render(request, 'lovehub/add_date_idea.html', context)

@login_required
def delete_note(request, pk):
    """حذف یادداشت"""
    user = request.user
    note = get_object_or_404(Note, pk=pk)
    
    # Check if user is authorized to delete this note
    if note.created_by != user:
        messages.error(request, 'فقط سازنده یادداشت می‌تواند آن را حذف کند')
        return redirect('note_detail', pk=note.pk)
    
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'یادداشت با موفقیت حذف شد')
        return redirect('notes_list')
    
    return redirect('note_detail', pk=pk)

@login_required
def delete_date_idea(request, pk):
    """حذف ایده قرار"""
    user = request.user
    idea = get_object_or_404(DateIdea, pk=pk)
    
    # Check if user is authorized to delete this idea
    if idea.created_by != user:
        messages.error(request, 'فقط سازنده ایده قرار می‌تواند آن را حذف کند')
        return redirect('date_idea_detail', pk=idea.pk)
    
    if request.method == 'POST':
        idea.delete()
        messages.success(request, 'ایده قرار با موفقیت حذف شد')
        return redirect('date_ideas')
    
    return redirect('date_idea_detail', pk=idea.pk)

@login_required
def edit_wish(request, pk):
    """ویرایش آرزو"""
    user = request.user
    wish = get_object_or_404(WishItem, pk=pk)
    
    # Check if user is authorized to edit this wish
    if wish.created_by != user:
        messages.error(request, 'فقط سازنده آرزو می‌تواند آن را ویرایش کند')
        return redirect('wishes_list')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        is_important = request.POST.get('is_important') == 'on'
        
        if title:
            wish.title = title
            wish.description = description
            wish.is_important = is_important
            wish.save()
            
            messages.success(request, 'آرزو با موفقیت ویرایش شد')
            return redirect('wishes_list')
        else:
            messages.error(request, 'لطفا عنوان آرزو را وارد کنید')
    
    context = {
        'form': {
            'title': {'value': wish.title},
            'description': {'value': wish.description},
            'is_important': {'value': wish.is_important}
        },
        'wish': wish,
        'edit_mode': True
    }
    
    return render(request, 'lovehub/add_wish.html', context)

@login_required
def delete_wish(request, pk):
    """حذف آرزو"""
    user = request.user
    wish = get_object_or_404(WishItem, pk=pk)
    
    # Check if user is authorized to delete this wish
    if wish.created_by != user:
        messages.error(request, 'فقط سازنده آرزو می‌تواند آن را حذف کند')
        return redirect('wishes_list')
    
    if request.method == 'POST':
        wish.delete()
        messages.success(request, 'آرزو با موفقیت حذف شد')
        return redirect('wishes_list')
    
    return redirect('wishes_list')

@login_required
def update_account(request):
    """به‌روزرسانی اطلاعات حساب کاربری"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        username = request.POST.get('username', '')
        
        # بررسی یکتا بودن نام کاربری
        if username != user.username and User.objects.filter(username=username).exists():
            messages.error(request, 'نام کاربری قبلاً استفاده شده است')
            return redirect('app_settings')
        
        user.username = username
        user.save()
        
        messages.success(request, 'اطلاعات حساب کاربری با موفقیت به‌روزرسانی شد')
        
        # ایجاد اعلان سیستمی
        Notification.objects.create(
            user=user,
            title='به‌روزرسانی حساب کاربری',
            message='اطلاعات حساب کاربری شما با موفقیت به‌روزرسانی شد',
            notification_type='system'
        )
        
    return redirect('app_settings')

@login_required
def change_password(request):
    """تغییر رمز عبور کاربر"""
    if request.method == 'POST':
        user = request.user
        old_password = request.POST.get('old_password', '')
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')
        
        # بررسی صحت رمز عبور فعلی
        if not user.check_password(old_password):
            messages.error(request, 'رمز عبور فعلی اشتباه است')
            return redirect('app_settings')
        
        # بررسی تطابق رمزهای عبور جدید
        if new_password1 != new_password2:
            messages.error(request, 'رمزهای عبور جدید مطابقت ندارند')
            return redirect('app_settings')
        
        # بررسی پیچیدگی رمز عبور
        if len(new_password1) < 8:
            messages.error(request, 'رمز عبور باید حداقل ۸ کاراکتر باشد')
            return redirect('app_settings')
        
        # تغییر رمز عبور
        user.set_password(new_password1)
        user.save()
        
        # به‌روزرسانی جلسه کاربر برای جلوگیری از خروج
        update_session_auth_hash(request, user)
        
        messages.success(request, 'رمز عبور با موفقیت تغییر کرد')
        
        # ایجاد اعلان سیستمی
        Notification.objects.create(
            user=user,
            title='تغییر رمز عبور',
            message='رمز عبور شما با موفقیت تغییر کرد',
            notification_type='system'
        )
        
    return redirect('app_settings')

@login_required
def update_notifications(request):
    """به‌روزرسانی تنظیمات اعلان‌ها"""
    if request.method == 'POST':
        user = request.user
        profile = get_object_or_404(UserProfile, user=user)
        
        # تنظیمات اعلان‌ها
        enabled = request.POST.get('enabled') == 'on'
        notify_events = request.POST.get('notify_events') == 'on'
        notify_moments = request.POST.get('notify_moments') == 'on'
        notify_wishes = request.POST.get('notify_wishes') == 'on'
        notify_comments = request.POST.get('notify_comments') == 'on'
        notify_daily_messages = request.POST.get('notify_daily_messages') == 'on'
        notification_method = request.POST.get('notification_method', 'app')
        
        # ذخیره تنظیمات
        notification_settings, created = NotificationSettings.objects.get_or_create(
            user=user,
            defaults={
                'enabled': enabled,
                'notify_events': notify_events,
                'notify_moments': notify_moments,
                'notify_wishes': notify_wishes,
                'notify_comments': notify_comments,
                'notify_daily_messages': notify_daily_messages,
                'notification_method': notification_method
            }
        )
        
        if not created:
            notification_settings.enabled = enabled
            notification_settings.notify_events = notify_events
            notification_settings.notify_moments = notify_moments
            notification_settings.notify_wishes = notify_wishes
            notification_settings.notify_comments = notify_comments
            notification_settings.notify_daily_messages = notify_daily_messages
            notification_settings.notification_method = notification_method
            notification_settings.save()
        
        messages.success(request, 'تنظیمات اعلان‌ها با موفقیت به‌روزرسانی شد')
        
    return redirect('app_settings')

@login_required
def update_appearance(request):
    """به‌روزرسانی تنظیمات ظاهری"""
    if request.method == 'POST':
        user = request.user
        
        # تنظیمات ظاهری
        theme = request.POST.get('theme', 'default')
        color_palette = request.POST.get('color_palette', 'default')
        font_size = request.POST.get('font_size', 'medium')
        
        # ذخیره تنظیمات
        appearance_settings, created = AppTheme.objects.get_or_create(
            user=user,
            defaults={
                'theme': theme,
                'color_palette': color_palette,
                'font_size': font_size
            }
        )
        
        if not created:
            appearance_settings.theme = theme
            appearance_settings.color_palette = color_palette
            appearance_settings.font_size = font_size
            appearance_settings.save()
        
        messages.success(request, 'تنظیمات ظاهری با موفقیت به‌روزرسانی شد')
        
    return redirect('app_settings')

@login_required
def update_privacy(request):
    """به‌روزرسانی تنظیمات حریم خصوصی"""
    if request.method == 'POST':
        user = request.user
        
        # تنظیمات حریم خصوصی
        activity_tracking = request.POST.get('activity_tracking') == 'on'
        data_sharing = request.POST.get('data_sharing') == 'on'
        
        # ذخیره تنظیمات
        privacy_settings, created = PrivacySettings.objects.get_or_create(
            user=user,
            defaults={
                'activity_tracking': activity_tracking,
                'data_sharing': data_sharing
            }
        )
        
        if not created:
            privacy_settings.activity_tracking = activity_tracking
            privacy_settings.data_sharing = data_sharing
            privacy_settings.save()
        
        messages.success(request, 'تنظیمات حریم خصوصی با موفقیت به‌روزرسانی شد')
        
    return redirect('app_settings')

@login_required
def update_relationship(request):
    """به‌روزرسانی تنظیمات رابطه"""
    if request.method == 'POST':
        user = request.user
        profile = get_object_or_404(UserProfile, user=user)
        
        # تنظیمات رابطه
        anniversary_date = request.POST.get('anniversary_date', '')
        partner_email = request.POST.get('partner_email', '')
        
        # تنظیم تاریخ شروع رابطه
        if anniversary_date:
            try:
                year, month, day = anniversary_date.split('/')
                profile.relationship_start_date = f"{year}-{month}-{day}"
            except ValueError:
                messages.error(request, 'فرمت تاریخ شروع رابطه نامعتبر است')
        
        # تنظیم همسر
        if partner_email and partner_email != user.email:
            try:
                partner_user = User.objects.get(email=partner_email)
                partner_profile = UserProfile.objects.get(user=partner_user)
                
                # بررسی اینکه آیا قبلاً این کاربر همسر دیگری دارد
                if partner_profile.partner and partner_profile.partner.user != user:
                    messages.error(request, 'این کاربر در حال حاضر با کاربر دیگری در ارتباط است')
                else:
                    # ایجاد ارتباط دوطرفه
                    profile.partner = partner_profile
                    partner_profile.partner = profile
                    partner_profile.save()
                    
                    # ایجاد اعلان برای همسر
                    Notification.objects.create(
                        user=partner_user,
                        title='درخواست ارتباط جدید',
                        message=f'{user.get_full_name()} شما را به عنوان همسر خود انتخاب کرده است',
                        notification_type='system'
                    )
            except User.DoesNotExist:
                messages.error(request, 'کاربری با این ایمیل یافت نشد')
            except UserProfile.DoesNotExist:
                messages.error(request, 'پروفایل کاربر یافت نشد')
        
        profile.save()
        messages.success(request, 'تنظیمات رابطه با موفقیت به‌روزرسانی شد')
        
    return redirect('app_settings')

@login_required
def update_widgets(request):
    """به‌روزرسانی تنظیمات ویجت‌ها"""
    if request.method == 'POST':
        user = request.user
        
        # تنظیمات ویجت‌ها
        active_widgets = request.POST.getlist('active_widgets')
        widget_order = request.POST.getlist('widget_order[]')
        
        # غیرفعال کردن همه ویجت‌ها
        UserWidget.objects.filter(user=user).update(is_active=False, order=0)
        
        # فعال کردن ویجت‌های انتخاب شده
        for widget_id in active_widgets:
            try:
                user_widget, created = UserWidget.objects.get_or_create(
                    user=user,
                    widget_id=widget_id,
                    defaults={'is_active': True}
                )
                
                if not created:
                    user_widget.is_active = True
                    user_widget.save()
            except:
                pass
        
        # تنظیم ترتیب ویجت‌ها
        for i, widget_id in enumerate(widget_order):
            try:
                user_widget = UserWidget.objects.get(user=user, widget_id=widget_id)
                user_widget.order = i + 1
                user_widget.save()
            except:
                pass
        
        messages.success(request, 'تنظیمات ویجت‌ها با موفقیت به‌روزرسانی شد')
        
    return redirect('app_settings')

@login_required
def download_data(request):
    """دانلود داده‌های کاربر"""
    user = request.user
    
    # جمع‌آوری داده‌های کاربر
    user_data = {
        'user': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined.isoformat()
        },
        'profile': {},
        'moments': [],
        'events': [],
        'wishes': [],
        'notes': []
    }
    
    # اطلاعات پروفایل
    try:
        profile = UserProfile.objects.get(user=user)
        user_data['profile'] = {
            'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
            'relationship_start_date': profile.relationship_start_date.isoformat() if profile.relationship_start_date else None,
            'partner': profile.partner.user.username if profile.partner else None
        }
    except UserProfile.DoesNotExist:
        pass
    
    # لحظات
    for moment in Moment.objects.filter(created_by=user):
        user_data['moments'].append({
            'id': moment.id,
            'title': moment.title,
            'description': moment.description,
            'date': moment.date.isoformat(),
            'location': moment.location,
            'latitude': float(moment.latitude) if moment.latitude else None,
            'longitude': float(moment.longitude) if moment.longitude else None,
            'mood': moment.mood,
            'image': bool(moment.image),
            'likes_count': moment.likes.count(),
            'comments': [{
                'user': comment.user.username,
                'text': comment.text,
                'created_at': comment.created_at.isoformat()
            } for comment in moment.comments.all()]
        })
    
    # رویدادها
    for event in Event.objects.filter(created_by=user):
        user_data['events'].append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'date': event.date.isoformat(),
            'event_type': event.event_type,
            'is_recurring': event.is_recurring,
            'enable_notification': event.enable_notification,
            'notification_days': event.notification_days,
            'notification_method': event.notification_method,
            'notify_partner': event.notify_partner
        })
    
    # آرزوها
    for wish in WishItem.objects.filter(created_by=user):
        user_data['wishes'].append({
            'id': wish.id,
            'title': wish.title,
            'description': wish.description,
            'is_important': wish.is_important,
            'is_completed': wish.is_completed,
            'created_at': wish.created_at.isoformat()
        })
    
    # یادداشت‌ها
    for note in Note.objects.filter(created_by=user):
        user_data['notes'].append({
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'created_at': note.created_at.isoformat(),
            'updated_at': note.updated_at.isoformat() if note.updated_at else None
        })
    
    # ایجاد فایل JSON
    response = HttpResponse(json.dumps(user_data, indent=4, ensure_ascii=False), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{user.username}_data.json"'
    
    # ایجاد اعلان سیستمی
    Notification.objects.create(
        user=user,
        title='دانلود داده‌ها',
        message='داده‌های شما با موفقیت دانلود شد',
        notification_type='system'
    )
    
    return response

@login_required
def delete_data(request):
    """حذف داده‌های کاربر"""
    user = request.user
    
    # حذف داده‌ها
    Moment.objects.filter(created_by=user).delete()
    Event.objects.filter(created_by=user).delete()
    WishItem.objects.filter(created_by=user).delete()
    Note.objects.filter(created_by=user).delete()
    Comment.objects.filter(user=user).delete()
    Notification.objects.filter(user=user).delete()
    DailyMood.objects.filter(user=user).delete()
    DailyMessage.objects.filter(user=user).delete()
    
    messages.success(request, 'داده‌های شما با موفقیت حذف شدند')
    
    # ایجاد اعلان سیستمی
    Notification.objects.create(
        user=user,
        title='حذف داده‌ها',
        message='داده‌های شما با موفقیت حذف شدند',
        notification_type='system'
    )
    
    return redirect('app_settings')

@login_required
def create_love_quotes(request):
    """ایجاد نقل قول های عاشقانه"""
    # Only allow admin users to create quotes
    if not request.user.is_superuser:
        messages.error(request, 'شما اجازه دسترسی به این بخش را ندارید')
        return redirect('dashboard')
    
    # Create quotes if none exist
    quotes_count = LoveQuote.objects.count()
    
    if quotes_count == 0:
        # List of romantic quotes with authors
        quotes = [
            {"text": "عشق، دیدن کسی است همانطور که خداوند او را دیده است.", "author": "فیودور داستایوفسکی"},
            {"text": "عشق یعنی یک روح در دو بدن زندگی کردن.", "author": "ارسطو"},
            {"text": "عشق، تنها چیزی است که وقتی به دیگران می‌بخشید، بیشتر می‌شود.", "author": "آنتوان دو سنت اگزوپری"},
            {"text": "وقتی به چشمانت نگاه می‌کنم، می‌بینم که تمام ستاره‌های آسمان آنجا هستند.", "author": ""},
            {"text": "تو شعر زیبایی هستی که هرگز نمی‌خواهم به پایان برسد.", "author": ""},
            {"text": "بزرگترین خوشبختی زندگی، اطمینان از دوست داشته شدن است.", "author": "ویکتور هوگو"},
            {"text": "عشق با دیدن آغاز می‌شود و با نگاه کردن ادامه می‌یابد.", "author": "سعدی"},
            {"text": "عشق، تنها کلیدی است که می‌تواند قفل قلب را باز کند.", "author": ""},
            {"text": "هر لحظه که با تو می‌گذرانم، بهترین لحظه زندگی‌ام است.", "author": ""},
            {"text": "عشق یعنی پذیرفتن کسی آنطور که هست، نه آنطور که می‌خواهی باشد.", "author": ""},
            {"text": "قلب من تنها به عشق تو می‌تپد و هر ضربان آن نام تو را فریاد می‌زند.", "author": ""},
            {"text": "تنها مسیری که هرگز از آن خسته نمی‌شوم، مسیر رسیدن به توست.", "author": ""},
            {"text": "عشق، مثل باران است؛ نمی‌توانی بگویی کی می‌آید، اما وقتی بیاید همه چیز را سرسبز می‌کند.", "author": ""},
            {"text": "من تو را با ضربان قلبم اندازه می‌گیرم نه با زمان.", "author": ""},
            {"text": "عشق، توانایی دیدن نامرئی‌ها، لمس ناملموس‌ها و رسیدن به غیرممکن‌هاست.", "author": "ویکتور هوگو"},
        ]
        
        # Create each quote in the database
        for quote_data in quotes:
            LoveQuote.objects.create(
                text=quote_data["text"],
                author=quote_data["author"],
                is_active=True
            )
        
        messages.success(request, f'تعداد {len(quotes)} نقل قول عاشقانه با موفقیت اضافه شد')
    else:
        messages.info(request, f'در حال حاضر {quotes_count} نقل قول در سیستم وجود دارد')
    
    return redirect('dashboard')

class AccountForm(forms.Form):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class NotificationForm(forms.Form):
    enabled = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    notify_events = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    notify_moments = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    notify_wishes = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    notify_comments = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    notify_daily_messages = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    CHOICES = [('app', 'درون برنامه‌ای'), ('email', 'ایمیل'), ('both', 'هر دو')]
    notification_method = forms.ChoiceField(choices=CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

class AppearanceForm(forms.Form):
    THEME_CHOICES = AppTheme.THEME_CHOICES
    theme = forms.ChoiceField(choices=THEME_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    COLOR_PALETTE_CHOICES = [
        ('default', 'پیش‌فرض'),
        ('purple', 'بنفش'),
        ('blue', 'آبی'),
        ('green', 'سبز'),
        ('orange', 'نارنجی')
    ]
    color_palette = forms.ChoiceField(choices=COLOR_PALETTE_CHOICES, widget=forms.RadioSelect())
    FONT_SIZE_CHOICES = [
        ('small', 'کوچک'),
        ('medium', 'متوسط'),
        ('large', 'بزرگ')
    ]
    font_size = forms.ChoiceField(choices=FONT_SIZE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

class PrivacyForm(forms.Form):
    activity_tracking = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    data_sharing = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

class RelationshipForm(forms.Form):
    anniversary_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    partner_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))

class WidgetForm(forms.Form):
    active_widgets = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'widget-checkbox'})
    )
    widget_order = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    def __init__(self, *args, **kwargs):
        available_widgets = kwargs.pop('available_widgets', [])
        super(WidgetForm, self).__init__(*args, **kwargs)
        
        self.fields['active_widgets'].choices = [(widget.id, widget.get_widget_type_display()) for widget in available_widgets]

@login_required
def get_unread_notifications(request):
    """دریافت اعلان‌های خوانده نشده برای استفاده در هدر"""
    user = request.user
    
    # دریافت اعلان‌های خوانده نشده
    notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).order_by('-created_at')[:5]
    
    # شمارش کل اعلان‌های خوانده نشده
    unread_count = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()
    
    return JsonResponse({
        'notifications': [
            {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'link': notification.link or '#',
                'created_at': notification.created_at.strftime('%Y/%m/%d %H:%M'),
                'is_read': notification.is_read,
            } for notification in notifications
        ],
        'unread_count': unread_count
    })

def lovehub_context_processor(request):
    """افزودن متغیرهای عمومی به همه تمپلیت‌ها"""
    context = {}
    
    if request.user.is_authenticated:
        user = request.user
        
        # دریافت پروفایل کاربر
        try:
            profile = UserProfile.objects.get(user=user)
            context['user_profile'] = profile
        except UserProfile.DoesNotExist:
            pass
        
        # دریافت اعلان‌های خوانده نشده
        context['unread_notifications'] = Notification.objects.filter(
            user=user,
            is_read=False
        ).order_by('-created_at')[:5]
        
        context['unread_notifications_count'] = Notification.objects.filter(
            user=user,
            is_read=False
        ).count()
        
        # دریافت تنظیمات ظاهری
        try:
            theme = AppTheme.objects.get(user=user)
            context['user_theme'] = theme
        except AppTheme.DoesNotExist:
            pass
    
    return context

@login_required
def notifications_list(request):
    """نمایش لیست اعلان‌ها"""
    user = request.user
    
    # دریافت همه اعلان‌ها
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    
    # علامت گذاری همه اعلان‌ها به عنوان خوانده شده
    if request.GET.get('mark_read') == 'all':
        Notification.objects.filter(user=user, is_read=False).update(is_read=True)
        messages.success(request, 'همه اعلان‌ها به عنوان خوانده شده علامت‌گذاری شدند')
        return redirect('notifications_list')
    
    # حذف همه اعلان‌های خوانده شده
    if request.GET.get('clear_read') == 'all':
        Notification.objects.filter(user=user, is_read=True).delete()
        messages.success(request, 'اعلان‌های خوانده شده حذف شدند')
        return redirect('notifications_list')
    
    # تقسیم‌بندی اعلان‌ها به خوانده شده و نشده
    unread_notifications = notifications.filter(is_read=False)
    read_notifications = notifications.filter(is_read=True)
    
    context = {
        'notifications': notifications,
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
        'unread_count': unread_notifications.count()
    }
    
    return render(request, 'lovehub/notifications_list.html', context)

@login_required
def moment_comment(request, pk):
    """افزودن کامنت به لحظه"""
    moment = get_object_or_404(Moment, pk=pk)
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)
    
    # بررسی دسترسی کاربر
    if moment.created_by != user and (not profile.partner or moment.created_by != profile.partner.user):
        messages.error(request, 'شما نمی‌توانید برای این لحظه کامنت اضافه کنید')
        return redirect('moments_list')
    
    if request.method == 'POST':
        text = request.POST.get('comment')
        
        if text:
            comment = MomentComment.objects.create(
                moment=moment,
                user=user,
                text=text
            )
            
            # اگر کامنت برای لحظه کاربر دیگری است، اعلان ایجاد کن
            if moment.created_by != user:
                # بررسی تنظیمات اعلان‌های صاحب لحظه
                owner_settings, created = NotificationSettings.objects.get_or_create(
                    user=moment.created_by,
                    defaults={
                        'enabled': True,
                        'notify_comments': True
                    }
                )
                
                if owner_settings.enabled and owner_settings.notify_comments:
                    Notification.objects.create(
                        user=moment.created_by,
                        title="کامنت جدید",
                        message=f"{user.get_full_name() or user.username} برای لحظه '{moment.title}' کامنت گذاشته است.",
                        notification_type='comment',
                        link=f'/moment/{moment.id}/',
                        related_object_id=moment.id
                    )
            
            messages.success(request, 'کامنت با موفقیت اضافه شد')
        else:
            messages.error(request, 'متن کامنت نمی‌تواند خالی باشد')
    
    return redirect('moment_detail', pk=moment.pk)

@login_required
def mark_notifications_read(request):
    """علامت‌گذاری همه اعلان‌ها به عنوان خوانده‌شده"""
    if request.method == 'POST':
        notification_ids = request.POST.getlist('notification_ids')
        if notification_ids:
            # تغییر وضعیت اعلان‌های انتخاب شده
            Notification.objects.filter(
                user=request.user, 
                id__in=notification_ids
            ).update(is_read=True)
        else:
            # تغییر وضعیت همه اعلان‌های خوانده نشده
            Notification.objects.filter(
                user=request.user, 
                is_read=False
            ).update(is_read=True)
        
        messages.success(request, 'اعلان‌ها به عنوان خوانده‌شده علامت‌گذاری شدند')
    
    if 'next' in request.GET:
        return redirect(request.GET.get('next'))
    
    return redirect('dashboard')
