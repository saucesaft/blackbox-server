from django.urls import path
from . import views


urlpatterns = [
	path('list/', views.PasswordNameListView.as_view()),
	path('id/', views.GetPassword.as_view())
]
