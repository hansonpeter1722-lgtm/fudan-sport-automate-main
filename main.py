from sport_api import *
from playground import playgrounds
import time
from argparse import ArgumentParser
import random

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-v', '--view', action='store_true', help="list available routes")
    parser.add_argument('-r', '--route', help="set route ID", type=int)
    parser.add_argument('-t', '--time', help="total time, in seconds", type=int)
    parser.add_argument('-d', '--distance', help="total distance, in meters", type=int)
    parser.add_argument('-q', '--delay', action='store_true', help="delay for random time")
    args = parser.parse_args()

    if args.view:
        routes = get_routes()
        supported_routes = filter(lambda r: r.id in playgrounds, routes)
        for route in supported_routes:
            route.pretty_print()
        exit()

    if args.route:
        # set distance
        distance = 1200
        if args.distance:
            distance = args.distance
        distance += random.uniform(-5.0, 25.0)

        # set time
        total_time = 360
        if args.time:
            total_time = args.time
        total_time += random.uniform(-10.0, 10.0)

        # get routes from server
        selected_route = None
        routes = get_routes()
        for route in routes:
            if route.id == args.route:
                selected_route = route

        if selected_route is None:
            print(f"ERROR: 服务端没有返回路线 {args.route}，可用路线请运行 python main.py --view 查看")
            exit(1)

        # delay random time, used in GitHub Action deployment
        if args.delay:
            sleep_time = random.randint(0, 240)
            time.sleep(sleep_time)

        # prepare & start running
        automator = FudanAPI(selected_route)
        playground = playgrounds[args.route]
        current_distance = 0
        automator.start()
        print(f"START: {selected_route.name}")
        while current_distance < distance:
            current_distance += distance / total_time
            message = automator.update(playground.random_offset(current_distance))
            print(f"UPDATE: {message} ({current_distance}m / {distance}m)")
            time.sleep(1)
        finish_message = automator.finish(playground.coordinate(distance))
        print(f"FINISHED: {finish_message}")
