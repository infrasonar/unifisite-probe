import aiohttp
from libprobe.asset import Asset
from libprobe.check import Check
from lib.unificonn import get_credentials, sanity_check
from urllib.parse import quote
from ..connector import get_connector


DEVICE_STATE = {
    0: 'offline',
    1: 'connected',
    2: 'pending adoption',
    4: 'updating',
    5: 'provisioning',
    6: 'unreachable',
    7: 'adopting',
    8: 'deleting',
    9: 'adoption error',
    10: 'adoption failed',
    11: 'isolated',
}


class CheckDevice(Check):
    key = 'device'
    unchanged_eol = 14400

    @staticmethod
    async def run(asset: Asset, local_config: dict, config: dict) -> dict:

        site_name = config.get('site', 'default')
        ssl = config.get('ssl', False)
        credentials = await get_credentials(asset, local_config, config)

        base_url = credentials['base_url']
        is_unifi_os = credentials['is_unifi_os']
        cookies = credentials['cookies']
        headers = credentials['headers']

        site_name = quote(site_name, safe="")

        prefix = '/proxy/network' if is_unifi_os else ''
        url = f"{base_url}{prefix}/api/s/{site_name}/stat/device-basic"

        async with aiohttp.ClientSession(cookies=cookies,
                                         connector=get_connector()) as session:
            async with session.get(url, headers=headers, ssl=ssl) as resp:
                await sanity_check(resp, url)
                data = await resp.json()

        device = [{
            'name': d['mac'],  # str
            'device_name': d.get('name', d['mac']),  # str, mac fallback
            'state': DEVICE_STATE.get(d.get('state')),  # str
            'adopted': d.get('adopted'),  # bool
            'disabled': d.get('disabled'),  # bool
            'type': d.get('type'),  # str
            'model': d.get('model'),  # str
            'in_gateway_mode': d.get('in_gateway_mode'),  # bool
        } for d in data['data']]

        return {
            'device': device
        }
