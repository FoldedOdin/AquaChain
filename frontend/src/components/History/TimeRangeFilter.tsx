import React from 'react';

export type TimeRange = '1day' | '1week' | '1month' | '3months';

interface TimeRangeFilterProps {
  selectedRange: TimeRange;
  onRangeChange: (range: TimeRange) => void;
}

const TimeRangeFilter: React.FC<TimeRangeFilterProps> = ({ 
  selectedRange, 
  onRangeChange 
}) => {
  const timeRanges: { value: TimeRange; label: string }[] = [
    { value: '1day', label: '24 Hours' },
    { value: '1week', label: '7 Days' },
    { value: '1month', label: '30 Days' },
    { value: '3months', label: '3 Months' }
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {timeRanges.map((range) => (
        <button
          key={range.value}
          onClick={() => onRangeChange(range.value)}
          className={`
            px-4 py-2 text-sm font-medium rounded-md transition-colors duration-200
            ${selectedRange === range.value
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }
          `}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
};

export default TimeRangeFilter;