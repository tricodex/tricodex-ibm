import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export const ProcessMetrics = ({ data }: { data: any }) => {
  const metricsData = [
    { name: 'Cycle Time', value: data?.performance?.timing?.cycle_time || 0 },
    { name: 'Processing Time', value: data?.performance?.timing?.processing_time || 0 },
    { name: 'Wait Time', value: data?.performance?.timing?.waiting_time || 0 },
    { name: 'Error Rate', value: (data?.performance?.quality?.error_rate || 0) * 100 },
    { name: 'Resource Util.', value: (data?.performance?.resources?.resource_utilization || 0) * 100 },
  ];

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={metricsData}>
          <CartesianGrid strokeDasharray="3 3" className="opacity-50" />
          <XAxis 
            dataKey="name" 
            tick={{ fill: 'hsl(var(--foreground))' }}
            axisLine={{ stroke: 'hsl(var(--border))' }}
          />
          <YAxis 
            tick={{ fill: 'hsl(var(--foreground))' }}
            axisLine={{ stroke: 'hsl(var(--border))' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--background))',
              border: '1px solid hsl(var(--border))',
              borderRadius: 'var(--radius)',
            }}
            labelStyle={{
              color: 'hsl(var(--foreground))',
            }}
          />
          <Bar 
            dataKey="value" 
            fill="hsl(var(--primary))"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};