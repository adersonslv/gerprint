# GerPrint — Sistema de Gestão de Impressoras
# Copyright (C) 2025  Aderson Silva <aderson.slv@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from pysnmp.hlapi.v1arch.asyncio import *

logger = logging.getLogger(__name__)


async def _snmp_get_async(ip, community, version, oid):
    if version == '1':
        auth = CommunityData(community, mpModel=0)
    else:
        auth = CommunityData(community, mpModel=1)

    transport = await UdpTransportTarget.create((ip, 161), timeout=2, retries=1)
    context = ContextData()
    obj = ObjectType(ObjectIdentity(oid))

    errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
        SnmpDispatcher(), auth, transport, context, obj
    )

    if errorIndication:
        return None, str(errorIndication)
    if errorStatus:
        return None, str(errorStatus)

    for varBind in varBinds:
        return int(varBind[1]), None

    return None, 'sem dados'


def snmp_get(ip, community, version, oid):
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        value, error = loop.run_until_complete(_snmp_get_async(ip, community, version, oid))
        loop.close()
        return value, error
    except Exception as e:
        return None, str(e)


def coletar_impressora(impressora):
    from .models import LeituraContador
    from django.utils import timezone

    valor, erro = snmp_get(
        impressora.ip,
        impressora.comunidade_snmp,
        impressora.versao_snmp,
        impressora.oid_contador,
    )

    nivel_toner = None
    if impressora.oid_toner and valor is not None:
        nivel_toner, _ = snmp_get(
            impressora.ip,
            impressora.comunidade_snmp,
            impressora.versao_snmp,
            impressora.oid_toner,
        )

    leitura = LeituraContador(
        impressora=impressora,
        lido_em=timezone.now(),
        valor_contador=valor if valor is not None else 0,
        nivel_toner=nivel_toner,
        erro=erro or '',
    )
    leitura.save()
    return leitura


def coletar_todas():
    from .models import Impressora
    resultados = []
    for impressora in Impressora.objects.filter(ativo=True):
        try:
            leitura = coletar_impressora(impressora)
            resultados.append({'impressora': impressora.nome, 'ok': not leitura.erro, 'erro': leitura.erro})
            logger.info(f'Coleta {impressora.nome}: {leitura.valor_contador}')
        except Exception as e:
            resultados.append({'impressora': impressora.nome, 'ok': False, 'erro': str(e)})
            logger.error(f'Erro ao coletar {impressora.nome}: {e}')
    return resultados
