# GerPrint — Sistema de Gestão de Impressoras
# Copyright (C) 2025  Aderson Silva <aderson.slv@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import datetime, timedelta

from django.db import models
from django.utils import timezone


class Impressora(models.Model):
    SNMP_VERSION = [
        ('1', 'v1'),
        ('2c', 'v2c'),
        ('3', 'v3'),
    ]

    nome = models.CharField(max_length=200)
    entidade = models.CharField(max_length=200, blank=True)
    localizacao = models.CharField(max_length=200, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    ip = models.GenericIPAddressField()
    comunidade_snmp = models.CharField(max_length=100, default='public')
    versao_snmp = models.CharField(max_length=3, choices=SNMP_VERSION, default='2c')
    oid_contador = models.CharField(max_length=200, default='1.3.6.1.2.1.43.10.2.1.4.1.1')
    oid_toner = models.CharField(max_length=200, blank=True)
    custo_por_pagina = models.DecimalField(max_digits=6, decimal_places=4, default=0.10)
    franquia_mensal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Impressora'
        verbose_name_plural = 'Impressoras'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.ip})'

    def ultima_leitura(self):
        if hasattr(self, '_ultima'):
            return self._ultima
        return self.leituras.order_by('-lido_em').first()

    def leitura_mes(self, ano, mes):
        return self.leituras.filter(lido_em__year=ano, lido_em__month=mes).order_by('-lido_em').first()


COR_CSS = {
    'K': '#212529',
    'C': '#0dcaf0',
    'M': '#d63384',
    'Y': '#ffc107',
    'O': '#6c757d',
}


class TonerConfig(models.Model):
    COR_CHOICES = [
        ('K', 'Preto'),
        ('C', 'Ciano'),
        ('M', 'Magenta'),
        ('Y', 'Amarelo'),
        ('O', 'Outro'),
    ]

    impressora = models.ForeignKey(Impressora, on_delete=models.CASCADE, related_name='toners')
    nome = models.CharField(max_length=50, default='Toner')
    cor = models.CharField(max_length=1, choices=COR_CHOICES, default='K')
    oid = models.CharField(max_length=200)
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Configuração de Toner'
        verbose_name_plural = 'Configurações de Toner'
        ordering = ['ordem', 'cor']

    def __str__(self):
        return f'{self.impressora.nome} — {self.nome}'

    @property
    def cor_css(self):
        return COR_CSS.get(self.cor, '#6c757d')


class LeituraContador(models.Model):
    impressora = models.ForeignKey(Impressora, on_delete=models.CASCADE, related_name='leituras')
    lido_em = models.DateTimeField(default=timezone.now)
    valor_contador = models.BigIntegerField()
    nivel_toner = models.IntegerField(null=True, blank=True)
    manual = models.BooleanField(default=False)
    erro = models.CharField(max_length=300, blank=True)
    status_hw = models.CharField(max_length=300, blank=True)

    class Meta:
        verbose_name = 'Leitura de Contador'
        verbose_name_plural = 'Leituras de Contadores'
        ordering = ['-lido_em']

    def __str__(self):
        return f'{self.impressora.nome} - {self.lido_em:%d/%m/%Y %H:%M} - {self.valor_contador}'


class LeituraToner(models.Model):
    leitura = models.ForeignKey(LeituraContador, on_delete=models.CASCADE, related_name='toners')
    toner = models.ForeignKey(TonerConfig, on_delete=models.SET_NULL, null=True)
    nome = models.CharField(max_length=50)
    cor = models.CharField(max_length=1)
    nivel = models.IntegerField()
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Leitura de Toner'
        verbose_name_plural = 'Leituras de Toner'
        ordering = ['ordem', 'cor']

    @property
    def cor_css(self):
        return COR_CSS.get(self.cor, '#6c757d')


class RelatorioMensal(models.Model):
    impressora = models.ForeignKey(Impressora, on_delete=models.CASCADE, related_name='relatorios')
    ano = models.IntegerField()
    mes = models.IntegerField()
    contador_inicial = models.BigIntegerField(default=0)
    contador_final = models.BigIntegerField(default=0)
    paginas_impressas = models.BigIntegerField(default=0)
    custo_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Relatório Mensal'
        verbose_name_plural = 'Relatórios Mensais'
        unique_together = ('impressora', 'ano', 'mes')
        ordering = ['-ano', '-mes']

    def __str__(self):
        return f'{self.impressora.nome} - {self.mes:02d}/{self.ano}'

    def save(self, *args, **kwargs):
        self.paginas_impressas = max(0, self.contador_final - self.contador_inicial)
        self.custo_total = self.paginas_impressas * self.impressora.custo_por_pagina
        super().save(*args, **kwargs)


class AgendamentoColeta(models.Model):
    FREQUENCIA_CHOICES = [
        ('diaria', 'Diária (horário fixo)'),
        ('intervalo', 'A cada X minutos'),
    ]

    nome = models.CharField(max_length=100)
    impressora = models.ForeignKey(
        Impressora, on_delete=models.CASCADE,
        null=True, blank=True, related_name='agendamentos',
        help_text='Deixe em branco para coletar todas as impressoras'
    )
    todas = models.BooleanField(default=False)
    frequencia = models.CharField(max_length=20, choices=FREQUENCIA_CHOICES, default='diaria')
    horario = models.TimeField(null=True, blank=True)
    intervalo_minutos = models.PositiveIntegerField(default=60)
    ativo = models.BooleanField(default=True)
    proxima_execucao = models.DateTimeField()
    ultima_execucao = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Agendamento de Coleta'
        verbose_name_plural = 'Agendamentos de Coleta'
        ordering = ['proxima_execucao']

    def __str__(self):
        alvo = 'Todas' if self.todas else (self.impressora.nome if self.impressora else '?')
        return f'{self.nome} — {alvo}'

    def alvo_str(self):
        if self.todas:
            return 'Todas as impressoras'
        return self.impressora.nome if self.impressora else '—'

    def calcular_proxima(self):
        now = timezone.localtime(timezone.now())
        if self.frequencia == 'diaria' and self.horario:
            dt = datetime.combine(now.date(), self.horario)
            proxima = timezone.make_aware(dt)
            if proxima <= timezone.now():
                proxima += timedelta(days=1)
            return proxima
        return timezone.now() + timedelta(minutes=self.intervalo_minutos)

    def esta_vencido(self):
        return timezone.now() >= self.proxima_execucao
