import asyncio
from typing import List, Dict, Any, Optional
import logging
from services.arp_service import ARPService
from services.profile_resolver import resolve_profile
import subprocess

from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine,
    CommunityData,
    UsmUserData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    get_cmd,
)

logger = logging.getLogger(__name__)


class SNMPService:
    """
    Асинхронный SNMP сервис для v2c и v3.
    """

    def __init__(self, timeout: float = 2.0, retries: int = 0, concurrency: int = 50):
        self.timeout = timeout
        self.retries = retries
        self.semaphore = asyncio.Semaphore(concurrency)
        self.engine = SnmpEngine()  # общий движок SNMP

    async def _snmp_get_once(
        self,
        ip: str,
        oid: str,
        community: Optional[str] = None,
        v3_user: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Выполнить один GET-запрос к IP по SNMPv2c или v3.
        :param community: строка community для v2c
        :param v3_user: словарь с ключами 'user', 'authKey', 'authProtocol', 'privKey', 'privProtocol' для v3
        """
        async with self.semaphore:
            try:
                if v3_user:
                    user_data = UsmUserData(
                        v3_user["user"],
                        authKey=v3_user.get("authKey"),
                        authProtocol=v3_user.get("authProtocol"),
                        privKey=v3_user.get("privKey"),
                        privProtocol=v3_user.get("privProtocol"),
                    )
                else:
                    user_data = CommunityData(community or "public", mpModel=1)

                transport = await UdpTransportTarget.create(
                    (ip, 161),
                    self.timeout,
                    self.retries
                )

                errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
                    self.engine,
                    user_data,
                    transport,
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )

                if errorIndication:
                    return {"oid": oid, "error": str(errorIndication)}
                elif errorStatus:
                    return {"oid": oid, "error": str(errorStatus)}
                else:
                    for vb in varBinds:
                        return {"oid": oid, "value": vb[1].prettyPrint()}
                    return {"oid": oid, "error": "no varbinds"}

            except Exception as e:
                logger.exception("SNMP request error")
                return {"oid": oid, "error": str(e)}
    async def scan_device(self, ip, community=None, v3_user=None):
        alive = await self.ping(ip)
        # --- ШАГ 1: проверяем, жив ли хост ---
        if not alive:
            return {
                "ip": ip,
                "alive": alive,
                "mac": None,
                "snmp": {},
                "data": {},
            }

        # --- ШАГ 2: получаем MAC ---
        mac = ARPService.get_mac(ip)
        print(mac)
        # --- ШАГ 3: SNMP мини-опрос ---
        snmp = await self.get_device_info(ip, community, v3_user)

        device_info = {
            "ip": ip,
            "mac": mac,
            "snmp": snmp,
        }

        # --- ШАГ 4: выбираем профиль ---
        profile_class = resolve_profile(device_info)
        profile = profile_class(ip, mac)

        # --- ШАГ 5: детальное сканирование профиля ---
        try:
            data = await profile.scan(self)
        except Exception as e:
            logger.exception(f"Ошибка профиля для {ip}")
            data = {"error": str(e)}

        return {
            "ip": ip,
            "alive": True,
            "mac": mac,
            "snmp": snmp,
            "results": snmp,
            "profile": profile.__class__.__name__,
            "data": data,
        }
            
    async def _scan_target(
        self,
        ip: str,
        oids: List[str],
        community: Optional[str] = None,
        v3_user: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        logger.info(f"🚀 Начинаю сканирование {ip}")
        tasks = [self._snmp_get_once(ip, oid, community, v3_user) for oid in oids]
        responses = await asyncio.gather(*tasks, return_exceptions=False)
        results: Dict[str, Any] = {}
        for r in responses:
            if "value" in r:
                results[r["oid"]] = {"value": r["value"]}
            else:
                results[r["oid"]] = {"error": r.get("error", "unknown")}
        return {"ip": ip, "results": results}

    async def scan(
        self,
        targets: List[str],
        oids: Optional[List[str]] = None,
        community: Optional[str] = None,
        v3_user: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Сканирование списка IP-адресов.
        :param community: для v2c
        :param v3_user: для v3, словарь с ключами 'user', 'authKey', 'authProtocol', 'privKey', 'privProtocol'
        """
        original_timeout = self.timeout
        original_retries = self.retries
        if timeout is not None:
            self.timeout = timeout
        if retries is not None:
            self.retries = retries

        if not oids:
            oids = ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.5.0", "1.3.6.1.2.1.2.2.1.6.1"]

        tasks = [self.scan_device(ip, community, v3_user) for ip in targets]
        details = await asyncio.gather(*tasks, return_exceptions=False)

        # Восстановим параметры
        self.timeout = original_timeout
        self.retries = original_retries

        summary = {"requested": len(targets), "completed": len(details)}
        return {"summary": summary, "details": details}
    async def get_device_info(self, ip: str, community=None, v3_user=None) -> dict:
        """
        Мини-обследование устройства — только базовые ОИДы, чтобы определить тип.
        """
        try:
            return await self.get_many(ip, [
                "1.3.6.1.2.1.1.1.0",  # sysDescr
                "1.3.6.1.2.1.1.5.0",  # sysName
            ], community=community, v3_user=v3_user)
        except Exception:
            return {}
    async def get_many(self, ip: str, oids: list, community=None, v3_user=None):
        tasks = [
            self._snmp_get_once(ip, oid, community=community, v3_user=v3_user)
            for oid in oids
        ]
        responses = await asyncio.gather(*tasks)

        results = {}
        for r in responses:
            if "value" in r:
                results[r["oid"]] = {"value": r["value"]}
            else:
                results[r["oid"]] = {"error": r.get("error", "unknown")}

        return results
    import asyncio

    async def ping(self, ip: str) -> bool:
        try:
            result = subprocess.run(
                ["cmd", "/c", f"ping -n 1 -w 400 {ip}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="cp866"
            )
            return result.returncode == 0
        except:
            return False