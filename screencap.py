
import argparse
import json
import os
import sys

import cv2

from core.device.device import Device

# use to cap screen for file - reads the same settings/fgo/config.json the
# app uses, so it follows whatever device / screencap / emulator is configured.
#
#   screencap.py                          -> screenshot.png (full screen)
#   screencap.py -o out.png               -> custom output path
#   screencap.py --crop X Y W H -o t.png  -> save only that region
#                                            (e.g. a thugImage.png template)
def buildDevice(configPath: str) -> Device:
    with open(configPath, encoding='utf-8') as f:
        configData = json.load(f)

    screencapType = Device.ScreenCapType(configData.get('screencap', 0))

    if 'emulator' in configData:
        emulatorType = Device.EmulatorType(configData['emulator'])
    else:
        emulatorType = Device.EmulatorType.MUMU if screencapType == Device.ScreenCapType.NEMUIPC else Device.EmulatorType.NONE

    return Device(configData['device'], screencapType, emulatorType, configData.get('emulatorPath') or None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Capture the emulator screen to a png file.')
    parser.add_argument('-c', '--config', default='settings/fgo/config.json', help='config file to read the device settings from')
    parser.add_argument('-o', '--out', default='screenshot.png', help='output png path')
    parser.add_argument('--crop', nargs=4, type=int, metavar=('X', 'Y', 'W', 'H'), help='only save this region of the screen')
    args = parser.parse_args()

    device = buildDevice(args.config)

    if not device.screenshot():
        print('Screenshot failed, check the device/screencap/emulator settings.')
        sys.exit(1)

    image = device.getScreenshot()
    if args.crop:
        x, y, w, h = args.crop
        image = image[y:y + h, x:x + w]

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    cv2.imwrite(args.out, image)
    print('Saved ' + args.out + ' ' + str(image.shape[1]) + 'x' + str(image.shape[0]))
