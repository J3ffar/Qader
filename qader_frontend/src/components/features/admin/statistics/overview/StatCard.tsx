import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string;
  icon: LucideIcon;
  description?: string;
  colorScheme?: 'blue' | 'green' | 'purple' | 'orange' | 'rose' | 'teal';
}

const colorSchemes = {
  blue: {
    gradient: "bg-gradient-to-br from-blue-50 to-blue-100/50 dark:from-blue-950/20 dark:to-blue-900/10",
    iconBg: "bg-blue-500/10 dark:bg-blue-400/10",
    iconColor: "text-blue-600 dark:text-blue-400",
    border: "border-blue-200/50 dark:border-blue-800/30",
    shadow: "shadow-blue-100/20 dark:shadow-blue-900/10"
  },
  green: {
    gradient: "bg-gradient-to-br from-emerald-50 to-green-100/50 dark:from-emerald-950/20 dark:to-green-900/10",
    iconBg: "bg-emerald-500/10 dark:bg-emerald-400/10",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    border: "border-emerald-200/50 dark:border-emerald-800/30",
    shadow: "shadow-emerald-100/20 dark:shadow-emerald-900/10"
  },
  purple: {
    gradient: "bg-gradient-to-br from-purple-50 to-violet-100/50 dark:from-purple-950/20 dark:to-violet-900/10",
    iconBg: "bg-purple-500/10 dark:bg-purple-400/10",
    iconColor: "text-purple-600 dark:text-purple-400",
    border: "border-purple-200/50 dark:border-purple-800/30",
    shadow: "shadow-purple-100/20 dark:shadow-purple-900/10"
  },
  orange: {
    gradient: "bg-gradient-to-br from-orange-50 to-amber-100/50 dark:from-orange-950/20 dark:to-amber-900/10",
    iconBg: "bg-orange-500/10 dark:bg-orange-400/10",
    iconColor: "text-orange-600 dark:text-orange-400",
    border: "border-orange-200/50 dark:border-orange-800/30",
    shadow: "shadow-orange-100/20 dark:shadow-orange-900/10"
  },
  rose: {
    gradient: "bg-gradient-to-br from-rose-50 to-pink-100/50 dark:from-rose-950/20 dark:to-pink-900/10",
    iconBg: "bg-rose-500/10 dark:bg-rose-400/10",
    iconColor: "text-rose-600 dark:text-rose-400",
    border: "border-rose-200/50 dark:border-rose-800/30",
    shadow: "shadow-rose-100/20 dark:shadow-rose-900/10"
  },
  teal: {
    gradient: "bg-gradient-to-br from-teal-50 to-cyan-100/50 dark:from-teal-950/20 dark:to-cyan-900/10",
    iconBg: "bg-teal-500/10 dark:bg-teal-400/10",
    iconColor: "text-teal-600 dark:text-teal-400",
    border: "border-teal-200/50 dark:border-teal-800/30",
    shadow: "shadow-teal-100/20 dark:shadow-teal-900/10"
  }
};

export function StatCard({
  title,
  value,
  icon: Icon,
  description,
  colorScheme = 'blue'
}: StatCardProps) {
  const colors = colorSchemes[colorScheme];
  
  return (
    <Card className={`relative overflow-hidden ${colors.gradient} ${colors.border} ${colors.shadow} shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-700 dark:text-gray-200">
          {title}
        </CardTitle>
        <div className={`p-2 rounded-lg ${colors.iconBg}`}>
          <Icon className={`h-5 w-5 ${colors.iconColor}`} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">
          {value}
        </div>
        {description && (
          <p className="text-xs text-gray-600 dark:text-gray-400">
            {description}
          </p>
        )}
      </CardContent>
      
      {/* Decorative elements */}
      <div className="absolute top-0 right-0 w-24 h-24 opacity-10">
        <div className={`w-full h-full rounded-full ${colors.iconColor.replace('text-', 'bg-')} blur-2xl`}></div>
      </div>
    </Card>
  );
}
