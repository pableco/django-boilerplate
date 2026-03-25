from django.urls import path
from . import views

app_name = 'card_sorting'

urlpatterns = [
    path('', views.index, name='index'),
    path('inicio/', views.start_session, name='start'),
    path('ordenar/<uuid:session_key>/', views.sort_cards, name='sort'),
    path('guardar/<uuid:session_key>/', views.save_sort, name='save'),
    path('completar/<uuid:session_key>/', views.complete_session, name='complete'),
    path('done/<uuid:session_key>/', views.session_done, name='done'),
    path('resultados/', views.results, name='results'),
]
