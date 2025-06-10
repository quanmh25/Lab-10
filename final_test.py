import itertools
import math

import matplotlib.pyplot as plt


points = [(25, 10), (-35, 15), (-10, 30), (10, 30), (10, -45)]
start = (0, 0)      # Office

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def plot_route(points, route, start):
    x = [start[0]] + [points[i][0] for i in route] + [start[0]]
    y = [start[1]] + [points[i][1] for i in route] + [start[1]]
    
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, 'o-', markersize=8)
    plt.scatter(start[0], start[1], c='red', s=100, label='Office')
    plt.grid(True)
    plt.title(f"Optimal Route (Distance: {min_distance:.2f} km)")
    plt.legend()
    plt.show()


if __name__ == '__main__':
    permutations = list(itertools.permutations(range(len(points))))
    min_distance = float('inf')
    best_route = None

    for per in permutations:
        total_distance = distance(start, points[per[0]])

        for i in range(len(per) - 1):
            total_distance += distance(points[per[i]], points[per[i+1]])
            total_distance += distance(points[per[-1]], start)

        if total_distance < min_distance:
            min_distance = total_distance
            best_route = per

    route_with_numbers = [i+1 for i in best_route]
    print("Кратчайший маршрут:", '-'.join(str(i+1) for i in best_route))
    print(f"Общая длина маршрута: {min_distance:.2f}")

    plot_route(points, best_route, start)