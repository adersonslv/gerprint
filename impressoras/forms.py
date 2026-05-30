# GerPrint — Sistema de Gestão de Impressoras
# Copyright (C) 2025  Aderson Silva <aderson.slv@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
from django import forms
from .models import Impressora, LeituraContador


class ImpressoraForm(forms.ModelForm):
    class Meta:
        model = Impressora
        fields = [
            'nome', 'localizacao', 'numero_serie', 'ip',
            'comunidade_snmp', 'versao_snmp', 'oid_contador', 'oid_toner',
            'custo_por_pagina', 'franquia_mensal', 'ativo', 'observacoes',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'ip': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '192.168.1.10'}),
            'comunidade_snmp': forms.TextInput(attrs={'class': 'form-control'}),
            'versao_snmp': forms.Select(attrs={'class': 'form-select'}),
            'oid_contador': forms.TextInput(attrs={'class': 'form-control'}),
            'oid_toner': forms.TextInput(attrs={'class': 'form-control'}),
            'custo_por_pagina': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'franquia_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class LeituraManualForm(forms.ModelForm):
    class Meta:
        model = LeituraContador
        fields = ['lido_em', 'valor_contador', 'nivel_toner']
        widgets = {
            'lido_em': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valor_contador': forms.NumberInput(attrs={'class': 'form-control'}),
            'nivel_toner': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }
