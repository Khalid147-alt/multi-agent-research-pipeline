import { useState } from "react"
import { buildCaption, emailSubject, AUTHOR } from "../lib/shareTemplates"

function shareUrl(platform, { topic, url }) {
  const caption = buildCaption({ topic, url, platform })
  const enc = encodeURIComponent
  switch (platform) {
    case "linkedin":
      // LinkedIn's share-offsite endpoint only takes a URL; the caption goes
      // through the user's compose box via the `sharing/share-offsite` page.
      // We pass both for the best preview.
      return `https://www.linkedin.com/sharing/share-offsite/?url=${enc(url)}`
    case "twitter":
      return `https://twitter.com/intent/tweet?text=${enc(caption)}`
    case "facebook":
      return `https://www.facebook.com/sharer/sharer.php?u=${enc(url)}&quote=${enc(
        caption,
      )}`
    case "whatsapp":
      return `https://api.whatsapp.com/send?text=${enc(caption)}`
    case "email":
      return `mailto:?subject=${enc(emailSubject(topic))}&body=${enc(caption)}`
    default:
      return url
  }
}

const PLATFORMS = [
  { key: "linkedin", label: "LinkedIn", color: "hover:bg-[#0a66c2]/20" },
  { key: "twitter", label: "X / Twitter", color: "hover:bg-white/10" },
  { key: "facebook", label: "Facebook", color: "hover:bg-[#1877f2]/20" },
  { key: "whatsapp", label: "WhatsApp", color: "hover:bg-[#25d366]/20" },
  { key: "email", label: "Email", color: "hover:bg-amber/20" },
]

export default function ShareBar({ topic, sessionId }) {
  const [copied, setCopied] = useState(false)
  const url =
    typeof window !== "undefined"
      ? `${window.location.origin}/report/${sessionId}`
      : `/report/${sessionId}`

  const openShare = (platform) => {
    const u = shareUrl(platform, { topic, url })
    if (platform === "email") {
      window.location.href = u
    } else {
      window.open(u, "_blank", "noopener,noreferrer,width=600,height=540")
    }
  }

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // navigator.clipboard can fail in non-secure contexts — fall back
      const ta = document.createElement("textarea")
      ta.value = url
      document.body.appendChild(ta)
      ta.select()
      try {
        document.execCommand("copy")
        setCopied(true)
        setTimeout(() => setCopied(false), 1500)
      } catch {}
      document.body.removeChild(ta)
    }
  }

  if (!sessionId) return null

  return (
    <div className="bg-panel border border-edge rounded-xl p-4">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="text-xs uppercase tracking-wider text-muted">
          Share this report
        </div>
        <button
          onClick={copyLink}
          className="text-xs px-2.5 py-1 rounded-md border border-edge hover:bg-edge/60 transition"
          title={url}
        >
          {copied ? "✓ Link copied" : "Copy link"}
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {PLATFORMS.map((p) => (
          <button
            key={p.key}
            onClick={() => openShare(p.key)}
            className={`text-sm border border-edge rounded-lg px-3 py-2 min-h-[44px] transition ${p.color}`}
          >
            {p.label}
          </button>
        ))}
      </div>
      <p className="text-[11px] text-muted mt-3 leading-relaxed">
        Captions include a link to the report and credit{" "}
        <a
          href={AUTHOR.linkedin}
          target="_blank"
          rel="noreferrer"
          className="text-accent hover:underline"
        >
          Khalid Hussain
        </a>{" "}
        ({AUTHOR.email}).
      </p>
    </div>
  )
}
