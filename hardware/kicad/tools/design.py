"""Pneuma Rev A — single source of truth for both boards.

Two boards, joined by a 30-way 0.5 mm FFC that runs under the battery:

  PNM-MAIN  (camera end)  Luckfox Core1106-1408 + nRF52840 wake island + audio + camera FPC
  PNM-PWR   (USB-C end)   USB-C + BQ24074 charger + EG800Q-NA modem + nano-SIM + fuel gauge + touch

Every component is (ref, lib_id, value, footprint, {pin: net}, fields).  Pins not
listed are explicitly no-connect.  gen_sch.py and gen_pcb.py both read this file,
so schematic and PCB nets can never drift apart.
"""

# Frozen revision date: generated files must not churn just because the clock moved.
REV_DATE = "2026-09-19"

R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
TP = "TestPoint:TestPoint_Pad_D1.0mm"
FFC30 = "Connector_FFC-FPC:Hirose_FH12-30S-0.5SH_1x30-1MP_P0.50mm_Horizontal"

# Inter-board FFC: identical pin -> net map on both boards (straight-through cable).
FFC_PINOUT = {
    1: "GND", 2: "VSYS", 3: "VSYS", 4: "VSYS", 5: "VSYS", 6: "GND", 7: "GND",
    8: "USB_SOC_DP", 9: "USB_SOC_DN", 10: "GND",
    11: "MDM_RXD_3V3", 12: "MDM_TXD_3V3", 13: "MDM_RTS_3V3", 14: "MDM_CTS_3V3", 15: "GND",
    16: "+3V3_AON", 17: "I2C_SCL", 18: "I2C_SDA",
    19: "MDM_PWRKEY", 20: "MDM_RESET", 21: "MDM_STATUS", 22: "MDM_RI", 23: "MDM_DTR",
    24: "USB_SEL", 25: "CHG_N", 26: "VBUS_DET_3V3", 27: "TOUCH_OUT", 28: "+3V3_SOC",
    29: "GND", 30: "GND",
}


class Board:
    def __init__(self, name, title):
        self.name, self.title = name, title
        self.parts = []       # dicts
        self.sheets = []      # (sheet_name, [refs])
        self._sheet = None

    def sheet(self, name):
        self._sheet = (name, [])
        self.sheets.append(self._sheet)

    def add(self, ref, lib_id, value, footprint, pins, dnp=False, **fields):
        self.parts.append(dict(ref=ref, lib_id=lib_id, value=value, footprint=footprint,
                               pins={str(k): v for k, v in pins.items()}, dnp=dnp, fields=fields))
        self._sheet[1].append(ref)

    # passives -----------------------------------------------------------
    def R(self, ref, value, a, b, fp=R0402, dnp=False, **f):
        self.add(ref, "Device:R", value, fp, {1: a, 2: b}, dnp=dnp, **f)

    def C(self, ref, value, a, b="GND", fp=C0402, dnp=False, **f):
        self.add(ref, "Device:C", value, fp, {1: a, 2: b}, dnp=dnp, **f)

    def TPt(self, ref, net, fp=TP):
        self.add(ref, "Connector:TestPoint", net, fp, {1: net})

    def nets(self):
        s = set()
        for p in self.parts:
            s.update(n for n in p["pins"].values() if n)
        return sorted(s)


# =====================================================================
# PNM-MAIN
# =====================================================================
def main_board():
    b = Board("pneuma-main", "Pneuma Rev A — Main (Core1106 + nRF52840 + audio + camera)")

    # ---- Compute module --------------------------------------------------
    b.sheet("Compute")
    core = {n: "GND" for n in (21, 25, 28, 29, 36, 47, 55, 56, 57, 75, 82, 83, 84, 89, 112)}
    core.update({
        79: "+VSOC", 80: "+VSOC", 81: "+VSOC",
        78: "+3V3_SOC", 77: "+1V8_SOC",
        74: "SOC_NPOR",
        22: "USB_SOC_DN", 23: "USB_SOC_DP", 24: "VBUS_DET_3V3",
        # MIPI CSI-2, 2 lanes (Luckfox camera wiring)
        9: "CSI_CKN", 10: "CSI_CKP", 11: "CSI_D0N", 12: "CSI_D0P", 7: "CSI_D1N", 8: "CSI_D1P",
        19: "CAM_MCLK", 18: "CAM_RST", 16: "CAM_SCL", 17: "CAM_SDA",
        # audio
        32: "SOC_MIC0N", 33: "SOC_MIC0P",
        102: "I2S_BCLK", 103: "I2S_LRCK", 106: "I2S_DOUT",
        # UART3_M0 <-> nRF
        65: "SOC_TX", 66: "SOC_RX",
        # UART5_M1 <-> modem (level-shifted on PNM-PWR)
        90: "MDM_RXD_3V3", 91: "MDM_TXD_3V3", 92: "MDM_CTS_3V3", 93: "MDM_RTS_3V3",
        # debug UART2_M1
        72: "SOC_DBG_TX", 73: "SOC_DBG_RX",
        # GPIO
        # NB: pins 60/61/62/67 are tied (1k) to WL_EN/HOST_WAKE on the WiFi variant,
        # and 63/64/68/69 carry the BT UART; they are deliberately left unused.
        94: "AMP_SD", 58: "SOC_WAKE", 59: "SOC_IRQ",   # 58/59 = GPIO0 bank (PMU, wake-capable)
        26: "SOC_RECOVERY",
        110: "SOC_GPIO2_B0", 111: "SOC_GPIO2_B1",
    })
    b.add("U1", "Pneuma:Core1106", "Core11061408", "Pneuma:Core1106-SMT-Cutout", core,
          MPN="Core11061408", Manufacturer="Luckfox",
          Description="RV1106G3 SoM, 256 MB DDR3L, 8 GB eMMC, WiFi6/BT5.2, 30x30 stamp-hole")
    b.C("C1", "22u", "+VSOC", fp=C0805, Voltage="10V")
    b.C("C2", "22u", "+VSOC", fp=C0805, Voltage="10V")
    b.C("C3", "100n", "+VSOC")
    b.C("C4", "10u", "+3V3_SOC", fp=C0603)
    b.R("R1", "10k", "SOC_RECOVERY", "+1V8_SOC")
    b.R("R2", "100k", "SOC_NPOR", "+3V3_SOC", dnp=True)
    b.TPt("TP1", "SOC_DBG_TX")
    b.TPt("TP2", "SOC_DBG_RX")
    b.TPt("TP3", "SOC_RECOVERY")
    b.TPt("TP4", "SOC_NPOR")
    b.TPt("TP5", "SOC_GPIO2_B0")
    b.TPt("TP6", "SOC_GPIO2_B1")

    # ---- SoC power switch -------------------------------------------------
    b.sheet("Power")
    b.add("U2", "Power_Management:TPS22917DBV", "TPS22917DBVR", "Package_TO_SOT_SMD:SOT-23-6",
          {1: "VSYS", 2: "GND", 3: "SOC_EN", 4: "SOC_SW_CT", 5: "SOC_SW_QOD", 6: "+VSOC"},
          MPN="TPS22917DBVR", Manufacturer="TI", Description="SoC rail load switch, 2 A")
    b.C("C5", "1n", "SOC_SW_CT")
    b.R("R14", "100", "SOC_SW_QOD", "+VSOC", Note="quick output discharge so a SoC power-cycle is a clean reset")
    b.C("C6", "4.7u", "VSYS", fp=C0603)
    b.R("R3", "100k", "SOC_EN", "GND")
    b.C("C7", "22u", "VSYS", fp=C0805, Voltage="10V")
    b.C("C8", "22u", "VSYS", fp=C0805, Voltage="10V")
    b.TPt("TP7", "VSYS")
    b.TPt("TP8", "+3V3_SOC")
    b.TPt("TP9", "+3V3_AON")
    b.TPt("TP10", "GND")

    # ---- Wake island -------------------------------------------------------
    b.sheet("WakeIsland")
    nrf = {n: "GND" for n in (1, 2, 15, 33, 55)}
    nrf.update({
        30: "VSYS",            # VDDH: high-voltage mode, REG0 makes VDD
        28: "+3V3_AON",        # VDD is an OUTPUT here (UICR.REGOUT0 must be set to 3V3)
        17: "XL1", 18: "XL2",
        51: "SWDIO", 53: "SWDCLK", 40: "NRF_RESET",   # P0.18 = nRESET
        19: "PDM_CLK", 16: "PDM_DAT",                  # P0.26 / P0.27
        22: "SOC_RX", 24: "SOC_TX",                    # P0.06 -> SoC RX ; P0.08 <- SoC TX
        27: "I2C_SCL", 29: "I2C_SDA",                  # P0.11 / P0.12
        3: "SOC_EN", 4: "SOC_NPOR", 5: "SOC_WAKE", 6: "SOC_IRQ",   # P1.10..P1.13
        8: "HAPTIC_EN", 41: "HAPTIC_TRIG",             # P1.15 / P0.17
        10: "LED_R", 11: "LED_G", 12: "LED_B",         # P0.29 / P0.02 / P0.31
        13: "TOUCH_OUT", 14: "CHG_N", 20: "VBUS_DET_3V3", 23: "USB_SEL",   # P0.28 P0.30 P0.04 P0.07
        25: "MDM_PWRKEY", 26: "MDM_RESET",             # P1.08 / P1.09
        37: "MDM_STATUS", 36: "MDM_RI", 39: "MDM_DTR", # P0.13 / P0.14 / P0.15
        47: "NRF_SWO",                                 # P1.00 (trace)
    })
    b.add("U3", "RF_Module:MDBT50Q-1MV2", "MDBT50Q-1MV2", "RF_Module:Raytac_MDBT50Q", nrf,
          MPN="MDBT50Q-1MV2", Manufacturer="Raytac", Description="nRF52840 module, chip antenna")
    b.C("C9", "4.7u", "VSYS", fp=C0603)
    b.C("C10", "100n", "VSYS")
    b.C("C11", "4.7u", "+3V3_AON", fp=C0603)
    b.C("C12", "100n", "+3V3_AON")
    b.add("Y1", "Device:Crystal", "32.768k", "Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm", {1: "XL1", 2: "XL2"},
          MPN="ECS-.327-7-12-TR", Manufacturer="ECS", Description="32.768 kHz, CL 7 pF")
    b.C("C13", "12p", "XL1")
    b.C("C14", "12p", "XL2")
    b.add("J1", "Connector:Conn_ARM_SWD_TagConnect_TC2030-NL", "TC2030-NL",
          "Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical",
          {1: "+3V3_AON", 2: "SWDIO", 3: "NRF_RESET", 4: "SWDCLK", 5: "GND", 6: "NRF_SWO"},
          Description="nRF SWD (Tag-Connect, no legs)")
    b.R("R4", "4.7k", "I2C_SCL", "+3V3_AON")
    b.R("R5", "4.7k", "I2C_SDA", "+3V3_AON")
    # wake microphone (PDM, always on)
    b.add("MK1", "Sensor_Audio:IM69D130", "IM69D130V01", "Sensor_Audio:Infineon_PG-LLGA-5-1",
          {1: "PDM_DAT", 2: "+3V3_AON", 3: "PDM_CLK", 4: "GND", 5: "GND"},
          MPN="IM69D130V01XTSA1", Manufacturer="Infineon", Description="PDM MEMS mic, bottom port")
    b.C("C15", "100n", "+3V3_AON")
    # status LED (common anode)
    b.add("D1", "Pneuma:LED_RGB_CA_0404", "SML-LX0404SIUPGUSB", "LED_SMD:LED_Lumex_SML-LX0404SIUPGUSB",
          {1: "+3V3_AON", 2: "LED_RK", 3: "LED_BK", 4: "LED_GK"},
          MPN="SML-LX0404SIUPGUSB", Manufacturer="Lumex", Description="RGB LED 1.0x1.0 mm, common anode")
    b.R("R6", "680", "LED_RK", "LED_R")
    b.R("R7", "270", "LED_GK", "LED_G")
    b.R("R8", "270", "LED_BK", "LED_B")

    # ---- Audio + haptics ---------------------------------------------------
    b.sheet("Audio")
    b.add("U4", "Audio:MAX98357A", "MAX98357AETE+T", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm",
          {1: "I2S_DOUT", 2: None, 3: "GND", 4: "AMP_SD", 7: "VSYS", 8: "VSYS",
           9: "SPK_P", 10: "SPK_N", 11: "GND", 14: "I2S_LRCK", 15: "GND", 16: "I2S_BCLK", 17: "GND"},
          MPN="MAX98357AETE+T", Manufacturer="Analog Devices", Description="I2S class-D mono amp")
    b.C("C16", "10u", "VSYS", fp=C0603)
    b.C("C17", "100n", "VSYS")
    b.R("R9", "1M", "AMP_SD", "GND")
    b.add("J2", "Connector_Generic:Conn_01x02", "SPK", "Pneuma:Pads_2x_1.2x1.6mm_P2.5mm",
          {1: "SPK_P", 2: "SPK_N"}, Description="Speaker solder pads (wire-lead micro speaker, see BOM)")
    b.add("U5", "Driver:DRV2605LDGS", "DRV2605LDGSR", "Package_SO:TSSOP-10_3x3mm_P0.5mm",
          {1: "HAP_REG", 2: "I2C_SCL", 3: "I2C_SDA", 4: "HAPTIC_TRIG", 5: "HAPTIC_EN", 6: "VSYS",
           7: "LRA_P", 8: "GND", 9: "LRA_N", 10: "VSYS"},
          MPN="DRV2605LDGSR", Manufacturer="TI", Description="LRA haptic driver")
    b.C("C18", "1u", "HAP_REG")
    b.C("C19", "1u", "VSYS")
    b.R("R10", "100k", "HAPTIC_TRIG", "GND")
    b.add("J3", "Connector_Generic:Conn_01x02", "LRA", "Pneuma:Pads_2x_1.2x1.6mm_P2.5mm",
          {1: "LRA_P", 2: "LRA_N"}, Description="LRA solder pads (Vybronics VG1040003D)")
    # session microphone (analog, into Core codec MIC0)
    b.add("MK2", "Sensor_Audio:IM73A135V01", "IM73A135V01", "Sensor_Audio:Infineon_PG-LLGA-5-2",
          {1: "MIC2_P", 2: "MIC2_VDD", 3: "MIC2_N", 4: "GND", 5: "GND"},
          MPN="IM73A135V01XTSA1", Manufacturer="Infineon", Description="Analog MEMS mic, bottom port")
    b.R("R11", "100", "+3V3_SOC", "MIC2_VDD")
    b.C("C20", "1u", "MIC2_VDD")
    b.C("C21", "1u", "MIC2_P", "SOC_MIC0P")
    b.C("C22", "1u", "MIC2_N", "SOC_MIC0N")

    # ---- Camera + interconnect -------------------------------------------
    b.sheet("Interconnect")
    # Luckfox 20-pin camera pinout (SC3336 3MP Camera (B) drawing)
    cam = {1: "GND", 2: "CAM_MCLK", 3: "GND", 4: "CSI_D0P", 5: "CSI_D0N", 6: "GND", 7: "CSI_CKP",
           8: "CSI_CKN", 9: "GND", 10: "CSI_D1P", 11: "CSI_D1N", 12: "GND", 13: "CAM_SCL",
           14: "CAM_SDA", 15: "GND", 16: "CAM_RST", 17: "GND", 18: "GND", 19: "+3V3_SOC",
           20: "+3V3_SOC", "MP": "GND"}
    b.add("J4", "Connector_Generic_MountingPin:Conn_01x20_MountingPin", "CAMERA",
          "Connector_FFC-FPC:Hirose_FH12-20S-0.5SH_1x20-1MP_P0.50mm_Horizontal", cam,
          MPN="FH12-20S-0.5SH(55)", Manufacturer="Hirose", Description="Camera FPC, Luckfox 20P pinout")
    b.C("C23", "10u", "+3V3_SOC", fp=C0603)
    b.R("R12", "4.7k", "CAM_SCL", "+1V8_SOC")
    b.R("R13", "4.7k", "CAM_SDA", "+1V8_SOC")
    ffc = dict(FFC_PINOUT)
    ffc["MP"] = "GND"
    b.add("J5", "Connector_Generic_MountingPin:Conn_01x30_MountingPin", "TO_PWR", FFC30, ffc,
          MPN="FH12-30S-0.5SH(55)", Manufacturer="Hirose", Description="Inter-board FFC (bottom side)")
    return b


# =====================================================================
# PNM-PWR
# =====================================================================
def pwr_board():
    b = Board("pneuma-pwr", "Pneuma Rev A — Power/Radio (USB-C, charger, EG800Q-NA, SIM)")

    # ---- USB-C + charger ---------------------------------------------------
    b.sheet("Power")
    b.add("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C",
          "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
          {"A1": "GND", "B1": "GND", "A12": "GND", "B12": "GND", "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
           "A5": "CC1", "B5": "CC2", "A6": "USBC_DP", "B6": "USBC_DP", "A7": "USBC_DN", "B7": "USBC_DN",
           "A8": None, "B8": None, "SH": "GND"},
          MPN="USB4105-GF-A", Manufacturer="GCT", Description="USB-C receptacle, USB 2.0, top mount")
    b.R("R1", "5.1k", "CC1", "GND")
    b.R("R2", "5.1k", "CC2", "GND")
    b.add("U1", "Power_Protection:USBLC6-2P6", "USBLC6-2P6", "Package_TO_SOT_SMD:SOT-666",
          {1: "USBC_DP", 6: "USBC_DP", 3: "USBC_DN", 4: "USBC_DN", 2: "GND", 5: "VBUS"},
          MPN="USBLC6-2P6", Manufacturer="ST", Description="USB ESD (SOT-666, 0.6 mm)")
    b.add("U2", "Battery_Management:BQ24074RGT", "BQ24074RGTR", "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm",
          {1: "CHG_TS", 2: "VBAT", 3: "VBAT", 4: "GND", 5: "VSYS", 6: "GND", 7: "PGOOD_N", 8: "GND",
           9: "CHG_N", 10: "VSYS", 11: "VSYS", 12: "CHG_ILIM", 13: "VBUS", 14: None, 15: None,
           16: "CHG_ISET", 17: "GND"},
          MPN="BQ24074RGTR", Manufacturer="TI",
          Description="1S Li-ion charger + power path. OUT(=VSYS) regulates to 4.4 V: modem stays on VBAT")
    b.C("C1", "4.7u", "VBUS", fp=C0603, Voltage="16V")
    b.C("C2", "10u", "VSYS", fp=C0603)
    b.C("C3", "10u", "VSYS", fp=C0603)
    b.C("C4", "10u", "VBAT", fp=C0603)
    b.R("R3", "10k", "CHG_TS", "GND", Note="fixed 10k = 25 C; replace with pack NTC if the cell has one")
    b.R("R4", "1.33k", "CHG_ILIM", "GND", Note="IIN max = 1610/1330 = 1.21 A")
    b.R("R5", "3.3k", "CHG_ISET", "GND", Note="ICHG = 890/3300 = 270 mA (~0.5C for a 550 mAh cell)")
    b.R("R6", "100k", "CHG_N", "+3V3_AON")
    b.R("R7", "100k", "PGOOD_N", "+3V3_AON")
    b.R("R8", "100k", "VBUS", "VBUS_DET_3V3")
    b.R("R9", "150k", "VBUS_DET_3V3", "GND")
    b.add("J2", "Connector_Generic_MountingPin:Conn_01x02_MountingPin", "BATTERY",
          "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal",
          {1: "VBAT", 2: "GND", "MP": None}, MPN="SM02B-GHS-TB", Manufacturer="JST",
          Description="1S LiPo, polarity per Pneuma harness: pin1 = +")
    b.add("U3", "Battery_Management:LC709203FQH-01TWG", "LC709203FQH-01TWG",
          "Package_DFN_QFN:WDFN-8-1EP_4x3mm_P0.65mm_EP2.4x1.8mm",
          {1: "GND", 2: "GND", 3: "VBAT", 4: None, 5: None, 6: None, 7: "I2C_SDA", 8: "I2C_SCL", 9: "GND"},
          MPN="LC709203FQH-01TWG", Manufacturer="onsemi", Description="Fuel gauge (I2C 0x0B), owned by nRF")
    b.C("C5", "100n", "VBAT")
    b.TPt("TP1", "VBAT")
    b.TPt("TP2", "VSYS")
    b.TPt("TP3", "VBUS")
    b.TPt("TP4", "GND")
    b.TPt("TP5", "PGOOD_N")

    # ---- USB routing ---------------------------------------------------------
    b.sheet("USB")
    b.add("U4", "Interface_USB:FSUSB42MUX", "FSUSB42MUX", "Package_SO:MSOP-10_3x3mm_P0.5mm",
          {1: "+3V3_AON", 2: "USB_SEL", 3: "USB_SOC_DP", 4: "USB_SOC_DN", 5: "GND",
           6: "USBC_DN", 7: "USBC_DP", 8: "MDM_USB_DM", 9: "MDM_USB_DP", 10: "GND"},
          MPN="FSUSB42MUX", Manufacturer="onsemi",
          Description="SoC USB -> USB-C (SEL=0, default/dev) or modem (SEL=1)")
    b.C("C6", "100n", "+3V3_AON")
    b.R("R10", "100k", "USB_SEL", "GND")

    # ---- Modem -----------------------------------------------------------------
    b.sheet("Modem")
    import eg800q
    mdm = {n: "GND" for n in eg800q.GND}
    mdm.update({
        42: "VBAT", 43: "VBAT", 7: "MDM_PWRKEY_N", 15: "MDM_RESET_N",
        24: "MDM_VDD_EXT", 25: "MDM_STATUS_1V8", 16: "MDM_NETSTAT_1V8",
        17: "MDM_RXD", 18: "MDM_TXD", 22: "MDM_CTS", 23: "MDM_RTS", 19: "MDM_DTR_1V8", 20: "MDM_RI_1V8",
        59: "MDM_USB_DP", 60: "MDM_USB_DM", 61: "MDM_USB_VBUS",
        14: "USIM_VDD", 11: "USIM_DATA", 12: "USIM_RST", 13: "USIM_CLK",
        35: "MDM_ANT", 38: "MDM_DBG_RXD", 39: "MDM_DBG_TXD", 82: "MDM_USB_BOOT",
    })
    b.add("U5", "Pneuma:EG800Q-NA", "EG800Q-NA", "Pneuma:Quectel_EG800Q_LGA-109", mdm,
          MPN="EG800Q-NA", Manufacturer="Quectel",
          Description="LTE Cat-1 bis, B2/4/5/12/13/66, LGA-109 15.8x17.7x2.4")
    b.C("C7", "47u", "VBAT", fp=C0805, Voltage="6.3V")
    b.C("C8", "47u", "VBAT", fp=C0805, Voltage="6.3V")
    b.C("C9", "100n", "VBAT")
    b.C("C10", "33p", "VBAT")
    b.C("C11", "10p", "VBAT")
    b.add("D1", "Device:D_TVS", "SMF5.0A", "Diode_SMD:D_SOD-123F", {1: "GND", 2: "VBAT"},
          MPN="SMF5.0A", Manufacturer="Littelfuse", Description="VBAT TVS (Quectel recommendation)")
    b.C("C12", "1u", "MDM_VDD_EXT")
    # PWRKEY / RESET: open-drain via NMOS, gate from nRF
    b.add("Q1", "Transistor_FET:2N7002", "2N7002", "Package_TO_SOT_SMD:SOT-23",
          {1: "MDM_PWRKEY", 2: "GND", 3: "MDM_PWRKEY_N"}, MPN="2N7002", Manufacturer="Nexperia")
    b.R("R11", "100k", "MDM_PWRKEY", "GND")
    b.add("Q2", "Transistor_FET:2N7002", "2N7002", "Package_TO_SOT_SMD:SOT-23",
          {1: "MDM_RESET", 2: "GND", 3: "MDM_RESET_N"}, MPN="2N7002", Manufacturer="Nexperia")
    b.R("R12", "100k", "MDM_RESET", "GND")
    # USB VBUS detect follows USB_SEL (3.3 V >= 3.0 V min)
    b.R("R13", "1k", "USB_SEL", "MDM_USB_VBUS")
    # RF: pi-network, 0R populated, shunts DNP until tuned
    b.R("R14", "0", "MDM_ANT", "MDM_ANT_J", Note="pi-match series; tune on the real antenna")
    b.C("C13", "DNP", "MDM_ANT", dnp=True)
    b.C("C14", "DNP", "MDM_ANT_J", dnp=True)
    b.add("J3", "Connector:Conn_Coaxial", "U.FL", "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
          {1: "MDM_ANT_J", 2: "GND"}, MPN="U.FL-R-SMT-1(10)", Manufacturer="Hirose", Description="LTE antenna")
    # level shifters: modem 1.8 V (VDD_EXT) <-> SoC 3.3 V / nRF 3.3 V
    b.add("U6", "Logic_LevelTranslator:TXB0104RGY", "TXB0104RGYR", "Package_DFN_QFN:Texas_S-PVQFN-N14",
          {1: "MDM_VDD_EXT", 2: "MDM_TXD", 3: "MDM_RXD", 4: "MDM_RTS", 5: "MDM_CTS", 7: "GND",
           8: "MDM_VDD_EXT", 10: "MDM_CTS_3V3", 11: "MDM_RTS_3V3", 12: "MDM_RXD_3V3", 13: "MDM_TXD_3V3",
           14: "+3V3_SOC", 15: "GND"},
          MPN="TXB0104RGYR", Manufacturer="TI",
          Description="Modem UART <-> SoC; VCCB from SoC 3V3 so it is fully off when the SoC is off")
    b.add("U7", "Logic_LevelTranslator:TXB0104RGY", "TXB0104RGYR", "Package_DFN_QFN:Texas_S-PVQFN-N14",
          {1: "MDM_VDD_EXT", 2: "MDM_STATUS_1V8", 3: "MDM_RI_1V8", 4: "MDM_DTR_1V8", 5: "MDM_NETSTAT_1V8",
           7: "GND", 8: "MDM_VDD_EXT", 10: "MDM_NETSTAT", 11: "MDM_DTR", 12: "MDM_RI", 13: "MDM_STATUS",
           14: "+3V3_AON", 15: "GND"},
          MPN="TXB0104RGYR", Manufacturer="TI", Description="Modem control <-> nRF")
    b.C("C15", "100n", "MDM_VDD_EXT")
    b.C("C16", "100n", "+3V3_SOC")
    b.C("C17", "100n", "+3V3_AON")
    # nano-SIM
    b.add("J4", "Connector:SIM_Card", "nanoSIM", "Connector_Card:nanoSIM_GCT_SIM8060-6-0-14-00",
          {1: "SIM_VCC", 2: "SIM_RST", 3: "SIM_CLK", 5: "GND", 6: None, 7: "SIM_IO"},
          MPN="SIM8060-6-0-14-00-A", Manufacturer="GCT", Description="Hinged nano-SIM, no detect")
    b.R("R15", "0", "USIM_VDD", "SIM_VCC")
    b.R("R16", "22", "USIM_RST", "SIM_RST")
    b.R("R17", "22", "USIM_CLK", "SIM_CLK")
    b.R("R18", "22", "USIM_DATA", "SIM_IO")
    b.R("R19", "15k", "USIM_DATA", "USIM_VDD")
    b.C("C18", "100n", "SIM_VCC")
    b.C("C19", "33p", "SIM_RST")
    b.C("C20", "33p", "SIM_CLK")
    b.C("C21", "33p", "SIM_IO")
    b.add("U8", "Power_Protection:ESDA6V1-5SC6", "ESDA6V1-5SC6", "Package_TO_SOT_SMD:SOT-23-6",
          {1: "SIM_VCC", 2: "GND", 3: "SIM_RST", 4: "SIM_CLK", 5: "SIM_IO", 6: None},
          MPN="ESDA6V1-5SC6", Manufacturer="ST", Description="SIM ESD")
    b.TPt("TP6", "MDM_DBG_TXD")
    b.TPt("TP7", "MDM_DBG_RXD")
    b.TPt("TP8", "MDM_USB_BOOT")
    b.TPt("TP9", "MDM_VDD_EXT")
    b.TPt("TP10", "MDM_USB_DP")
    b.TPt("TP11", "MDM_USB_DM")
    b.TPt("TP12", "MDM_NETSTAT")

    # ---- Touch + interconnect ---------------------------------------------------
    b.sheet("Interconnect")
    b.add("U9", "Sensor_Touch:AT42QT1011-M", "AT42QT1011-MAH", "Package_DFN_QFN:DFN-8-1EP_2x2mm_P0.5mm_EP0.9x1.5mm",
          {1: "TOUCH_SNSK", 2: None, 3: None, 4: "GND", 5: "TOUCH_OUT", 6: "GND", 7: "+3V3_AON", 8: "TOUCH_SNS", 9: "GND"},
          MPN="AT42QT1011-MAH", Manufacturer="Microchip", Description="1-key capacitive touch, UDFN-8 2x2")
    b.C("C22", "100n", "+3V3_AON")
    b.C("C23", "22n", "TOUCH_SNS", "TOUCH_SNSK", Note="Cs; tune for electrode size")
    b.R("R20", "4.7k", "TOUCH_SNSK", "TOUCH_E")
    b.add("TP13", "Connector:TestPoint", "TOUCH_E", "Pneuma:SpringPad_3.0x2.0mm", {1: "TOUCH_E"},
          Description="Touch electrode spring-contact pad")
    ffc = dict(FFC_PINOUT)
    ffc["MP"] = "GND"
    b.add("J5", "Connector_Generic_MountingPin:Conn_01x30_MountingPin", "TO_MAIN", FFC30, ffc,
          MPN="FH12-30S-0.5SH(55)", Manufacturer="Hirose", Description="Inter-board FFC (top side)")
    return b


BOARDS = [main_board, pwr_board]

if __name__ == "__main__":
    for mk in BOARDS:
        b = mk()
        print(b.name, len(b.parts), "parts", len(b.nets()), "nets")
