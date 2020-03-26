# azure-iot-sample-home-alrets

Azure IOT Sample for Home based Alert and Dashboard with historical data of Temperature, Humidity, Air Quality, LPG Leakage and Sound.

## Architecture
![Alert Email](Docs/images/architecture.png)

## Devices


## Installation


## Outcome

1. Every 5 minutes there will be check for alerts, if the sensors measures crossed pre-defined threshold (average of 5 minutes), example `average temperature for 5 minutes >= 35 degree celsius`

**Sample Alert:**
![Alert Email](Docs/images/alert.png)

2. Dashboard with latest measures from all sensors as well as historical data of measures in graphical format (can be filtered with data)

**Sample Dashboard Latest Measures:**
![Alert Email](Docs/images/dashboard_1.png)

**Sample Dashboard Historical Data:**
![Alert Email](Docs/images/dashboard_2.png)
![Alert Email](Docs/images/dashboard_3.png)
![Alert Email](Docs/images/dashboard_4.png)

**Sample Dashboard with Date Filter:**
![Alert Email](Docs/images/dashboard_2_filter.png)