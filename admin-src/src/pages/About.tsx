import { useEffect, useState, useRef, type FormEvent } from "react";
import RichEditor from "../components/RichEditor";
import { get, post, put, uploadImage, uploadCV, uploadSynthesis } from "../lib/api";

interface About {
  id: number;
  photo_url: string | null;
  bio: string | null;
  github_url: string | null;
  linkedin_url: string | null;
  cv_url: string | null;
  published: boolean;
}

const empty = () => ({
  photo_url: "",
  bio: "",
  github_url: "",
  linkedin_url: "",
  cv_url: "",
  published: true,
});

export default function About() {
  const [about, setAbout] = useState<About | null>(null);
  const [form, setForm] = useState(empty());
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadingCV, setUploadingCV] = useState(false);
  const [cvSuccess, setCvSuccess] = useState("");
  const [uploadingSynthesis, setUploadingSynthesis] = useState(false);
  const [synthesisSuccess, setSynthesisSuccess] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const cvFileRef = useRef<HTMLInputElement>(null);
  const synthesisFileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    get<About | null>("/about/").then((data) => {
      if (data) {
        setAbout(data);
        setForm({
          photo_url: data.photo_url || "",
          bio: data.bio || "",
          github_url: data.github_url || "",
          linkedin_url: data.linkedin_url || "",
          cv_url: data.cv_url || "",
          published: data.published,
        });
      }
    }).catch(() => {});
  }, []);

  const set = (field: keyof typeof form, value: unknown) =>
    setForm((f) => ({ ...f, [field]: value }));

  const handleSynthesisUpload = async (file: File) => {
    setUploadingSynthesis(true);
    setSynthesisSuccess("");
    try {
      await uploadSynthesis(file);
      setSynthesisSuccess("Tableau de synthèse mis à jour.");
    } catch {
      setError("Erreur upload tableau de synthèse");
    } finally {
      setUploadingSynthesis(false);
    }
  };

  const handleCVUpload = async (file: File) => {
    setUploadingCV(true);
    setCvSuccess("");
    try {
      await uploadCV(file);
      setCvSuccess("CV mis à jour.");
    } catch {
      setError("Erreur upload CV");
    } finally {
      setUploadingCV(false);
    }
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    try { const url = await uploadImage(file); set("photo_url", url); }
    catch { setError("Erreur upload photo"); }
    finally { setUploading(false); }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(""); setSuccess("");
    try {
      if (about) {
        await put(`/about/${about.id}`, form);
      } else {
        await post("/about/", { ...form, site_id: 1 });
      }
      setSuccess("Page « À propos » sauvegardée.");
      // Reload
      get<About>("/about/").then((data) => setAbout(data)).catch(() => {});
    } catch (err) {
      setError(String(err));
    }
  };

  return (
    <>
      <div className="page-header">
        <h1>À propos</h1>
        <span style={{ fontSize: "0.78rem", color: "var(--mid)", textTransform: "uppercase", letterSpacing: "1px" }}>
          Page unique
        </span>
      </div>

      <div className="form-panel">
        {error && <div className="msg msg-error">{error}</div>}
        {success && <div className="msg msg-success">{success}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-grid">

            {/* Photo */}
            <div className="form-group full">
              <label>Photo de profil</label>
              <div className="input-upload">
                <input
                  value={form.photo_url}
                  onChange={(e) => set("photo_url", e.target.value)}
                  placeholder="https://... ou importer"
                />
                <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }}
                  onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])} />
                <button type="button" className="btn btn-secondary btn-sm"
                  onClick={() => fileRef.current?.click()} disabled={uploading}>
                  {uploading ? "Envoi..." : "📎 Importer"}
                </button>
              </div>
              {form.photo_url && (
                <img src={form.photo_url} alt="photo"
                  style={{ marginTop: "0.6rem", width: "100px", height: "100px", objectFit: "cover", border: "var(--border)" }} />
              )}
            </div>

            <div className="form-group full">
              <label>Présentation</label>
              <RichEditor
                value={form.bio}
                onChange={(v) => set("bio", v)}
              />
            </div>

            {/* Liens */}
            <div className="form-group">
              <label>GitHub URL</label>
              <input value={form.github_url} onChange={(e) => set("github_url", e.target.value)} placeholder="https://github.com/..." />
            </div>
            <div className="form-group">
              <label>LinkedIn URL</label>
              <input value={form.linkedin_url} onChange={(e) => set("linkedin_url", e.target.value)} placeholder="https://linkedin.com/in/..." />
            </div>
            <div className="form-group full">
              <label>CV (PDF)</label>
              <div className="input-upload">
                <input
                  value={form.cv_url}
                  onChange={(e) => set("cv_url", e.target.value)}
                  placeholder="https://api.t-etendard.fr/api/cv"
                />
                <input ref={cvFileRef} type="file" accept="application/pdf" style={{ display: "none" }}
                  onChange={(e) => e.target.files?.[0] && handleCVUpload(e.target.files[0])} />
                <button type="button" className="btn btn-secondary btn-sm"
                  onClick={() => cvFileRef.current?.click()} disabled={uploadingCV}>
                  {uploadingCV ? "Envoi..." : "📎 Importer PDF"}
                </button>
              </div>
              {cvSuccess && <div className="msg msg-success" style={{ marginTop: "0.4rem" }}>{cvSuccess}</div>}
            </div>

            <div className="form-group full">
              <label>Tableau de synthèse (PDF)</label>
              <div className="input-upload">
                <input ref={synthesisFileRef} type="file" accept="application/pdf" style={{ display: "none" }}
                  onChange={(e) => e.target.files?.[0] && handleSynthesisUpload(e.target.files[0])} />
                <button type="button" className="btn btn-secondary btn-sm"
                  onClick={() => synthesisFileRef.current?.click()} disabled={uploadingSynthesis}>
                  {uploadingSynthesis ? "Envoi..." : "📎 Importer PDF"}
                </button>
              </div>
              {synthesisSuccess && <div className="msg msg-success" style={{ marginTop: "0.4rem" }}>{synthesisSuccess}</div>}
            </div>
            <div className="form-group">
              <div className="form-check" style={{ marginTop: "1.8rem" }}>
                <input type="checkbox" id="about-pub" checked={form.published}
                  onChange={(e) => set("published", e.target.checked)} />
                <label htmlFor="about-pub">Publié</label>
              </div>
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary">
              {about ? "Enregistrer" : "Créer"}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
