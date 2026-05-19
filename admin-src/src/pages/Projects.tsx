import { useEffect, useState, useRef, type FormEvent } from "react";
import MDEditor from "@uiw/react-md-editor";
import { get, post, put, del, uploadImage, getSiteId } from "../lib/api";

interface Project {
  id: number;
  title: string;
  slug: string;
  description: string | null;
  content: string | null;
  image_url: string | null;
  technologies: string | null;
  github_url: string | null;
  live_url: string | null;
  published: boolean;
  featured: boolean;
  sort_order: number;
  banner_link: string | null;
  banner_label: string | null;
}

const empty = (): Omit<Project, "id"> => ({
  title: "", slug: "", description: "", content: "",
  image_url: "", technologies: "", github_url: "", live_url: "",
  published: true, featured: false, sort_order: 0,
  banner_link: "", banner_label: "",
});

function slugify(s: string) {
  return s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
}

export default function Projects() {
  const [items, setItems] = useState<Project[]>([]);
  const [form, setForm] = useState(empty());
  const [editing, setEditing] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const mdFileRef = useRef<HTMLInputElement>(null);
  const contentImgRef = useRef<HTMLInputElement>(null);
  const editorWrapRef = useRef<HTMLDivElement>(null);

  const load = () => get<Project[]>("/portfolio/projects").then(setItems).catch(() => {});
  useEffect(() => { load(); }, []);

  const setField = (field: keyof typeof form, value: unknown) =>
    setForm((f) => ({ ...f, [field]: value }));

  const handleEdit = (item: Project) => {
    setEditing(item.id);
    setForm({
      title: item.title, slug: item.slug,
      description: item.description || "", content: item.content || "",
      image_url: item.image_url || "", technologies: item.technologies || "",
      github_url: item.github_url || "", live_url: item.live_url || "",
      published: item.published, featured: item.featured, sort_order: item.sort_order,
      banner_link: item.banner_link || "", banner_label: item.banner_label || "",
    });
    setError(""); setSuccess("");
  };

  const handleCancel = () => { setEditing(null); setForm(empty()); setError(""); setSuccess(""); };

  const handleDelete = async (id: number) => {
    if (!confirm("Supprimer ce projet ?")) return;
    await del(`/portfolio/projects/${id}`);
    load();
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    try { const url = await uploadImage(file); setField("image_url", url); }
    catch { setError("Erreur upload image"); }
    finally { setUploading(false); }
  };

  const handleContentImageUpload = async (file: File) => {
    setUploading(true);
    try {
      const url = await uploadImage(file);
      const snippet = `![](${url})`;
      const textarea = editorWrapRef.current?.querySelector("textarea") ?? null;
      const current = form.content || "";
      if (textarea) {
        const start = textarea.selectionStart ?? current.length;
        const end = textarea.selectionEnd ?? current.length;
        const newContent = current.slice(0, start) + snippet + current.slice(end);
        setField("content", newContent);
        requestAnimationFrame(() => {
          textarea.selectionStart = textarea.selectionEnd = start + snippet.length;
          textarea.focus();
        });
      } else {
        setField("content", current + "\n" + snippet);
      }
    } catch { setError("Erreur upload image"); }
    finally { setUploading(false); }
  };

  const handleMdImport = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => setField("content", e.target?.result as string);
    reader.readAsText(file);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(""); setSuccess("");
    try {
      if (editing) { await put(`/portfolio/projects/${editing}`, form); setSuccess("Projet modifié."); }
      else { await post("/portfolio/projects", { ...form, site_id: Number(getSiteId()) }); setSuccess("Projet créé."); }
      handleCancel(); load();
    } catch (err) { setError(String(err)); }
  };

  const q = search.toLowerCase();
  const filtered = items.filter((item) =>
    item.title.toLowerCase().includes(q) ||
    (item.technologies || "").toLowerCase().includes(q)
  );

  return (
    <>
      <div className="page-header">
        <h1>Projets</h1>
        {editing === null && (
          <button className="btn btn-primary" onClick={() => { setEditing(0); setForm(empty()); }}>
            + Nouveau projet
          </button>
        )}
      </div>

      {editing !== null && (
        <div className="form-panel">
          <h2>{editing ? "Modifier le projet" : "Nouveau projet"}</h2>
          {error && <div className="msg msg-error">{error}</div>}
          {success && <div className="msg msg-success">{success}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label>Titre *</label>
                <input
                  value={form.title}
                  onChange={(e) => {
                    setField("title", e.target.value);
                    if (!editing) setField("slug", slugify(e.target.value));
                  }}
                  required
                />
              </div>
              <div className="form-group">
                <label>Slug *</label>
                <input value={form.slug} onChange={(e) => setField("slug", e.target.value)} required />
              </div>

              <div className="form-group full">
                <label>Description courte</label>
                <textarea
                  value={form.description || ""}
                  onChange={(e) => setField("description", e.target.value)}
                  rows={2}
                />
              </div>

              {/* Image upload */}
              <div className="form-group full">
                <label>Image</label>
                <div className="input-upload">
                  <input
                    value={form.image_url || ""}
                    onChange={(e) => setField("image_url", e.target.value)}
                    placeholder="https://... ou importer ci-contre"
                  />
                  <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }}
                    onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])} />
                  <button type="button" className="btn btn-secondary btn-sm"
                    onClick={() => fileRef.current?.click()} disabled={uploading}>
                    {uploading ? "Envoi..." : "📎 Importer"}
                  </button>
                </div>
                {form.image_url && (
                  <img src={form.image_url} alt="preview" style={{ marginTop: "0.5rem", maxHeight: "120px", border: "var(--border-thin)" }} />
                )}
              </div>

              {/* Markdown editor */}
              <div className="form-group full">
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.4rem" }}>
                  <label style={{ margin: 0 }}>Contenu (Markdown)</label>
                  <div style={{ display: "flex", gap: "0.4rem" }}>
                    <input ref={mdFileRef} type="file" accept=".md,.txt" style={{ display: "none" }}
                      onChange={(e) => e.target.files?.[0] && handleMdImport(e.target.files[0])} />
                    <button type="button" className="btn btn-secondary btn-sm"
                      onClick={() => mdFileRef.current?.click()}>
                      📄 Importer .md
                    </button>
                    <input ref={contentImgRef} type="file" accept="image/*" style={{ display: "none" }}
                      onChange={(e) => { if (e.target.files?.[0]) { handleContentImageUpload(e.target.files[0]); e.target.value = ""; } }} />
                    <button type="button" className="btn btn-secondary btn-sm"
                      onClick={() => contentImgRef.current?.click()} disabled={uploading}>
                      {uploading ? "Envoi..." : "🖼 Insérer image"}
                    </button>
                    <button type="button" className="btn btn-secondary btn-sm"
                      onClick={() => setField("content", "")}>
                      Vider
                    </button>
                  </div>
                </div>
                <div data-color-mode="light" ref={editorWrapRef}>
                  <MDEditor
                    value={form.content || ""}
                    onChange={(v) => setField("content", v || "")}
                    height={320}
                    preview="live"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Technologies</label>
                <input value={form.technologies || ""} onChange={(e) => setField("technologies", e.target.value)} placeholder="React, Python, Docker" />
              </div>
              <div className="form-group">
                <label>Ordre</label>
                <input type="number" value={form.sort_order} onChange={(e) => setField("sort_order", Number(e.target.value))} />
              </div>
              <div className="form-group">
                <label>GitHub URL</label>
                <input value={form.github_url || ""} onChange={(e) => setField("github_url", e.target.value)} placeholder="https://github.com/..." />
              </div>
              <div className="form-group">
                <label>Live URL</label>
                <input value={form.live_url || ""} onChange={(e) => setField("live_url", e.target.value)} placeholder="https://..." />
              </div>
              <div className="form-group full">
                <label>Bannière — Lien (optionnel)</label>
                <input value={form.banner_link || ""} onChange={(e) => setField("banner_link", e.target.value)} placeholder="https://..." />
              </div>
              <div className="form-group full">
                <label>Bannière — Texte (optionnel)</label>
                <input value={form.banner_label || ""} onChange={(e) => setField("banner_label", e.target.value)} placeholder="Voir la démo" />
              </div>
              <div className="form-group">
                <div className="form-check">
                  <input type="checkbox" id="proj-pub" checked={form.published} onChange={(e) => setField("published", e.target.checked)} />
                  <label htmlFor="proj-pub">Publié</label>
                </div>
              </div>
              <div className="form-group">
                <div className="form-check">
                  <input type="checkbox" id="proj-feat" checked={form.featured} onChange={(e) => setField("featured", e.target.checked)} />
                  <label htmlFor="proj-feat">En vedette</label>
                </div>
              </div>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary">{editing ? "Enregistrer" : "Créer"}</button>
              <button type="button" className="btn btn-secondary" onClick={handleCancel}>Annuler</button>
            </div>
          </form>
        </div>
      )}

      <div style={{ marginBottom: "1rem", display: "flex", alignItems: "center", gap: "1rem" }}>
        <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Rechercher par titre, technologie..." style={{ width: "300px" }} />
        {search && <span style={{ fontSize: "0.82rem", color: "var(--mid)" }}>{filtered.length} résultat{filtered.length !== 1 ? "s" : ""}</span>}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Image</th><th>Titre</th><th>Technologies</th><th>Vedette</th><th>Publié</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr><td colSpan={6} style={{ textAlign: "center", color: "var(--mid)", padding: "2rem" }}>{search ? `Aucun résultat pour "${search}"` : "Aucun projet"}</td></tr>
            )}
            {filtered.map((item) => (
              <tr key={item.id}>
                <td>{item.image_url ? <img src={item.image_url} alt={item.title} className="thumb" /> : "—"}</td>
                <td className="truncate">{item.title}</td>
                <td className="truncate">{item.technologies || "—"}</td>
                <td><span className={`badge ${item.featured ? "badge-on" : "badge-off"}`}>{item.featured ? "Oui" : "Non"}</span></td>
                <td><span className={`badge ${item.published ? "badge-on" : "badge-off"}`}>{item.published ? "Oui" : "Non"}</span></td>
                <td><div className="td-actions">
                  <button className="btn btn-secondary btn-sm" onClick={() => handleEdit(item)}>Modifier</button>
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(item.id)}>Supprimer</button>
                </div></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
