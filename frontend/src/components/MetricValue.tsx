import type { Decision } from '../lib/api'

type Metric = NonNullable<Decision['model_statistics']>['precision']
export function MetricValue({ metric }: { metric?: Metric | null }) {
  if (!metric || metric.status === 'unverified') return <>Unavailable — {metric?.reason ?? 'stored denominator counts unavailable'}</>
  if (!metric.defined || metric.value === null) return <>Undefined — {metric.reason}</>
  return <>{metric.value.toFixed(6)}</>
}
