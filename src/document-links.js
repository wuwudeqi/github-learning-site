// Resolve against the published catalog, never by title or basename alone.
export function createDocumentLinkResolver(documents, assetURL) {
  const key = (url) => url.origin + decodeURIComponent(url.pathname);
  const index = new Map(
    documents.map((doc) => [key(new URL(assetURL(doc.file))), doc]),
  );
  return (href, sourceURL) => {
    try {
      const target = new URL(href, sourceURL);
      const doc = index.get(key(target));
      if (!doc || !["http:", "https:"].includes(target.protocol)) return null;
      const section =
        doc.type === "MD" && target.hash
          ? "?section=" +
            encodeURIComponent(decodeURIComponent(target.hash.slice(1)))
          : "";
      return "#/read/" + doc.id + section;
    } catch {
      return null;
    }
  };
}
