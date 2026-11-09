#!/usr/bin/env bash
# Запуск на Ubuntu / Linux: bash start.sh
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

echo "===================================================="
echo " Сравнение морских маршрутов — запуск проекта"
echo "===================================================="

if ! command -v python3 >/dev/null 2>&1; then
  echo "Ошибка: Python 3 не найден. Установите: sudo apt install python3 python3-venv"
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "[1/3] Создаю отдельное окружение Python..."
  if ! python3 -m venv .venv; then
    echo "Не удалось создать окружение. На Ubuntu установите: sudo apt install python3-venv"
    exit 1
  fi
fi

# В первый раз потребуются интернет и загрузка пакетов.
if ! .venv/bin/python -c 'import geographiclib, matplotlib' >/dev/null 2>&1; then
  echo "[2/3] Устанавливаю необходимые библиотеки (нужен интернет)..."
  if ! .venv/bin/python -m pip install -r requirements.txt; then
    echo "Ошибка установки. Проверьте интернет или запустите ещё раз."
    exit 1
  fi
fi

echo "[3/3] Запускаю расчёт..."
echo
.venv/bin/python route_calc.py "$@"
echo
if [ -t 0 ]; then
  read -r -p "Готово. Нажмите Enter для выхода... " _ || true
fi
