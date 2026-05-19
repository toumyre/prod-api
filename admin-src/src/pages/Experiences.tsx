import { useEffect, useState, type FormEvent } from "react";
import MDEditor from "@uiw/react-md-editor";
import { get, post, put, del, getSiteId } from "../lib/api";

interface Experience {
  id: number;
  title: string;
  company: string;
  location: string | null;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  technologies: string | null;
  published: boolean;
  sort_order: number;
}

const empty = (): Omit<Experience, "id"> => ({
  title: "",
  company: "",
  location: "",
  description: "",
  start_date: "",
  end_date: "",
  technologies: "",
  published: true,
  sort_order: 0,
});

export default function Experiences() {
  const [items, setItems] = useState<Experience[]>([]);
  const [form, setForm] = useState(empty());
  const [editing, setEditing] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [search, setSearch] = useState("");

  const load = () => get<Experience[]>("/experience").then(setItems).catch(() => {});
  useEffect(() => { load(); }, []);

  const setField = (field: keyof typeof form, value: unknown) =>
    setForm((f) => ({ ...f, [field]: value }));

  const handleEdit = (item: Experience) => {
    setEditing(item.id);
    setForm({
      title: item.title,
      company: item.company,
      location: item.location || "",
      description: item.description || "",
      start_date: item.start_date || "",
      end_date: item.end_date || "",
      technologies: item.technologies || "",
      published: item.published,
      sort_order: item.sort_order,
    });
    setError(""); setSuccess("");
  };

  const handleCancel = () => { setEditing(null); setForm(empty()); setError(""); setSuccess(""); };

  const handleDelete = async (id: number) => {
    if (!confirm("Supprimer cette experience ?")) return;
    await del(`/experience/${id}`);
    load();
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(""); setSuccess("");
    try {
      if (editing) {
        await put(`/experience/${editing}`, form);
        setSuccess("Experience modifiee.");
      } else {
        await post("/experience", { ...form, site_id: Number(getSiteId()) });
        setSuccess("Experience creee.");
      }
      handleCancel(); load();
    } catch (err) { setError(String(err)); }
  };

  const q = search.toLowerCase();
  const filtered = items.filter((item) =>
    item.title.toLowerCase().includes(q) ||
    item.company.toLowerCase().includes(q) ||
    (item.technologies || "").toLowerCase().includes(q)
  );

  return (
    <>
      <div className="page-header">
        <h1>Experiences</h1>
        {editing === null && (
          <button className="btn btn-primary" onClick={() => { setEditing(0); setForm(empty()); }}>
            + Nouvelle experience
          </button>
        )}
      </div>

      {editing !== null && (
        <div className="form-panel">
          <h2>{editing ? "Modifier l'experience" : "Nouvelle experience"}</h2>
          {error && <div className="msg msg-error">{error}</div>}
          {success && <div className="msg msg-success">{success}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label>Poste *</label>
                <input
                  value={form.title}
                  onChange={(e) => setField("title", e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Entreprise *</label>
                <input
                  value={form.company}
                  onChange={(e) => setField("company", e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Lieu</label>
                <input
                  value={form.location || ""}
                  onChange={(e) => setField("location", e.target.value)}
                  placeholder="Paris, France"
                />
              </div>
              <div className="form-group">
                <label>Technologies</label>
                <input
                  value={form.technologies || ""}
                  onChange={(e) => setField("technologies", e.target.value)}
                  placeholder="Python,Docker,Linux"
                />
              </div>
              <div className="form-group">
                <label>Date debut</label>
                <input
                  value={form.start_date || ""}
                  onChange={(e) => setField("start_date", e.target.value)}
                  placeholder="2023-01"
                />
              </div>
              <div className="form-group">
                <label>Date fin</label>
                <input
                  value={form.end_date || ""}
                  onChange={(e) => setField("end_date", e.target.value)}
                  placeholder="2024-06 (ou vide si en cours)"
                />
              </div>
              <div className="form-group full">
                <label>Description (Markdown)</label>
                <div data-color-mode="light">
                  <MDEditor
                    value={form.description || ""}
                    onChange={(v) => setField("description", v || "")}
                    height={260}
                    preview="live"
                  />
                </div>
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
                    id="exp-pub"
                    checked={form.published}
                    onChange={(e) => setField("published", e.target.checked)}
                  />
                  <label htmlFor="exp-pub">Publie</label>
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
        <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Rechercher par poste, entreprise, technologies..." style={{ width: "300px" }} />
        {search && <span style={{ fontSize: "0.82rem", color: "var(--mid)" }}>{filtered.length} résultat{filtered.length !== 1 ? "s" : ""}</span>}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Poste</th>
              <th>Entreprise</th>
              <th>Lieu</th>
              <th>Debut</th>
              <th>Fin</th>
              <th>Publie</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", color: "var(--mid)", padding: "2rem" }}>
                  {search ? `Aucun résultat pour "${search}"` : "Aucune experience"}
                </td>
              </tr>
            )}
            {filtered.map((item) => (
              <tr key={item.id}>
                <td className="truncate">{item.title}</td>
                <td className="truncate">{item.company}</td>
                <td className="truncate">{item.location || "—"}</td>
                <td>{item.start_date || "—"}</td>
                <td>{item.end_date || "En cours"}</td>
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
