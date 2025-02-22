import { Document, Page, View, Text, StyleSheet } from '@react-pdf/renderer';
import { type AnalysisResult } from '@/types';

const styles = StyleSheet.create({
  page: {
    padding: 30,
    fontSize: 12,
  },
  header: {
    fontSize: 24,
    marginBottom: 20,
  },
  section: {
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 16,
    marginBottom: 10,
  },
  metricsGrid: {
    display: 'flex',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  metricBox: {
    padding: 10,
    border: '1pt solid #ccc',
    width: '45%',
  },
  thoughtStream: {
    marginTop: 20,
  },
  thought: {
    marginBottom: 10,
    padding: 8,
    backgroundColor: '#f5f5f5',
  },
  timestamp: {
    color: '#666',
    fontSize: 10,
  }
});

export const AnalysisPDF = ({ data }: { data: AnalysisResult }) => (
  <Document>
    <Page size="A4" style={styles.page}>
      {/* Header */}
      <View>
        <Text style={styles.header}>Process Analysis Report</Text>
        <Text>Generated on: {new Date().toLocaleDateString()}</Text>
      </View>

      {/* Key Metrics */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Key Performance Metrics</Text>
        <View style={styles.metricsGrid}>
          {Object.entries(data.results?.performance || {}).map(([key, value]) => (
            <View key={key} style={styles.metricBox}>
              <Text>
                {key}: {typeof value === 'number' 
                  ? (value as number).toFixed(2) 
                  : JSON.stringify(value)}
              </Text>
            </View>
          ))}
        </View>
      </View>

      {/* Patterns */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Identified Process Patterns</Text>
        {data.results?.patterns.map((pattern, index) => (
          <View key={index} style={styles.metricBox}>
            <Text>Pattern: {pattern.name}</Text>
            <Text>Frequency: {pattern.frequency}</Text>
            <Text>Impact: {pattern.performance_metrics?.business_impact || 'N/A'}</Text>
          </View>
        ))}
      </View>

      {/* Recommendations */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Improvement Recommendations</Text>
        {data.results?.improvements.map((improvement: any, index: number) => (
          <View key={index} style={styles.metricBox}>
            <Text>Action: {improvement.action}</Text>
            <Text>Expected Impact: {improvement.expected_impact}%</Text>
            <Text>Implementation: {improvement.implementation_complexity} days</Text>
          </View>
        ))}
      </View>

      {/* Thought Stream */}
      <View style={styles.thoughtStream}>
        <Text style={styles.sectionTitle}>Analysis Timeline</Text>
        {data.thoughts.map((thought, index) => (
          <View key={index} style={styles.thought}>
            <Text style={styles.timestamp}>
              {new Date(thought.timestamp).toLocaleString()}
            </Text>
            <Text>{thought.thought}</Text>
          </View>
        ))}
      </View>
    </Page>
  </Document>
);