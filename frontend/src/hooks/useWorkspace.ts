import { useCallback, useEffect, useRef, useState } from 'react'
import { api, post } from '../lib/api'
import type { AuditPage, Decision, DecisionPage, EventPage, Overview } from '../lib/api'

function mergeRows<T>(recent: T[], loaded: T[], key: (item: T) => number | string): T[] {
  const rows = new Map(recent.map(item => [key(item), item]))
  for (const item of loaded) if (!rows.has(key(item))) rows.set(key(item), item)
  return [...rows.values()]
}

function refreshPage<T, C>(recent: { items: T[]; next_before: C }, loaded: { items: T[]; next_before: C }, key: (item: T) => number | string) {
  if (!loaded.items.length) return recent
  const known = new Set(loaded.items.map(key))
  // If more than a page arrived while disconnected, retain the server's cursor
  // rather than merge across an unobserved gap and skip it on the next page.
  if (recent.items.length && !recent.items.some(item => known.has(key(item)))) return recent
  return { items: mergeRows(recent.items, loaded.items, key), next_before: loaded.next_before }
}

const markStale = (record: Decision, state: Overview['state']): Decision => ({ ...record,
  stale: record.stale || record.evaluation.generation !== state.generation || record.evaluation.state_version !== state.version,
})

export function useWorkspace() {
  const [overview, setOverview] = useState<Overview | null>(null)
  const [events, setEvents] = useState<EventPage>({ items: [], next_before: null })
  const [history, setHistory] = useState<DecisionPage>({ items: [], next_before: null })
  const [audit, setAudit] = useState<AuditPage>({ items: [], next_before: null })
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [connection, setConnection] = useState<'connecting' | 'live' | 'reconnecting'>('connecting')
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const requestSequence = useRef(0)
  const accepted = useRef<Overview | null>(null)
  const invalidate = useCallback(() => { requestSequence.current++ }, [])
  const refresh = useCallback(async () => {
    const sequence = ++requestSequence.current
    try {
      const next = await api<Overview>('/overview')
      const generation = next.state.generation
      const [recentEvents, decisions, auditTrail] = await Promise.all([
        api<EventPage>(`/events?generation=${generation}`), api<DecisionPage>(`/decisions?generation=${generation}`), api<AuditPage>('/audit'),
      ])
      if (sequence !== requestSequence.current) return
      const previous = accepted.current
      if (previous && (generation < previous.state.generation ||
          (generation === previous.state.generation && (next.state.version < previous.state.version ||
            next.notification_cursor < previous.notification_cursor)))) return
      accepted.current = next
      const sameGeneration = previous?.state.generation === generation
      setOverview(next)
      setEvents(loaded => sameGeneration ? refreshPage(recentEvents, loaded, row => row.seq) : recentEvents)
      setHistory(loaded => {
        const page = sameGeneration ? refreshPage(decisions, loaded, row => row.evaluation.id) : decisions
        return { ...page, items: page.items.map(row => markStale(row, next.state)) }
      })
      setAudit(loaded => previous ? refreshPage(auditTrail, loaded, row => row.seq) : auditTrail)
      setLastUpdated(new Date().toISOString()); setError(null)
    } catch (reason) { if (sequence === requestSequence.current) setError(reason instanceof Error ? reason.message : 'Connection failed.') }
  }, [])
  useEffect(() => {
    void refresh()
    let timer: ReturnType<typeof setTimeout> | undefined
    const schedule = () => { clearTimeout(timer); timer = setTimeout(() => void refresh(), 100) }
    const stream = new EventSource('/api/events/stream')
    stream.onopen = () => { setConnection('live'); schedule() }
    stream.onerror = () => setConnection('reconnecting')
    stream.addEventListener('update', schedule)
    stream.addEventListener('snapshot', schedule)
    stream.addEventListener('reset', schedule)
    const fallback = setInterval(() => void refresh(), 10000)
    return () => { stream.close(); clearTimeout(timer); clearInterval(fallback); invalidate() }
  }, [refresh, invalidate])
  useEffect(() => {
    if (!overview?.recalculating) return
    const timer = setInterval(() => void refresh(), 1000)
    return () => clearInterval(timer)
  }, [overview?.recalculating, refresh])
  const mutate = useCallback(async <T,>(work: () => Promise<T>, success: string): Promise<T | undefined> => {
    setBusy(true); setError(null); setNotice(null)
    try { const result = await work(); setNotice(success); await refresh(); return result }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'The update failed.'); return undefined }
    finally { setBusy(false) }
  }, [refresh])
  const generation = overview?.state.generation
  const version = overview?.state.version
  const postCurrent = useCallback(<T,>(path: string, body?: unknown) => {
    if (generation === undefined || version === undefined) return Promise.reject(new Error('Load the workspace before changing it.'))
    return post<T>(`${path}?expected_generation=${generation}&expected_version=${version}`, body)
  }, [generation, version])
  const evaluate = (request: object = {}) => mutate(() => postCurrent<Decision>('/decisions/evaluate', request), 'Comparison calculated and saved to the audit trail.')
  const loadMoreEvents = async () => {
    if (!events.next_before) return
    const cursor = events.next_before
    try {
      const page = await api<EventPage>(`/events?generation=${generation}&before=${cursor}`)
      setEvents(previous => accepted.current?.state.generation === generation && previous.next_before === cursor
        ? { items: mergeRows(previous.items, page.items, row => row.seq), next_before: page.next_before } : previous)
    }
    catch (reason) { setError(String(reason)) }
  }
  const loadMoreHistory = async () => {
    if (!history.next_before) return
    const cursor = history.next_before
    try {
      const page = await api<DecisionPage>(`/decisions?generation=${generation}&before=${encodeURIComponent(cursor)}`)
      const state = accepted.current?.state
      setHistory(previous => state && state.generation === generation && previous.next_before === cursor
        ? { items: mergeRows(previous.items, page.items, row => row.evaluation.id).map(row => markStale(row, state)), next_before: page.next_before } : previous)
    }
    catch (reason) { setError(String(reason)) }
  }
  const loadMoreAudit = async () => {
    if (!audit.next_before) return
    const cursor = audit.next_before
    try {
      const page = await api<AuditPage>(`/audit?before=${cursor}`)
      setAudit(previous => previous.next_before === cursor
        ? { items: mergeRows(previous.items, page.items, row => row.seq), next_before: page.next_before } : previous)
    }
    catch (reason) { setError(String(reason)) }
  }
  return { overview, events, history, audit, error, notice, busy, connection, lastUpdated, refresh, mutate, evaluate,
    loadMoreEvents, loadMoreHistory, loadMoreAudit, setError, setNotice, postCurrent }
}
