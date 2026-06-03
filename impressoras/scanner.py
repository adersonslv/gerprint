# GerPrint — Sistema de Gestão de Impressoras
# Copyright (C) 2025  Aderson Silva <aderson.slv@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
import asyncio
import ipaddress
import logging
import socket

from pysnmp.hlapi.v1arch.asyncio import (
    CommunityData,
    ObjectIdentity,
    ObjectType,
    SnmpDispatcher,
    UdpTransportTarget,
    get_cmd,
)

logger = logging.getLogger(__name__)

_PRINTER_KEYWORDS = [
    'printer', 'print', 'ricoh', 'aficio', 'canon', 'brother', 'hp ',
    'epson', 'kyocera', 'lexmark', 'xerox', 'konica', 'minolta', 'sharp',
    'laserjet', 'pixma', 'officejet', 'ecosys', 'imagerunner', 'imageclass',
    'mf', 'lbp', 'mfc-', 'hl-', 'dcp-',
]

_OID_SYS_DESCR   = '1.3.6.1.2.1.1.1.0'
_OID_SYS_NAME    = '1.3.6.1.2.1.1.5.0'
_OID_SYS_CONTACT = '1.3.6.1.2.1.1.4.0'
_OID_SYS_LOCATION= '1.3.6.1.2.1.1.6.0'
_OID_COUNTER     = '1.3.6.1.2.1.43.10.2.1.4.1.1'   # prtMarkerLifeCount
_OID_MODEL_RICOH = '1.3.6.1.4.1.367.3.2.1.1.1.1.0'


def _snmp_str(val) -> str | None:
    if val is None:
        return None
    cls = val.__class__.__name__
    if cls in ('NoSuchObject', 'NoSuchInstance', 'EndOfMibView'):
        return None
    raw = bytes(val) if cls == 'OctetString' else str(val).encode()
    return raw.decode('utf-8', errors='replace').strip()


async def _get_one(dispatcher, auth, transport, oid):
    try:
        err, estat, _, vbs = await get_cmd(dispatcher, auth, transport,
                                           ObjectType(ObjectIdentity(oid)))
        if err or estat:
            return None
        return vbs[0][1]
    except Exception:
        return None


async def _probe(ip: str, community: str) -> dict | None:
    try:
        auth = CommunityData(community, mpModel=1)
        transport = await UdpTransportTarget.create(
            (ip, 161), timeout=0.9, retries=0
        )
    except Exception:
        return None

    disp = SnmpDispatcher()

    sys_descr_val = await _get_one(disp, auth, transport, _OID_SYS_DESCR)
    if sys_descr_val is None:
        return None  # sem resposta SNMP

    sys_descr  = _snmp_str(sys_descr_val) or ''
    sys_name   = _snmp_str(await _get_one(disp, auth, transport, _OID_SYS_NAME))   or ''
    sys_loc    = _snmp_str(await _get_one(disp, auth, transport, _OID_SYS_LOCATION)) or ''
    model_ricoh= _snmp_str(await _get_one(disp, auth, transport, _OID_MODEL_RICOH)) or ''

    # Verifica se é impressora pelo OID do contador
    contador_val = await _get_one(disp, auth, transport, _OID_COUNTER)
    is_printer = (contador_val is not None and
                  contador_val.__class__.__name__ not in
                  ('NoSuchObject', 'NoSuchInstance', 'EndOfMibView'))

    # Fallback: palavras-chave no sysDescr / sysName
    if not is_printer:
        combined = (sys_descr + ' ' + sys_name + ' ' + model_ricoh).lower()
        is_printer = any(kw in combined for kw in _PRINTER_KEYWORDS)

    nome = model_ricoh or sys_name or sys_descr[:60]

    return {
        'ip': ip,
        'nome': nome[:80],
        'descr': sys_descr[:120],
        'localizacao': sys_loc[:80],
        'comunidade': community,
        'is_printer': is_printer,
        'contador': (int(contador_val)
                     if is_printer and contador_val is not None
                     and contador_val.__class__.__name__ not in
                     ('NoSuchObject', 'NoSuchInstance', 'EndOfMibView')
                     else None),
    }


async def _scan_async(subnet: str, community: str) -> list[dict]:
    network = ipaddress.IPv4Network(subnet, strict=False)
    if network.num_addresses > 1024:
        raise ValueError(f'Rede muito grande ({network.num_addresses} endereços). Use uma sub-rede /24 ou menor.')

    sem = asyncio.Semaphore(80)

    async def limited(ip):
        async with sem:
            return await _probe(str(ip), community)

    tasks = [limited(ip) for ip in network.hosts()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, dict)]


def escanear(subnet: str, community: str = 'public') -> list[dict]:
    """Varre a sub-rede via SNMP e retorna dispositivos encontrados."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_scan_async(subnet, community))
    finally:
        loop.run_until_complete(asyncio.sleep(0.05))
        loop.close()


def detectar_subnet() -> str:
    """Detecta automaticamente a sub-rede local (/24)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return str(ipaddress.IPv4Network(f'{local_ip}/24', strict=False))
    except Exception:
        return '192.168.1.0/24'
