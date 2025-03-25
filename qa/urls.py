from django.urls import path
from .views import AsyncQAView, AsyncAskView, ask_form_view

urlpatterns = [
    path('', AsyncQAView.as_view(), name='qa-history'),
    path('<int:pk>/', AsyncQAView.as_view(), name='qa-detail'),
    path('ask/', AsyncAskView.as_view(), name='ask-question'),
    path('askQuestion/', ask_form_view, name='ask-form')
]