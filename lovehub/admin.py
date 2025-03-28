from django.contrib import admin
from .models import (
    UserProfile, DailyMood, DailyMessage, Moment, MomentComment, MomentLike,
    Event, WishItem, DateIdea, DateIdeaRating, GratitudeNote, DashboardWidget,
    AppTheme, LoveQuote
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'partner', 'birth_date', 'relationship_start_date')
    search_fields = ('user__username',)

@admin.register(DailyMood)
class DailyMoodAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'mood')
    list_filter = ('date', 'mood')
    search_fields = ('user__username',)

@admin.register(DailyMessage)
class DailyMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'date', 'message')
    list_filter = ('date',)
    search_fields = ('sender__username', 'message')

class MomentCommentInline(admin.TabularInline):
    model = MomentComment
    extra = 0

class MomentLikeInline(admin.TabularInline):
    model = MomentLike
    extra = 0

@admin.register(Moment)
class MomentAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'date', 'location_name')
    list_filter = ('date', 'created_by')
    search_fields = ('title', 'description', 'location_name')
    inlines = [MomentCommentInline, MomentLikeInline]

@admin.register(MomentComment)
class MomentCommentAdmin(admin.ModelAdmin):
    list_display = ('moment', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'user__username')

@admin.register(MomentLike)
class MomentLikeAdmin(admin.ModelAdmin):
    list_display = ('moment', 'user', 'created_at')
    list_filter = ('created_at',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'event_type', 'date', 'is_recurring')
    list_filter = ('event_type', 'date', 'is_recurring')
    search_fields = ('title', 'description')

@admin.register(WishItem)
class WishItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'created_at')
    search_fields = ('title', 'description')

@admin.register(DateIdea)
class DateIdeaAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'budget', 'location', 'mood')
    list_filter = ('budget', 'location', 'mood')
    search_fields = ('title', 'description')

@admin.register(DateIdeaRating)
class DateIdeaRatingAdmin(admin.ModelAdmin):
    list_display = ('date_idea', 'user', 'liked', 'created_at')
    list_filter = ('liked', 'created_at')

@admin.register(GratitudeNote)
class GratitudeNoteAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'text_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text',)
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'متن'

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'widget_type', 'is_enabled', 'position')
    list_filter = ('widget_type', 'is_enabled')
    search_fields = ('user__username',)

@admin.register(AppTheme)
class AppThemeAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme')
    list_filter = ('theme',)
    search_fields = ('user__username',)

@admin.register(LoveQuote)
class LoveQuoteAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'author', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('text', 'author')
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'متن'
