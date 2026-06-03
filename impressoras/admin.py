# GerPrint — Sistema de Gestão de Impressoras
# Copyright (C) 2025  Aderson Silva <aderson.slv@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib import admin

from .models import Impressora, LeituraContador, LeituraToner, RelatorioMensal, TonerConfig


class TonerConfigInline(admin.TabularInline):
    model = TonerConfig
    extra = 1
    fields = ['nome', 'cor', 'oid', 'ordem']


@admin.register(Impressora)
class ImpressoraAdmin(admin.ModelAdmin):
    list_display = ['nome', 'entidade', 'localizacao', 'ip', 'versao_snmp', 'custo_por_pagina', 'ativo']
    list_filter = ['ativo', 'versao_snmp', 'entidade']
    search_fields = ['nome', 'ip', 'numero_serie', 'entidade']
    list_editable = ['ativo']
    inlines = [TonerConfigInline]


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
