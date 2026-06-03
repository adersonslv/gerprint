# GerPrint — Sistema de Gestão de Impressoras
# Copyright (C) 2025  Aderson Silva <aderson.slv@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('impressoras/', views.impressora_list, name='impressora_list'),
    path('impressoras/nova/', views.impressora_create, name='impressora_create'),
    path('impressoras/<int:pk>/', views.impressora_detail, name='impressora_detail'),
    path('impressoras/<int:pk>/editar/', views.impressora_edit, name='impressora_edit'),
    path('impressoras/<int:pk>/excluir/', views.impressora_delete, name='impressora_delete'),
    path('impressoras/<int:pk>/coletar/', views.coletar_agora, name='coletar_impressora'),
    path('impressoras/<int:pk>/leitura-manual/', views.leitura_manual, name='leitura_manual'),
    path('coletar/', views.coletar_view, name='coletar'),
    path('coletar/agora/', views.coletar_agora, name='coletar_todas'),
    path('relatorios/', views.relatorios_view, name='relatorios'),
    path('relatorios/exportar/', views.relatorios_csv, name='relatorios_csv'),
    path('api/status/', views.api_status, name='api_status'),
    path('impressoras/escanear/', views.escanear_rede, name='escanear_rede'),
    path('impressoras/<int:pk>/snmp-probe/', views.snmp_probe, name='snmp_probe'),
]
