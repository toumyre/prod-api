import { useEffect, useState, useRef, type FormEvent } from "react";
import { get, post, put, del, uploadImage, getSiteId } from "../lib/api";

interface GalleryItem {
  id: number;
  type: string;
  category: string | null;
  title: string | null;
  description: string | null;
  image_url: string | null;
  video_url: string | null;
  tags: string | null;
  published: boolean;
  sort_order: number;
}

const empty = (): Omit<GalleryItem, "id"> => ({
  type: "photo",
  category: "",
  title: "",
  description: "",
  image_url: "",
  video_url: "",
  tags: "",
  published: true,
  sort_order: 0,
});

export default function Gallery() {
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [form, setForm] = useState(empty());
  const [editing, setEditing] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => get<GalleryItem[]>("/gallery").then(setItems).catch(() => {});
  useEffect(() => { load(); }, []);

  const setField = (field: keyof typeof form, value: unknown) =>
    setForm((f) => ({ ...f, [field]: value }));

  const handleEdit = (item: GalleryItem) => {
    setEditing(item.id);
    setForm({
      type: item.type,
      category: item.category || "",
      title: item.title || "",
      description: item.description || "",
      image_url: item.image_url || "",
      video_url: item.video_url || "",
      tags: item.tags || "",
      published: item.published,
      sort_order: item.sort_order,
    });
    setError(""); setSuccess("");
  };

  const handleCancel = () => { setEditing(null); setForm(empty()); setError(""); setSuccess(""); };

  const handleDelete = async (id: number) => {
    if (!confirm("Supprimer cet element de galerie ?")) return;
    await del(`/gallery/${id}`);
    load();
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    try { const url = await uploadImage(file); setField("image_url", url); }
    catch { setError("Erreur upload"); }
    finally { setUploading(false); }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(""); setSuccess("");
    try {
      if (editing) {
        await put(`/gallery/${editing}`, form);
        setSuccess("Element modifie.");
      } else {
        await post("/gallery", { ...form, site_id: Number(getSiteId()) });
        setSuccess("Element cree.");
      }
      handleCancel(); load();
    } catch (err) { setError(String(err)); }
  };

  const q = search.toLowerCase();
  const filtered = items.filter((item) =>
    (item.title || "").toLowerCase().includes(q) ||
    (item.category || "").toLowerCase().includes(q) ||
    (item.tags || "").toLowerCase().includes(q)
  );

  return (
    <>
      <div className="page-header">
        <h1>Galerie</h1>
        {editing === null && (
          <button className="btn btn-primary" onClick={() => { setEditing(0); setForm(empty()); }}>
            + Nouvel element
          </button>
        )}
      </div>

      {editing !== null && (
        <div className="form-panel">
          <h2>{editing ? "Modifier l'element" : "Nouvel element"}</h2>
          {error && <div className="msg msg-error">{error}</div>}
          {success && <div className="msg msg-success">{success}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label>Type *</label>
                <select value={form.type} onChange={(e) => setField("type", e.target.value)}>
                  <option value="photo">Photo</option>
                  <option value="video">Video</option>
                </select>
              </div>
              <div className="form-group">
                <label>Categorie</label>
                <input
                  value={form.category || ""}
                  onChange={(e) => setField("category", e.target.value)}
                  placeholder="Evenement,Portrait"
                />
              </div>
              <div className="form-group full">
                <label>Titre</label>
                <input
                  value={form.title || ""}
                  onChange={(e) => setField("title", e.target.value)}
                />
              </div>
              <div className="form-group full">
                <label>Description</label>
                <textarea
                  value={form.description || ""}
                  onChange={(e) => setField("description", e.target.value)}
                  rows={3}
                />
              </div>
              <div className="form-group full">
                <label>Image URL</label>
                <div className="input-upload">
                  <input
                    value={form.image_url || ""}
                    onChange={(e) => setField("image_url", e.target.value)}
                    placeholder="https://..."
                  />
                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/*"
                    style={{ display: "none" }}
                    onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
                  />
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => fileRef.current?.click()}
                    disabled={uploading}
                  >
                    {uploading ? "..." : "Importer"}
                  </button>
                </div>
                {form.image_url && (
                  <img src={form.image_url} alt="preview" className="thumb" style={{ marginTop: "0.4rem" }} />
                )}
              </div>
              {form.type === "video" && (
                <div className="form-group full">
                  <label>Video URL</label>
                  <input
                    value={form.video_url || ""}
                    onChange={(e) => setField("video_url", e.target.value)}
                    placeholder="https://youtube.com/..."
                  />
                </div>
              )}
              <div className="form-group">
                <label>Tags</label>
                <input
                  value={form.tags || ""}
                  onChange={(e) => setField("tags", e.target.value)}
                  placeholder="sport,event"
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
                    id="gal-pub"
                    checked={form.published}
                    onChange={(e) => setField("published", e.target.checked)}
                  />
                  <label htmlFor="gal-pub">Publie</label>
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
              <th>Type</th>
              <th>Titre</th>
              <th>Categorie</th>
              <th>Tags</th>
              <th>Ordre</th>
              <th>Publie</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} style={{ textAlign: "center", color: "var(--mid)", padding: "2rem" }}>
                  {search ? `Aucun résultat pour "${search}"` : "Aucun element"}
                </td>
              </tr>
            )}
            {filtered.map((item) => (
              <tr key={item.id}>
                <td>
                  {item.image_url
                    ? <img src={item.image_url} alt={item.title || "gallery"} className="thumb" />
                    : "—"}
                </td>
                <td>
                  <span className="badge badge-off" style={{ background: "#e0f2fe", color: "#0369a1" }}>
                    {item.type}
                  </span>
                </td>
                <td className="truncate">{item.title || "—"}</td>
                <td className="truncate">{item.category || "—"}</td>
                <td className="truncate">{item.tags || "—"}</td>
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
