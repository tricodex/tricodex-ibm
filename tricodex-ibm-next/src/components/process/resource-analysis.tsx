import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

export const ResourceAnalysis = ({ data }: { data: any }) => {
  const resourceData = data?.performance?.resources?.resource_patterns?.resource_load || {};
  
  // Transform resource data for visualization with proper type handling
  const chartData = Object.entries(resourceData).map(([resource, load]: [string, any]) => ({
    name: resource,
    value: typeof load === 'number' 
      ? load 
      : (Object.values(load as Record<string, number>).reduce((a, b) => (a || 0) + (b || 0), 0))
  }));

  const COLORS = [
    'hsl(var(--chart-1))',
    'hsl(var(--chart-2))',
    'hsl(var(--chart-3))',
    'hsl(var(--chart-4))',
    'hsl(var(--chart-5))'
  ];

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            fill="#8884d8"
            paddingAngle={5}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};