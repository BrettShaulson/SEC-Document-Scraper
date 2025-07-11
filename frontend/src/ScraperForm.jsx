import { useState } from "react";
import axios from "axios";

const SECTIONS = ["1", "1A", "1B", "3", "7", "7A", "8", "9", "15"];

export default function ScraperForm() {
  const [url, setUrl] = useState("");
  const [ticks, setTicks] = useState({});
  const toggle = id => setTicks(p => ({ ...p, [id]: !p[id] }));

  const submit = async () => {
    const chosen = Object.entries(ticks).filter(([, v]) => v).map(([k]) => k);
    if (!url || !chosen.length) return alert("Need URL + at least one section");
    try {
      const { data } = await axios.post(
        \`\${process.env.REACT_APP_API_BASE}/scrape\`,
        { filing_url: url, sections: chosen }
      );
      alert(JSON.stringify(data, null, 2));
    } catch (e) {
      alert(e);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "2rem auto", fontFamily: "sans-serif" }}>
      <h2>SEC Scraper</h2>
      <input
        style={{ width: "100%", padding: 8 }}
        placeholder="SEC filing URL…"
        value={url}
        onChange={e => setUrl(e.target.value)}
      />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 4, margin: '1rem 0' }}>
        {SECTIONS.map(id => (
          <label key={id}>
            <input type="checkbox" checked={!!ticks[id]} onChange={() => toggle(id)} /> {id}
          </label>
        ))}
      </div>
      <button onClick={submit}>Scrape</button>
    </div>
  );
}
