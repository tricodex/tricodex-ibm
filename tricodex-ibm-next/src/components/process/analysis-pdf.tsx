import React from 'react';
import { Page, Text, View, Document, StyleSheet } from '@react-pdf/renderer';
import { AnalysisResult, ProcessPattern, ProcessImprovement, ProcessMetric } from '@/types';

interface AnalysisPDFProps {
  data: AnalysisResult;
}

const styles = StyleSheet.create({
  page: {
    flexDirection: 'column',
    padding: 30,
  },
  section: {
    margin: 10,
    padding: 10,
  },
  header: {
    fontSize: 24,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    marginBottom: 10,
  },
  text: {
    fontSize: 12,
    marginBottom: 5,
  },
  metricBox: {
    padding: 10,
    marginBottom: 10,
    borderBottom: '1pt solid #ccc',
  },
  insightBox: {
    padding: 8,
    marginBottom: 8,
  },
});

export const AnalysisPDF = ({ data }: { data: AnalysisResult }) => {
  // Safely access potentially undefined results
  const patterns = data.results?.patterns ?? [];
  const improvements = data.results?.improvements ?? [];
  const metrics = data.results?.synthesis?.metrics ?? {};
  const insights = data.results?.synthesis?.insights ?? [];

  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <View style={styles.section}>
          <Text style={styles.header}>Process Analysis Report</Text>
          <Text style={styles.text}>Task ID: {data.taskId}</Text>
          <Text style={styles.text}>Status: {data.status}</Text>
          <Text style={styles.text}>Progress: {data.progress}%</Text>
          {data.error && (
            <Text style={{ ...styles.text, color: 'red' }}>Error: {data.error}</Text>
          )}
        </View>

        {insights.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Key Insights</Text>
            {insights.map((insight, index) => (
              <View key={index} style={styles.insightBox}>
                <Text style={styles.text}>{insight}</Text>
              </View>
            ))}
          </View>
        )}

        {patterns.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Process Patterns</Text>
            {patterns.map((pattern, index) => (
              <View key={index} style={styles.metricBox}>
                <Text style={styles.text}>Pattern: {pattern.name}</Text>
                <Text style={styles.text}>Frequency: {pattern.frequency}</Text>
                {pattern.description && (
                  <Text style={styles.text}>Description: {pattern.description}</Text>
                )}
                {pattern.performance_metrics && (
                  <View>
                    {pattern.performance_metrics.avg_duration && (
                      <Text style={styles.text}>Average Duration: {pattern.performance_metrics.avg_duration}</Text>
                    )}
                    {pattern.performance_metrics.business_impact && (
                      <Text style={styles.text}>Business Impact: {pattern.performance_metrics.business_impact}%</Text>
                    )}
                  </View>
                )}
              </View>
            ))}
          </View>
        )}

        {Object.keys(metrics).length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Performance Metrics</Text>
            {Object.entries(metrics).map(([key, metric]: [string, ProcessMetric], index) => (
              <View key={index} style={styles.metricBox}>
                <Text style={styles.text}>
                  {metric.label}: {metric.value} {metric.unit}
                </Text>
              </View>
            ))}
          </View>
        )}

        {improvements.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Recommendations</Text>
            {improvements.map((improvement, index) => (
              <View key={index} style={styles.insightBox}>
                <Text style={styles.text}>
                  {improvement.action}: {improvement.suggestion}
                </Text>
                <Text style={styles.text}>
                  Expected Impact: {improvement.expected_impact}%
                </Text>
                <Text style={styles.text}>
                  Implementation Time: {improvement.implementation_complexity} days
                </Text>
              </View>
            ))}
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Analysis Timeline</Text>
          {data.thoughts.map((thought, index) => (
            <View key={index} style={styles.insightBox}>
              <Text style={styles.text}>
                {new Date(thought.timestamp).toLocaleString()}: {thought.thought}
              </Text>
            </View>
          ))}
        </View>
      </Page>
    </Document>
  );
};