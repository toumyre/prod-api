import { useEffect, useState, useRef, type FormEvent } from "react";
import { get, post, put, del, uploadImage, getSiteId } from "../lib/api";

interface RosterMember {
  id: number;
  name: string;
  number: string | null;
  role: string | null;
  photo_url: string | null;
  eva_url: string | null;
  published: boolean;
  sort_order: number;
}

const empty = (): Omit<RosterMember, "id"> => ({
  name: "",
  number: "",
  role: "",
  photo_url: "",
  eva_url: "",
  published: true,
  sort_order: 0,
});

export default function Roster() {
  const [items, setItems] = useState<RosterMember[]>([]);
  const [form, setForm] = useState(empty());
  const [editing, setEditing] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [uploadingEva, setUploadingEva] = useState(false);
  const [search, setSearch] = useState("");
  const photoRef = useRef<HTMLInputElement>(null);
  const evaRef = useRef<HTMLInputElement>(null);

  const load = () => get<RosterMember[]>("/roster").then(setItems).catch(() => {});
  useEffect(() => { load(); }, []);

  const setField = (field: keyof typeof form, value: unknown) =>
    setForm((f) => ({ ...f, [field]: value }));

  const handleEdit = (item: RosterMember) => {
    setEditing(item.id);
    setForm({
      name: item.name,
      number: item.number || "",
      role: item.role || "",
      photo_url: item.photo_url || "",
      eva_url: item.eva_url || "",
      published: item.published,
      sort_order: item.sort_order,
    });
    setError(""); setSuccess("");
  };

  const handleCancel = () => { setEditing(null); setForm(empty()); setError(""); setSuccess(""); };

  const handleDelete = async (id: number) => {
    if (!confirm("Supprimer ce membre ?")) return;
    await del(`/roster/${id}`);
    load();
  };

  const handleUploadPhoto = async (file: File) => {
    setUploadingPhoto(true);
    try { const url = await uploadImage(file); setField("photo_url", url); }
    catch { setError("Erreur upload photo"); }
    finally { setUploadingPhoto(false); }
  };

  const handleUploadEva = async (file: File) => {
    setUploadingEva(true);
    try { const url = await uploadImage(file); setField("eva_url", url); }
    catch { setError("Erreur upload eva"); }
    finally { setUploadingEva(false); }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(""); setSuccess("");
    try {
      if (editing) {
        await put(`/roster/${editing}`, form);
        setSuccess("Membre modifie.");
      } else {
        await post("/roster", { ...form, site_id: Number(getSiteId()) });
        setSuccess("Membre cree.");
      }
      handleCancel(); load();
    } catch (err) { setError(String(err)); }
  };

  const q = search.toLowerCase();
  const filtered = items.filter((item) =>
    item.name.toLowerCase().includes(q) ||
    (item.role || "").toLowerCase().includes(q)
  );

  return (
    <>
      <div className="page-header">
        <h1>Roster</h1>
        {editing === null && (
          <button className="btn btn-primary" onClick={() => { setEditing(0); setForm(empty()); }}>
            + Nouveau membre
          </button>
        )}
      </div>

      {editing !== null && (
        <div className="form-panel">
          <h2>{editing ? "Modifier le membre" : "Nouveau membre"}</h2>
          {error && <div className="msg msg-error">{error}</div>}
          {success && <div className="msg msg-success">{success}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label>Nom *</label>
                <input
                  value={form.name}
                  onChange={(e) => setField("name", e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Numero</label>
                <input
                  value={form.number || ""}
                  onChange={(e) => setField("number", e.target.value)}
                  placeholder="10"
                />
              </div>
              <div className="form-group full">
                <label>Role / Poste</label>
                <input
                  value={form.role || ""}
                  onChange={(e) => setField("role", e.target.value)}
                  placeholder="Attaquant, Gardien..."
                />
              </div>
              <div className="form-group full">
                <label>Photo URL</label>
                <div className="input-upload">
                  <input
                    value={form.photo_url || ""}
                    onChange={(e) => setField("photo_url", e.target.value)}
                    placeholder="https://..."
                  />
                  <input
                    ref={photoRef}
                    type="file"
                    accept="image/*"
                    style={{ display: "none" }}
                    onChange={(e) => e.target.files?.[0] && handleUploadPhoto(e.target.files[0])}
                  />
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => photoRef.current?.click()}
                    disabled={uploadingPhoto}
                  >
                    {uploadingPhoto ? "..." : "Importer"}
                  </button>
                </div>
                {form.photo_url && (
                  <img src={form.photo_url} alt="photo" className="thumb" style={{ marginTop: "0.4rem" }} />
                )}
              </div>
              <div className="form-group full">
                <label>EVA URL (image alternative)</label>
                <div className="input-upload">
                  <input
                    value={form.eva_url || ""}
                    onChange={(e) => setField("eva_url", e.target.value)}
                    placeholder="https://..."
                  />
                  <input
                    ref={evaRef}
                    type="file"
                    accept="image/*"
                    style={{ display: "none" }}
                    onChange={(e) => e.target.files?.[0] && handleUploadEva(e.target.files[0])}
                  />
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => evaRef.current?.click()}
                    disabled={uploadingEva}
                  >
                    {uploadingEva ? "..." : "Importer"}
                  </button>
                </div>
                {form.eva_url && (
                  <img src={form.eva_url} alt="eva" className="thumb" style={{ marginTop: "0.4rem" }} />
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
                    id="roster-pub"
                    checked={form.published}
                    onChange={(e) => setField("published", e.target.checked)}
                  />
                  <label htmlFor="roster-pub">Publie</label>
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
        <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Rechercher par nom, rôle..." style={{ width: "300px" }} />
        {search && <span style={{ fontSize: "0.82rem", color: "var(--mid)" }}>{filtered.length} résultat{filtered.length !== 1 ? "s" : ""}</span>}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Photo</th>
              <th>Nom</th>
              <th>No.</th>
              <th>Role</th>
              <th>EVA</th>
              <th>Ordre</th>
              <th>Publie</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} style={{ textAlign: "center", color: "var(--mid)", padding: "2rem" }}>
                  {search ? `Aucun résultat pour "${search}"` : "Aucun membre"}
                </td>
              </tr>
            )}
            {filtered.map((item) => (
              <tr key={item.id}>
                <td>
                  {item.photo_url
                    ? <img src={item.photo_url} alt={item.name} className="thumb" />
                    : "—"}
                </td>
                <td className="truncate">{item.name}</td>
                <td>{item.number || "—"}</td>
                <td className="truncate">{item.role || "—"}</td>
                <td>
                  {item.eva_url
                    ? <img src={item.eva_url} alt="eva" className="thumb" />
                    : "—"}
                </td>
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
