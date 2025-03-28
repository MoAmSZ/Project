from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    partner = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='partner_profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='تصویر پروفایل')
    birth_date = models.DateField(null=True, blank=True, verbose_name='تاریخ تولد')
    relationship_start_date = models.DateField(null=True, blank=True, verbose_name='تاریخ شروع رابطه')
    
    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل‌های کاربران'
    
    def __str__(self):
        return f"پروفایل {self.user.username}"

class DailyMood(models.Model):
    MOOD_CHOICES = [
        ('😊', 'خوشحال'),
        ('😍', 'عاشقانه'),
        ('🤔', 'متفکر'),
        ('🙂', 'معمولی'),
        ('❤️', 'عاشق'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moods', verbose_name='کاربر')
    date = models.DateField(default=timezone.now, verbose_name='تاریخ')
    mood = models.CharField(max_length=10, choices=MOOD_CHOICES, verbose_name='حالت')
    note = models.TextField(blank=True, null=True, verbose_name='یادداشت')
    
    class Meta:
        verbose_name = 'حس روزانه'
        verbose_name_plural = 'حس‌های روزانه'
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"حس {self.user.username} در {self.date}: {self.mood}"

class DailyMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name='فرستنده')
    date = models.DateField(default=timezone.now, verbose_name='تاریخ')
    message = models.TextField(max_length=500, verbose_name='پیام')
    
    class Meta:
        verbose_name = 'پیام روزانه'
        verbose_name_plural = 'پیام‌های روزانه'
        unique_together = ['sender', 'date']
    
    def __str__(self):
        return f"پیام {self.sender.username} در {self.date}"

class Moment(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moments', verbose_name='ایجاد کننده')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = models.TextField(verbose_name='توضیحات')
    date = models.DateTimeField(default=timezone.now, verbose_name='تاریخ')
    image = models.ImageField(upload_to='moments/', null=True, blank=True, verbose_name='تصویر')
    audio = models.FileField(upload_to='moment_audios/', null=True, blank=True, verbose_name='صدا')
    location_name = models.CharField(max_length=200, null=True, blank=True, verbose_name='نام مکان')
    latitude = models.FloatField(null=True, blank=True, verbose_name='عرض جغرافیایی')
    longitude = models.FloatField(null=True, blank=True, verbose_name='طول جغرافیایی')
    mood_tags = models.CharField(max_length=200, null=True, blank=True, verbose_name='تگ‌های حسی')
    
    class Meta:
        verbose_name = 'لحظه'
        verbose_name_plural = 'لحظات'
        ordering = ['-date']
    
    def __str__(self):
        return self.title

class MomentComment(models.Model):
    moment = models.ForeignKey(Moment, on_delete=models.CASCADE, related_name='comments', verbose_name='لحظه')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moment_comments', verbose_name='کاربر')
    text = models.TextField(verbose_name='متن')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    
    class Meta:
        verbose_name = 'کامنت لحظه'
        verbose_name_plural = 'کامنت‌های لحظات'
        ordering = ['created_at']
    
    def __str__(self):
        return f"کامنت {self.user.username} روی {self.moment.title}"

class MomentLike(models.Model):
    moment = models.ForeignKey(Moment, on_delete=models.CASCADE, related_name='likes', verbose_name='لحظه')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moment_likes', verbose_name='کاربر')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    
    class Meta:
        verbose_name = 'لایک لحظه'
        verbose_name_plural = 'لایک‌های لحظات'
        unique_together = ['moment', 'user']
    
    def __str__(self):
        return f"لایک {self.user.username} روی {self.moment.title}"

class Event(models.Model):
    EVENT_TYPES = [
        ('anniversary', 'سالگرد'),
        ('birthday', 'تولد'),
        ('special', 'مناسبت خاص'),
        ('reminder', 'یادآوری'),
    ]
    
    NOTIFICATION_METHODS = [
        ('app', 'درون برنامه‌ای'),
        ('email', 'ایمیل'),
        ('both', 'هر دو'),
    ]
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events', verbose_name='ایجاد کننده')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = models.TextField(null=True, blank=True, verbose_name='توضیحات')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='special', verbose_name='نوع رویداد')
    date = models.DateField(verbose_name='تاریخ')
    is_recurring = models.BooleanField(default=False, verbose_name='تکرار سالانه')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='زمان ایجاد')
    
    # تنظیمات نوتیفیکیشن
    enable_notification = models.BooleanField(default=False, verbose_name='فعال‌سازی یادآوری')
    notification_days = models.PositiveIntegerField(default=1, verbose_name='روزهای قبل از یادآوری')
    notification_method = models.CharField(max_length=10, choices=NOTIFICATION_METHODS, default='app', verbose_name='روش اعلان')
    notify_partner = models.BooleanField(default=True, verbose_name='یادآوری به همسر')
    
    class Meta:
        verbose_name = 'رویداد'
        verbose_name_plural = 'رویدادها'
        ordering = ['date']
    
    def __str__(self):
        return self.title

class WishItem(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishes', verbose_name='ایجاد کننده')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = models.TextField(null=True, blank=True, verbose_name='توضیحات')
    is_completed = models.BooleanField(default=False, verbose_name='انجام شده')
    is_important = models.BooleanField(default=False, verbose_name='مهم')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    
    class Meta:
        verbose_name = 'آرزو'
        verbose_name_plural = 'آرزوها'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class DateIdea(models.Model):
    BUDGET_CHOICES = [
        ('free', 'رایگان'),
        ('low', 'کم هزینه'),
        ('medium', 'متوسط'),
        ('high', 'گران'),
    ]
    
    LOCATION_CHOICES = [
        ('indoor', 'داخل خانه'),
        ('outdoor', 'بیرون از خانه'),
        ('any', 'هر جایی'),
    ]
    
    MOOD_CHOICES = [
        ('energetic', 'پرانرژی'),
        ('calm', 'آرام'),
        ('romantic', 'عاشقانه'),
        ('adventurous', 'ماجراجویانه'),
        ('creative', 'خلاقانه'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = models.TextField(verbose_name='توضیحات')
    budget = models.CharField(max_length=10, choices=BUDGET_CHOICES, default='low', verbose_name='بودجه')
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES, default='any', verbose_name='مکان')
    mood = models.CharField(max_length=15, choices=MOOD_CHOICES, default='romantic', verbose_name='حال و هوا')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='date_ideas', verbose_name='ایجاد کننده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    
    class Meta:
        verbose_name = 'ایده قرار'
        verbose_name_plural = 'ایده‌های قرار'
    
    def __str__(self):
        return self.title

class DateIdeaRating(models.Model):
    date_idea = models.ForeignKey(DateIdea, on_delete=models.CASCADE, related_name='ratings', verbose_name='ایده قرار')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='date_idea_ratings', verbose_name='کاربر')
    liked = models.BooleanField(verbose_name='پسندیده شد')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    
    class Meta:
        verbose_name = 'امتیاز ایده قرار'
        verbose_name_plural = 'امتیازهای ایده‌های قرار'
        unique_together = ['date_idea', 'user']
    
    def __str__(self):
        status = 'پسندیده' if self.liked else 'نپسندیده'
        return f"{self.user.username} این ایده را {status}"

class GratitudeNote(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gratitude_notes', verbose_name='ایجاد کننده')
    text = models.TextField(verbose_name='متن')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    
    class Meta:
        verbose_name = 'یادداشت قدردانی'
        verbose_name_plural = 'یادداشت‌های قدردانی'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"قدردانی {self.created_by.username} در {self.created_at.date()}"

class DashboardWidget(models.Model):
    WIDGET_TYPES = [
        ('counter', 'شمارشگر اصلی'),
        ('upcoming_events', 'رویدادهای نزدیک'),
        ('this_day', 'در چنین روزی'),
        ('latest_moment', 'آخرین خاطره'),
        ('love_quote', 'نقل قول عاشقانه'),
        ('daily_challenge', 'چالش روزانه'),
        ('daily_mood', 'نبض رابطه'),
        ('daily_message', 'پیام روزانه'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_widgets', verbose_name='کاربر')
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES, verbose_name='نوع ویجت')
    is_enabled = models.BooleanField(default=True, verbose_name='فعال است')
    position = models.PositiveIntegerField(default=0, verbose_name='موقعیت')
    
    class Meta:
        verbose_name = 'ویجت داشبورد'
        verbose_name_plural = 'ویجت‌های داشبورد'
        ordering = ['position']
        unique_together = ['user', 'widget_type']
    
    def __str__(self):
        return f"{self.get_widget_type_display()} برای {self.user.username}"

class AppTheme(models.Model):
    """تم های قابل انتخاب توسط کاربر"""
    THEME_CHOICES = (
        ('default', 'پیش‌فرض'),
        ('dark', 'تاریک'),
        ('light', 'روشن'),
        ('nature', 'طبیعت'),
        ('romance', 'رمانتیک'),
        ('royal', 'سلطنتی'),
        ('ocean', 'اقیانوس'),
        ('sunset', 'غروب آفتاب'),
    )
    
    COLOR_PALETTE_CHOICES = (
        ('default', 'پیش‌فرض'),
        ('purple', 'بنفش'),
        ('blue', 'آبی'),
        ('green', 'سبز'),
        ('orange', 'نارنجی'),
        ('red', 'قرمز'),
        ('pink', 'صورتی'),
        ('teal', 'فیروزه‌ای'),
    )
    
    FONT_SIZE_CHOICES = (
        ('small', 'کوچک'),
        ('medium', 'متوسط'),
        ('large', 'بزرگ'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='theme')
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='default')
    color_palette = models.CharField(max_length=20, choices=COLOR_PALETTE_CHOICES, default='default')
    font_size = models.CharField(max_length=10, choices=FONT_SIZE_CHOICES, default='medium')

class Note(models.Model):
    """یادداشت‌های کاربر"""
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_shared = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title

class LoveQuote(models.Model):
    text = models.TextField(verbose_name='متن')
    author = models.CharField(max_length=100, null=True, blank=True, verbose_name='نویسنده')
    is_active = models.BooleanField(default=True, verbose_name='فعال است')
    
    class Meta:
        verbose_name = 'نقل قول عاشقانه'
        verbose_name_plural = 'نقل قول‌های عاشقانه'
    
    def __str__(self):
        return f"{self.text[:50]}..."

class Notification(models.Model):
    """اعلان‌های سیستم"""
    NOTIFICATION_TYPES = (
        ('event', 'رویداد'),
        ('moment', 'لحظه'),
        ('wish', 'آرزو'),
        ('comment', 'نظر'),
        ('system', 'سیستمی'),
        ('daily_message', 'پیام روزانه'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='کاربر')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    message = models.TextField(verbose_name='پیام')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system', verbose_name='نوع اعلان')
    is_read = models.BooleanField(default=False, verbose_name='خوانده شده')
    link = models.CharField(max_length=255, null=True, blank=True, verbose_name='لینک')
    related_object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='شناسه شیء مرتبط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    
    class Meta:
        verbose_name = 'اعلان'
        verbose_name_plural = 'اعلان‌ها'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} برای {self.user.username}"

class NotificationSettings(models.Model):
    """تنظیمات اعلان‌های کاربر"""
    NOTIFICATION_METHODS = (
        ('app', 'درون برنامه‌ای'),
        ('email', 'ایمیل'),
        ('both', 'هر دو'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings', verbose_name='کاربر')
    enabled = models.BooleanField(default=True, verbose_name='اعلان‌ها فعال است')
    notify_events = models.BooleanField(default=True, verbose_name='اعلان رویدادها')
    notify_moments = models.BooleanField(default=True, verbose_name='اعلان لحظات')
    notify_wishes = models.BooleanField(default=True, verbose_name='اعلان آرزوها')
    notify_comments = models.BooleanField(default=True, verbose_name='اعلان نظرات')
    notify_daily_messages = models.BooleanField(default=True, verbose_name='اعلان پیام‌های روزانه')
    notification_method = models.CharField(max_length=10, choices=NOTIFICATION_METHODS, default='app', verbose_name='روش اعلان')
    
    class Meta:
        verbose_name = 'تنظیمات اعلان'
        verbose_name_plural = 'تنظیمات اعلان‌ها'
    
    def __str__(self):
        return f"تنظیمات اعلان {self.user.username}"

class PrivacySettings(models.Model):
    """تنظیمات حریم خصوصی کاربر"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='privacy_settings', verbose_name='کاربر')
    activity_tracking = models.BooleanField(default=True, verbose_name='ردیابی فعالیت‌ها')
    data_sharing = models.BooleanField(default=True, verbose_name='اشتراک‌گذاری داده‌ها')
    
    class Meta:
        verbose_name = 'تنظیمات حریم خصوصی'
        verbose_name_plural = 'تنظیمات حریم خصوصی'
    
    def __str__(self):
        return f"تنظیمات حریم خصوصی {self.user.username}"

class UserWidget(models.Model):
    """ویجت‌های فعال کاربر"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='widgets', verbose_name='کاربر')
    widget = models.ForeignKey(DashboardWidget, on_delete=models.CASCADE, related_name='user_widgets', verbose_name='ویجت')
    is_active = models.BooleanField(default=True, verbose_name='فعال است')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    
    class Meta:
        verbose_name = 'ویجت کاربر'
        verbose_name_plural = 'ویجت‌های کاربر'
        ordering = ['order']
        unique_together = ['user', 'widget']
    
    def __str__(self):
        return f"{self.widget.get_widget_type_display()} برای {self.user.username}"
