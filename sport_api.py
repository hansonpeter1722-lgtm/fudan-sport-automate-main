from geopy.point import Point
import requests
import json
import os


def get_routes():
    route_url = 'https://sport.fudan.edu.cn/sapi/route/list'
    params = {'userid': os.getenv('USER_ID'), 'token': os.getenv('FUDAN_SPORT_TOKEN')}
    response = requests.get(route_url, params=params)
    data = json.loads(response.text)
    try:
        # 2026 起官方接口的田径场路线变成「起点 + 中点」两个点，原来只认单点导致所有场地被筛掉，
        # 这里放宽为至少一个点（FudanRoute 只用 points[0] 作起点）。
        route_data_list = filter(lambda route: route['points'] is not None and len(route['points']) >= 1,
                                 data['data']['list'])
        return [FudanRoute(route_data) for route_data in route_data_list]
    except:
        print(f"ERROR: {data['message']}")
        exit(1)

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
        response = requests.get(start_url, params=params)
        data = json.loads(response.text)
        try:
            self.run_id = data['data']['run_id']
        except:
            print(f"ERROR: {data['message']}")
            exit(1)

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
