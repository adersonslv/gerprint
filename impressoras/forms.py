# GerPrint — Sistema de Gestão de Impressoras
# Copyright (C) 2025  Aderson Silva <aderson.slv@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
from django import forms
from django.forms import inlineformset_factory

from .models import Impressora, LeituraContador, TonerConfig


class ImpressoraForm(forms.ModelForm):
    class Meta:
        model = Impressora
        fields = [
            'nome', 'entidade', 'localizacao', 'numero_serie', 'ip',
            'comunidade_snmp', 'versao_snmp', 'oid_contador',
            'custo_por_pagina', 'franquia_mensal', 'ativo', 'observacoes',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'entidade': forms.TextInput(attrs={'class': 'form-control', 'list': 'entidades-datalist'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'ip': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '192.168.1.10'}),
            'comunidade_snmp': forms.TextInput(attrs={'class': 'form-control'}),
            'versao_snmp': forms.Select(attrs={'class': 'form-select'}),
            'oid_contador': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 3,
                'placeholder': '1.3.6.1.2.1.43.10.2.1.4.1.1\n(um OID por linha — valores somados)',
            }),
            'custo_por_pagina': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'franquia_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


TonerFormSet = inlineformset_factory(
    Impressora, TonerConfig,
    fields=['nome', 'cor', 'oid', 'ordem'],
    widgets={
        'nome': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'ex: Toner Preto'}),
        'cor': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        'oid': forms.TextInput(attrs={'class': 'form-control form-control-sm font-monospace', 'placeholder': '1.3.6.1...'}),
        'ordem': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:65px', 'min': 0}),
    },
    extra=1,
    can_delete=True,
)


class LeituraManualForm(forms.ModelForm):
    class Meta:
        model = LeituraContador
        fields = ['lido_em', 'valor_contador', 'nivel_toner']
        widgets = {
            'lido_em': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valor_contador': forms.NumberInput(attrs={'class': 'form-control'}),
            'nivel_toner': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }
