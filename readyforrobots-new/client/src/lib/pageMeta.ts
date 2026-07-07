/**
 * Set document title + Open Graph / Twitter meta for shareable pages.
 * LinkedIn reads og:* tags when /preview is pasted into a post.
 */
import { useEffect } from "react";

type PageMetaInput = {
  title: string;
  description: string;
  path?: string;
  image?: string;
  imageAlt?: string;
  /** LinkedIn company page numeric ID → urn:li:organization:{id} */
  linkedInOrgId?: string;
};

const SITE =
  typeof import.meta !== "undefined" && import.meta.env?.VITE_SITE_URL
    ? String(import.meta.env.VITE_SITE_URL).replace(/\/$/, "")
    : "https://readyforrobots.com";

const DEFAULT_OG_IMAGE = `${SITE}/marketing/robot-industrial.jpg`;

function upsertMeta(attr: "name" | "property", key: string, content: string) {
  if (!content) return;
  const selector = `meta[${attr}="${key}"]`;
  let el = document.querySelector(selector) as HTMLMetaElement | null;
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
}

export function linkedInOrganizationUrn(orgId: string): string {
  return `urn:li:organization:${orgId}`;
}

export const LINKEDIN_ORG_ID =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_LINKEDIN_ORG_ID
    ? String(import.meta.env.VITE_LINKEDIN_ORG_ID)
    : "114404417") || "114404417";

export const LINKEDIN_ORG_URN = linkedInOrganizationUrn(LINKEDIN_ORG_ID);

export function linkedInShareUrl(opts: {
  url: string;
  title: string;
  summary: string;
}): string {
  const params = new URLSearchParams({
    mini: "true",
    url: opts.url,
    title: opts.title.slice(0, 200),
    summary: opts.summary.slice(0, 700),
    source: "readyforrobots.com",
  });
  return `https://www.linkedin.com/shareArticle?${params.toString()}`;
}

export function usePageMeta({
  title,
  description,
  path = "",
  image = DEFAULT_OG_IMAGE,
  imageAlt = "Ready For Robots — robot sales intelligence",
  linkedInOrgId = LINKEDIN_ORG_ID,
}: PageMetaInput) {
  useEffect(() => {
    const url = `${SITE}${path.startsWith("/") ? path : `/${path}`}`;
    document.title = title;

    upsertMeta("name", "description", description);
    upsertMeta("property", "og:type", "website");
    upsertMeta("property", "og:site_name", "Ready For Robots");
    upsertMeta("property", "og:title", title);
    upsertMeta("property", "og:description", description);
    upsertMeta("property", "og:url", url);
    upsertMeta("property", "og:image", image);
    upsertMeta("property", "og:image:alt", imageAlt);
    upsertMeta("name", "twitter:card", "summary_large_image");
    upsertMeta("name", "twitter:title", title);
    upsertMeta("name", "twitter:description", description);
    upsertMeta("name", "twitter:image", image);

    // LinkedIn org identity (Community Management API uses urn:li:organization:{id})
    upsertMeta("name", "linkedin:owner", linkedInOrganizationUrn(linkedInOrgId));

    return () => {
      document.title = "ReadyForRobots — SIGNAL";
    };
  }, [title, description, path, image, imageAlt, linkedInOrgId]);
}
