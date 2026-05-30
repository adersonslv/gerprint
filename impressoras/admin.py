# GerPrint — Sistema de Gestão de Impressoras
# Copyright (C) 2025  Aderson Silva <aderson.slv@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib import admin
from .models import Impressora, LeituraContador, RelatorioMensal


@admin.register(Impressora)
class ImpressoraAdmin(admin.ModelAdmin):
    list_display = ['nome', 'localizacao', 'ip', 'versao_snmp', 'custo_por_pagina', 'ativo']
    list_filter = ['ativo', 'versao_snmp']
    search_fields = ['nome', 'ip', 'numero_serie']
    list_editable = ['ativo']


@admin.register(LeituraContador)
class LeituraContadorAdmin(admin.ModelAdmin):
    list_display = ['impressora', 'lido_em', 'valor_contador', 'nivel_toner', 'manual', 'erro']
    list_filter = ['impressora', 'manual']
    date_hierarchy = 'lido_em'
    readonly_fields = ['lido_em']


@admin.register(RelatorioMensal)
class RelatorioMensalAdmin(admin.ModelAdmin):
    list_display = ['impressora', 'mes', 'ano', 'paginas_impressas', 'custo_total']
    list_filter = ['ano', 'impressora']
    ordering = ['-ano', '-mes']
