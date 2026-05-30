# GerPrint — Sistema de Gestão de Impressoras
# Copyright (C) 2025  Aderson Silva <aderson.slv@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
import csv
import json
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Max
from .models import Impressora, LeituraContador, RelatorioMensal, AgendamentoColeta
from .forms import ImpressoraForm, LeituraManualForm


MESES_PT = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
             'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']


def _ano_padrao():
    from .models import RelatorioMensal
    ultimo = RelatorioMensal.objects.values_list('ano', flat=True).order_by('-ano').first()
    return ultimo or timezone.now().year


def _mes_padrao(ano):
    from .models import RelatorioMensal
    ultimo = RelatorioMensal.objects.filter(ano=ano).values_list('mes', flat=True).order_by('-mes').first()
    return ultimo or timezone.now().month


def dashboard(request):
    ano = int(request.GET.get('ano', _ano_padrao()))
    mes = int(request.GET.get('mes', _mes_padrao(ano)))

    impressoras = Impressora.objects.filter(ativo=True)
    total_impressoras = impressoras.count()
    total_inativas = Impressora.objects.filter(ativo=False).count()

    relatorios_mes = RelatorioMensal.objects.filter(ano=ano, mes=mes)
    total_paginas_mes = relatorios_mes.aggregate(t=Sum('paginas_impressas'))['t'] or 0
    custo_mes = relatorios_mes.aggregate(t=Sum('custo_total'))['t'] or 0

    # Volume mensal acumulado (todos meses do ano)
    labels_meses = []
    data_volumes = []
    data_custos = []
    for m in range(1, 13):
        rel = RelatorioMensal.objects.filter(ano=ano, mes=m)
        paginas = rel.aggregate(t=Sum('paginas_impressas'))['t'] or 0
        custo = float(rel.aggregate(t=Sum('custo_total'))['t'] or 0)
        labels_meses.append(MESES_PT[m - 1])
        data_volumes.append(paginas)
        data_custos.append(custo)

    # Top impressoras por volume no mês
    top_impressoras = (
        RelatorioMensal.objects.filter(ano=ano, mes=mes)
        .select_related('impressora')
        .order_by('-paginas_impressas')[:10]
    )

    # Status SNMP (última leitura)
    status_list = []
    for imp in impressoras:
        ultima = imp.ultima_leitura()
        status_list.append({
            'impressora': imp,
            'ultima_leitura': ultima,
            'online': ultima and not ultima.erro if ultima else False,
        })

    anos_disponiveis = (
        RelatorioMensal.objects.values_list('ano', flat=True)
        .distinct().order_by('-ano')
    )

    context = {
        'ano': ano,
        'mes': mes,
        'mes_nome': MESES_PT[mes - 1],
        'total_impressoras': total_impressoras,
        'total_inativas': total_inativas,
        'total_paginas_mes': total_paginas_mes,
        'custo_mes': custo_mes,
        'labels_meses': json.dumps(labels_meses),
        'data_volumes': json.dumps(data_volumes),
        'data_custos': json.dumps(data_custos),
        'top_impressoras': top_impressoras,
        'status_list': status_list,
        'anos_disponiveis': anos_disponiveis,
        'meses_range': range(1, 13),
        'meses_pt': MESES_PT,
    }
    return render(request, 'impressoras/dashboard.html', context)


def impressora_list(request):
    impressoras = Impressora.objects.all().prefetch_related('leituras')
    context = {'impressoras': impressoras}
    return render(request, 'impressoras/impressora_list.html', context)


def impressora_detail(request, pk):
    imp = get_object_or_404(Impressora, pk=pk)
    ano = int(request.GET.get('ano', timezone.now().year))

    relatorios = imp.relatorios.filter(ano=ano).order_by('mes')
    leituras = imp.leituras.order_by('-lido_em')[:30]

    labels = [MESES_PT[r.mes - 1] for r in relatorios]
    data_paginas = [r.paginas_impressas for r in relatorios]
    data_custos = [float(r.custo_total) for r in relatorios]

    anos = imp.relatorios.values_list('ano', flat=True).distinct().order_by('-ano')

    context = {
        'impressora': imp,
        'ano': ano,
        'relatorios': relatorios,
        'leituras': leituras,
        'labels': json.dumps(labels),
        'data_paginas': json.dumps(data_paginas),
        'data_custos': json.dumps(data_custos),
        'anos': anos,
    }
    return render(request, 'impressoras/impressora_detail.html', context)


def impressora_create(request):
    if request.method == 'POST':
        form = ImpressoraForm(request.POST)
        if form.is_valid():
            imp = form.save()
            messages.success(request, f'Impressora "{imp.nome}" cadastrada com sucesso.')
            return redirect('impressora_detail', pk=imp.pk)
    else:
        form = ImpressoraForm()
    return render(request, 'impressoras/impressora_form.html', {'form': form, 'titulo': 'Nova Impressora'})


def impressora_edit(request, pk):
    imp = get_object_or_404(Impressora, pk=pk)
    if request.method == 'POST':
        form = ImpressoraForm(request.POST, instance=imp)
        if form.is_valid():
            form.save()
            messages.success(request, 'Impressora atualizada.')
            return redirect('impressora_detail', pk=imp.pk)
    else:
        form = ImpressoraForm(instance=imp)
    return render(request, 'impressoras/impressora_form.html', {'form': form, 'titulo': 'Editar Impressora', 'impressora': imp})


def impressora_delete(request, pk):
    imp = get_object_or_404(Impressora, pk=pk)
    if request.method == 'POST':
        nome = imp.nome
        imp.delete()
        messages.success(request, f'Impressora "{nome}" removida.')
        return redirect('impressora_list')
    return render(request, 'impressoras/impressora_confirm_delete.html', {'impressora': imp})


def coletar_agora(request, pk=None):
    from .snmp_collector import coletar_impressora, coletar_todas
    if pk:
        imp = get_object_or_404(Impressora, pk=pk)
        try:
            leitura = coletar_impressora(imp)
            if leitura.erro:
                messages.error(request, f'Erro SNMP: {leitura.erro}')
            else:
                messages.success(request, f'Coletado: {leitura.valor_contador} páginas.')
        except Exception as e:
            messages.error(request, f'Falha na coleta: {e}')
        return redirect('impressora_detail', pk=pk)
    else:
        resultados = coletar_todas()
        ok = sum(1 for r in resultados if r['ok'])
        messages.success(request, f'Coleta concluída: {ok}/{len(resultados)} impressoras.')
        return redirect('dashboard')


def leitura_manual(request, pk):
    imp = get_object_or_404(Impressora, pk=pk)
    if request.method == 'POST':
        form = LeituraManualForm(request.POST)
        if form.is_valid():
            leitura = form.save(commit=False)
            leitura.impressora = imp
            leitura.manual = True
            leitura.save()
            messages.success(request, 'Leitura registrada.')
            return redirect('impressora_detail', pk=pk)
    else:
        form = LeituraManualForm()
    return render(request, 'impressoras/leitura_manual.html', {'form': form, 'impressora': imp})


def _executar_agendamento(ag):
    from .snmp_collector import coletar_impressora, coletar_todas
    if ag.todas:
        resultados = coletar_todas()
        ok = sum(1 for r in resultados if r['ok'])
        log = f'{ok}/{len(resultados)} impressoras OK'
    else:
        leitura = coletar_impressora(ag.impressora)
        log = f'{leitura.valor_contador} págs' if not leitura.erro else f'Erro: {leitura.erro}'
    ag.ultima_execucao = timezone.now()
    ag.proxima_execucao = ag.calcular_proxima()
    ag.save(update_fields=['ultima_execucao', 'proxima_execucao'])
    return log


def coletar_view(request):
    impressoras = Impressora.objects.filter(ativo=True).order_by('nome')
    agendamentos = AgendamentoColeta.objects.select_related('impressora').order_by('proxima_execucao')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'coletar':
            from .snmp_collector import coletar_impressora, coletar_todas
            imp_id = request.POST.get('impressora_id')
            if imp_id == 'todas':
                resultados = coletar_todas()
                ok = sum(1 for r in resultados if r['ok'])
                messages.success(request, f'Coleta concluída: {ok}/{len(resultados)} impressoras OK.')
            else:
                imp = get_object_or_404(Impressora, pk=imp_id)
                leitura = coletar_impressora(imp)
                if leitura.erro:
                    messages.error(request, f'Erro SNMP em {imp.nome}: {leitura.erro}')
                else:
                    messages.success(request, f'{imp.nome}: {leitura.valor_contador} páginas coletadas.')

        elif action == 'agendar':
            from datetime import time as dtime
            nome = request.POST.get('nome', '').strip()
            imp_id = request.POST.get('impressora_id', 'todas')
            frequencia = request.POST.get('frequencia', 'diaria')
            horario_str = request.POST.get('horario', '')
            intervalo = max(1, int(request.POST.get('intervalo_minutos', 60) or 60))

            ag = AgendamentoColeta(
                nome=nome,
                todas=(imp_id == 'todas'),
                impressora=None if imp_id == 'todas' else get_object_or_404(Impressora, pk=imp_id),
                frequencia=frequencia,
                intervalo_minutos=intervalo,
                proxima_execucao=timezone.now(),
            )
            if frequencia == 'diaria' and horario_str:
                h, m = map(int, horario_str.split(':'))
                ag.horario = dtime(h, m)
            ag.proxima_execucao = ag.calcular_proxima()
            ag.save()
            messages.success(request, f'Agendamento "{ag.nome}" criado com sucesso.')

        elif action == 'toggle':
            ag = get_object_or_404(AgendamentoColeta, pk=request.POST.get('agendamento_id'))
            ag.ativo = not ag.ativo
            ag.save(update_fields=['ativo'])
            estado = 'ativado' if ag.ativo else 'pausado'
            messages.success(request, f'Agendamento "{ag.nome}" {estado}.')

        elif action == 'excluir':
            ag = get_object_or_404(AgendamentoColeta, pk=request.POST.get('agendamento_id'))
            nome = ag.nome
            ag.delete()
            messages.success(request, f'Agendamento "{nome}" removido.')

        elif action == 'executar_agora':
            ag = get_object_or_404(AgendamentoColeta, pk=request.POST.get('agendamento_id'))
            try:
                log = _executar_agendamento(ag)
                messages.success(request, f'"{ag.nome}" executado: {log}')
            except Exception as e:
                messages.error(request, f'Falha ao executar "{ag.nome}": {e}')

        return redirect('coletar')

    context = {
        'impressoras': impressoras,
        'agendamentos': agendamentos,
        'now': timezone.now(),
    }
    return render(request, 'impressoras/coletar.html', context)


def relatorios_csv(request):
    ano = int(request.GET.get('ano', _ano_padrao()))
    tipo = request.GET.get('tipo', 'volume')  # 'volume' ou 'custos'

    relatorios = (
        RelatorioMensal.objects.filter(ano=ano)
        .select_related('impressora')
        .order_by('impressora__nome', 'mes')
    )

    pivot_dict = {}
    vol_totais_mes = [0] * 12
    custo_totais_mes = [0.0] * 12
    total_paginas_ano = 0
    total_custo_ano = 0.0

    for r in relatorios:
        pid = r.impressora_id
        if pid not in pivot_dict:
            pivot_dict[pid] = {
                'impressora': r.impressora,
                'meses': [None] * 12,
                'total_paginas': 0,
                'total_custo': 0.0,
            }
        pivot_dict[pid]['meses'][r.mes - 1] = r
        pivot_dict[pid]['total_paginas'] += r.paginas_impressas
        pivot_dict[pid]['total_custo'] += float(r.custo_total)
        vol_totais_mes[r.mes - 1] += r.paginas_impressas
        custo_totais_mes[r.mes - 1] += float(r.custo_total)
        total_paginas_ano += r.paginas_impressas
        total_custo_ano += float(r.custo_total)

    filename = f'relatorio_{tipo}_{ano}.csv'
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('﻿')  # BOM para Excel reconhecer UTF-8

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Impressora', 'Localização'] + MESES_PT + ['Total'])

    for row in pivot_dict.values():
        if tipo == 'custos':
            cells = [
                f"{float(r.custo_total):.2f}".replace('.', ',') if r else ''
                for r in row['meses']
            ]
            total = f"{row['total_custo']:.2f}".replace('.', ',')
        else:
            cells = [r.paginas_impressas if r else '' for r in row['meses']]
            total = row['total_paginas']

        writer.writerow([
            row['impressora'].nome,
            row['impressora'].localizacao or '',
            *cells,
            total,
        ])

    if tipo == 'custos':
        totais = [f"{v:.2f}".replace('.', ',') if v else '' for v in custo_totais_mes]
        total_geral = f"{total_custo_ano:.2f}".replace('.', ',')
    else:
        totais = [v if v else '' for v in vol_totais_mes]
        total_geral = total_paginas_ano

    writer.writerow(['Total Geral', '', *totais, total_geral])
    return response


def api_status(request):
    impressoras = Impressora.objects.filter(ativo=True)
    data = []
    for imp in impressoras:
        ultima = imp.ultima_leitura()
        data.append({
            'id': imp.pk,
            'nome': imp.nome,
            'ip': imp.ip,
            'contador': ultima.valor_contador if ultima else None,
            'nivel_toner': ultima.nivel_toner if ultima else None,
            'online': bool(ultima and not ultima.erro),
            'ultima_leitura': ultima.lido_em.isoformat() if ultima else None,
            'erro': ultima.erro if ultima else None,
        })
    return JsonResponse({'impressoras': data})


def relatorios_view(request):
    ano = int(request.GET.get('ano', _ano_padrao()))
    relatorios = (
        RelatorioMensal.objects.filter(ano=ano)
        .select_related('impressora')
        .order_by('impressora__nome', 'mes')
    )
    anos = RelatorioMensal.objects.values_list('ano', flat=True).distinct().order_by('-ano')

    pivot_dict = {}
    vol_totais_mes = [0] * 12
    custo_totais_mes = [0.0] * 12
    total_paginas_ano = 0
    total_custo_ano = 0.0

    for r in relatorios:
        pid = r.impressora_id
        if pid not in pivot_dict:
            pivot_dict[pid] = {
                'impressora': r.impressora,
                'meses': [None] * 12,
                'total_paginas': 0,
                'total_custo': 0.0,
            }
        pivot_dict[pid]['meses'][r.mes - 1] = r
        pivot_dict[pid]['total_paginas'] += r.paginas_impressas
        pivot_dict[pid]['total_custo'] += float(r.custo_total)
        vol_totais_mes[r.mes - 1] += r.paginas_impressas
        custo_totais_mes[r.mes - 1] += float(r.custo_total)
        total_paginas_ano += r.paginas_impressas
        total_custo_ano += float(r.custo_total)

    context = {
        'ano': ano,
        'anos': anos,
        'pivot': list(pivot_dict.values()),
        'meses_pt': MESES_PT,
        'vol_totais_mes': vol_totais_mes,
        'custo_totais_mes': [round(v, 2) for v in custo_totais_mes],
        'total_paginas_ano': total_paginas_ano,
        'total_custo_ano': round(total_custo_ano, 2),
    }
    return render(request, 'impressoras/relatorios.html', context)
