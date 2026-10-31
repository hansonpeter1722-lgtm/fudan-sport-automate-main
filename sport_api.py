from geopy.point import Point
import requests
import json
import os


def _redact(text, limit=200):
    """打日志时把 token/userid 抹掉，仓库是公开的，日志也是公开的。"""
    out = str(text)[:limit]
    for secret_name in ('FUDAN_SPORT_TOKEN', 'USER_ID'):
        value = os.getenv(secret_name)
        if value:
            out = out.replace(value, '***')
    return out


def _fail(message, response=None):
    extra = ''
    if response is not None:
        extra = f" (http={response.status_code}, body={_redact(response.text)!r})"
    print(f"ERROR: {message}{extra}")
    exit(1)


def get_routes():
    route_url = 'https://sport.fudan.edu.cn/sapi/route/list'
    params = {'userid': os.getenv('USER_ID'), 'token': os.getenv('FUDAN_SPORT_TOKEN')}
    response = requests.get(route_url, params=params, timeout=30)
    try:
        data = json.loads(response.text)
    except Exception:
        _fail('路线列表返回的不是 JSON', response)
    try:
        # 2026 起官方接口的田径场路线变成「起点 + 中点」两个点，原来只认单点导致所有场地被筛掉，
        # 这里放宽为至少一个点（FudanRoute 只用 points[0] 作起点）。
        route_data_list = filter(lambda route: route['points'] is not None and len(route['points']) >= 1,
                                 data['data']['list'])
        return [FudanRoute(route_data) for route_data in route_data_list]
    except Exception:
        _fail(data.get('message', '取路线列表失败'), response)

def default_env(name, default):
    if os.getenv(name) is None or os.getenv(name).strip() == '':
        return default
    else:
        return os.getenv(name)

class FudanAPI:
    def __init__(self, route):
        self.route = route
        self.user_id = os.getenv('USER_ID')
        self.token = os.getenv('FUDAN_SPORT_TOKEN')
        self.system = default_env('PLATFORM_OS', 'iOS 2016.3.1')
        self.device = default_env('PLATFORM_DEVICE', 'iPhone|iPhone 13<iPhone14,5>')
        self.run_id = None

    def start(self):
        start_url = 'https://sport.fudan.edu.cn/sapi/run/start'
        params = {'userid': self.user_id,
                  'token': self.token,
                  'route_id': self.route.id,
                  'route_type': self.route.type,
                  'system': self.system,
                  'device': self.device,
                  'lng': self.route.start_point.longitude,
                  'lat': self.route.start_point.latitude}
        response = requests.get(start_url, params=params, timeout=30)
        data = json.loads(response.text)
        try:
            self.run_id = data['data']['run_id']
        except Exception:
            _fail(data.get('message', '开始跑步失败'), response)

    def update(self, point):
        update_url = 'https://sport.fudan.edu.cn/sapi/run/point'
        params = {'userid': self.user_id,
                  'token': self.token,
                  'run_id': self.run_id,
                  'lng': point.longitude,
                  'lat': point.latitude}
        response = requests.get(update_url, params)
        try:
            data = json.loads(response.text)
            return data['message']
        except:
            return response.text

    def finish(self, point):
        finish_url = 'https://sport.fudan.edu.cn/sapi/run/finish'
        params = {'userid': self.user_id,
                  'token': self.token,
                  'run_id': self.run_id,
                  'system': self.system,
                  'device': self.device,
                  'lng': point.longitude,
                  'lat': point.latitude}
        response = requests.get(finish_url, params)
        data = json.loads(response.text)
        return data['message']

class FudanRoute:
    def __init__(self, data):
        self.id = data['route_id']
        self.name = data['name']
        self.type = data['types'][0]
        self.start_point = Point(data['points'][0]['lat'],
                                 data['points'][0]['lng'])

    def pretty_print(self):
        print(f"#{self.id}: {self.name}")
