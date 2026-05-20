// Helper to build a consistent set of meta tags per route. Consumed via
// react-helmet-async <Helmet> in page components.

const SITE_NAME = "Multi-Agent Research Pipeline"
const DEFAULT_DESC =
  "4 AI agents collaborate live to research, analyze, fact-check, and write cited reports with confidence scores."

export function metaFor({
  title,
  description,
  url,
  type = "website",
  image,
} = {}) {
  const finalTitle = title ? `${title} · ${SITE_NAME}` : SITE_NAME
  const finalDesc = description || DEFAULT_DESC
  return {
    title: finalTitle,
    description: finalDesc,
    og: {
      title: finalTitle,
      description: finalDesc,
      type,
      url: url || (typeof window !== "undefined" ? window.location.href : ""),
      siteName: SITE_NAME,
      image: image || null,
    },
    twitter: {
      card: "summary_large_image",
      title: finalTitle,
      description: finalDesc,
      image: image || null,
    },
  }
}
