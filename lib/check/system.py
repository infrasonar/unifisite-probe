import aiohttp
from libprobe.asset import Asset
from lib.unificonn import get_session
from urllib.parse import quote


async def check_system(
    asset: Asset,
    asset_config: dict,
    check_config: dict
) -> dict:
    site_name = check_config.get('site', 'default')
    ssl = check_config.get('ssl', False)
    session, is_unifi_os = await get_session(asset, asset_config, check_config)
    uri = '/proxy/network/api/s/' if is_unifi_os else '/api/s/'
    url = f'{uri}{quote(site_name, safe="")}/stat/sysinfo'
    async with aiohttp.ClientSession(**session) as session:
        async with session.get(url, ssl=ssl) as resp:
            resp.raise_for_status()
            data = await resp.json()

    system = [{
        'name': d['name'],
        'timezone': d.get('timezone'),
        'autobackup': d.get('autobackup'),
        'build': d.get('build'),
        'version': d.get('version'),
        'previous_version': d.get('previous_version'),
        'data_retention_days': d.get('data_retention_days'),
        'data_retention_time_in_hours_for_5minutes_scale':
        d.get('data_retention_time_in_hours_for_5minutes_scale'),
        'data_retention_time_in_hours_for_hourly_scale':
        d.get('data_retention_time_in_hours_for_hourly_scale'),
        'data_retention_time_in_hours_for_daily_scale':
        d.get('data_retention_time_in_hours_for_daily_scale'),
        'data_retention_time_in_hours_for_monthly_scale':
        d.get('data_retention_time_in_hours_for_monthly_scale'),
        'data_retention_time_in_hours_for_others':
        d.get('data_retention_time_in_hours_for_others'),
        'update_available': d.get('update_available'),
        'update_downloaded': d.get('update_downloaded'),
        'live_chat': d.get('live_chat'),
        'store_enabled': d.get('store_enabled'),
        'hostname': d.get('hostname'),
        'ip_addrs': d.get('ip_addrs'),
        'inform_port': d.get('inform_port'),
        'https_port': d.get('https_port'),
        'portal_http_port': d.get('portal_http_port'),
        'override_inform_host': d.get('override_inform_host'),
        'image_maps_use_google_engine':
        d.get('image_maps_use_google_engine'),
        'radius_disconnect_running': d.get('radius_disconnect_running'),
        'facebook_wifi_registered': d.get('facebook_wifi_registered'),
        'sso_app_id': d.get('sso_app_id'),
        'sso_app_sec': d.get('sso_app_sec'),
        'uptime': d.get('uptime'),
        'anonymous_controller_id': d.get('anonymous_controller_id'),
        'has_webrtc_support': d.get('has_webrtc_support'),
        'debug_setting_preference': d.get('debug_setting_preference'),
        'debug_mgmt': d.get('debug_mgmt'),
        'debug_system': d.get('debug_system'),
        'debug_device': d.get('debug_device'),
        'debug_sdn': d.get('debug_sdn'),
        'unsupported_device_count': d.get('unsupported_device_count'),
        # unsupported_device_list is a list but the list item type is not
        # documented; therefore we only keep unsupported_device_count
        # 'unsupported_device_list': d.get('unsupported_device_list'),
        'unifi_go_enabled': d.get('unifi_go_enabled'),
    } for d in data['data']]

    return {
        'system': system
    }
