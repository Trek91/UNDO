import type { components, paths } from '../types/api'
export type Overview = components['schemas']['Overview']
export type State = components['schemas']['State']
export type Decision = components['schemas']['DecisionRecord']
export type Evaluation = components['schemas']['Evaluation']
export type ActionResult = components['schemas']['ActionResult']
export type EventPage = components['schemas']['EventPage']
export type DecisionPage = components['schemas']['DecisionPage']
export type AuditPage = components['schemas']['AuditPage']
export type Event = components['schemas']['EventRecord']['event']
export type EventInput = paths['/api/events']['post']['requestBody']['content']['application/json']
export type ModelEvidence = components['schemas']['ModelEvidence']
export type LabResult = components['schemas']['LabResult']
export type LabRequest = components['schemas']['LabRequest']
export type ScenarioChanges = components['schemas']['ScenarioChanges']

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 30000)
  try {
    const response = await fetch(`/api${path}`, { ...options, signal: options.signal ?? controller.signal,
      headers: { 'Content-Type': 'application/json', ...options.headers } })
    const body = await response.json()
    if (!response.ok) {
      const issues = body.error?.issues?.map((issue: { field: string; message: string }) => `${issue.field}: ${issue.message}`).join('; ')
      throw new Error(issues || body.error?.message || 'The request could not be completed.')
    }
    return body as T
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw new Error('The request timed out. Refresh and retry.')
    throw error
  } finally { window.clearTimeout(timeout) }
}
export const post = <T,>(path: string, body?: unknown) => api<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
export const currency = (paise: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: paise % 100 === 0 ? 0 : 2 }).format(paise / 100)
export const percent = (value: number) => new Intl.NumberFormat('en-IN', { style: 'percent', maximumFractionDigits: 1 }).format(value)
export const dateLabel = (value: string) => new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', timeZone: 'Asia/Kolkata' }).format(new Date(value.length === 10 ? `${value}T12:00:00+05:30` : value))
export const timeLabel = (value: string) => new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'Asia/Kolkata' }).format(new Date(value))
