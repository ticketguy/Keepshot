import { useState } from 'react'
import { Bookmark, Copy, Check, GripHorizontal } from 'lucide-react'
import { useAuthStore } from '../store/auth'

// Minified bookmarklet — API_URL is injected at build time via the env var,
// falling back to the same origin so it works in any deployment.
const API_URL = import.meta.env.VITE_API_URL ?? ''

const BOOKMARKLET_CODE =
  `javascript:(function(){` +
  `var A="${API_URL}/api/v1";` +
  `var t=localStorage.getItem("keepshot_token");` +
  `if(!t){t=prompt("Paste your Keepshot API token:");if(!t)return;localStorage.setItem("keepshot_token",t)}` +
  `fetch(A+"/bookmarks",{method:"POST",headers:{"Content-Type":"application/json","Authorization":"Bearer "+t},` +
  `body:JSON.stringify({content_type:"url",url:location.href,title:document.title,monitoring_enabled:false})})` +
  `.then(function(r){` +
  `if(r.status===401){localStorage.removeItem("keepshot_token");alert("Token expired — click the bookmarklet again.");return}` +
  `if(!r.ok)return r.json().then(function(e){throw new Error(e.detail||r.status)});` +
  `alert("Saved to Keepshot!")` +
  `}).catch(function(e){alert("Keepshot error: "+e.message)})` +
  `})();`

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium text-zinc-400 hover:text-zinc-100 hover:bg-zinc-700 transition-colors"
    >
      {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function Step({ n, title, children }) {
  return (
    <div className="flex gap-4">
      <div className="flex-shrink-0 flex h-7 w-7 items-center justify-center rounded-full bg-indigo-500/20 text-indigo-400 text-xs font-bold">
        {n}
      </div>
      <div className="pt-0.5">
        <p className="text-sm font-medium text-zinc-100">{title}</p>
        <div className="mt-1 text-sm text-zinc-400">{children}</div>
      </div>
    </div>
  )
}

export default function Bookmarklet() {
  const token = useAuthStore((s) => s.token)

  return (
    <div className="mx-auto max-w-2xl px-6 py-10 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-zinc-100">Get the Bookmarklet</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Save any page to Keepshot with one click — no extension required.
        </p>
      </div>

      {/* Drag target */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-center space-y-3">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Drag to your bookmarks toolbar
        </p>
        {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
        <a
          href={BOOKMARKLET_CODE}
          onClick={(e) => e.preventDefault()}
          draggable="true"
          className="inline-flex items-center gap-2 rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-5 py-3 text-sm font-semibold text-indigo-300 hover:bg-indigo-500/20 transition-colors cursor-grab active:cursor-grabbing select-none"
        >
          <GripHorizontal size={15} className="text-indigo-400" />
          <Bookmark size={15} />
          Save to Keepshot
        </a>
        <p className="text-xs text-zinc-600">
          Click is intentionally disabled — drag the button above to your toolbar.
        </p>
      </div>

      {/* Steps */}
      <div className="space-y-5">
        <Step n="1" title="Show your bookmarks toolbar">
          In Chrome: <kbd className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs font-mono text-zinc-300">Ctrl+Shift+B</kbd>
          {' '}/ Mac <kbd className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs font-mono text-zinc-300">⌘+Shift+B</kbd>.
          In Firefox: <kbd className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs font-mono text-zinc-300">View → Toolbars → Bookmarks</kbd>.
        </Step>

        <Step n="2" title="Drag the button to the toolbar">
          Grab the <span className="text-indigo-300 font-medium">Save to Keepshot</span> button above
          and drop it onto your bookmarks toolbar. It will appear as a bookmark named "Save to Keepshot".
        </Step>

        <Step n="3" title="Use your API token">
          The first time you click the bookmarklet, it will ask for your API token.
          Copy it from below and paste it in:
          <div className="mt-2 flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 font-mono text-xs text-zinc-300 break-all">
            <span className="flex-1 truncate">{token ?? '— log in to see your token —'}</span>
            {token && <CopyButton text={token} />}
          </div>
          <p className="mt-1 text-xs text-zinc-600">
            The token is stored in the browser you used and not sent anywhere except Keepshot.
            If it expires, click the bookmarklet again to re-enter it.
          </p>
        </Step>

        <Step n="4" title="Save any page">
          Navigate to any page and click <span className="text-indigo-300 font-medium">Save to Keepshot</span> in your toolbar.
          You'll see a confirmation and the bookmark appears instantly in your{' '}
          <a href="/bookmarks" className="text-indigo-400 underline underline-offset-2 hover:text-indigo-300">Bookmarks</a>.
        </Step>
      </div>

      {/* Raw code for power users */}
      <details className="group rounded-xl border border-zinc-800 bg-zinc-900">
        <summary className="flex cursor-pointer items-center justify-between px-4 py-3 text-sm text-zinc-400 hover:text-zinc-100 transition-colors list-none">
          <span>Raw bookmarklet code</span>
          <span className="text-xs text-zinc-600 group-open:hidden">Show</span>
          <span className="text-xs text-zinc-600 hidden group-open:block">Hide</span>
        </summary>
        <div className="border-t border-zinc-800 px-4 py-3">
          <div className="flex items-start justify-between gap-3">
            <pre className="flex-1 overflow-x-auto whitespace-pre-wrap break-all text-xs text-zinc-400 font-mono leading-relaxed">
              {BOOKMARKLET_CODE}
            </pre>
            <CopyButton text={BOOKMARKLET_CODE} />
          </div>
          <p className="mt-2 text-xs text-zinc-600">
            Copy this, create a new bookmark manually, and paste it as the URL.
          </p>
        </div>
      </details>
    </div>
  )
}
