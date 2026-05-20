// Centralised share captions. Khalid's contact placeholders will be replaced
// by the real Gmail + LinkedIn URL once he provides them. These are intentionally
// distinctive strings so a single grep finds them.

export const AUTHOR = {
  name: "Khalid Hussain",
  email: "sindhikhalid126@gmail.com",
  linkedin: "https://www.linkedin.com/in/khalid-hussain-55714727a/",
  twitter: "https://x.com/KhalidUnar27322",
  github: "https://github.com/Khalid147-alt",
}

const APP_NAME = "Multi-Agent Research Pipeline"
const APP_PITCH =
  "4 AI agents (Researcher, Analyst, Fact-Checker, Writer) collaborate to produce a cited report with confidence scores."

function attribution() {
  const parts = [
    `Built by ${AUTHOR.name}`,
    AUTHOR.linkedin && `LinkedIn: ${AUTHOR.linkedin}`,
    AUTHOR.email && `Email: ${AUTHOR.email}`,
  ].filter(Boolean)
  return parts.join(" · ")
}

export function buildCaption({ topic, url, platform }) {
  const headline = `Just generated a research report on "${topic}" with ${APP_NAME}.`
  const body = APP_PITCH
  const cta = `Try it: ${url}`
  const author = attribution()

  // Per-platform tweaks
  switch (platform) {
    case "twitter":
      // 280-char target. Trim ruthlessly.
      return `${headline} ${cta}\n\n${body}`.slice(0, 270)
    case "linkedin":
      return [
        headline,
        "",
        body,
        "",
        cta,
        "",
        author,
        "",
        "#AI #Agents #LLM #CrewAI #FastAPI #Portfolio",
      ].join("\n")
    case "facebook":
      return [headline, "", body, cta, "", author].join("\n")
    case "whatsapp":
      return `${headline}\n\n${body}\n\n${cta}\n${author}`
    case "email":
      return [
        body,
        "",
        cta,
        "",
        author,
        "",
        "—",
        `Source: ${APP_NAME}`,
      ].join("\n")
    default:
      return `${headline}\n\n${body}\n\n${cta}\n\n${author}`
  }
}

export function emailSubject(topic) {
  return `Research report: ${topic}`
}
