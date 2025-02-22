import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export const ProcessPatterns = ({ data }: { data: any }) => {
  // Transform patterns data for visualization
  const patternsData = data?.patterns?.map((pattern: any) => ({
    name: pattern.name,
    frequency: pattern.frequency,
    duration: pattern.performance_metrics?.avg_duration || 0,
    impact: pattern.performance_metrics?.business_impact || 0
  })) || [];

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={patternsData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          <Tooltip />
          <Legend />
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="frequency" 
            stroke="hsl(var(--chart-2))" 
            name="Frequency"
          />
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="impact" 
            stroke="hsl(var(--chart-3))" 
            name="Business Impact"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};