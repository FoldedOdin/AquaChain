import React, { useState, useEffect } from 'react';
import { useABTesting } from '../../hooks/useABTesting';
import { ABTest, ABTestResult } from '../../services/abTestingService';

interface ABTestDashboardProps {
  className?: string;
}

const ABTestDashboard: React.FC<ABTestDashboardProps> = ({ className = '' }) => {
  const { isInitialized, getActiveTests, getTestResults } = useABTesting();
  const [activeTests, setActiveTests] = useState<ABTest[]>([]);
  const [selectedTest, setSelectedTest] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<ABTestResult[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (isInitialized) {
      const tests = getActiveTests();
      setActiveTests(tests);
      setIsLoading(false);
    }
  }, [isInitialized, getActiveTests]);

  useEffect(() => {
    if (selectedTest) {
      const results = getTestResults(selectedTest);
      setTestResults(results);
    }
  }, [selectedTest, getTestResults]);

  const handleTestSelect = (testId: string) => {
    setSelectedTest(testId);
  };

  const getWinningVariant = (results: ABTestResult[]) => {
    return results.reduce((winner, current) => 
      current.conversionRate > winner.conversionRate ? current : winner
    );
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const formatConfidence = (confidence: number) => {
    if (confidence >= 95) return { text: formatPercentage(confidence), color: 'text-green-600' };
    if (confidence >= 90) return { text: formatPercentage(confidence), color: 'text-yellow-600' };
    return { text: formatPercentage(confidence), color: 'text-red-600' };
  };

  if (!isInitialized || isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-md ${className}`}>
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900">A/B Test Dashboard</h2>
        <p className="text-gray-600 mt-1">Monitor and analyze your active experiments</p>
      </div>

      <div className="p-6">
        {activeTests.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-lg mb-2">No active tests</div>
            <p className="text-gray-500">Create your first A/B test to start optimizing conversions</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Test List */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Tests</h3>
              <div className="space-y-3">
                {activeTests.map((test) => (
                  <div
                    key={test.testId}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedTest === test.testId
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleTestSelect(test.testId)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-gray-900">{test.testName}</h4>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        test.status === 'active' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {test.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{test.description}</p>
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>{test.variants.length} variants</span>
                      <span>{test.trafficAllocation}% traffic</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Test Results */}
            <div>
              {selectedTest && testResults ? (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Results</h3>
                  <div className="space-y-4">
                    {testResults.map((result) => {
                      const confidence = formatConfidence(result.confidence);
                      const isWinner = result === getWinningVariant(testResults);
                      
                      return (
                        <div
                          key={result.variantId}
                          className={`p-4 border rounded-lg ${
                            isWinner ? 'border-green-500 bg-green-50' : 'border-gray-200'
                          }`}
                        >
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <h4 className="font-medium text-gray-900 flex items-center">
                                {result.variantName}
                                {isWinner && (
                                  <span className="ml-2 px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                                    Winner
                                  </span>
                                )}
                              </h4>
                              <p className="text-sm text-gray-600">
                                {result.participants} participants
                              </p>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-semibold text-gray-900">
                                {formatPercentage(result.conversionRate)}
                              </div>
                              <div className={`text-sm ${confidence.color}`}>
                                {confidence.text} confidence
                              </div>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-gray-500">Conversions:</span>
                              <span className="ml-1 font-medium">{result.conversions}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">Significant:</span>
                              <span className={`ml-1 font-medium ${
                                result.statisticalSignificance ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {result.statisticalSignificance ? 'Yes' : 'No'}
                              </span>
                            </div>
                          </div>

                          {/* Progress Bar */}
                          <div className="mt-3">
                            <div className="flex justify-between text-xs text-gray-500 mb-1">
                              <span>Conversion Rate</span>
                              <span>{formatPercentage(result.conversionRate)}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${
                                  isWinner ? 'bg-green-500' : 'bg-blue-500'
                                }`}
                                style={{ width: `${Math.min(result.conversionRate, 100)}%` }}
                              ></div>
                            </div>
                          </div>

                          {/* Additional Metrics */}
                          {Object.keys(result.metrics).length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-200">
                              <h5 className="text-sm font-medium text-gray-700 mb-2">Additional Metrics</h5>
                              <div className="grid grid-cols-2 gap-2 text-xs">
                                {Object.entries(result.metrics).map(([metric, value]) => (
                                  <div key={metric} className="flex justify-between">
                                    <span className="text-gray-500 capitalize">
                                      {metric.replace(/_/g, ' ')}:
                                    </span>
                                    <span className="font-medium">{value}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Test Summary */}
                  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-2">Test Summary</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Total Participants:</span>
                        <span className="ml-1 font-medium">
                          {testResults.reduce((sum, r) => sum + r.participants, 0)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Total Conversions:</span>
                        <span className="ml-1 font-medium">
                          {testResults.reduce((sum, r) => sum + r.conversions, 0)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Best Variant:</span>
                        <span className="ml-1 font-medium">
                          {getWinningVariant(testResults).variantName}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Improvement:</span>
                        <span className="ml-1 font-medium text-green-600">
                          +{(getWinningVariant(testResults).conversionRate - 
                             (testResults.find(r => r.variantName.includes('Control'))?.conversionRate || 0)
                          ).toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-gray-400 text-lg mb-2">Select a test</div>
                  <p className="text-gray-500">Choose a test from the list to view detailed results</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ABTestDashboard;