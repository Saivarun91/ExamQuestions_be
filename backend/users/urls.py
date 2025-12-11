# from django.urls import path
# from .views import signup, login, get_profile

# urlpatterns = [
#     path("signup/", signup, name="signup"),
#     path("login/", login, name="login"),
#     path("profile/", get_profile, name="get_profile"),
#     # path('admin/signup/', admin_signup, name='admin-signup'),
#     # path('admin/login/', admin_login, name='admin-login'),
# ]



from django.urls import path
from .views import (
    register_user, login_user, user_profile,current_user,
    register_admin, login_admin, admin_profile, update_admin_credentials,
    forgot_password, verify_otp, reset_password, google_oauth, get_all_users,
    search_users_by_email
)

urlpatterns = [
    path('register/', register_user, name='register_user'),
    path('login/', login_user, name='login_user'),
    path("me/", current_user, name="current-user"),
    path("forgot-password/", forgot_password, name="forgot-password"),
    path("verify-otp/", verify_otp, name="verify-otp"),
    path("reset-password/", reset_password, name="reset-password"),
    path("google-oauth/", google_oauth, name="google-oauth"),
    path('profile/', user_profile, name='user_profile'),

    path('admin/register/', register_admin, name='register_admin'),
    path('admin/login/', login_admin, name='login_admin'),
    path('admin/profile/', admin_profile, name='admin_profile'),
    path('admin/update-credentials/', update_admin_credentials, name='update_admin_credentials'),
    path('admin/all/', get_all_users, name='get_all_users'),
    path('admin/search/', search_users_by_email, name='search_users_by_email'),
]

