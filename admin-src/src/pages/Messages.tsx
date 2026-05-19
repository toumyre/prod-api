import { useEffect, useState } from "react";
import { get, del } from "../lib/api";

interface Message {
  id: number;
  name: string;
  email: string;
  subject: string | null;
  content: string;
  is_read: boolean;
  created_at: string;
}

export default function Messages() {
  const [items, setItems] = useState<Message[]>([]);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [search, setSearch] = useState("");

  const load = () => get<Message[]>("/messages").then(setItems).catch(() => {});
  useEffect(() => { load(); }, []);

  const handleDelete = async (id: number) => {
    if (!confirm("Supprimer ce message ?")) return;
    await del(`/messages/${id}`);
    if (expanded === id) setExpanded(null);
    load();
  };

  const fmt = (dt: string) => {
    try {
      return new Date(dt).toLocaleString("fr-FR", {
        day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit",
      });
    } catch {
      return dt;
    }
  };

  const q = search.toLowerCase();
  const filtered = items.filter((item) =>
    item.name.toLowerCase().includes(q) ||
    item.email.toLowerCase().includes(q) ||
    (item.subject || "").toLowerCase().includes(q) ||
    item.content.toLowerCase().includes(q)
  );

  return (
    <>
      <div className="page-header">
        <h1>Messages</h1>
        <span style={{ fontSize: "0.82rem", color: "var(--mid)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" }}>
          {items.length} message{items.length !== 1 ? "s" : ""}
        </span>
      </div>

      <div style={{ marginBottom: "1rem", display: "flex", alignItems: "center", gap: "1rem" }}>
        <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Rechercher par nom, email, sujet, contenu..." style={{ width: "300px" }} />
        {search && <span style={{ fontSize: "0.82rem", color: "var(--mid)" }}>{filtered.length} résultat{filtered.length !== 1 ? "s" : ""}</span>}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Statut</th>
              <th>Nom</th>
              <th>Email</th>
              <th>Sujet</th>
              <th>Message</th>
              <th>Recu le</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", color: "var(--mid)", padding: "2rem" }}>
                  {search ? `Aucun résultat pour "${search}"` : "Aucun message"}
                </td>
              </tr>
            )}
            {filtered.map((item) => (
              <>
                <tr key={item.id} style={{ cursor: "pointer" }} onClick={() => setExpanded(expanded === item.id ? null : item.id)}>
                  <td>
                    <span className={`badge ${item.is_read ? "badge-off" : "badge-on"}`}
                      style={item.is_read ? {} : { background: "#fef9c3", color: "#854d0e" }}>
                      {item.is_read ? "Lu" : "Nouveau"}
                    </span>
                  </td>
                  <td style={{ fontWeight: item.is_read ? 400 : 700 }}>{item.name}</td>
                  <td className="truncate">{item.email}</td>
                  <td className="truncate">{item.subject || "—"}</td>
                  <td className="truncate" style={{ maxWidth: "240px" }}>{item.content}</td>
                  <td style={{ whiteSpace: "nowrap", fontSize: "0.78rem" }}>{fmt(item.created_at)}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <div className="td-actions">
                      <button className="btn btn-danger btn-sm" onClick={() => handleDelete(item.id)}>
                        Supprimer
                      </button>
                    </div>
                  </td>
                </tr>
                {expanded === item.id && (
                  <tr key={`exp-${item.id}`}>
                    <td colSpan={7} style={{ background: "var(--grey)", padding: "1rem 1.5rem" }}>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                        <div>
                          <strong style={{ fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "1px" }}>
                            De :
                          </strong>{" "}
                          {item.name} &lt;{item.email}&gt;
                        </div>
                        {item.subject && (
                          <div>
                            <strong style={{ fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "1px" }}>
                              Sujet :
                            </strong>{" "}
                            {item.subject}
                          </div>
                        )}
                        <div style={{ marginTop: "0.5rem", lineHeight: 1.6, whiteSpace: "pre-wrap", fontSize: "0.88rem" }}>
                          {item.content}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
