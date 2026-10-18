import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { useWorkspace } from '../src/hooks/useWorkspace'
import { api, post } from '../src/lib/api'
import type { Overview } from '../src/lib/api'
import fixture from './fixture.json'

vi.mock('../src/lib/api', () => ({ api: vi.fn(), post: vi.fn() }))
const overview = (generation: number, version: number, cursor: number): Overview => ({
  state: { ...fixture.snapshot, generation, version } as Overview['state'],
  outstanding_obligations_paise: 11000000, outstanding_receivables_paise: 4000000,
  latest_decision: null, recalculating: false, worker_error: null, notification_cursor: cursor,
  near_term_mandatory_paise: 5000000, near_term_horizon_days: 7,
})
beforeEach(() => {
  vi.stubGlobal('EventSource', class { addEventListener() {} close() {} })
  vi.mocked(api).mockImplementation(async path => path === '/overview' ? overview(1, 2, 5) : { items: [], next_before: null })
})
afterEach(() => { vi.unstubAllGlobals(); vi.clearAllMocks() })

test('refresh scopes financial history to its overview generation', async () => {
  const { result } = renderHook(useWorkspace)
  await waitFor(() => expect(result.current.overview?.state.version).toBe(2))
  expect(api).toHaveBeenCalledWith('/events?generation=1')
  expect(api).toHaveBeenCalledWith('/decisions?generation=1')
})

test('a response from older financial state cannot overwrite a newer state', async () => {
  const { result } = renderHook(useWorkspace)
  await waitFor(() => expect(result.current.overview?.state.version).toBe(2))
  vi.mocked(api).mockImplementation(async path => path === '/overview' ? overview(1, 1, 4) : { items: [], next_before: null })
  await act(async () => { await result.current.refresh() })
  expect(result.current.overview?.state.version).toBe(2)
})

test('evaluation carries the version and generation rendered to the user', async () => {
  const { result } = renderHook(useWorkspace)
  await waitFor(() => expect(result.current.overview?.state.version).toBe(2))
  await act(async () => { await result.current.evaluate({ paths: 100 }) })
  expect(post).toHaveBeenCalledWith('/decisions/evaluate?expected_generation=1&expected_version=2', { paths: 100 })
})

test('live refresh retains previously loaded immutable event pages', async () => {
  const item = (seq: number) => ({ seq, event: { type: 'PAYMENT_CONFIRMED', event_id: `event-${seq}`, business_id: 'demo', timestamp: '2026-10-17T08:00:00Z', currency: 'INR', obligation_id: 'supplier', amount_paise: 1 } })
  vi.mocked(api).mockImplementation(async path => {
    if (path === '/overview') return overview(1, 2, 5)
    if (path.includes('/events?')) return path.includes('before=') ? { items: [item(1)], next_before: null } : { items: [item(2)], next_before: 2 }
    return { items: [], next_before: null }
  })
  const { result } = renderHook(useWorkspace)
  await waitFor(() => expect(result.current.events.items).toHaveLength(1))
  await act(async () => { await result.current.loadMoreEvents() })
  expect(result.current.events.items.map(row => row.seq)).toEqual([2, 1])
  await act(async () => { await result.current.refresh() })
  expect(result.current.events.items.map(row => row.seq)).toEqual([2, 1])
  expect(result.current.events.next_before).toBeNull()
})

test('a refresh after a disconnected burst keeps a cursor that can recover missing records', async () => {
  let seq = 2
  vi.mocked(api).mockImplementation(async path => {
    if (path === '/overview') return overview(1, 2, 5)
    if (path.includes('/events?')) return { items: [{ seq, event: { type: 'PAYMENT_CONFIRMED', event_id: `event-${seq}`, business_id: 'demo', timestamp: '2026-10-17T08:00:00Z', currency: 'INR', obligation_id: 'supplier', amount_paise: 1 } }], next_before: seq }
    return { items: [], next_before: null }
  })
  const { result } = renderHook(useWorkspace)
  await waitFor(() => expect(result.current.events.items[0]?.seq).toBe(2))
  seq = 4
  await act(async () => { await result.current.refresh() })
  expect(result.current.events.items.map(row => row.seq)).toEqual([4])
  expect(result.current.events.next_before).toBe(4)
})
