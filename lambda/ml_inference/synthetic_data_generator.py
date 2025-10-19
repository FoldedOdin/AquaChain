"""
Synthetic Water Quality Data Generator for AquaChain ML Training
Generates realistic water quality data with seasonal patterns, geographic variation,
and anomaly injection for contamination and sensor fault scenarios.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple, List
import json


class SyntheticDataGenerator:
    """
    Generate realistic synthetic water quality data for ML model training
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize the synthetic data generator
        
        Args:
            seed: Random seed for reproducibility
        """
        np.random.seed(seed)
        self.seed = seed
        
        # Geographic regions with different water quality characteristics
        self.regions = {
            'coastal': {'lat_range': (8.0, 10.0), 'lon_range': (76.0, 77.0), 
                       'tds_base': 400, 'turbidity_base': 3.0},
            'inland': {'lat_range': (10.0, 11.5), 'lon_range': (76.5, 77.5),
                      'tds_base': 250, 'turbidity_base': 1.5},
            'mountain': {'lat_range': (11.5, 12.0), 'lon_range': (75.5, 76.5),
                        'tds_base': 150, 'turbidity_base': 0.8},
            'urban': {'lat_range': (9.5, 10.5), 'lon_range': (76.0, 76.8),
                     'tds_base': 500, 'turbidity_base': 4.0}
        }
        
        # Seasonal patterns (monsoon, summer, winter)
        self.seasons = {
            'monsoon': {'months': [6, 7, 8, 9], 'turbidity_mult': 2.5, 'humidity_add': 20},
            'summer': {'months': [3, 4, 5], 'temp_add': 5, 'humidity_sub': 10},
            'winter': {'months': [12, 1, 2], 'temp_sub': 3, 'humidity_sub': 5},
            'post_monsoon': {'months': [10, 11], 'turbidity_mult': 1.3, 'humidity_add': 5}
        }
    
    def generate_dataset(self, n_samples: int = 10000, 
                        contamination_rate: float = 0.05,
                        sensor_fault_rate: float = 0.03) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        """
        Generate complete synthetic dataset with labels
        
        Args:
            n_samples: Number of samples to generate
            contamination_rate: Proportion of contamination events (0-1)
            sensor_fault_rate: Proportion of sensor fault events (0-1)
            
        Returns:
            Tuple of (features_df, wqi_targets, anomaly_labels)
        """
        print(f"Generating {n_samples} synthetic water quality samples...")
        
        # Generate temporal data
        timestamps = self._generate_timestamps(n_samples)
        
        # Generate geographic data
        locations = self._generate_locations(n_samples)
        
        # Generate base sensor readings
        sensor_data = self._generate_sensor_readings(n_samples, timestamps, locations)
        
        # Inject anomalies
        sensor_data, anomaly_labels = self._inject_anomalies(
            sensor_data, contamination_rate, sensor_fault_rate
        )
        
        # Calculate WQI targets
        wqi_targets = self._calculate_wqi_targets(sensor_data)
        
        # Create feature dataframe
        features_df = self._create_feature_dataframe(sensor_data, locations, timestamps)
        
        print(f"Generated dataset: {len(features_df)} samples")
        print(f"  Normal: {np.sum(anomaly_labels == 0)} ({np.sum(anomaly_labels == 0)/len(anomaly_labels)*100:.1f}%)")
        print(f"  Sensor Faults: {np.sum(anomaly_labels == 1)} ({np.sum(anomaly_labels == 1)/len(anomaly_labels)*100:.1f}%)")
        print(f"  Contamination: {np.sum(anomaly_labels == 2)} ({np.sum(anomaly_labels == 2)/len(anomaly_labels)*100:.1f}%)")
        
        return features_df, wqi_targets, anomaly_labels
    
    def _generate_timestamps(self, n_samples: int) -> List[datetime]:
        """Generate realistic timestamps spanning multiple years"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2025, 10, 19)
        
        # Generate random timestamps
        time_range = (end_date - start_date).total_seconds()
        random_seconds = np.random.uniform(0, time_range, n_samples)
        timestamps = [start_date + timedelta(seconds=int(s)) for s in random_seconds]
        
        return sorted(timestamps)
    
    def _generate_locations(self, n_samples: int) -> Dict[str, np.ndarray]:
        """Generate geographic locations with regional clustering"""
        # Assign samples to regions
        region_names = list(self.regions.keys())
        region_assignments = np.random.choice(region_names, n_samples)
        
        latitudes = np.zeros(n_samples)
        longitudes = np.zeros(n_samples)
        
        for i, region_name in enumerate(region_assignments):
            region = self.regions[region_name]
            latitudes[i] = np.random.uniform(*region['lat_range'])
            longitudes[i] = np.random.uniform(*region['lon_range'])
        
        return {
            'latitude': latitudes,
            'longitude': longitudes,
            'region': region_assignments
        }
    
    def _generate_sensor_readings(self, n_samples: int, timestamps: List[datetime],
                                 locations: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Generate realistic sensor readings with seasonal and geographic patterns"""
        
        # Extract temporal features
        hours = np.array([ts.hour for ts in timestamps])
        months = np.array([ts.month for ts in timestamps])
        
        # Initialize sensor readings
        pH = np.zeros(n_samples)
        turbidity = np.zeros(n_samples)
        tds = np.zeros(n_samples)
        temperature = np.zeros(n_samples)
        humidity = np.zeros(n_samples)
        
        for i in range(n_samples):
            region_name = locations['region'][i]
            region = self.regions[region_name]
            month = months[i]
            hour = hours[i]
            
            # Get seasonal adjustments
            season_adj = self._get_seasonal_adjustments(month)
            
            # pH: normally distributed around 7.0 with slight regional variation
            pH_base = 7.0 + (0.3 if region_name == 'urban' else 0.0)
            pH[i] = np.random.normal(pH_base, 0.5)
            pH[i] = np.clip(pH[i], 6.0, 8.5)
            
            # Turbidity: log-normal distribution with regional and seasonal variation
            turbidity_base = region['turbidity_base']
            turbidity_seasonal = turbidity_base * season_adj.get('turbidity_mult', 1.0)
            turbidity[i] = np.random.lognormal(np.log(turbidity_seasonal), 0.5)
            turbidity[i] = np.clip(turbidity[i], 0.1, 50)
            
            # TDS: normal distribution with regional variation
            tds_base = region['tds_base']
            tds[i] = np.random.normal(tds_base, tds_base * 0.3)
            tds[i] = np.clip(tds[i], 50, 1500)
            
            # Temperature: seasonal and diurnal variation
            temp_base = 25.0
            temp_seasonal = temp_base + season_adj.get('temp_add', 0) - season_adj.get('temp_sub', 0)
            temp_diurnal = 3.0 * np.sin((hour - 6) * np.pi / 12)  # Peak at 2 PM
            temperature[i] = np.random.normal(temp_seasonal + temp_diurnal, 2.0)
            temperature[i] = np.clip(temperature[i], 15, 40)
            
            # Humidity: seasonal variation with inverse correlation to temperature
            humidity_base = 60.0
            humidity_seasonal = (humidity_base + 
                               season_adj.get('humidity_add', 0) - 
                               season_adj.get('humidity_sub', 0))
            humidity_temp_adj = -(temperature[i] - 25) * 0.5  # Inverse correlation
            humidity[i] = np.random.normal(humidity_seasonal + humidity_temp_adj, 10)
            humidity[i] = np.clip(humidity[i], 30, 95)
        
        return {
            'pH': pH,
            'turbidity': turbidity,
            'tds': tds,
            'temperature': temperature,
            'humidity': humidity,
            'hour': hours,
            'month': months
        }
    
    def _get_seasonal_adjustments(self, month: int) -> Dict[str, float]:
        """Get seasonal adjustment factors for a given month"""
        for season_name, season_data in self.seasons.items():
            if month in season_data['months']:
                return {k: v for k, v in season_data.items() if k != 'months'}
        return {}
    
    def _inject_anomalies(self, sensor_data: Dict[str, np.ndarray],
                         contamination_rate: float,
                         sensor_fault_rate: float) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
        """
        Inject contamination and sensor fault anomalies
        
        Returns:
            Tuple of (modified_sensor_data, anomaly_labels)
            Labels: 0=normal, 1=sensor_fault, 2=contamination
        """
        n_samples = len(sensor_data['pH'])
        anomaly_labels = np.zeros(n_samples, dtype=int)
        
        # Calculate number of anomalies
        n_contamination = int(n_samples * contamination_rate)
        n_sensor_faults = int(n_samples * sensor_fault_rate)
        
        # Randomly select indices for anomalies
        all_indices = np.arange(n_samples)
        np.random.shuffle(all_indices)
        
        contamination_indices = all_indices[:n_contamination]
        sensor_fault_indices = all_indices[n_contamination:n_contamination + n_sensor_faults]
        
        # Inject contamination events
        for idx in contamination_indices:
            anomaly_labels[idx] = 2
            
            # Contamination patterns
            contamination_type = np.random.choice(['chemical', 'biological', 'industrial'])
            
            if contamination_type == 'chemical':
                # Acidic or alkaline contamination
                sensor_data['pH'][idx] = np.random.choice([
                    np.random.uniform(4.0, 5.5),  # Acidic
                    np.random.uniform(9.0, 11.0)  # Alkaline
                ])
                sensor_data['tds'][idx] *= np.random.uniform(2.0, 4.0)
                
            elif contamination_type == 'biological':
                # High turbidity and moderate pH change
                sensor_data['turbidity'][idx] = np.random.uniform(20, 100)
                sensor_data['pH'][idx] += np.random.uniform(-1.0, 1.5)
                sensor_data['tds'][idx] *= np.random.uniform(1.5, 2.5)
                
            elif contamination_type == 'industrial':
                # Very high TDS and turbidity
                sensor_data['tds'][idx] = np.random.uniform(1500, 3000)
                sensor_data['turbidity'][idx] = np.random.uniform(15, 60)
                sensor_data['pH'][idx] = np.random.uniform(5.0, 9.5)
        
        # Inject sensor fault events
        for idx in sensor_fault_indices:
            anomaly_labels[idx] = 1
            
            # Sensor fault patterns
            fault_type = np.random.choice(['stuck', 'drift', 'noise', 'out_of_range'])
            faulty_sensor = np.random.choice(['pH', 'turbidity', 'tds', 'temperature', 'humidity'])
            
            if fault_type == 'stuck':
                # Sensor stuck at constant value
                stuck_value = sensor_data[faulty_sensor][max(0, idx - 10)]
                sensor_data[faulty_sensor][idx] = stuck_value
                
            elif fault_type == 'drift':
                # Gradual drift from normal range
                if faulty_sensor == 'pH':
                    sensor_data[faulty_sensor][idx] = np.random.choice([
                        np.random.uniform(3.0, 5.0),
                        np.random.uniform(10.0, 12.0)
                    ])
                elif faulty_sensor == 'temperature':
                    sensor_data[faulty_sensor][idx] = np.random.choice([
                        np.random.uniform(-5, 5),
                        np.random.uniform(45, 60)
                    ])
                elif faulty_sensor == 'humidity':
                    sensor_data[faulty_sensor][idx] = np.random.choice([
                        np.random.uniform(0, 15),
                        np.random.uniform(98, 100)
                    ])
                    
            elif fault_type == 'noise':
                # High frequency noise
                sensor_data[faulty_sensor][idx] += np.random.normal(0, 
                    sensor_data[faulty_sensor][idx] * 0.5)
                
            elif fault_type == 'out_of_range':
                # Physically impossible values
                if faulty_sensor == 'pH':
                    sensor_data[faulty_sensor][idx] = np.random.choice([-1, 15])
                elif faulty_sensor == 'turbidity':
                    sensor_data[faulty_sensor][idx] = np.random.uniform(500, 1000)
                elif faulty_sensor == 'temperature':
                    sensor_data[faulty_sensor][idx] = np.random.choice([-20, 80])
        
        # Clip all values to physical limits
        sensor_data['pH'] = np.clip(sensor_data['pH'], 0, 14)
        sensor_data['turbidity'] = np.clip(sensor_data['turbidity'], 0, 1000)
        sensor_data['tds'] = np.clip(sensor_data['tds'], 0, 5000)
        sensor_data['temperature'] = np.clip(sensor_data['temperature'], -10, 80)
        sensor_data['humidity'] = np.clip(sensor_data['humidity'], 0, 100)
        
        return sensor_data, anomaly_labels
    
    def _calculate_wqi_targets(self, sensor_data: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate Water Quality Index targets based on sensor readings"""
        
        pH = sensor_data['pH']
        turbidity = sensor_data['turbidity']
        tds = sensor_data['tds']
        temperature = sensor_data['temperature']
        humidity = sensor_data['humidity']
        
        # Normalize each parameter to 0-100 scale
        pH_score = 100 - np.abs(pH - 7.0) * 15
        pH_score = np.clip(pH_score, 0, 100)
        
        # Turbidity scoring (lower is better)
        turbidity_score = np.where(turbidity <= 1, 100,
                                  np.where(turbidity <= 5, 85,
                                          np.where(turbidity <= 10, 70,
                                                  np.where(turbidity <= 25, 50,
                                                          np.maximum(0, 50 - (turbidity - 25))))))
        
        # TDS scoring
        tds_score = np.where(tds <= 300, 100,
                            np.where(tds <= 600, 85,
                                    np.where(tds <= 900, 70,
                                            np.where(tds <= 1200, 50,
                                                    np.maximum(0, 50 - (tds - 1200) * 0.03)))))
        
        # Temperature scoring (20-30°C optimal)
        temp_deviation = np.minimum(np.abs(temperature - 20), np.abs(temperature - 30))
        temp_score = np.where((temperature >= 20) & (temperature <= 30), 100,
                             np.maximum(0, 100 - temp_deviation * 4))
        
        # Humidity scoring (40-70% optimal)
        humidity_score = np.where((humidity >= 40) & (humidity <= 70), 100,
                                 np.where(humidity < 40, 
                                         np.maximum(0, 100 - (40 - humidity) * 1.5),
                                         np.maximum(0, 100 - (humidity - 70) * 1.5)))
        
        # Weighted average
        weights = np.array([0.25, 0.25, 0.20, 0.15, 0.15])
        wqi = (pH_score * weights[0] + 
               turbidity_score * weights[1] + 
               tds_score * weights[2] + 
               temp_score * weights[3] + 
               humidity_score * weights[4])
        
        # Add small amount of noise
        wqi += np.random.normal(0, 2, len(wqi))
        wqi = np.clip(wqi, 0, 100)
        
        return wqi
    
    def _create_feature_dataframe(self, sensor_data: Dict[str, np.ndarray],
                                 locations: Dict[str, np.ndarray],
                                 timestamps: List[datetime]) -> pd.DataFrame:
        """Create feature dataframe with all features and derived features"""
        
        # Extract temporal features
        hours = sensor_data['hour']
        months = sensor_data['month']
        weekdays = np.array([ts.weekday() for ts in timestamps])
        
        # Create derived features
        pH_temp_interaction = sensor_data['pH'] * sensor_data['temperature']
        turbidity_tds_ratio = sensor_data['turbidity'] / np.maximum(sensor_data['tds'], 1)
        pH_deviation = np.abs(sensor_data['pH'] - 7.0)
        temp_deviation = sensor_data['temperature'] - 25.0
        
        # Create dataframe
        features_df = pd.DataFrame({
            # Base sensor features
            'pH': sensor_data['pH'],
            'turbidity': sensor_data['turbidity'],
            'tds': sensor_data['tds'],
            'temperature': sensor_data['temperature'],
            'humidity': sensor_data['humidity'],
            
            # Location features
            'latitude': locations['latitude'],
            'longitude': locations['longitude'],
            
            # Temporal features
            'hour': hours,
            'month': months,
            'weekday': weekdays,
            
            # Derived features
            'pH_temp_interaction': pH_temp_interaction,
            'turbidity_tds_ratio': turbidity_tds_ratio,
            'pH_deviation': pH_deviation,
            'temp_deviation': temp_deviation,
            
            # Metadata
            'timestamp': timestamps,
            'region': locations['region']
        })
        
        return features_df
    
    def save_dataset(self, features_df: pd.DataFrame, wqi_targets: np.ndarray,
                    anomaly_labels: np.ndarray, output_path: str):
        """Save generated dataset to file"""
        
        # Add targets to dataframe
        dataset = features_df.copy()
        dataset['wqi_target'] = wqi_targets
        dataset['anomaly_label'] = anomaly_labels
        
        # Save to CSV
        dataset.to_csv(output_path, index=False)
        print(f"Dataset saved to {output_path}")
        
        # Save metadata
        metadata = {
            'n_samples': len(dataset),
            'n_features': len(features_df.columns) - 2,  # Exclude timestamp and region
            'contamination_count': int(np.sum(anomaly_labels == 2)),
            'sensor_fault_count': int(np.sum(anomaly_labels == 1)),
            'normal_count': int(np.sum(anomaly_labels == 0)),
            'wqi_mean': float(np.mean(wqi_targets)),
            'wqi_std': float(np.std(wqi_targets)),
            'generation_date': datetime.utcnow().isoformat(),
            'seed': self.seed
        }
        
        metadata_path = output_path.replace('.csv', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to {metadata_path}")


def main():
    """Generate and save synthetic training dataset"""
    
    # Initialize generator
    generator = SyntheticDataGenerator(seed=42)
    
    # Generate dataset
    features_df, wqi_targets, anomaly_labels = generator.generate_dataset(
        n_samples=50000,
        contamination_rate=0.05,
        sensor_fault_rate=0.03
    )
    
    # Save dataset
    generator.save_dataset(
        features_df, 
        wqi_targets, 
        anomaly_labels,
        'training_data.csv'
    )
    
    print("\nDataset generation complete!")
    print(f"Total samples: {len(features_df)}")
    print(f"Features: {len(features_df.columns) - 2}")  # Exclude timestamp and region
    print(f"WQI range: {wqi_targets.min():.2f} - {wqi_targets.max():.2f}")
    print(f"WQI mean: {wqi_targets.mean():.2f} ± {wqi_targets.std():.2f}")


if __name__ == "__main__":
    main()
