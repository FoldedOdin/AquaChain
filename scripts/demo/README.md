# AquaChain ML Model Demo Scripts

This directory contains demo scripts for showcasing the AquaChain ML models during presentations and live demos.

## Available Scripts

### 1. Interactive Demo (`ml_model_demo.py`)
**Best for:** Live presentations where you want to control the pace

- Displays predictions for 5 different water quality scenarios
- Waits for user input (Enter key) between scenarios
- Color-coded terminal output with visual progress bars
- Shows detailed WQI scores and anomaly detection results

**Run:**
```bash
python scripts/demo/ml_model_demo.py
# or
scripts\demo\run-ml-demo.bat
```

### 2. Auto Demo (`ml_model_demo_auto.py`)
**Best for:** Automated presentations or quick demonstrations

- Runs through all 5 scenarios automatically
- 3-second delay between scenarios
- Same visual output as interactive version
- No user input required

**Run:**
```bash
python scripts/demo/ml_model_demo_auto.py
# or
scripts\demo\run-ml-demo-auto.bat
```

## Demo Scenarios

The demo showcases 5 different water quality scenarios:

### 🟢 Scenario 1: Excellent Water Quality
- pH: 7.2, Turbidity: 1.5 NTU, TDS: 180 ppm, Temp: 22°C
- Expected: WQI ~97/100, Status: Normal

### 🟡 Scenario 2: Moderate Quality (High TDS)
- pH: 7.5, Turbidity: 3.2 NTU, TDS: 450 ppm, Temp: 26°C
- Expected: WQI ~93/100, Status: Normal

### 🔴 Scenario 3: Poor Quality (High Turbidity)
- pH: 6.8, Turbidity: 15.0 NTU, TDS: 320 ppm, Temp: 28°C
- Expected: WQI ~85/100, Status: Normal

### ⚠️ Scenario 4: Potential Contamination (Acidic)
- pH: 5.2, Turbidity: 8.5 NTU, TDS: 280 ppm, Temp: 24°C
- Expected: WQI ~87/100, Status: Contamination

### ⚠️ Scenario 5: Severe Contamination (Extreme pH)
- pH: 12.5, Turbidity: 0.1 NTU, TDS: 50 ppm, Temp: 45°C
- Expected: WQI ~76/100, Status: Contamination
- Note: Extreme values that indicate severe alkaline contamination

## Requirements

### Python Packages
```bash
pip install xgboost numpy scikit-learn
```

### Model Files
The scripts expect the following files in `ml_models_backup/`:
- `WQI-model-v1.0.pkl` - XGBoost regressor for WQI prediction
- `Anomaly-model-v1.0.pkl` - XGBoost classifier for anomaly detection
- `feature-scaler-v1.0.pkl` - StandardScaler for feature normalization
- `model-metadata-v1.0.json` - Model metadata and configuration

## Output Format

Each scenario displays:

1. **Sensor Readings**
   - pH Level (0-14)
   - Turbidity (NTU)
   - TDS (ppm)
   - Temperature (°C)

2. **Water Quality Index (WQI)**
   - Score (0-100)
   - Color-coded interpretation:
     - 90-100: Excellent (Green)
     - 70-89: Good (Green)
     - 50-69: Fair (Yellow)
     - 25-49: Poor (Yellow)
     - 0-24: Very Poor (Red)

3. **Anomaly Detection**
   - Status: Normal / Contamination / Sensor Fault
   - Confidence percentage
   - Class probability distribution (visual bars)

## Model Information

- **Algorithm:** XGBoost (GPU-accelerated)
- **Accuracy:** 99.74%
- **Features:** 14 engineered features
- **Inference Time:** <500ms
- **Training Date:** 2025-10-20

### Feature Engineering

The demo automatically engineers 14 features from raw sensor data:

**Base Features (7):**
- pH, Turbidity, TDS, Temperature, Humidity, Latitude, Longitude

**Temporal Features (3):**
- Hour of day, Month, Day of week

**Derived Features (4):**
- pH × Temperature interaction
- Turbidity / TDS ratio
- |pH - 7.0| deviation
- Temperature - 25°C deviation

## Troubleshooting

### "Module not found" errors
```bash
pip install xgboost numpy scikit-learn
```

### "Model file not found" errors
Ensure you're running the script from the project root directory:
```bash
cd C:\PROJECT\AquaChain-Final
python scripts/demo/ml_model_demo_auto.py
```

### Color codes not displaying
The scripts use ANSI color codes. If colors don't display:
- Windows: Use Windows Terminal or enable ANSI support
- Linux/Mac: Should work in any terminal

### Demo runs too fast/slow
Edit the `time.sleep(3)` value in `ml_model_demo_auto.py` to adjust the delay between scenarios.

## Customization

### Adding New Scenarios

Edit the `scenarios` list in either script:

```python
scenarios.append({
    'name': '🆕 Your Scenario Name',
    'data': {
        'pH': 7.0,
        'turbidity': 2.0,
        'tds': 200,
        'temperature': 25.0,
        'humidity': 60.0,
        'latitude': 10.0,
        'longitude': 76.0
    }
})
```

### Changing Display Format

Modify the `display_prediction()` method to customize:
- Color schemes
- Progress bar styles
- Information displayed
- Layout and formatting

## Usage Tips

### For Presentations
1. Use **interactive mode** for live demos where you explain each scenario
2. Use **auto mode** for quick overviews or when time is limited
3. Run a test before your presentation to ensure dependencies are installed

### For Development
1. Use these scripts to test model changes
2. Add new scenarios to validate edge cases
3. Compare predictions across model versions

### For Documentation
1. Capture terminal output for documentation
2. Use screenshots of the color-coded results
3. Reference the scenarios in technical reports

## Integration with Presentation

These demos complement the presentation slides in `DOCS/presentation/AquaChain-Presentation-Slides.md`:

- **Slide 6 (ML Model):** Run demo to show live predictions
- **Slide 8 (Performance Metrics):** Reference the 99.74% accuracy shown in demo
- **Slide 18 (Demo Highlights):** Use these scripts as the live demo component

## Support

For issues or questions:
1. Check that all model files exist in `ml_models_backup/`
2. Verify Python version (3.8+)
3. Ensure XGBoost is properly installed
4. Check that you're running from the project root directory
