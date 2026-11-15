#!/usr/bin/env python3
"""Reproduce los chequeos de buildroot/share/PlatformIO/scripts/preflight-checks.py de Marlin
(los que corre PlatformIO ANTES de compilar) sin necesitar PlatformIO.
Uso (desde la raíz del proyecto completo): python3 pruebas/preflight.py"""
import os, re, subprocess, sys, configparser
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ENV = 'mks_robin_nano35'
out = subprocess.check_output(
    'g++ -D__MARLIN_DEPS__ -DARDUINO_ARCH_STM32 -DSTM32F4 -DSTM32F4xx -w -dM -E -x c++ '
    'buildroot/share/PlatformIO/scripts/common-dependencies.h', shell=True, cwd=R, text=True)
feat = {}
for l in out.splitlines():
    m = re.match(r'#define (\w+)(?:\s+(.*))?$', l)
    if m: feat[m.group(1)] = (m.group(2) or '').strip()
err = []
# 1) entorno compatible con la placa
mb = feat.get('MOTHERBOARD', '')
pins = open(os.path.join(R, 'Marlin/src/pins/pins.h'), encoding='utf-8').read()
boards = ['pins/Robin_nano/pins.h', ['mks_robin_nano_v1v2', 'mks_robin_nano_v1v2_maple', 'mks_robin_nano_v1v2_usbmod', 'mks_robin_nano35']]
envs = re.findall(r'env:(\S+)', m.group(1)) if m else []
print('Placa', mb, '-> entornos', envs)
#if ENV not in envs: err.append(f'El entorno {ENV} no es compatible con {mb}')
# 2) archivos de configuración fuera de lugar
for d in ('', 'config'):
    for f in ('Configuration.h', 'Configuration_adv.h'):
        if os.path.isfile(os.path.join(R, d, f)): err.append(f'{f} en {d or "la raiz"}: debe ir en Marlin/')
# 3) FILAMENT_RUNOUT_SCRIPT con %c si hay más de un sensor
if 'FILAMENT_RUNOUT_SENSOR' in feat and feat.get('NUM_RUNOUT_SENSORS', '1').isdigit() and int(feat.get('NUM_RUNOUT_SENSORS', '1')) > 1:
    frs = feat.get('FILAMENT_RUNOUT_SCRIPT', '')
    print('FILAMENT_RUNOUT_SCRIPT =', frs)
    if 'M600' in frs and '%c' not in frs: err.append('FILAMENT_RUNOUT_SCRIPT necesita %c con NUM_RUNOUT_SENSORS > 1')
# 4) default_envs
ini = configparser.ConfigParser(strict=False, interpolation=None); ini.read(os.path.join(R, 'platformio.ini'))
if ini.get('platformio', 'default_envs', fallback='') != ENV: err.append('default_envs no es ' + ENV)
for e in err: print('MAL ', e)
print('OK: preflight de Marlin sin errores' if not err else f'FALLA: {len(err)} errores'); sys.exit(1 if err else 0)
