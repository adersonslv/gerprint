# GerPrint — Sistema de Gestão de Impressoras
# Copyright (C) 2025  Aderson Silva <aderson.slv@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from pysnmp.hlapi.v1arch.asyncio import *  # noqa: F401, F403

logger = logging.getLogger(__name__)

# HOST-RESOURCES-MIB — OIDs de status padrão (sem configuração por impressora)
_OID_HR_PRINTER_STATUS     = '1.3.6.1.2.1.25.3.5.1.1.1'
_OID_HR_ERROR_STATE        = '1.3.6.1.2.1.25.3.5.1.2.1'
_OID_HR_DEVICE_STATUS      = '1.3.6.1.2.1.25.3.2.1.5.1'

# Bitmask hrPrinterDetectedErrorState (RFC 2790)
# Bit 0 = MSB do primeiro byte (0x80), bit 7 = LSB (0x01), bit 8 = MSB do segundo byte, etc.
_ERROR_BITS = [
    (0,  'Papel baixo'),
    (1,  'Sem papel'),
    (2,  'Toner baixo'),
    (3,  'Sem toner'),
    (4,  'Tampa aberta'),
    (5,  'Atolamento de papel'),
    (6,  'Offline'),
    (7,  'Serviço necessário'),
    (8,  'Bandeja de entrada ausente'),
    (9,  'Bandeja de saída ausente'),
    (10, 'Cartucho ausente'),
    (11, 'Saída quase cheia'),
    (12, 'Saída cheia'),
    (13, 'Bandeja de entrada vazia'),
    (14, 'Manutenção preventiva pendente'),
    (15, 'Bandeja de saída quase cheia'),
]

_HR_DEVICE_STATUS = {1: 'Desconhecido', 2: 'Operando', 3: 'Aviso', 4: 'Testando', 5: 'Parado'}


def _decodificar_error_state(raw_bytes: bytes) -> str:
    """Converte o bitmask hrPrinterDetectedErrorState em lista de erros em PT-BR."""
    erros = []
    for bit, descricao in _ERROR_BITS:
        byte_idx = bit // 8
        bit_offset = 7 - (bit % 8)  # MSB primeiro
        if byte_idx < len(raw_bytes) and (raw_bytes[byte_idx] >> bit_offset) & 1:
            erros.append(descricao)
    return ', '.join(erros)


async def _snmp_get_async(ip, community, version, oid):
    if version == '1':
        auth = CommunityData(community, mpModel=0)
    else:
        auth = CommunityData(community, mpModel=1)

    transport = await UdpTransportTarget.create((ip, 161), timeout=2, retries=1)
    obj = ObjectType(ObjectIdentity(oid))

    errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
        SnmpDispatcher(), auth, transport, obj
    )

    if errorIndication:
        return None, str(errorIndication)
    if errorStatus:
        return None, str(errorStatus)

    for varBind in varBinds:
        raw = varBind[1]
        if raw.__class__.__name__ in ('NoSuchObject', 'NoSuchInstance', 'EndOfMibView'):
            return None, f'OID não suportado: {raw.__class__.__name__}'
        try:
            return int(raw), None
        except (ValueError, TypeError) as e:
            return None, f'valor não inteiro: {raw!r} ({e})'

    return None, 'sem dados'


def snmp_get(ip, community, version, oid):
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            value, error = loop.run_until_complete(_snmp_get_async(ip, community, version, oid))
        finally:
            loop.run_until_complete(asyncio.sleep(0))
            loop.close()
        return value, error
    except Exception as e:
        return None, str(e)


def snmp_get_total(ip, community, version, oid_campo):
    """Suporta múltiplos OIDs (um por linha) somando os resultados."""
    oids = [o.strip() for o in oid_campo.splitlines() if o.strip()]
    if not oids:
        return None, 'nenhum OID configurado'

    if len(oids) == 1:
        return snmp_get(ip, community, version, oids[0])

    total = 0
    erros = []
    for oid in oids:
        val, err = snmp_get(ip, community, version, oid)
        if val is not None:
            total += val
        else:
            erros.append(f'{oid}: {err}')

    if erros and total == 0:
        return None, ' | '.join(erros)
    return total, (' | '.join(erros) if erros else None)


def _coletar_status_hw(ip, community, version) -> str:
    """Lê os OIDs de status padrão e retorna string de erros (vazia = OK)."""
    import asyncio

    async def _async():
        mp = 0 if version == '1' else 1
        auth = CommunityData(community, mpModel=mp)
        try:
            transport = await UdpTransportTarget.create((ip, 161), timeout=2, retries=1)
        except Exception:
            return ''

        disp = SnmpDispatcher()
        partes = []

        # hrDeviceStatus — estado geral do dispositivo
        err, estat, _, vbs = await get_cmd(disp, auth, transport,
                                           ObjectType(ObjectIdentity(_OID_HR_DEVICE_STATUS)))
        if not err and not estat:
            val = vbs[0][1]
            cls = val.__class__.__name__
            if cls not in ('NoSuchObject', 'NoSuchInstance', 'EndOfMibView'):
                codigo = int(val)
                if codigo >= 3:  # 3=warning 4=testing 5=down
                    partes.append(_HR_DEVICE_STATUS.get(codigo, f'Status {codigo}'))

        # hrPrinterDetectedErrorState — bitmask de erros de hardware
        err, estat, _, vbs = await get_cmd(disp, auth, transport,
                                           ObjectType(ObjectIdentity(_OID_HR_ERROR_STATE)))
        if not err and not estat:
            val = vbs[0][1]
            cls = val.__class__.__name__
            if cls not in ('NoSuchObject', 'NoSuchInstance', 'EndOfMibView'):
                raw = bytes(val)
                if any(raw):  # pelo menos um byte não-zero
                    decoded = _decodificar_error_state(raw)
                    if decoded:
                        partes.append(decoded)

        return ', '.join(partes)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_async())
    except Exception:
        return ''
    finally:
        loop.run_until_complete(asyncio.sleep(0))
        loop.close()


def _coletar_nivel_toner(impressora, toner_cfg):
    """Retorna o nível (0-100) de um TonerConfig, ou None em caso de erro."""
    nivel, erro = snmp_get(impressora.ip, impressora.comunidade_snmp, impressora.versao_snmp, toner_cfg.oid)
    if erro:
        logger.warning(f'Toner {toner_cfg.nome} em {impressora.nome}: {erro}')
        return None
    if nivel is None:
        return None
    if nivel > 100:
        oid_max = toner_cfg.oid.replace('.9.', '.8.')
        if oid_max != toner_cfg.oid:
            capacidade_max, _ = snmp_get(impressora.ip, impressora.comunidade_snmp, impressora.versao_snmp, oid_max)
            if capacidade_max and capacidade_max > 0:
                return round(nivel * 100 / capacidade_max)
            logger.warning(f'Toner {toner_cfg.nome} em {impressora.nome}: não foi possível obter capacidade máxima')
            return None
    return nivel


def coletar_impressora(impressora):
    from django.utils import timezone

    from .models import LeituraContador, LeituraToner

    valor, erro = snmp_get_total(
        impressora.ip,
        impressora.comunidade_snmp,
        impressora.versao_snmp,
        impressora.oid_contador,
    )

    toner_readings = []
    for toner_cfg in impressora.toners.order_by('ordem', 'cor'):
        nivel = _coletar_nivel_toner(impressora, toner_cfg)
        if nivel is not None:
            toner_readings.append((toner_cfg, nivel))

    # nivel_toner = pior toner (mínimo) para compatibilidade com exibições simples
    nivel_toner = min(n for _, n in toner_readings) if toner_readings else None

    status_hw = _coletar_status_hw(impressora.ip, impressora.comunidade_snmp, impressora.versao_snmp)
    if status_hw:
        logger.warning(f'Status HW {impressora.nome} ({impressora.ip}): {status_hw}')

    leitura = LeituraContador(
        impressora=impressora,
        lido_em=timezone.now(),
        valor_contador=valor if valor is not None else 0,
        nivel_toner=nivel_toner,
        erro=erro or '',
        status_hw=status_hw,
    )
    leitura.save()

    for toner_cfg, nivel in toner_readings:
        LeituraToner.objects.create(
            leitura=leitura,
            toner=toner_cfg,
            nome=toner_cfg.nome,
            cor=toner_cfg.cor,
            nivel=nivel,
            ordem=toner_cfg.ordem,
        )

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
