# 🌊 AquaChain Water Quality Sensors

## 4 Sensors Monitor Water Quality

### 1. pH Sensor
- **Measures:** Water acidity/alkalinity
- **Range:** 0-14 pH
- **Safe Range:** 6.5-8.5 pH
- **Why:** Acidic/alkaline water is unsafe to drink

### 2. Turbidity Sensor
- **Measures:** Water cloudiness/clarity
- **Range:** 0-1000 NTU
- **Safe Range:** 0.5-5 NTU
- **Why:** Cloudy water indicates contamination

### 3. TDS Sensor
- **Measures:** Total Dissolved Solids
- **Range:** 0-2000 ppm
- **Safe Range:** 50-500 ppm
- **Why:** High TDS = too many minerals/salts

### 4. Temperature Sensor
- **Measures:** Water temperature
- **Range:** -55°C to 125°C
- **Normal Range:** 15-35°C
- **Why:** Affects chemistry and bacteria growth

---

## Data Sent Every 30-60 Seconds

```json
{
  "device_id": "DEV-001",
  "timestamp": "2025-10-31T10:30:00Z",
  "readings": {
    "pH": 7.2,
    "turbidity": 1.5,
    "tds": 150,
    "temperature": 22.5
  },
  "wqi": 87
}
```

---

## Water Quality Index (WQI)

**Formula:**
```
WQI = (pH_score × 0.4) + (turbidity_score × 0.3) + (tds_score × 0.3)
```

**Scale:**
- 90-100: Excellent
- 70-89: Good
- 50-69: Fair
- 25-49: Poor
- 0-24: Very Poor

---

**Note:** We do NOT use humidity sensors. Humidity measures air, not water.
