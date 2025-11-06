# 🌊 AquaChain IoT Sensors - Quick Summary

## Water Quality Sensors

### ✅ 4 Sensors - Measure Water Quality

1. **pH Sensor** (6.5-8.5 normal)
   - Measures water acidity/alkalinity
   - Critical for drinking water safety

2. **Turbidity Sensor** (0.5-5 NTU normal)
   - Measures water cloudiness/clarity
   - Detects suspended particles, contamination

3. **TDS Sensor** (50-500 ppm normal)
   - Measures Total Dissolved Solids
   - Detects minerals, salts, metals in water

4. **Temperature Sensor** (15-35°C normal)
   - Measures water temperature
   - Affects chemical reactions and bacterial growth

---

## Water Quality Index (WQI) Calculation

**Uses these 3 primary water parameters:**
```python
WQI = (pH_score * 0.4) + (turbidity_score * 0.3) + (tds_score * 0.3)
```

**Temperature is used for context but not in primary WQI formula.**

---

## Summary

**4 sensors measure water quality:**
- pH, Turbidity, TDS, Temperature

**Total: 4 sensor readings sent every 30-60 seconds**

---

**Last Updated:** October 31, 2025
