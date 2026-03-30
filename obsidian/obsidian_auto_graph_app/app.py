#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from flask import Flask, jsonify, render_template_string, request

APP_TITLE = "Obsidian Problem Graph Generator"

app = Flask(__name__)

HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Obsidian Problem Graph Generator</title>
  <style>
    :root {
      --bg:#0f1115; --panel:#171a21; --panel2:#1f2430; --text:#e7eaf0; --muted:#9aa4b2;
      --accent:#7aa2f7; --border:#2b3240; --good:#8bd5ca; --warn:#f5a97f; --danger:#ed8796;
    }
    *{box-sizing:border-box}
    body{
      margin:0; font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
      background:linear-gradient(180deg,#0b0d12,#12151c 30%,#0f1115); color:var(--text);
    }
    .wrap{max-width:1500px;margin:0 auto;padding:20px;display:grid;grid-template-columns:430px 1fr;gap:16px;min-height:100vh}
    .panel{background:rgba(23,26,33,.92);border:1px solid var(--border);border-radius:18px;overflow:hidden}
    .panel header{padding:16px 18px 12px;border-bottom:1px solid var(--border);background:rgba(31,36,48,.65)}
    .panel header h1,.panel header h2{margin:0;font-size:18px;line-height:1.25}
    .panel header p{margin:6px 0 0;color:var(--muted);font-size:13px}
    .content{padding:16px 18px 18px}
    .stack{display:grid;gap:10px}
    .card{background:rgba(31,36,48,.75);border:1px solid var(--border);border-radius:14px;padding:12px}
    label{display:block;margin-bottom:6px;font-size:12px;color:var(--muted)}
    input[type="text"],input[type="number"],textarea,select{
      width:100%;background:#0f1218;border:1px solid var(--border);color:var(--text);
      border-radius:12px;padding:10px 12px;outline:none;font:inherit
    }
    textarea{min-height:130px;resize:vertical}
    input:focus,textarea:focus,select:focus{border-color:#4a5a7a;box-shadow:0 0 0 3px rgba(122,162,247,.15)}
    button,.btn{
      appearance:none;border:1px solid transparent;background:var(--accent);color:#081018;
      padding:10px 14px;border-radius:12px;font:inherit;font-weight:650;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:8px
    }
    .secondary{background:#242b38;color:var(--text);border-color:var(--border)}
    .danger{background:var(--danger);color:#1a0a0d}
    .tiny{font-size:12px;padding:8px 10px;border-radius:10px}
    .muted{color:var(--muted);font-size:12px}
    .split{display:grid;grid-template-columns:1fr 1fr;gap:10px}
    .files{max-height:240px;overflow:auto;border:1px solid var(--border);border-radius:12px;background:#0f1218}
    .file-item{display:flex;justify-content:space-between;gap:10px;padding:8px 10px;border-bottom:1px solid rgba(43,50,64,.65);font-size:13px;align-items:center}
    .file-item:last-child{border-bottom:0}
    .pill{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--border);background:#0f1218;border-radius:999px;padding:5px 10px;font-size:12px;color:var(--muted)}
    .main{display:grid;gap:16px;grid-template-rows:auto 1fr;min-width:0}
    .tabs{display:flex;gap:8px;flex-wrap:wrap}
    .tab{background:#242b38;color:var(--text);border:1px solid var(--border);padding:8px 12px;border-radius:10px;cursor:pointer;font-size:13px}
    .tab.active{background:var(--accent);color:#071018}
    .preview{height:calc(100vh - 110px);min-height:700px;overflow:auto;position:relative}
    pre{margin:0;white-space:pre-wrap;word-break:break-word;font-size:12px;line-height:1.45;color:#dfe7f1}
    table{width:100%;border-collapse:collapse;font-size:13px}
    th,td{border-bottom:1px solid rgba(43,50,64,.65);text-align:left;padding:8px 8px;vertical-align:top}
    th{color:var(--muted);font-weight:600}
    .status{padding:10px 12px;border-radius:12px;background:rgba(139,213,202,.08);border:1px solid rgba(139,213,202,.22);color:#c8f4ef;font-size:13px}
    .status.warn{background:rgba(245,169,127,.08);border-color:rgba(245,169,127,.22);color:#ffd6be}
    .status.err{background:rgba(237,135,150,.08);border-color:rgba(237,135,150,.22);color:#ffd4dc}
    .canvas-box{border:1px dashed #334055;border-radius:18px;padding:16px;background:rgba(15,18,24,.5);overflow:hidden}
    .note{background:rgba(15,18,24,.75);border:1px solid var(--border);border-radius:14px;padding:12px;font-size:13px;line-height:1.5;color:#dfe7f1}
    .note code{background:#0c1016;border:1px solid #2f3746;padding:1px 5px;border-radius:6px;color:#b7c7ff}
    .hidden{display:none !important}
    .small{font-size:12px;color:var(--muted)}
    .toolbar{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap}
    .taglist{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
    .tag{font-size:11px;padding:4px 8px;border-radius:999px;border:1px solid var(--border);background:#0e131b;color:#c6d3f0}
    @media (max-width:1100px){.wrap{grid-template-columns:1fr}.preview{height:auto;min-height:500px}}
  </style>
</head>
<body>
<div class="wrap">
  <section class="panel">
    <header>
      <h1>Obsidian Problem Graph Generator</h1>
      <p>Local website to auto-analyze problem notes, build similarity links, and export <span class="mono">graph.json</span> and <span class="mono">graph.canvas</span>.</p>
    </header>
    <div class="content stack">
      <div class="card stack">
        <div>
          <label>Import Markdown notes from a folder</label>
          <input id="fileInput" type="file" accept=".md,.markdown,text/markdown" multiple webkitdirectory />
          <div class="small" style="margin-top:6px;">Select your vault folder or Problems folder. The app reads all Markdown files inside.</div>
        </div>
        <div class="row">
          <button id="analyzeBtn">Analyze notes</button>
          <button id="buildBtn" class="secondary">Build graph</button>
        </div>
        <div class="row">
          <button id="exportJsonBtn" class="secondary tiny">Download graph.json</button>
          <button id="exportCanvasBtn" class="secondary tiny">Download graph.canvas</button>
          <button id="saveStateBtn" class="secondary tiny">Save local project</button>
          <button id="loadStateBtn" class="secondary tiny">Load local project</button>
          <button id="clearBtn" class="danger tiny">Clear</button>
        </div>
        <div id="status" class="status warn">No notes loaded yet.</div>
      </div>

      <div class="card stack">
        <h2 style="margin:0;font-size:16px;">Add a problem manually</h2>
        <div class="split">
          <div>
            <label>Filename / note path</label>
            <input id="manualPath" type="text" placeholder="Problems/P1314.md" />
          </div>
          <div>
            <label>Title</label>
            <input id="manualTitle" type="text" placeholder="P1314" />
          </div>
        </div>
        <div class="split">
          <div>
            <label>Tags (comma separated)</label>
            <input id="manualTags" type="text" placeholder="dp, prefix sums, binary search" />
          </div>
          <div>
            <label>Techniques (comma separated)</label>
            <input id="manualTechniques" type="text" placeholder="prefix sums, monotonicity" />
          </div>
        </div>
        <div class="split">
          <div>
            <label>Outgoing links (comma separated)</label>
            <input id="manualLinks" type="text" placeholder="[[P4552]], [[P8218]]" />
          </div>
          <div>
            <label>Language</label>
            <input id="manualLang" type="text" placeholder="en" value="en" />
          </div>
        </div>
        <div>
          <label>Statement / solution text</label>
          <textarea id="manualBody" placeholder="Paste statement, notes, solution, or core idea here..."></textarea>
        </div>
        <div class="row">
          <button id="addManualBtn">Add problem</button>
          <button id="sampleBtn" class="secondary">Load sample data</button>
        </div>
      </div>

      <div class="card stack">
        <div class="toolbar">
          <strong>Graph settings</strong>
        </div>
        <div class="split">
          <div>
            <label>Top neighbors per node</label>
            <input id="topK" type="number" min="1" max="20" value="4" />
          </div>
          <div>
            <label>Similarity threshold</label>
            <input id="threshold" type="number" min="0" max="1" step="0.01" value="0.18" />
          </div>
        </div>
        <div class="split">
          <div>
            <label>Boost for explicit links</label>
            <input id="explicitBoost" type="number" min="0" max="2" step="0.05" value="0.55" />
          </div>
          <div>
            <label>Use title/path in similarity</label>
            <select id="useTitlePath">
              <option value="yes" selected>Yes</option>
              <option value="no">No</option>
            </select>
          </div>
        </div>
        <div class="split">
          <div>
            <label>Use AI analysis on server</label>
            <select id="useAi">
              <option value="yes" selected>Yes, if server is configured</option>
              <option value="no">No, heuristic only</option>
            </select>
          </div>
          <div>
            <label>AI detail level</label>
            <select id="detailLevel">
              <option value="balanced" selected>Balanced</option>
              <option value="deep">Deep</option>
            </select>
          </div>
        </div>
        <div class="small">
          The backend can summarize statements, infer techniques, and create embeddings when configured. API keys stay on the server, not in the browser.
        </div>
      </div>

      <div class="card stack">
        <h2 style="margin:0;font-size:16px;">Loaded notes</h2>
        <div id="files" class="files"></div>
      </div>
    </div>
  </section>

  <section class="main">
    <section class="panel">
      <header>
        <h2>Output</h2>
        <p>Switch tabs to inspect the generated graph, JSON, and similarity table.</p>
      </header>
      <div class="content">
        <div class="tabs">
          <button class="tab active" data-tab="graph">Graph preview</button>
          <button class="tab" data-tab="json">graph.json</button>
          <button class="tab" data-tab="canvas">graph.canvas</button>
          <button class="tab" data-tab="table">Similarity table</button>
        </div>
      </div>
    </section>

    <section class="panel preview">
      <div class="content">
        <div id="graphTab" class="tabPane">
          <div class="canvas-box">
            <svg id="svg" width="100%" height="760" viewBox="0 0 1600 760" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="strokeWidth">
                  <path d="M0,0 L10,5 L0,10 z" fill="#6f7f99"></path>
                </marker>
              </defs>
            </svg>
          </div>
        </div>

        <div id="jsonTab" class="tabPane hidden">
          <pre id="jsonOut"></pre>
        </div>

        <div id="canvasTab" class="tabPane hidden">
          <pre id="canvasOut"></pre>
        </div>

        <div id="tableTab" class="tabPane hidden">
          <div class="note">
            Strong links are chosen from semantic similarity, shared tags, shared techniques, and explicit note-to-note links. Use the AI analyzer to get better fingerprints from raw statements.
          </div>
          <div style="height:12px;"></div>
          <div style="overflow:auto;">
            <table>
              <thead>
                <tr>
                  <th>From</th><th>To</th><th>Score</th><th>Why</th>
                </tr>
              </thead>
              <tbody id="tableBody"></tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  </section>
</div>

<script>
(() => {
  const state = {
    notes: [],
    analyzed: [],
    graph: { nodes: [], edges: [] },
    canvas: { nodes: [], edges: [] },
    similarityRows: [],
  };

  const $ = (id) => document.getElementById(id);
  const fileInput = $("fileInput");
  const filesBox = $("files");
  const statusBox = $("status");
  const svg = $("svg");
  const jsonOut = $("jsonOut");
  const canvasOut = $("canvasOut");
  const tableBody = $("tableBody");
  const tabs = Array.from(document.querySelectorAll(".tab"));
  const panes = { graph: $("graphTab"), json: $("jsonTab"), canvas: $("canvasTab"), table: $("tableTab") };

  function setStatus(message, kind = "warn") {
    statusBox.textContent = message;
    statusBox.className = `status ${kind === "ok" ? "" : kind}`;
  }

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, s => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[s]));
  }

  function slugify(s) {
    return String(s || "").toLowerCase().trim().replace(/['"]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  }

  function uniq(arr) {
    return [...new Set(arr.filter(Boolean))];
  }

  function parseYamlListValue(value) {
    const v = value.trim();
    if (!v) return [];
    if (v.startsWith("[") && v.endsWith("]")) {
      return v.slice(1, -1).split(",").map(x => x.trim().replace(/^['"]|['"]$/g, "")).filter(Boolean);
    }
    return [v.replace(/^['"]|['"]$/g, "")];
  }

  function parseFrontmatter(text) {
    const out = {};
    if (!text.startsWith("---")) return out;
    const lines = text.split(/\r?\n/);
    if (lines[0].trim() !== "---") return out;
    let i = 1;
    for (; i < lines.length; i++) {
      const line = lines[i];
      if (line.trim() === "---") break;
      const idx = line.indexOf(":");
      if (idx === -1) continue;
      const key = line.slice(0, idx).trim();
      const value = line.slice(idx + 1).trim();
      if (value === "") {
        const list = [];
        i++;
        while (i < lines.length && /^\s*-\s+/.test(lines[i])) {
          list.push(lines[i].replace(/^\s*-\s+/, "").trim().replace(/^['"]|['"]$/g, ""));
          i++;
        }
        i--;
        out[key] = list;
      } else if (value === "true") out[key] = true;
      else if (value === "false") out[key] = false;
      else if (/^-?\d+(\.\d+)?$/.test(value)) out[key] = Number(value);
      else if (value.startsWith("[") && value.endsWith("]")) out[key] = parseYamlListValue(value);
      else out[key] = value.replace(/^['"]|['"]$/g, "");
    }
    return out;
  }

  function stripFrontmatter(text) {
    if (!text.startsWith("---")) return text;
    const end = text.indexOf("\n---", 3);
    if (end === -1) return text;
    return text.slice(end + 4).replace(/^\s*\n/, "");
  }

  function markdownToText(md) {
    return md.replace(/```[\s\S]*?```/g, " ").replace(/`([^`]+)`/g, "$1").replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, "$2")
      .replace(/\[\[([^\]]+)\]\]/g, "$1").replace(/#{1,6}\s+/g, "").replace(/[*_~>`\-]+/g, " ").replace(/\s+/g, " ").trim();
  }

  function extractInlineTags(text) {
    const tags = [];
    const re = /(^|[^A-Za-z0-9_/])#([A-Za-z0-9/_-]+)/g;
    let m;
    while ((m = re.exec(text)) !== null) tags.push(m[2]);
    return tags;
  }

  function extractLinks(text) {
    const links = [];
    const re = /\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]/g;
    let m;
    while ((m = re.exec(text)) !== null) links.push(m[1].trim());
    return uniq(links);
  }

  function extractHeadingTitle(text, fallback) {
    const m = text.match(/^\s*#\s+(.+)$/m);
    return m ? m[1].trim() : fallback;
  }

  function parseFrontmatterBlock(text) {
    const fm = parseFrontmatter(text);
    const body = stripFrontmatter(text);
    return { fm, body };
  }

  function normalizeList(x) {
    if (!x) return [];
    if (Array.isArray(x)) return x.flatMap(normalizeList).filter(Boolean);
    if (typeof x === "string") return x.split(",").map(s => s.trim()).filter(Boolean);
    return [];
  }

  function tokenize(text) {
    const stop = new Set(["the","and","or","to","of","a","in","for","on","with","as","is","are","be","this","that","it","by","an","at","from","into","use","using","used","can","will","we","you","your","their","problem","solution","idea","ideas","note","notes","core","approach","statement","given","then","than","also","may","must","should","all","each","every","new","old","more","less","when","where","which","what","how","why","while","between","within","without","have","has","had","but","not","only","if","else","just","over","under","same","different"]);
    return String(text || "").toLowerCase().replace(/\[\[[^\]]+\]\]/g, " ").replace(/https?:\/\/\S+/g, " ").replace(/[^a-z0-9]+/g, " ")
      .split(/\s+/).filter(w => w && w.length > 1 && !stop.has(w));
  }

  function cosineSimilarity(aTokens, bTokens) {
    const fa = new Map(), fb = new Map();
    aTokens.forEach(t => fa.set(t, (fa.get(t) || 0) + 1));
    bTokens.forEach(t => fb.set(t, (fb.get(t) || 0) + 1));
    let dot = 0, na = 0, nb = 0;
    for (const [k, v] of fa) {
      na += v * v;
      if (fb.has(k)) dot += v * fb.get(k);
    }
    for (const v of fb.values()) nb += v * v;
    if (!na || !nb) return 0;
    return dot / (Math.sqrt(na) * Math.sqrt(nb));
  }

  function jaccard(a, b) {
    const A = new Set(a.filter(Boolean).map(x => String(x).toLowerCase()));
    const B = new Set(b.filter(Boolean).map(x => String(x).toLowerCase()));
    if (!A.size && !B.size) return 0;
    let inter = 0;
    for (const x of A) if (B.has(x)) inter++;
    return inter / new Set([...A, ...B]).size;
  }

  function parseNote(filePath, text) {
    const frontmatter = parseFrontmatter(text);
    const body = stripFrontmatter(text);
    const title = frontmatter.title || extractHeadingTitle(body, filePath.split(/[\\/]/).pop().replace(/\.(md|markdown)$/i, "")) || filePath;
    const tags = uniq([...(normalizeList(frontmatter.tags)), ...extractInlineTags(body)]);
    const techniques = uniq([...(normalizeList(frontmatter.techniques)), ...(normalizeList(frontmatter.ideas)), ...(normalizeList(frontmatter.methods))]);
    const outgoingLinks = extractLinks(body);
    const plain = markdownToText(body);
    return {
      id: slugify(frontmatter.problem_id || title || filePath),
      file: filePath,
      title,
      language: frontmatter.language || frontmatter.lang || "unknown",
      tags,
      techniques,
      outgoingLinks,
      body,
      text: plain,
      ideaText: uniq([...techniques, ...tags]).join(" "),
      frontmatter,
      ai: null,
    };
  }

  async function readFileAsText(file) {
    return await file.text();
  }

  async function importFiles(fileList) {
    const files = Array.from(fileList || []).filter(f => /\.(md|markdown)$/i.test(f.name));
    if (!files.length) {
      setStatus("No Markdown files found in the selected input.", "err");
      return;
    }
    const notes = [];
    for (const file of files) {
      const text = await readFileAsText(file);
      const rel = file.webkitRelativePath || file.name;
      notes.push(parseNote(rel, text));
    }
    state.notes = notes;
    renderLoadedFiles();
    setStatus(`Loaded ${notes.length} notes. Click “Analyze notes”.`, "ok");
  }

  function addManualNote() {
    const file = $("manualPath").value.trim() || `Problems/${($("manualTitle").value.trim() || "untitled").replace(/\s+/g, "_")}.md`;
    const title = $("manualTitle").value.trim() || file.replace(/^.*[\\/]/, "").replace(/\.(md|markdown)$/i, "");
    const tags = $("manualTags").value.split(",").map(s => s.trim()).filter(Boolean);
    const techniques = $("manualTechniques").value.split(",").map(s => s.trim()).filter(Boolean);
    const outgoingLinks = $("manualLinks").value.split(",").map(s => s.trim()).filter(Boolean).map(s => s.replace(/^\[\[/, "").replace(/\]\]$/, ""));
    const body = $("manualBody").value.trim() || "";
    const language = $("manualLang").value.trim() || "unknown";
    const text = `---\ntitle: ${JSON.stringify(title)}\nlanguage: ${JSON.stringify(language)}\ntags: ${JSON.stringify(tags)}\ntechniques: ${JSON.stringify(techniques)}\n---\n\n${body}`;
    const note = parseNote(file, text);
    note.tags = uniq(tags.concat(note.tags));
    note.techniques = uniq(techniques.concat(note.techniques));
    note.outgoingLinks = uniq(outgoingLinks.concat(note.outgoingLinks));
    note.language = language;
    note.body = body;
    note.text = markdownToText(body);
    state.notes.push(note);
    renderLoadedFiles();
    setStatus(`Added note "${note.title}".`, "ok");
  }

  async function analyzeNotes() {
    if (!state.notes.length) {
      setStatus("Load some Markdown files first.", "err");
      return;
    }
    setStatus("Analyzing notes on the server...", "warn");
    const useAi = $("useAi").value === "yes";
    const detailLevel = $("detailLevel").value;
    const analyzed = [];
    for (let i = 0; i < state.notes.length; i++) {
      const note = state.notes[i];
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: note.file,
          title: note.title,
          text: note.body,
          frontmatter: note.frontmatter,
          use_ai: useAi,
          detail_level: detailLevel,
        })
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(`Analyze failed for ${note.file}: ${err}`);
      }
      const data = await res.json();
      analyzed.push(data);
      setStatus(`Analyzed ${i + 1}/${state.notes.length}: ${note.title}`, "warn");
    }
    state.analyzed = analyzed;
    setStatus(`Analyzed ${analyzed.length} notes. Now click “Build graph”.`, "ok");
  }

  async function buildGraph() {
    if (!state.notes.length) {
      setStatus("Load some Markdown files first.", "err");
      return;
    }
    if (!state.analyzed.length || state.analyzed.length !== state.notes.length) {
      await analyzeNotes();
    }
    const payload = {
      notes: state.analyzed,
      top_k: Math.max(1, Number($("topK").value || 4)),
      threshold: Math.max(0, Number($("threshold").value || 0.18)),
      explicit_boost: Math.max(0, Number($("explicitBoost").value || 0.55)),
      use_title_path: $("useTitlePath").value === "yes",
    };
    const res = await fetch("/api/build", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Build failed: ${err}`);
    }
    const data = await res.json();
    state.graph = data.graph;
    state.canvas = data.canvas;
    state.similarityRows = data.rows || [];
    renderOutputs();
    setStatus(`Built graph with ${state.graph.nodes.length} nodes and ${state.graph.edges.length} edges.`, "ok");
  }

  function renderLoadedFiles() {
    if (!state.notes.length) {
      filesBox.innerHTML = `<div class="file-item"><span>No files loaded</span><span class="muted">—</span></div>`;
      return;
    }
    filesBox.innerHTML = state.notes.map((n, i) => `
      <div class="file-item">
        <div>
          <div><strong>${escapeHtml(n.title)}</strong></div>
          <div class="muted mono">${escapeHtml(n.file)}</div>
          <div class="taglist">${n.techniques.slice(0,4).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join("")}</div>
        </div>
        <button class="tiny secondary" data-remove="${i}">Remove</button>
      </div>
    `).join("");
    filesBox.querySelectorAll("[data-remove]").forEach(btn => {
      btn.addEventListener("click", () => {
        const idx = Number(btn.getAttribute("data-remove"));
        state.notes.splice(idx, 1);
        state.analyzed.splice(idx, 1);
        renderLoadedFiles();
        setStatus(`Removed one note. ${state.notes.length} notes remain.`, "ok");
      });
    });
  }

  function renderOutputs() {
    jsonOut.textContent = JSON.stringify(state.graph || {}, null, 2);
    canvasOut.textContent = JSON.stringify(state.canvas || {}, null, 2);
    renderTable();
    drawGraph();
  }

  function renderTable() {
    if (!state.similarityRows || !state.similarityRows.length) {
      tableBody.innerHTML = `<tr><td colspan="4" class="muted">No edges yet. Build graph first.</td></tr>`;
      return;
    }
    tableBody.innerHTML = state.similarityRows.slice(0, 200).map(r => `
      <tr>
        <td>${escapeHtml(r.from)}</td>
        <td>${escapeHtml(r.to)}</td>
        <td class="mono">${Number(r.score).toFixed(3)}</td>
        <td class="muted">${escapeHtml(r.why)}</td>
      </tr>
    `).join("");
  }

  function drawGraph() {
    const width = 1600, height = 760;
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    while (svg.childNodes.length > 1) svg.removeChild(svg.lastChild);

    const nodeMap = new Map();
    const nodes = state.graph.nodes || [];
    const edges = state.graph.edges || [];
    for (const n of nodes) nodeMap.set(n.id, n);

    for (const e of edges) {
      const a = nodeMap.get(e.fromNode);
      const b = nodeMap.get(e.toNode);
      if (!a || !b) continue;
      const x1 = a.x + a.width, y1 = a.y + a.height/2;
      const x2 = b.x, y2 = b.y + b.height/2;
      const mx = (x1 + x2) / 2;
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", e.color === "5" ? "#8bd5ca" : "#6f7f99");
      path.setAttribute("stroke-width", "2.2");
      path.setAttribute("marker-end", "url(#arrow)");
      path.setAttribute("opacity", "0.82");
      svg.appendChild(path);
      if (e.label) {
        const tx = document.createElementNS("http://www.w3.org/2000/svg", "text");
        tx.setAttribute("x", mx);
        tx.setAttribute("y", (y1 + y2) / 2 - 6);
        tx.setAttribute("fill", "#dfe7f1");
        tx.setAttribute("font-size", "12");
        tx.setAttribute("text-anchor", "middle");
        tx.textContent = e.label;
        svg.appendChild(tx);
      }
    }

    for (const n of nodes) {
      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("x", n.x);
      rect.setAttribute("y", n.y);
      rect.setAttribute("rx", 16);
      rect.setAttribute("ry", 16);
      rect.setAttribute("width", n.width);
      rect.setAttribute("height", n.height);
      rect.setAttribute("fill", "#171a21");
      rect.setAttribute("stroke", n.color === "4" ? "#8bd5ca" : "#2b3240");
      rect.setAttribute("stroke-width", "1.4");
      g.appendChild(rect);

      const title = document.createElementNS("http://www.w3.org/2000/svg", "text");
      title.setAttribute("x", n.x + 16);
      title.setAttribute("y", n.y + 28);
      title.setAttribute("fill", "#e7eaf0");
      title.setAttribute("font-size", "15");
      title.setAttribute("font-weight", "700");
      title.textContent = n.file.replace(/^.*[\\/]/, "").replace(/\.(md|markdown)$/i, "");
      g.appendChild(title);

      const pathText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      pathText.setAttribute("x", n.x + 16);
      pathText.setAttribute("y", n.y + 49);
      pathText.setAttribute("fill", "#9aa4b2");
      pathText.setAttribute("font-size", "11");
      pathText.textContent = n.file;
      g.appendChild(pathText);

      const note = state.analyzed.find(x => slugify(x.file) === slugify(n.file) || x.id === n.id);
      const tags = note ? uniq([...(note.techniques || []), ...(note.tags || [])]).slice(0, 4) : [];
      tags.forEach((t, idx) => {
        const pill = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        pill.setAttribute("x", n.x + 16 + idx * 74);
        pill.setAttribute("y", n.y + 72);
        pill.setAttribute("width", 68);
        pill.setAttribute("height", 24);
        pill.setAttribute("rx", 12);
        pill.setAttribute("fill", "#0f1218");
        pill.setAttribute("stroke", "#2b3240");
        g.appendChild(pill);

        const tText = document.createElementNS("http://www.w3.org/2000/svg", "text");
        tText.setAttribute("x", n.x + 50 + idx * 74);
        tText.setAttribute("y", n.y + 89);
        tText.setAttribute("fill", "#c6d3f0");
        tText.setAttribute("font-size", "10");
        tText.setAttribute("text-anchor", "middle");
        tText.textContent = t.length > 10 ? t.slice(0, 10) + "…" : t;
        g.appendChild(tText);
      });
      svg.appendChild(g);
    }
  }

  function download(filename, content, mime = "application/json") {
    const blob = new Blob([content], { type: mime + ";charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  function exportGraphJson() {
    if (!state.graph.nodes.length) return setStatus("Build the graph first.", "err");
    download("graph.json", JSON.stringify(state.graph, null, 2), "application/json");
  }

  function exportCanvas() {
    if (!state.canvas.nodes.length) return setStatus("Build the graph first.", "err");
    download("graph.canvas", JSON.stringify(state.canvas, null, 2), "application/json");
  }

  function saveLocalProject() {
    const payload = { notes: state.notes, analyzed: state.analyzed, graph: state.graph, canvas: state.canvas, similarityRows: state.similarityRows };
    localStorage.setItem("obsidian_problem_graph_project", JSON.stringify(payload));
    setStatus("Saved to localStorage in this browser.", "ok");
  }

  function loadLocalProject() {
    const raw = localStorage.getItem("obsidian_problem_graph_project");
    if (!raw) return setStatus("No saved local project found.", "err");
    const payload = JSON.parse(raw);
    state.notes = payload.notes || [];
    state.analyzed = payload.analyzed || [];
    state.graph = payload.graph || { nodes: [], edges: [] };
    state.canvas = payload.canvas || { nodes: [], edges: [] };
    state.similarityRows = payload.similarityRows || [];
    renderLoadedFiles();
    renderOutputs();
    setStatus(`Loaded ${state.notes.length} notes from localStorage.`, "ok");
  }

  function clearAll() {
    state.notes = [];
    state.analyzed = [];
    state.graph = { nodes: [], edges: [] };
    state.canvas = { nodes: [], edges: [] };
    state.similarityRows = [];
    renderLoadedFiles();
    renderOutputs();
    setStatus("Cleared all in-memory data.", "warn");
  }

  function loadSample() {
    state.notes = [
      parseNote("Problems/P1314.md", `---
title: P1314
tags: [prefix sums, binary search]
techniques: [prefix sums, monotonicity]
language: en
---

# P1314

## Core Idea
- transform to prefix sums
- binary search the answer
- use a monotonic feasibility check

[[P4552]]
`),
      parseNote("Problems/P4552.md", `---
title: P4552
tags: [monotonic queue, prefix sums]
techniques: [prefix sums, monotonic queue]
language: en
---

# P4552

## Solution
- prefix sums
- maintain a deque for best candidate
- optimize transitions
`),
      parseNote("Problems/P8218.md", `---
title: P8218
tags: [sqrt decomposition, range query]
techniques: [sqrt decomposition, range query]
language: en
---

# P8218

## Approach
- split blocks
- precompute transitions
- answer with block decomposition
`)
    ];
    state.analyzed = [];
    renderLoadedFiles();
    buildGraph().catch(err => setStatus(err.message, "err"));
  }

  tabs.forEach(tab => tab.addEventListener("click", () => {
    tabs.forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    const name = tab.dataset.tab;
    Object.entries(panes).forEach(([k, el]) => el.classList.toggle("hidden", k !== name));
  }));

  fileInput.addEventListener("change", async (e) => { await importFiles(e.target.files); });
  $("addManualBtn").addEventListener("click", addManualNote);
  $("sampleBtn").addEventListener("click", loadSample);
  $("analyzeBtn").addEventListener("click", () => analyzeNotes().catch(err => setStatus(err.message, "err")));
  $("buildBtn").addEventListener("click", () => buildGraph().catch(err => setStatus(err.message, "err")));
  $("exportJsonBtn").addEventListener("click", exportGraphJson);
  $("exportCanvasBtn").addEventListener("click", exportCanvas);
  $("saveStateBtn").addEventListener("click", saveLocalProject);
  $("loadStateBtn").addEventListener("click", loadLocalProject);
  $("clearBtn").addEventListener("click", clearAll);

  renderLoadedFiles();
  renderOutputs();
})();
</script>
</body>
</html>
"""

def strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[end + 4:].lstrip("\n")

def parse_frontmatter(text: str) -> Dict[str, Any]:
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: Dict[str, Any] = {}
    i = 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---":
            break
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                items = [x.strip().strip('"').strip("'") for x in value[1:-1].split(",") if x.strip()]
                out[key] = items
            elif value.lower() in {"true", "false"}:
                out[key] = value.lower() == "true"
            elif re.fullmatch(r"-?\d+(\.\d+)?", value):
                out[key] = float(value) if "." in value else int(value)
            else:
                out[key] = value.strip('"').strip("'")
        i += 1
    return out

def extract_links(text: str) -> List[str]:
    return list(dict.fromkeys(m.strip() for m in re.findall(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", text)))

def extract_inline_tags(text: str) -> List[str]:
    tags = []
    for m in re.finditer(r"(^|[^A-Za-z0-9_/])#([A-Za-z0-9/_-]+)", text):
        tags.append(m.group(2))
    return list(dict.fromkeys(tags))

def extract_heading_block(text: str, headings: List[str]) -> str:
    for h in headings:
        esc = re.escape(h)
        m = re.search(rf"^#{2,6}\s+{esc}\s*$([\s\S]*?)(?=^#{2,6}\s+|\Z)", text, re.M)
        if m:
            return m.group(1).strip()
    return ""

def first_paragraphs(text: str, limit: int = 3) -> str:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return "\n\n".join(parts[:limit])

def markdown_to_text(md: str) -> str:
    md = re.sub(r"```[\s\S]*?```", " ", md)
    md = re.sub(r"`([^`]+)`", r"\1", md)
    md = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", md)
    md = re.sub(r"\[\[([^\]]+)\]\]", r"\1", md)
    md = re.sub(r"#{1,6}\s+", "", md)
    md = re.sub(r"[*_~>`\-]+", " ", md)
    md = re.sub(r"\s+", " ", md)
    return md.strip()

def normalize_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        out = []
        for v in value:
            out.extend(normalize_list(v))
        return [x for x in dict.fromkeys(x for x in out if x)]
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()]
    return []

def heuristic_techniques(text: str, tags: List[str], explicit: List[str]) -> List[str]:
    kw = {
        "prefix sums": ["prefix sum", "prefix sums", "cumulative sum"],
        "binary search": ["binary search", "search on answer", "search the answer"],
        "dp": ["dp", "dynamic programming"],
        "greedy": ["greedy"],
        "two pointers": ["two pointer", "two pointers", "sliding window"],
        "monotonic stack": ["monotonic stack"],
        "monotonic queue": ["monotonic queue", "deque"],
        "segment tree": ["segment tree", "lazy propagation"],
        "fenwick tree": ["fenwick", "bit"],
        "dijkstra": ["dijkstra"],
        "bfs": ["bfs", "breadth first search"],
        "dfs": ["dfs", "depth first search"],
        "sqrt decomposition": ["sqrt decomposition", "block decomposition"],
        "bitmask dp": ["bitmask", "subset dp"],
        "hashing": ["rolling hash", "hashing", "hash "],
        "topological sort": ["topological sort", "dag"],
    }
    hay = text.lower()
    found = []
    for tech, variants in kw.items():
        if any(v in hay for v in variants):
            found.append(tech)
    return list(dict.fromkeys(normalize_list(explicit) + found + normalize_list(tags)))

def build_fingerprint(note: Dict[str, Any]) -> str:
    parts = []
    if note.get("type_hint"):
        parts.append(f"TYPE: {note['type_hint']}")
    if note.get("transform"):
        parts.append(f"TRANSFORM: {note['transform']}")
    if note.get("invariant"):
        parts.append(f"INVARIANT: {note['invariant']}")
    if note.get("techniques"):
        parts.append("TECHNIQUES: " + ", ".join(note["techniques"][:8]))
    if note.get("complexity"):
        parts.append(f"COMPLEXITY: {note['complexity']}")
    if note.get("pitfalls"):
        parts.append(f"PITFALLS: {note['pitfalls']}")
    return "\n".join(parts).strip()

def heuristic_analyze(path: str, title: str, text: str, frontmatter: Dict[str, Any], detail_level: str = "balanced") -> Dict[str, Any]:
    body = strip_frontmatter(text)
    title = frontmatter.get("title") or title or path.rsplit("/", 1)[-1].replace(".md", "").replace(".markdown", "")
    statement = extract_heading_block(body, ["Statement", "Problem", "Description", "Task"])
    solution = extract_heading_block(body, ["Solution", "Core Idea", "Approach", "Idea", "Explanation", "Analysis"])
    summary_source = statement or first_paragraphs(body, 2)
    solution_source = solution or first_paragraphs(body, 4)
    tags = list(dict.fromkeys(normalize_list(frontmatter.get("tags")) + extract_inline_tags(body)))
    techniques = heuristic_techniques(body, tags, frontmatter.get("techniques"))
    lang = str(frontmatter.get("language") or frontmatter.get("lang") or "unknown")
    type_hint = "unknown"
    hay = (title + " " + body).lower()
    if any(x in hay for x in ["range query", "interval", "subarray", "segment"]):
        type_hint = "range query"
    if any(x in hay for x in ["graph", "tree", "edge", "vertex", "dijkstra", "bfs", "dfs"]):
        type_hint = "graph/tree"
    if any(x in hay for x in ["string", "substring", "prefix", "suffix", "hash"]):
        type_hint = "string"
    transform = ""
    for c in ["prefix sums", "compress coordinates", "sort by", "binary search", "reduce to", "convert to", "model as", "split into blocks"]:
        if c in hay:
            transform = c
            break
    invariant = ""
    for c in ["monotonic", "greedy choice", "feasible", "maintain", "minimum", "maximum", "balance"]:
        if c in hay:
            invariant = c
            break
    complexity = ""
    m = re.search(r"o\(\s*[^)]*?\)", body, re.I)
    if m:
        complexity = m.group(0)
    if not complexity:
        complexity = frontmatter.get("complexity") or ""
    pitfalls = ""
    if any(x in hay for x in ["off by one", "boundary", "overflow", "index"]):
        pitfalls = "boundary / indexing issues"
    core_summary = summary_source[:700].strip()
    solution_summary = solution_source[:700].strip()
    if detail_level == "deep":
        core_summary = summary_source[:1200].strip()
        solution_summary = solution_source[:1200].strip()
    fingerprint = build_fingerprint({
        "type_hint": type_hint,
        "transform": transform,
        "invariant": invariant,
        "techniques": techniques,
        "complexity": complexity,
        "pitfalls": pitfalls,
    })
    return {
        "path": path,
        "title": title,
        "language": lang,
        "tags": tags,
        "techniques": techniques,
        "statement_summary": core_summary,
        "solution_summary": solution_summary,
        "fingerprint": fingerprint,
        "explicit_links": extract_links(body),
        "raw_text": markdown_to_text(body),
        "frontmatter": frontmatter,
        "type_hint": type_hint,
        "transform": transform,
        "invariant": invariant,
        "complexity": complexity,
        "pitfalls": pitfalls,
        "embedding": None,
        "analysis_source": "heuristic",
    }

def openai_chat_json(prompt: str, model: str) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = os.getenv("OPENAI_CHAT_URL", "https://api.openai.com/v1/chat/completions")
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You extract structured competitive-programming note metadata. "
                    "Return ONLY valid JSON with keys: title, language, tags, techniques, statement_summary, "
                    "solution_summary, type_hint, transform, invariant, complexity, pitfalls, fingerprint."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=90)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        # tolerate fenced JSON
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I | re.M)
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            return None
        return json.loads(content[start:end + 1])
    except Exception:
        return None

def openai_embedding(text: str, model: Optional[str] = None) -> Optional[List[float]]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    model = model or os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = os.getenv("OPENAI_EMBED_URL", "https://api.openai.com/v1/embeddings")
    try:
        r = requests.post(url, headers=headers, json={"model": model, "input": text[:12000]}, timeout=90)
        r.raise_for_status()
        data = r.json()
        return data["data"][0]["embedding"]
    except Exception:
        return None

def analyze_note(path: str, title: str, text: str, frontmatter: Dict[str, Any], use_ai: bool = True, detail_level: str = "balanced") -> Dict[str, Any]:
    heuristic = heuristic_analyze(path, title, text, frontmatter, detail_level)
    if not use_ai:
        return heuristic
    model = os.getenv("OPENAI_MODEL", "gpt-5.4")
    prompt = f"""
Analyze this markdown note from a competitive-programming vault.

File path: {path}
Title: {title}
Frontmatter: {json.dumps(frontmatter, ensure_ascii=False)}
Markdown:
{text[:16000]}

Return strict JSON only.
Requirements:
- title: short canonical title
- language: detected language
- tags: list of concise topic tags
- techniques: list of algorithmic techniques
- statement_summary: 1-3 concise paragraphs
- solution_summary: 1-3 concise paragraphs
- type_hint: short problem family
- transform: main reduction / transformation
- invariant: key invariant / condition
- complexity: asymptotic complexity
- pitfalls: main pitfall
- fingerprint: very compact idea fingerprint
"""
    ai = openai_chat_json(prompt, model)
    if not ai:
        return heuristic
    result = dict(heuristic)
    for k in ["title", "language", "statement_summary", "solution_summary", "type_hint", "transform", "invariant", "complexity", "pitfalls", "fingerprint"]:
        if ai.get(k):
            result[k] = ai[k]
    if ai.get("tags"):
        result["tags"] = list(dict.fromkeys(normalize_list(ai["tags"]) + result["tags"]))
    if ai.get("techniques"):
        result["techniques"] = list(dict.fromkeys(normalize_list(ai["techniques"]) + result["techniques"]))
    result["analysis_source"] = "openai"
    emb_text = "\n".join([
        result.get("title", ""),
        result.get("statement_summary", ""),
        result.get("solution_summary", ""),
        result.get("fingerprint", ""),
        "TECHNIQUES: " + ", ".join(result.get("techniques", [])),
        "TAGS: " + ", ".join(result.get("tags", [])),
    ]).strip()
    embedding = openai_embedding(emb_text)
    result["embedding"] = embedding
    return result

def cosine(a: Optional[List[float]], b: Optional[List[float]]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)

def jaccard(a: List[str], b: List[str]) -> float:
    A = set(x.lower() for x in a if x)
    B = set(x.lower() for x in b if x)
    if not A and not B:
        return 0.0
    return len(A & B) / len(A | B)

def tokenize(text: str) -> List[str]:
    stop = {
        "the","and","or","to","of","a","in","for","on","with","as","is","are","be","this","that","it","by","an","at","from","into","use","using","used","can","will","we","you","your","their",
        "problem","solution","idea","ideas","note","notes","core","approach","statement","given","then","than","also","may","must","should","all","each","every","new","old","more","less","when","where","which","what","how","why","while","between","within","without","have","has","had","but","not","only","if","else","just","over","under","same","different"
    }
    toks = re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).split()
    return [t for t in toks if len(t) > 1 and t not in stop]

def link_score(a: Dict[str, Any], b: Dict[str, Any], explicit_boost: float, use_title_path: bool) -> tuple[float, List[str]]:
    tag_sim = jaccard(a.get("tags", []), b.get("tags", []))
    tech_sim = jaccard(a.get("techniques", []), b.get("techniques", []))
    text_sim = cosine(None, None)
    if a.get("embedding") and b.get("embedding"):
        text_sim = cosine(a["embedding"], b["embedding"])
    else:
        text_sim = cosine_similarity_tokens(tokenize(a.get("raw_text", "") + " " + a.get("fingerprint", "")), tokenize(b.get("raw_text", "") + " " + b.get("fingerprint", "")))
    explicit = 1.0 if is_explicit_link(a, b) else 0.0
    title_boost = jaccard(tokenize(a.get("title", "") + " " + a.get("path", "")), tokenize(b.get("title", "") + " " + b.get("path", ""))) if use_title_path else 0.0
    score = explicit * explicit_boost + tag_sim * 0.22 + tech_sim * 0.38 + text_sim * 0.28 + title_boost * 0.12
    reasons = []
    if explicit:
        reasons.append("explicit link")
    if tag_sim > 0:
        reasons.append(f"tags {tag_sim:.2f}")
    if tech_sim > 0:
        reasons.append(f"techniques {tech_sim:.2f}")
    if text_sim > 0:
        reasons.append(f"semantic {text_sim:.2f}")
    if title_boost > 0:
        reasons.append(f"title/path {title_boost:.2f}")
    return score, reasons

def cosine_similarity_tokens(a_tokens: List[str], b_tokens: List[str]) -> float:
    ca, cb = Counter(a_tokens), Counter(b_tokens)
    dot = sum(ca[t] * cb[t] for t in ca.keys() & cb.keys())
    na = math.sqrt(sum(v * v for v in ca.values()))
    nb = math.sqrt(sum(v * v for v in cb.values()))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)

def is_explicit_link(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    links_a = {x.lower() for x in a.get("explicit_links", [])}
    links_b = {x.lower() for x in b.get("explicit_links", [])}
    title_a = str(a.get("title", "")).lower()
    title_b = str(b.get("title", "")).lower()
    id_a = str(a.get("id", "")).lower()
    id_b = str(b.get("id", "")).lower()
    return (title_b in links_a) or (title_a in links_b) or (id_b in links_a) or (id_a in links_b) or (slugify(title_b) in links_a) or (slugify(title_a) in links_b)

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"['\"]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

def make_graph(notes: List[Dict[str, Any]], top_k: int = 4, threshold: float = 0.18, explicit_boost: float = 0.55, use_title_path: bool = True) -> Dict[str, Any]:
    nodes = []
    edges = []
    rows = []
    n = len(notes)
    cols = max(1, math.ceil(math.sqrt(n or 1)))
    for i, note in enumerate(notes):
        x = (i % cols) * 380
        y = (i // cols) * 220
        node_id = note["id"]
        nodes.append({
            "id": node_id,
            "type": "file",
            "file": note["path"],
            "x": x,
            "y": y,
            "width": 320,
            "height": 160,
            "color": "4" if note.get("techniques") else "2",
        })
    edge_set = set()
    def add_edge(a_id: str, b_id: str, label: str, color: str = "4"):
        key = tuple(sorted([a_id, b_id]))
        if key in edge_set:
            return
        edge_set.add(key)
        edges.append({
            "id": f"e_{a_id}__{b_id}",
            "fromNode": a_id,
            "toNode": b_id,
            "fromEnd": "none",
            "toEnd": "arrow",
            "label": label,
            "color": color,
        })

    for i in range(n):
        for j in range(i + 1, n):
            a, b = notes[i], notes[j]
            score, reasons = link_score(a, b, explicit_boost, use_title_path)
            if score >= threshold:
                rows.append({"from": a["title"], "to": b["title"], "score": score, "why": ", ".join(reasons) or "similar"})
            a_id, b_id = a["id"], b["id"]
            # top-K enforced below; still store candidate score
            a.setdefault("_cands", []).append((score, b, reasons))
            b.setdefault("_cands", []).append((score, a, reasons))

    for note in notes:
        cands = sorted(note.get("_cands", []), key=lambda x: x[0], reverse=True)[:top_k]
        for score, other, reasons in cands:
            if score < threshold:
                continue
            label = "explicit" if "explicit link" in reasons else (reasons[0] if reasons else "similar")
            add_edge(note["id"], other["id"], label, "5" if "explicit link" in reasons else "4")

    canvas = {"nodes": nodes, "edges": edges}
    graph = {"nodes": nodes, "edges": edges}
    rows.sort(key=lambda x: x["score"], reverse=True)
    return {"graph": graph, "canvas": canvas, "rows": rows}

@app.get("/")
def index():
    return render_template_string(HTML)

@app.post("/api/analyze")
def api_analyze():
    payload = request.get_json(force=True)
    path = payload.get("path", "")
    title = payload.get("title", "")
    text = payload.get("text", "")
    frontmatter = payload.get("frontmatter") or {}
    use_ai = bool(payload.get("use_ai", True))
    detail_level = payload.get("detail_level", "balanced")
    analyzed = analyze_note(path, title, text, frontmatter, use_ai=use_ai, detail_level=detail_level)
    analyzed["id"] = slugify(analyzed["title"] or analyzed["path"])
    return jsonify(analyzed)

@app.post("/api/build")
def api_build():
    payload = request.get_json(force=True)
    notes = payload.get("notes", [])
    top_k = int(payload.get("top_k", 4))
    threshold = float(payload.get("threshold", 0.18))
    explicit_boost = float(payload.get("explicit_boost", 0.55))
    use_title_path = bool(payload.get("use_title_path", True))
    built = make_graph(notes, top_k=top_k, threshold=threshold, explicit_boost=explicit_boost, use_title_path=use_title_path)
    return jsonify(built)

@app.get("/health")
def health():
    return jsonify({"ok": True, "title": APP_TITLE})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
