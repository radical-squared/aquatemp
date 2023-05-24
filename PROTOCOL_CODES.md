# Protocol Codes

## Control parameters

| Parameter   | Description     |
| ----------- | --------------- |
| Power       | Power           |
| Mode        | HVAC Mode       |
| Manual-mute | Fan Mode        |
| 2074        | 2074            |
| 2075        | 2075            |
| 2076        | 2076            |
| 2077        | 2077            |
| Set_Temp    | Set Temperature |
| 1158        | 1158            |
| 1159        | 1159            |

## Hardware parameter

| Parameter | Description                                          |
| --------- | ---------------------------------------------------- |
| /01       | Whether enable system 1 high pressure switch         |
| /02       | Whether enable system 2 high pressure switch         |
| /03       | Whether enable system 1 low pressure switch          |
| /04       | Whether enable system 2 low pressure switch          |
| /05       | Whether enable phase monitor protection              |
| /06       | Whether enable water flow protection                 |
| /07       | Whether enable electrical heater Overload protection |
| /08       | Whether enable system 1 overload protection          |
| /09       | Whether enable system 2 overload protection          |
| /10       | Whether enable remote on/off switch                  |
| /11       | Whether enable system protect                        |
| /12       | Whether enable Outlet probe                          |
| /13       | Whether enable Coil 1 probe                          |
| /14       | Whether enable Coil 2 probe                          |
| /15       | Whether enable Ambient probe                         |
| /16       | Whether enable deice 1 probe                         |
| /17       | Whether enable deice 2 probe                         |
| /18       | Whether enable Suction 1 probe                       |
| /19       | Whether enable Suction 2 probe                       |
| /20       | Whether enable exhaust 1 probe                       |
| /21       | Whether enable exhaust 2 probe                       |
| /22       | Whether enable ΔT1 protect                           |
| /23       | Whether enable Cooling mode                          |
| /24       | Whether enable Economic heating                      |
| /25       | Whether enable AUTO mode                             |
| /26       | Whether enable Heating mode                          |
| /27       | Whether enable High demand                           |
| /28       | Whether enable heat recovery temperature             |

## Protection parameter

| Parameter | Description                                     |
| --------- | ----------------------------------------------- |
| A01       | High pressure alarm time delay                  |
| A02       | Low pressure alarm time delay                   |
| A03       | Stop unit air temperature                       |
| A04       | Antifreeze setting temperature                  |
| A05       | Antifreeze differential protection              |
| A06       | Discharge temp. protection setting              |
| A07       | Discharge temp. differential protection         |
| A08       | Inlet/Out differential protection setting value |
| A09       | Start spraying air temperature                  |

## Compressor parameter

| Parameter | Description                               |
| --------- | ----------------------------------------- |
| C01       | Minimum on time                           |
| C02       | Minimum off time                          |
| C03       | Delay between starts of the 2 compressors |
| C04       | Rotation                                  |

## Defrost parameter

| Parameter | Description                  |
| --------- | ---------------------------- |
| D01       | Start defrosting temperature |
| D02       | End defrost temperature      |
| D03       | defrosting cycle             |
| D04       | Maximum defrosting time      |
| D05       | Minimum defrosting time      |
| D06       | Defrost mode                 |
| D07       | Defrost heater control       |
| D08       | Defrost AUTO set             |

## EEV parameter

| Parameter | Description     |
| --------- | --------------- |
| E01       | EEV 1 mode      |
| E02       | Super heat 1    |
| E03       | Initial place 1 |
| E04       | EEV 2 mode      |
| E05       | Super heat 2    |
| E06       | Initial place 2 |
| E07       | Minimum place   |
| E08       | Defrost place   |
| E09       | Cooling place   |
| E10       | Low exhaust     |
| E11       | High exhaust    |

## Fan parameter

| Parameter | Description                                       |
| --------- | ------------------------------------------------- |
| F01       | Fan parameter                                     |
| F02       | Coil temperature in high speed fan mode (Cooling) |
| F03       | Coil temperature in low speed fan mode (Cooling)  |
| F04       | Coil temperature when the fan stop (Cooling)      |
| F05       | Coil temperature in high speed fan mode (Heating) |
| F06       | Coil temperature in low speed fan mode (Heating)  |
| F07       | Coil temperature when the fan stop (Heating)      |
| F08       | Fan start low speed running time                  |
| F09       | Fan stop low speed running time                   |
| F10       | Fan quantity                                      |
| F11       | Fan speed control temp.                           |

## System parameter

| Parameter | Description          |
| --------- | -------------------- |
| H01       | Automatic restarting |
| H02       | System quantity      |
| H03       | 4-way valve polarity |
| H04       | 4-way valve control  |
| H05       | Model                |
| H06       | Type                 |
| H07       | Class                |
| H08       | Capacity Control     |
| H09       | Coil sensor function |
| H10       | Physical address     |
| H11       | Baud rate            |
| H12       | Parity bit           |
| H13       | Stop bit             |

## Water pump parameter

| Parameter | Description                                                      |
| --------- | ---------------------------------------------------------------- |
| R01       | Water pump mode                                                  |
| P02       | Water pump running cycle                                         |
| P03       | Water pump running time                                          |
| P04       | Delay in switching on the compressor after switching on the pump |
| P05       | Filter                                                           |
| P06       | Start filter 1                                                   |
| P07       | Stop filter 1                                                    |
| P08       | Start filter 2                                                   |
| P09       | Stop filter 2                                                    |

## Temp parameter

| Parameter | Description                                          |
| --------- | ---------------------------------------------------- |
| R01       | Inlet water setting temperature (cooling)            |
| R02       | Inlet water setting temperature (Heating)            |
| R03       | Target setting temperature (Auto mode)               |
| R04       | Cooling differential                                 |
| R05       | Cooling stop differential                            |
| R06       | Heating differential                                 |
| R07       | Heating stop differential                            |
| R08       | Minimum set point in Cooling                         |
| R09       | Maximum Cooling set point                            |
| R10       | Minimum Heating set point                            |
| R11       | Maximum Heating set point                            |
| R12       | Electrical ΔT6                                       |
| R13       | Electrical Ambient                                   |
| R14       | Electrical Delay                                     |
| R15       | Electrical force                                     |
| R16       | Compensation                                         |
| R17       | Maximum ΔT7                                          |
| R18       | Cooling compensation constant                        |
| R19       | Cooling compensation start air temperature           |
| R20       | Heating compensation start air temperature           |
| R21       | Whether enable heat recovery                         |
| R22       | The target temperature Of heat recovery              |
| R23       | Temperature differential of heat recovery            |
| R24       | Temperature to stop heat recovery                    |
| R25       | Temperature differential to stop heat recovery       |
| R26       | Electric heater mode                                 |
| R27       | Ambient temperature to start up antifreezing heater  |
| R28       | Temperature differential to stop antifreezing heater |

## Water flow parameter

| Parameter | Description  |
| --------- | ------------ |
| U01       | Flow meter   |
| U02       | Pulse        |
| U03       | Flow protect |
| U04       | Flow alarm   |

## Switch state checking

| Parameter | Description                |
| --------- | -------------------------- |
| S01       | System1 HP                 |
| S02       | System2 HP                 |
| S03       | System1 LP                 |
| S04       | System2 LP                 |
| S05       | Phase monitor              |
| S06       | Water Flow switch          |
| S07       | Electrical heater overload |
| S08       | COMP1 overload             |
| S09       | COMP2 overload             |
| S10       | On/Off switch              |
| S11       | Mode switch                |
| S12       | System protect             |
| S13       | Water flow                 |

## Temp. checking

| Parameter | Description              |
| --------- | ------------------------ |
| T01       | Suction temperature      |
| T02       | Inlet water temp.        |
| T03       | Outlet water temp        |
| T04       | Coil temperature         |
| T05       | Ambient temperature      |
| T06       | Antifreeze 1 temperature |
| T07       | Antifreeze 2 temperature |
| T08       | Suction 1 temperature    |
| T09       | Suction 2 temperature    |
| T10       | Exhaust 1 temperature    |
| T11       | Exhaust 2 temperature    |
| T12       | Hot water temperature    |
| T14       | None                     |

## Load output

| Parameter | Description                         |
| --------- | ----------------------------------- |
| O01       | Compressor 1 output                 |
| O02       | Compressor 2 output                 |
| O03       | Fan output (High speed)             |
| O04       | Fan output (Low speed)              |
| O05       | Circulate pump output               |
| O06       | 4-way valve output                  |
| O07       | Heat element output                 |
| O08       | Alarm output                        |
| O09       | Spray valve output                  |
| O10       | Electronic Expansion valve 1 output |
| O11       | Electronic Expansion valve 2 output |
