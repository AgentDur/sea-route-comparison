#!/usr/bin/env python3
"""Сравнение ортодромии, локсодромии и геодезической линии WGS 84.

Ортодромия и локсодромия: сфера радиуса 6371 км.
Геодезическая линия: эллипсоид WGS 84, алгоритм GeographicLib.

Пример запуска:
    python route_calc.py
    python route_calc.py --plot
    python route_calc.py --lat1 40 --lon1 -30 --lat2 50 --lon2 -20
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

from geographiclib.geodesic import Geodesic

EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True)
class RouteResult:
    distance_km: float
    initial_bearing_deg: float


def _normalize_delta_lon(deg: float) -> float:
    """Самая короткая разность долгот в диапазоне [-180, 180)."""
    return (deg + 180.0) % 360.0 - 180.0


def _bearing(y: float, x: float) -> float:
    return math.degrees(math.atan2(y, x)) % 360.0


def great_circle(lat1: float, lon1: float, lat2: float, lon2: float) -> RouteResult:
    """Кратчайшая дуга большого круга на сфере, формула гаверсинусов."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlam = math.radians(_normalize_delta_lon(lon2 - lon1))

    h = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    h = min(1.0, max(0.0, h))
    angle = 2.0 * math.atan2(math.sqrt(h), math.sqrt(1.0 - h))
    distance = EARTH_RADIUS_KM * angle

    y = math.sin(dlam) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    return RouteResult(distance, _bearing(y, x))


def _mercator_psi(phi: float) -> float:
    """Изометрическая широта для сферы (в радианах)."""
    return math.log(math.tan(math.pi / 4.0 + phi / 2.0))


def rhumb_line(lat1: float, lon1: float, lat2: float, lon2: float) -> RouteResult:
    """Локсодромия на сфере: расстояние и постоянный истинный курс."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlam = math.radians(_normalize_delta_lon(lon2 - lon1))
    dpsi = _mercator_psi(phi2) - _mercator_psi(phi1)
    q = dphi / dpsi if abs(dpsi) > 1e-12 else math.cos(phi1)
    distance = EARTH_RADIUS_KM * math.hypot(dphi, q * dlam)
    return RouteResult(distance, _bearing(dlam, dpsi))


def ellipsoid_geodesic(lat1: float, lon1: float, lat2: float, lon2: float) -> RouteResult:
    """Обратная геодезическая задача на WGS 84 (GeographicLib)."""
    result = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
    return RouteResult(result["s12"] / 1000.0, result["azi1"] % 360.0)


def compare(lat1: float, lon1: float, lat2: float, lon2: float) -> dict[str, RouteResult]:
    if not all(math.isfinite(v) for v in (lat1, lon1, lat2, lon2)):
        raise ValueError("Все координаты должны быть конечными числами.")
    if not (-90.0 < lat1 < 90.0 and -90.0 < lat2 < 90.0):
        raise ValueError("Для локсодромии в этом примере широты должны лежать между -90° и 90°.")
    if not (-180.0 <= lon1 <= 180.0 and -180.0 <= lon2 <= 180.0):
        raise ValueError("Долготы должны лежать в пределах [-180°, 180°].")
    if lat1 == lat2 and _normalize_delta_lon(lon2-lon1) == 0:
        raise ValueError("Начальная и конечная точки совпадают — курс не определён.")
    return {
        "Ортодромия (сфера)": great_circle(lat1, lon1, lat2, lon2),
        "Локсодромия (сфера)": rhumb_line(lat1, lon1, lat2, lon2),
        "Геодезическая (WGS 84)": ellipsoid_geodesic(lat1, lon1, lat2, lon2),
    }


def render_report(lat1: float, lon1: float, lat2: float, lon2: float, routes: dict[str, RouteResult]) -> str:
    return "\n".join([
        "СРАВНЕНИЕ МАРШРУТОВ МЕЖДУ ТОЧКАМИ A И B",
        f"A: {lat1:.2f}°, {lon1:.2f}°    B: {lat2:.2f}°, {lon2:.2f}°",
        "Сферическая модель: R = 6371 км. Эллипсоид: WGS 84.",
        "-" * 79,
        f"{'Метод':28} {'Расстояние, км':>17} {'Курс/азимут, °':>21}",
        "-" * 79,
        *[f"{name:28} {res.distance_km:17.3f} {res.initial_bearing_deg:21.2f}" for name, res in routes.items()],
        "-" * 79,
        f"Разница: локсодромия - ортодромия = {routes['Локсодромия (сфера)'].distance_km - routes['Ортодромия (сфера)'].distance_km:.3f} км",
        f"Разница: WGS 84 - ортодромия = {routes['Геодезическая (WGS 84)'].distance_km - routes['Ортодромия (сфера)'].distance_km:.3f} км",
        "Примечание: маршруты на разных моделях нельзя напрямую сравнивать как",
        "разные физические траектории на одной и той же поверхности.",
    ])


def save_plot(routes: dict[str, RouteResult], dest: Path) -> None:
    """Один график отклонений расстояния от сферической ортодромии."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Для сохранения графика установите matplotlib.") from exc
    base = routes["Ортодромия (сфера)"].distance_km
    labels = ["Ортодромия (сфера)", "Геодезическая (WGS 84)", "Локсодромия (сфера)"]
    diffs = [routes[n].distance_km - base for n in labels]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.barh(labels, diffs)
    ax.invert_yaxis()
    ax.set_xlabel("Разница относительно ортодромии на сфере, км")
    ax.set_title("Сравнение результатов расчёта маршрутов")
    ax.set_xlim(0, max(diffs) * 1.2)
    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)
    for idx, value in enumerate(diffs):
        ax.text(value + max(diffs) * 0.015, idx, f"{value:.3f} км", va="center")
    fig.tight_layout()
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Расчёт трёх способов построения морского маршрута.")
    parser.add_argument("--lat1", type=float, default=40.0, help="Широта точки A в градусах")
    parser.add_argument("--lon1", type=float, default=-30.0, help="Долгота точки A в градусах")
    parser.add_argument("--lat2", type=float, default=50.0, help="Широта точки B в градусах")
    parser.add_argument("--lon2", type=float, default=-20.0, help="Долгота точки B в градусах")
    parser.add_argument("--plot", action="store_true", help="Сохранить график в PNG")
    args = parser.parse_args()
    try:
        routes = compare(args.lat1, args.lon1, args.lat2, args.lon2)
        print(render_report(args.lat1, args.lon1, args.lat2, args.lon2, routes))
        if args.plot:
            path = Path("route_comparison.png")
            save_plot(routes, path)
            print(f"График сохранён: {path}")
    except (ValueError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
