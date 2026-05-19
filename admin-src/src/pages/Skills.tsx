import { useEffect, useState, useRef, type FormEvent } from "react";
import MDEditor from "@uiw/react-md-editor";
import { get, post, put, del, uploadImage, getSiteId } from "../lib/api";

interface Skill {
  id: number;
  name: string;
  logo_url: string | null;
  category: string | null;
  description: string | null;
  details: string | null;
  published: boolean;
  sort_order: number;
}

const empty = (): Omit<Skill, "id"> => ({
  name: "",
  logo_url: "",
  category: "",
  description: "",
  details: "",
  published: true,
  sort_order: 0,
});

export default function Skills() {
  const [items, setItems] = useState<Skill[]>([]);
  const [form, setForm] = useState(empty());
  const [editing, setEditing] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => get<Skill[]>("/skills").then(setItems).catch(() => {});
  useEffect(() => { load(); }, []);

  const setField = (field: keyof typeof form, value: unknown) =>
    setForm((f) => ({ ...f, [field]: value }));

  const handleEdit = (item: Skill) => {
    setEditing(item.id);
    setForm({
      name: item.name,
      logo_url: item.logo_url || "",
      category: item.category || "",
      description: item.description || "",
      details: item.details || "",
      published: item.published,
      sort_order: item.sort_order,
    });
    setError(""); setSuccess("");
  };

  const handleCancel = () => { setEditing(null); setForm(empty()); setError(""); setSuccess(""); };

  const handleDelete = async (id: number) => {
    if (!confirm("Supprimer cette competence ?")) return;
    await del(`/skills/${id}`);
    load();
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    try { const url = await uploadImage(file); setField("logo_url", url); }
    catch { setError("Erreur upload"); }
    finally { setUploading(false); }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(""); setSuccess("");
    try {
      if (editing) {
        await put(`/skills/${editing}`, form);
        setSuccess("Competence modifiee.");
      } else {
        await post("/skills/", { ...form, site_id: Number(getSiteId()) });
        setSuccess("Competence creee.");
      }
      handleCancel(); load();
    } catch (err) { setError(String(err)); }
  };

  const q = search.toLowerCase();
  const filtered = items.filter((item) =>
    item.name.toLowerCase().includes(q) ||
    (item.category || "").toLowerCase().includes(q)
  );

  return (
    <>
      <div className="page-header">
        <h1>Competences</h1>
        {editing === null && (
          <button className="btn btn-primary" onClick={() => { setEditing(0); setForm(empty()); }}>
            + Nouvelle competence
          </button>
        )}
      </div>

      {editing !== null && (
        <div className="form-panel">
          <h2>{editing ? "Modifier" : "Nouvelle competence"}</h2>
          {error && <div className="msg msg-error">{error}</div>}
          {success && <div className="msg msg-success">{success}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label>Nom *</label>
                <input value={form.name} onChange={(e) => setField("name", e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Catégorie (tags, séparés par virgule)</label>
                <input value={form.category || ""} onChange={(e) => setField("category", e.target.value)} placeholder="Réseau,Cisco" />
              </div>
              <div className="form-group full">
                <label>Description (résumé court)</label>
                <textarea value={form.description || ""} onChange={(e) => setField("description", e.target.value)} rows={2} placeholder="Courte description visible sur la carte..." />
              </div>
              <div className="form-group full">
                <label>Détails (Markdown — affiché au clic sur la carte)</label>
                <div data-color-mode="light">
                  <MDEditor
                    value={form.details || ""}
                    onChange={(v) => setField("details", v || "")}
                    height={280}
                    preview="live"
                  />
                </div>
              </div>
              <div className="form-group full">
                <label>Logo URL</label>
                <div className="input-upload">
                  <input
                    value={form.logo_url || ""}
                    onChange={(e) => setField("logo_url", e.target.value)}
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
                {form.logo_url && (
                  <img src={form.logo_url} alt="logo" className="thumb" style={{ marginTop: "0.4rem" }} />
                )}
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
                    id="skill-pub"
                    checked={form.published}
                    onChange={(e) => setField("published", e.target.checked)}
                  />
                  <label htmlFor="skill-pub">Publie</label>
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
        <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Rechercher par nom, catégorie..." style={{ width: "300px" }} />
        {search && <span style={{ fontSize: "0.82rem", color: "var(--mid)" }}>{filtered.length} résultat{filtered.length !== 1 ? "s" : ""}</span>}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Logo</th>
              <th>Nom</th>
              <th>Categorie</th>
              <th>Ordre</th>
              <th>Publie</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} style={{ textAlign: "center", color: "var(--mid)", padding: "2rem" }}>
                  {search ? `Aucun résultat pour "${search}"` : "Aucune competence"}
                </td>
              </tr>
            )}
            {filtered.map((item) => (
              <tr key={item.id}>
                <td>
                  {item.logo_url
                    ? <img src={item.logo_url} alt={item.name} className="thumb" />
                    : "—"}
                </td>
                <td className="truncate">{item.name}</td>
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
