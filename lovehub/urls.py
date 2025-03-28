from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='lovehub/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login', template_name='lovehub/logged_out.html'), name='logout'),
    
    # Daily mood and message
    path('mood/update/', views.update_daily_mood, name='update_mood'),
    path('message/update/', views.update_daily_message, name='update_message'),
    
    # Moments
    path('moments/', views.moments_list, name='moments_list'),
    path('moments/add/', views.add_moment, name='add_moment'),
    path('moments/<int:pk>/', views.moment_detail, name='moment_detail'),
    path('moments/<int:pk>/edit/', views.edit_moment, name='edit_moment'),
    path('moments/<int:pk>/delete/', views.delete_moment, name='delete_moment'),
    path('moments/<int:pk>/like/', views.like_moment, name='like_moment'),
    path('moments/<int:pk>/comment/', views.moment_comment, name='moment_comment'),
    
    # Events
    path('events/', views.events_list, name='events_list'),
    path('events/add/', views.add_event, name='add_event'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/<int:pk>/edit/', views.edit_event, name='edit_event'),
    path('events/<int:pk>/delete/', views.delete_event, name='delete_event'),
    path('events/<int:pk>/notification/', views.enable_notification, name='enable_notification'),
    
    # Wishes
    path('wishes/', views.wishes_list, name='wishes_list'),
    path('wishes/add/', views.add_wish, name='add_wish'),
    path('wishes/<int:pk>/toggle/', views.toggle_wish_completed, name='complete_wish'),
    path('wishes/<int:pk>/edit/', views.edit_wish, name='edit_wish'),
    path('wishes/<int:pk>/delete/', views.delete_wish, name='delete_wish'),
    
    # Date ideas
    path('date-ideas/', views.date_ideas, name='date_ideas'),
    path('date-ideas/add/', views.add_date_idea, name='add_date_idea'),
    path('date-ideas/<int:pk>/', views.date_idea_detail, name='date_idea_detail')
    ,
    path('date-ideas/<int:pk>/edit/', views.edit_date_idea, name='edit_date_idea'),
    path('date-ideas/<int:pk>/delete/', views.delete_date_idea, name='delete_date_idea'),
    path('date-ideas/<int:pk>/rate/', views.rate_date_idea, name='rate_date_idea'),
    
    # Gratitude notes
    path('gratitude/', views.gratitude_notes, name='gratitude_notes'),
    
    # Settings
    path('settings/widgets/', views.widget_settings, name='widget_settings'),
    path('settings/', views.app_settings, name='app_settings'),
    
    # تنظیمات جدید
    path('settings/account/update/', views.update_account, name='update_account'),
    path('settings/password/change/', views.change_password, name='change_password'),
    path('settings/notifications/update/', views.update_notifications, name='update_notifications'),
    path('settings/appearance/update/', views.update_appearance, name='update_appearance'),
    path('settings/privacy/update/', views.update_privacy, name='update_privacy'),
    path('settings/relationship/update/', views.update_relationship, name='update_relationship'),
    path('settings/widgets/update/', views.update_widgets, name='update_widgets'),
    path('settings/data/download/', views.download_data, name='download_data'),
    path('settings/data/delete/', views.delete_data, name='delete_data'),
    
    # Views
    path('map/', views.map_view, name='map_view'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    
    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/unread/', views.get_unread_notifications, name='get_unread_notifications'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Partner invitations
    path('invite/', views.invite_partner, name='invite_partner'),
    path('accept-invite/', views.accept_invite, name='accept_invite_form'),
    path('accept-invite/<str:code>/', views.accept_invite, name='accept_invite'),
    path('generate-new-invite-code/', views.generate_new_invite_code, name='generate_new_invite_code'),
    path('send-invite-email/', views.send_invite_email, name='send_invite_email'),
    
    # Mood tracking
    path('mood/track/', views.track_mood, name='track_mood'),
    
    # Notes
    path('notes/', views.notes_list, name='notes_list'),
    path('notes/add/', views.add_note, name='add_note'),
    path('notes/<int:pk>/', views.note_detail, name='note_detail'),
    path('notes/<int:pk>/edit/', views.edit_note, name='edit_note'),
    path('notes/<int:pk>/delete/', views.delete_note, name='delete_note'),
    
    # Love Quotes
    path('quotes/create/', views.create_love_quotes, name='create_love_quotes'),
] 