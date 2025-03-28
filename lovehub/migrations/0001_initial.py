# Generated by Django 5.1.7 on 2025-03-27 21:23

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LoveQuote",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField(verbose_name="متن")),
                (
                    "author",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="نویسنده"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="فعال است"),
                ),
            ],
            options={
                "verbose_name": "نقل قول عاشقانه",
                "verbose_name_plural": "نقل قول\u200cهای عاشقانه",
            },
        ),
        migrations.CreateModel(
            name="AppTheme",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "theme",
                    models.CharField(
                        choices=[
                            ("default", "پیش\u200cفرض"),
                            ("dark", "تاریک"),
                            ("light", "روشن"),
                            ("winter", "زمستانی"),
                            ("spring", "بهاری"),
                            ("summer", "تابستانی"),
                            ("fall", "پاییزی"),
                        ],
                        default="default",
                        max_length=20,
                        verbose_name="تم",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="theme",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "تم برنامه",
                "verbose_name_plural": "تم\u200cهای برنامه",
            },
        ),
        migrations.CreateModel(
            name="DateIdea",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="عنوان")),
                ("description", models.TextField(verbose_name="توضیحات")),
                (
                    "budget",
                    models.CharField(
                        choices=[
                            ("free", "رایگان"),
                            ("low", "کم هزینه"),
                            ("medium", "متوسط"),
                            ("high", "گران"),
                        ],
                        default="low",
                        max_length=10,
                        verbose_name="بودجه",
                    ),
                ),
                (
                    "location",
                    models.CharField(
                        choices=[
                            ("indoor", "داخل خانه"),
                            ("outdoor", "بیرون از خانه"),
                            ("any", "هر جایی"),
                        ],
                        default="any",
                        max_length=10,
                        verbose_name="مکان",
                    ),
                ),
                (
                    "mood",
                    models.CharField(
                        choices=[
                            ("energetic", "پرانرژی"),
                            ("calm", "آرام"),
                            ("romantic", "عاشقانه"),
                            ("adventurous", "ماجراجویانه"),
                            ("creative", "خلاقانه"),
                        ],
                        default="romantic",
                        max_length=15,
                        verbose_name="حال و هوا",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="date_ideas",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="ایجاد کننده",
                    ),
                ),
            ],
            options={
                "verbose_name": "ایده قرار",
                "verbose_name_plural": "ایده\u200cهای قرار",
            },
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="عنوان")),
                (
                    "description",
                    models.TextField(blank=True, null=True, verbose_name="توضیحات"),
                ),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("anniversary", "سالگرد"),
                            ("birthday", "تولد"),
                            ("special", "مناسبت خاص"),
                            ("reminder", "یادآوری"),
                        ],
                        default="special",
                        max_length=20,
                        verbose_name="نوع رویداد",
                    ),
                ),
                ("date", models.DateField(verbose_name="تاریخ")),
                (
                    "is_recurring",
                    models.BooleanField(default=False, verbose_name="تکرار سالانه"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="ایجاد کننده",
                    ),
                ),
            ],
            options={
                "verbose_name": "رویداد",
                "verbose_name_plural": "رویدادها",
                "ordering": ["date"],
            },
        ),
        migrations.CreateModel(
            name="GratitudeNote",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField(verbose_name="متن")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="gratitude_notes",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="ایجاد کننده",
                    ),
                ),
            ],
            options={
                "verbose_name": "یادداشت قدردانی",
                "verbose_name_plural": "یادداشت\u200cهای قدردانی",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Moment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="عنوان")),
                ("description", models.TextField(verbose_name="توضیحات")),
                (
                    "date",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="تاریخ"
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="moments/",
                        verbose_name="تصویر",
                    ),
                ),
                (
                    "audio",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="moment_audios/",
                        verbose_name="صدا",
                    ),
                ),
                (
                    "location_name",
                    models.CharField(
                        blank=True, max_length=200, null=True, verbose_name="نام مکان"
                    ),
                ),
                (
                    "latitude",
                    models.FloatField(
                        blank=True, null=True, verbose_name="عرض جغرافیایی"
                    ),
                ),
                (
                    "longitude",
                    models.FloatField(
                        blank=True, null=True, verbose_name="طول جغرافیایی"
                    ),
                ),
                (
                    "mood_tags",
                    models.CharField(
                        blank=True,
                        max_length=200,
                        null=True,
                        verbose_name="تگ\u200cهای حسی",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="moments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="ایجاد کننده",
                    ),
                ),
            ],
            options={
                "verbose_name": "لحظه",
                "verbose_name_plural": "لحظات",
                "ordering": ["-date"],
            },
        ),
        migrations.CreateModel(
            name="MomentComment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField(verbose_name="متن")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد"),
                ),
                (
                    "moment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="lovehub.moment",
                        verbose_name="لحظه",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="moment_comments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "کامنت لحظه",
                "verbose_name_plural": "کامنت\u200cهای لحظات",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "avatar",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="avatars/",
                        verbose_name="تصویر پروفایل",
                    ),
                ),
                (
                    "birth_date",
                    models.DateField(blank=True, null=True, verbose_name="تاریخ تولد"),
                ),
                (
                    "relationship_start_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="تاریخ شروع رابطه"
                    ),
                ),
                (
                    "partner",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="partner_profile",
                        to="lovehub.userprofile",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "پروفایل کاربر",
                "verbose_name_plural": "پروفایل\u200cهای کاربران",
            },
        ),
        migrations.CreateModel(
            name="WishItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="عنوان")),
                (
                    "description",
                    models.TextField(blank=True, null=True, verbose_name="توضیحات"),
                ),
                (
                    "is_completed",
                    models.BooleanField(default=False, verbose_name="انجام شده"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wishes",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="ایجاد کننده",
                    ),
                ),
            ],
            options={
                "verbose_name": "آرزو",
                "verbose_name_plural": "آرزوها",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DailyMessage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "date",
                    models.DateField(
                        default=django.utils.timezone.now, verbose_name="تاریخ"
                    ),
                ),
                ("message", models.TextField(max_length=500, verbose_name="پیام")),
                (
                    "sender",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sent_messages",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="فرستنده",
                    ),
                ),
            ],
            options={
                "verbose_name": "پیام روزانه",
                "verbose_name_plural": "پیام\u200cهای روزانه",
                "unique_together": {("sender", "date")},
            },
        ),
        migrations.CreateModel(
            name="DailyMood",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "date",
                    models.DateField(
                        default=django.utils.timezone.now, verbose_name="تاریخ"
                    ),
                ),
                (
                    "mood",
                    models.CharField(
                        choices=[
                            ("😊", "خوشحال"),
                            ("😍", "عاشقانه"),
                            ("🤔", "متفکر"),
                            ("🙂", "معمولی"),
                            ("❤️", "عاشق"),
                        ],
                        max_length=10,
                        verbose_name="حالت",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="moods",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "حس روزانه",
                "verbose_name_plural": "حس\u200cهای روزانه",
                "unique_together": {("user", "date")},
            },
        ),
        migrations.CreateModel(
            name="DashboardWidget",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "widget_type",
                    models.CharField(
                        choices=[
                            ("counter", "شمارشگر اصلی"),
                            ("upcoming_events", "رویدادهای نزدیک"),
                            ("this_day", "در چنین روزی"),
                            ("latest_moment", "آخرین خاطره"),
                            ("love_quote", "نقل قول عاشقانه"),
                            ("daily_challenge", "چالش روزانه"),
                            ("daily_mood", "نبض رابطه"),
                            ("daily_message", "پیام روزانه"),
                        ],
                        max_length=20,
                        verbose_name="نوع ویجت",
                    ),
                ),
                (
                    "is_enabled",
                    models.BooleanField(default=True, verbose_name="فعال است"),
                ),
                (
                    "position",
                    models.PositiveIntegerField(default=0, verbose_name="موقعیت"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dashboard_widgets",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "ویجت داشبورد",
                "verbose_name_plural": "ویجت\u200cهای داشبورد",
                "ordering": ["position"],
                "unique_together": {("user", "widget_type")},
            },
        ),
        migrations.CreateModel(
            name="DateIdeaRating",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("liked", models.BooleanField(verbose_name="پسندیده شد")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد"),
                ),
                (
                    "date_idea",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ratings",
                        to="lovehub.dateidea",
                        verbose_name="ایده قرار",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="date_idea_ratings",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "امتیاز ایده قرار",
                "verbose_name_plural": "امتیازهای ایده\u200cهای قرار",
                "unique_together": {("date_idea", "user")},
            },
        ),
        migrations.CreateModel(
            name="MomentLike",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد"),
                ),
                (
                    "moment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="likes",
                        to="lovehub.moment",
                        verbose_name="لحظه",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="moment_likes",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "لایک لحظه",
                "verbose_name_plural": "لایک\u200cهای لحظات",
                "unique_together": {("moment", "user")},
            },
        ),
    ]
