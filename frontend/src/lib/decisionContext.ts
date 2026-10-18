import type { Evaluation } from './api'

export type DecisionContext = Pick<Evaluation['request'], 'proposal_id' | 'horizon_days' | 'paths' | 'seed' | 'action_ids'>

export function readDecisionLink(hash: string): Partial<DecisionContext> & { view: string } {
  const [view, query = ''] = hash.replace(/^#/, '').split('?')
  const params = new URLSearchParams(query)
  const bounded = (name: string, minimum: number, maximum: number) => {
    const raw = params.get(name)
    const number = Number(raw)
    return raw !== null && Number.isInteger(number) && number >= minimum && number <= maximum ? number : undefined
  }
  const actions = params.get('actions')?.split(',')
  return { view: view || 'overview', proposal_id: params.get('proposal') ?? undefined,
    horizon_days: bounded('horizon', 1, 30), paths: bounded('paths', 1, 5000), seed: bounded('seed', 0, 2**32-1),
    action_ids: actions?.length && actions.every(id => ['full', 'partial', 'defer', 'hold'].includes(id)) ? actions as DecisionContext['action_ids'] : undefined }
}

export function decisionLink(view: string, context: DecisionContext): string {
  const params = new URLSearchParams({ proposal: context.proposal_id, horizon: String(context.horizon_days),
    paths: String(context.paths), seed: String(context.seed), actions: context.action_ids.join(',') })
  return `${view}?${params}`
}

// Association only: financial calculations remain exclusively on the backend.
export function matchesDecision(evaluation: Evaluation, context: DecisionContext): boolean {
  const request = evaluation.request
  return request.proposal_id === context.proposal_id && request.horizon_days === context.horizon_days &&
    request.paths === context.paths && request.seed === context.seed &&
    [...request.action_ids].sort().join('|') === [...context.action_ids].sort().join('|')
}
