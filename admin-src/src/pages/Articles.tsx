import { useEffect, useState, useRef, type FormEvent } from "react";
import RichEditor from "../components/RichEditor";
import { get, post, put, del, uploadImage, getSiteId } from "../lib/api";

interface Article {
  id: number;
  title: string;
  slug: string;
  summary: string | null;
  content: string | null;
  image_url: string | null;
  category: string | null;
  tags: string | null;
  published: boolean;
  sort_order: number;
  banner_link: string | null;
  banner_label: string | null;
}

const empty = (): Omit<Article, "id"> => ({
  title: "",
  slug: "",
  summary: "",
  content: "",
  image_url: "",
  category: "",
  tags: "",
  published: true,
  sort_order: 0,
  banner_link: "",
  banner_label: "",
});

function slugify(s: string) {
  return s.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
}

export default function Articles() {
  const [items, setItems] = useState<Article[]>([]);
  const [form, setForm] = useState(empty());
  const [editing, setEditing] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => get<Article[]>("/articles").then(setItems).catch(() => {});
  useEffect(() => { load(); }, []);

  const setField = (field: keyof typeof form, value: unknown) =>
    setForm((f) => ({ ...f, [field]: value }));

  const handleEdit = (item: Article) => {
    setEditing(item.id);
    setForm({
      title: item.title,
      slug: item.slug,
      summary: item.summary || "",
      content: item.content || "",
      image_url: item.image_url || "",
      category: item.category || "",
      tags: item.tags || "",
      published: item.published,
      sort_order: item.sort_order,
      banner_link: item.banner_link || "",
      banner_label: item.banner_label || "",
    });
    setError(""); setSuccess("");
  };

  const handleCancel = () => { setEditing(null); setForm(empty()); setError(""); setSuccess(""); };

  const handleDelete = async (id: number) => {
    if (!confirm("Supprimer cet article ?")) return;
    await del(`/articles/${id}`);
    load();
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    try { const url = await uploadImage(file); setField("image_url", url); }
    catch { setError("Erreur upload image"); }
    finally { setUploading(false); }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(""); setSuccess("");
    try {
      if (editing) {
        await put(`/articles/${editing}`, form);
        setSuccess("Article modifié.");
      } else {
        await post("/articles", { ...form, site_id: Number(getSiteId()) });
        setSuccess("Article créé.");
      }
      handleCancel(); load();
    } catch (err) { setError(String(err)); }
  };

  const q = search.toLowerCase();
  const filtered = items.filter((item) =>
    item.title.toLowerCase().includes(q) ||
    (item.category || "").toLowerCase().includes(q) ||
    (item.tags || "").toLowerCase().includes(q)
  );

  return (
    <>
      <div className="page-header">
        <h1>Articles</h1>
        {editing === null && (
          <button className="btn btn-primary" onClick={() => { setEditing(0); setForm(empty()); }}>
            + Nouvel article
          </button>
        )}
      </div>

      {editing !== null && (
        <div className="form-panel">
          <h2>{editing ? "Modifier l'article" : "Nouvel article"}</h2>
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
                <input
                  value={form.slug}
                  onChange={(e) => setField("slug", e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Categorie</label>
                <input
                  value={form.category || ""}
                  onChange={(e) => setField("category", e.target.value)}
                  placeholder="Tech,News"
                />
              </div>
              <div className="form-group">
                <label>Tags</label>
                <input
                  value={form.tags || ""}
                  onChange={(e) => setField("tags", e.target.value)}
                  placeholder="react,typescript"
                />
              </div>
              <div className="form-group full">
                <label>Resume</label>
                <textarea
                  value={form.summary || ""}
                  onChange={(e) => setField("summary", e.target.value)}
                  rows={3}
                />
              </div>
              <div className="form-group full">
                <label>Image</label>
                <div className="input-upload">
                  <input value={form.image_url || ""} onChange={(e) => setField("image_url", e.target.value)} placeholder="https://... ou importer ci-contre" />
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
              <div className="form-group full">
                <label>Contenu</label>
                <RichEditor
                  key={editing ?? 'new'}
                  value={form.content || ""}
                  onChange={(v) => setField("content", v)}
                />
              </div>
              <div className="form-group full">
                <label>Bannière — Lien (optionnel)</label>
                <input
                  value={form.banner_link || ""}
                  onChange={(e) => setField("banner_link", e.target.value)}
                  placeholder="https://..."
                />
              </div>
              <div className="form-group full">
                <label>Bannière — Texte (optionnel)</label>
                <input
                  value={form.banner_label || ""}
                  onChange={(e) => setField("banner_label", e.target.value)}
                  placeholder="Voir la procédure complète"
                />
              </div>
              <div className="form-group">
                <label>Ordre</label>
                <input
                  type="number"
                  value={form.sort_order}
                  onChange={(e) => setField("sort_order", Number(e.target.value))}
                />
              </div>
              <div className="form-group">
                <label>&nbsp;</label>
                <div className="form-check">
                  <input
                    type="checkbox"
                    id="art-pub"
                    checked={form.published}
                    onChange={(e) => setField("published", e.target.checked)}
                  />
                  <label htmlFor="art-pub">Publie</label>
                </div>
              </div>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary">{editing ? "Enregistrer" : "Creer"}</button>
              <button type="button" className="btn btn-secondary" onClick={handleCancel}>Annuler</button>
            </div>
          </form>
        </div>
      )}

      <div style={{ marginBottom: "1rem", display: "flex", alignItems: "center", gap: "1rem" }}>
        <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Rechercher par titre, catégorie, tags..." style={{ width: "300px" }} />
        {search && <span style={{ fontSize: "0.82rem", color: "var(--mid)" }}>{filtered.length} résultat{filtered.length !== 1 ? "s" : ""}</span>}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Image</th>
              <th>Titre</th>
              <th>Slug</th>
              <th>Categorie</th>
              <th>Ordre</th>
              <th>Publie</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", color: "var(--mid)", padding: "2rem" }}>
                  {search ? `Aucun résultat pour "${search}"` : "Aucun article"}
                </td>
              </tr>
            )}
            {filtered.map((item) => (
              <tr key={item.id}>
                <td>
                  {item.image_url
                    ? <img src={item.image_url} alt={item.title} className="thumb" />
                    : "—"}
                </td>
                <td className="truncate">{item.title}</td>
                <td className="truncate">{item.slug}</td>
                <td className="truncate">{item.category || "—"}</td>
                <td>{item.sort_order}</td>
                <td>
                  <span className={`badge ${item.published ? "badge-on" : "badge-off"}`}>
                    {item.published ? "Oui" : "Non"}
                  </span>
                </td>
                <td>
                  <div className="td-actions">
                    <button className="btn btn-secondary btn-sm" onClick={() => handleEdit(item)}>Modifier</button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(item.id)}>Supprimer</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
