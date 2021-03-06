from car import *

b220100 = bytes.fromhex(hex(0x220100)[2:])
b220101 = bytes.fromhex(hex(0x220101)[2:])
b220105 = bytes.fromhex(hex(0x220105)[2:])

class KONA_EV(Car):

    def __init__(self, dongle):
        self.dongle = dongle
        self.dongle.setProtocol('CAN_11_500')
        self.dongle.setCANRxMask(0x7ff)

    def getData(self):
        raw = {}

        self.dongle.setCANRxFilter(0x7ec)
        self.dongle.setCanID(0x7e4)
        for cmd in [b220101,b220105]:
            raw[cmd] = self.dongle.sendCommand(cmd)

        #self.dongle.setCANRxFilter(0x7ee)
        #self.dongle.setCanID(0x7e6)
        #raw[b220100] = self.dongle.sendCommand(b220100)

        data = self.getBaseData()

        data['SOC_BMS'] = raw[b220101][0x7ec][1][1] / 2.0
        data['SOC_DISPLAY'] = raw[b220105][0x7ec][5][0] / 2.0

        chargingBits = raw[b220101][0x7ec][7][5]
        normalChargePort = raw[b220101][0x7ec][1][6] == 3
        normalChargeBit = chargingBits & 0x02 == 0x02
        dcBatteryCurrent = int.from_bytes(raw[b220101][0x7ec][2][0:2], byteorder='big', signed=True) / 10.0
        dcBatteryVoltage = int.from_bytes(raw[b220101][0x7ec][2][2:4], byteorder='big', signed=False) / 10.0

        data['EXTENDED'] = {
                'auxBatteryVoltage':        raw[b220101][0x7ec][4][5] / 10.0,
                'batteryInletTemperature':  int.from_bytes(raw[b220101][0x7ec][3][5:6], byteorder='big', signed=True),
                'batteryMaxTemperature':    int.from_bytes(raw[b220101][0x7ec][2][4:5], byteorder='big', signed=True),
                'batteryMinTemperature':    int.from_bytes(raw[b220101][0x7ec][2][5:6], byteorder='big', signed=True),
                'cumulativeEnergyCharged':  int.from_bytes(raw[b220101][0x7ec][6][0:4], byteorder='big', signed=False) / 10.0,
                'cumulativeEnergyDischarged': int.from_bytes(raw[b220101][0x7ec][6][4:7] + raw[b220101][0x7ec][7][0:1], byteorder='big', signed=False) / 10.0,
                'charging':                 1 if (chargingBits & 0xc) == 0x8 else 0,
                'normalChargePort':         1 if normalChargeBit and normalChargePort else 0,
                'rapidChargePort':          1 if normalChargeBit and not normalChargePort else 0,
                'dcBatteryCurrent':         dcBatteryCurrent,
                'dcBatteryPower':           dcBatteryCurrent * dcBatteryVoltage / 1000.0,
                'dcBatteryVoltage':         dcBatteryVoltage,
                'soh':                      int.from_bytes(raw[b220105][0x7ec][4][1:3], byteorder='big', signed=False) / 10.0,
                #'externalTemperature':      (raw[b220100][0x7ee][1][3] - 80) / 2.0,
                }

        return data

    def getBaseData(self):
        return {
            "CAPACITY": 64,
            "SLOW_SPEED": 2.3,
            "NORMAL_SPEED": 4.6,
            "FAST_SPEED": 50
        }
