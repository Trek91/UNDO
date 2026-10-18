// Forwards /api/* to the FastAPI backend on Render (Netlify cannot run Python servers).
// A plain proxy rewrite is not enough: browsers send `Origin: <netlify site>` on POST, which the
// backend's CSRF boundary rejects (403 origin_denied), and rewrites buffer the SSE stream.
// This proxy enforces the same-origin rule itself, then presents the backend's own origin upstream,
// and streams responses unchanged. No financial logic runs here.
const DEFAULT_BACKEND = 'https://undo-4ul2.onrender.com'
const HOP_BY_HOP = ['connection', 'keep-alive', 'transfer-encoding', 'upgrade', 'host', 'content-length']

export default async (request: Request) => {
  const backend = new URL(Netlify.env.get('UNDO_BACKEND_URL') || DEFAULT_BACKEND)
  const incoming = new URL(request.url)
  const writes = !['GET', 'HEAD', 'OPTIONS'].includes(request.method)
  const origin = request.headers.get('origin')
  if (writes && origin && origin !== incoming.origin) {
    return Response.json({ error: { code: 'origin_denied', message: 'Origin is not allowed.' } }, { status: 403 })
  }
  const headers = new Headers(request.headers)
  for (const name of HOP_BY_HOP) headers.delete(name)
  headers.delete('origin')
  headers.delete('referer')
  if (writes) headers.set('origin', backend.origin)
  const target = new URL(incoming.pathname + incoming.search, backend)
  try {
    const upstream = await fetch(target, { method: request.method, headers, redirect: 'manual',
      body: writes ? await request.arrayBuffer() : undefined })
    const responseHeaders = new Headers(upstream.headers)
    for (const name of HOP_BY_HOP) responseHeaders.delete(name)
    return new Response(upstream.body, { status: upstream.status, statusText: upstream.statusText, headers: responseHeaders })
  } catch {
    return Response.json({ error: { code: 'backend_unreachable', message: 'The backend could not be reached. It may be waking up; retry shortly.' } }, { status: 502 })
  }
}

export const config = { path: '/api/*' }
