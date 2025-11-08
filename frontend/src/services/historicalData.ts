import { TimeRange } from '../components/History/TimeRangeFilter';

export interface HistoricalDataPoint {
  timestamp: string;
  pH: number;
  turbidity: number;
  tds: number;
  temperature: number;
  humidity: number;
  wqi: number;
}

// Generate mock historical data
const generateHistoricalData = (days: number, pointsPerDay: number = 24): HistoricalDataPoint[] => {
  const data: HistoricalDataPoint[] = [];
  const now = new Date();
  
  for (let day = days - 1; day >= 0; day--) {
    for (let hour = 0; hour < pointsPerDay; hour++) {
      const timestamp = new Date(now.getTime() - (day * 24 * 60 * 60 * 1000) - (hour * 60 * 60 * 1000));
      
      // Base values with some seasonal and daily variation
      const timeOfDay = hour / 24; // 0 to 1
      const dayOfPeriod = (days - day) / days; // 0 to 1
      
      // Simulate daily patterns and gradual changes over time
      const dailyVariation = Math.sin(timeOfDay * 2 * Math.PI) * 0.1;
      const seasonalTrend = Math.sin(dayOfPeriod * Math.PI) * 0.2;
      const randomNoise = (Math.random() - 0.5) * 0.1;
      
      const baseValues = {
        pH: 7.2 + dailyVariation + seasonalTrend + randomNoise,
        turbidity: 1.5 + Math.abs(dailyVariation * 2) + Math.abs(randomNoise * 3),
        tds: 150 + dailyVariation * 50 + seasonalTrend * 100 + randomNoise * 30,
        temperature: 24 + dailyVariation * 3 + seasonalTrend * 5 + randomNoise * 2,
        humidity: 65 + dailyVariation * 10 + seasonalTrend * 15 + randomNoise * 5
      };
      
      // Ensure values stay within realistic ranges
      const readings = {
        pH: Math.max(0, Math.min(14, baseValues.pH)),
        turbidity: Math.max(0, baseValues.turbidity),
        tds: Math.max(0, baseValues.tds),
        temperature: Math.max(-10, Math.min(50, baseValues.temperature)),
        humidity: Math.max(0, Math.min(100, baseValues.humidity))
      };
      
      // Calculate WQI based on readings
      const wqi = calculateWQI(readings);
      
      data.push({
        timestamp: timestamp.toISOString(),
        ...readings,
        wqi
      });
    }
  }
  
  return data.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
};

// Calculate Water Quality Index
const calculateWQI = (readings: { pH: number; turbidity: number; tds: number; temperature: number; humidity: number }): number => {
  // Normalize each parameter to 0-100 scale
  const pHScore = readings.pH >= 6.5 && readings.pH <= 8.5 ? 100 : Math.max(0, 100 - Math.abs(readings.pH - 7.0) * 20);
  const turbidityScore = Math.max(0, 100 - (readings.turbidity / 4.0) * 100);
  const tdsScore = Math.max(0, 100 - (readings.tds / 500) * 100);
  const tempScore = readings.temperature >= 0 && readings.temperature <= 40 ? 100 : Math.max(0, 100 - Math.abs(readings.temperature - 20) * 5);
  const humidityScore = readings.humidity >= 30 && readings.humidity <= 70 ? 100 : Math.max(0, 100 - Math.abs(readings.humidity - 50) * 2);
  
  // Weighted average
  const weights = { pH: 0.25, turbidity: 0.25, tds: 0.20, temperature: 0.15, humidity: 0.15 };
  const wqi = (
    pHScore * weights.pH +
    turbidityScore * weights.turbidity +
    tdsScore * weights.tds +
    tempScore * weights.temperature +
    humidityScore * weights.humidity
  );
  
  return Math.round(Math.max(0, Math.min(100, wqi)));
};

// Generate data with some anomalies for testing
const generateDataWithAnomalies = (baseData: HistoricalDataPoint[]): HistoricalDataPoint[] => {
  return baseData.map((point, index) => {
    // Add some anomalies randomly (5% chance)
    if (Math.random() < 0.05) {
      const anomalyType = Math.random();
      if (anomalyType < 0.33) {
        // pH anomaly
        return {
          ...point,
          pH: Math.random() < 0.5 ? 4.0 + Math.random() * 2 : 9.0 + Math.random() * 2,
          wqi: Math.min(point.wqi, 30)
        };
      } else if (anomalyType < 0.66) {
        // Turbidity spike
        return {
          ...point,
          turbidity: 5 + Math.random() * 10,
          wqi: Math.min(point.wqi, 40)
        };
      } else {
        // TDS spike
        return {
          ...point,
          tds: 500 + Math.random() * 300,
          wqi: Math.min(point.wqi, 35)
        };
      }
    }
    return point;
  });
};

// Cache for generated data
const dataCache: { [key: string]: HistoricalDataPoint[] } = {};

export const getHistoricalData = (timeRange: TimeRange): HistoricalDataPoint[] => {
  if (dataCache[timeRange]) {
    return dataCache[timeRange];
  }
  
  let days: number;
  let pointsPerDay: number;
  
  switch (timeRange) {
    case '1day':
      days = 1;
      pointsPerDay = 24; // Hourly data
      break;
    case '1week':
      days = 7;
      pointsPerDay = 8; // Every 3 hours
      break;
    case '1month':
      days = 30;
      pointsPerDay = 4; // Every 6 hours
      break;
    case '3months':
      days = 90;
      pointsPerDay = 1; // Daily data
      break;
    default:
      days = 7;
      pointsPerDay = 8;
  }
  
  const baseData = generateHistoricalData(days, pointsPerDay);
  const dataWithAnomalies = generateDataWithAnomalies(baseData);
  
  dataCache[timeRange] = dataWithAnomalies;
  return dataWithAnomalies;
};

// Export data for specific device
export const getDeviceHistoricalData = (deviceId: string, timeRange: TimeRange): HistoricalDataPoint[] => {
  // For now, return the same data regardless of device
  // In a real implementation, this would filter by device
  return getHistoricalData(timeRange);
};