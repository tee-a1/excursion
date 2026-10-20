const STORAGE_KEY = "my-library";
const REMOVED_KEY = "my-library-removed";
const SHELF_PADDING = 32;
const SPINE_GAP = 3;
// Leather bindings: oxblood, bottle green, navy, tan, plum, ochre, umber, slate.
const SPINE_COLORS = ["#5c1d1d", "#1f3b2d", "#1b2a46", "#6e4a2a", "#47263a", "#7a5626", "#3a2a1f", "#2c3438"];

let books = load();
let currentShelf = "all";
let editingId = null;

const $ = (sel) => document.querySelector(sel);
const bookcase = $("#bookcase");
const dialog = $("#book-dialog");
const form = $("#book-form");

/* STORAGE */

function load() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    } catch {
        return [];
    }
}

function save() {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(books));
    } catch {
        // Storage unavailable (private mode etc.) – library still works for this session.
    }
}

// Books removed in the app that came from books.js, so they don't reappear on reload.
function removedSeeds() {
    try {
        return JSON.parse(localStorage.getItem(REMOVED_KEY)) || [];
    } catch {
        return [];
    }
}

function rememberRemoved(seedKey) {
    try {
        localStorage.setItem(REMOVED_KEY, JSON.stringify([...removedSeeds(), seedKey]));
    } catch {}
}

/* ISBN */

const cleanIsbn = (isbn) => String(isbn || "").replace(/[^0-9Xx]/g, "").toUpperCase();

// default=false makes Open Library 404 when it has no scan, so the spine shows instead of a blank image.
const isbnCover = (isbn) => `https://covers.openlibrary.org/b/isbn/${isbn}-L.jpg?default=false`;

// Look up title and author for many ISBNs in one request.
async function fetchIsbnDetails(isbns) {
    if (!isbns.length) return {};
    try {
        const keys = isbns.map((i) => `ISBN:${i}`).join(",");
        const data = await (await fetch(`https://openlibrary.org/api/books?bibkeys=${keys}&format=json&jscmd=data`)).json();
        const details = {};
        for (const isbn of isbns) {
            const entry = data[`ISBN:${isbn}`];
            if (entry) details[isbn] = { title: entry.title, author: (entry.authors || []).map((a) => a.name).join(", ") };
        }
        return details;
    } catch {
        return {};
    }
}

/* BOOKS.JS COLLECTION */

async function syncCollection() {
    if (typeof MY_BOOKS === "undefined") return;
    const removed = removedSeeds();
    let changed = false;

    for (const entry of MY_BOOKS) {
        const isbn = cleanIsbn(entry.isbn);
        const seedKey = isbn || `${entry.title}|${entry.author || ""}`.toLowerCase();
        if (removed.includes(seedKey)) continue;

        let book = books.find((b) => b.seedKey === seedKey);
        if (!book) {
            book = { id: crypto.randomUUID(), added: Date.now(), seedKey, title: "", author: "", status: "read", rating: 0, notes: "" };
            if (entry.status) book.status = entry.status;
            if (entry.rating) book.rating = entry.rating;
            books.push(book);
        }
        // books.js decides the edition details; shelf, rating and notes stay as set in the app.
        Object.assign(book, {
            isbn,
            format: entry.format || (isbn ? "hardcover" : "kindle"),
            title: entry.title || book.title || (isbn ? `ISBN ${isbn}` : ""),
            author: entry.author || book.author,
            cover: entry.cover || (isbn ? isbnCover(isbn) : book.cover),
            spine: entry.spine || book.spine,
            spineRatio: entry.spine ? entry.spineRatio || 0.16 : book.spineRatio,
        });
        changed = true;
    }
    if (!changed) return;
    save();
    render();

    const missing = books.filter((b) => b.seedKey && b.isbn && b.title === `ISBN ${b.isbn}`);
    const details = await fetchIsbnDetails(missing.map((b) => b.isbn));
    for (const book of missing) Object.assign(book, details[book.isbn] || {});
    if (Object.keys(details).length) {
        save();
        render();
    }
}

/* RENDERING */

function hashOf(text) {
    let hash = 0;
    for (const ch of text) hash = (hash * 31 + ch.charCodeAt(0)) | 0;
    return Math.abs(hash);
}

// Each book keeps the same binding, thickness and height every time it's drawn.
function spineFor(book) {
    const hash = hashOf(book.title + (book.author || ""));
    const height = 228 + ((hash >> 4) % 6) * 10;
    // A spine photo keeps its real proportions; otherwise thickness follows the title length.
    const width = book.spine && book.spineRatio
        ? Math.min(90, Math.max(24, height * Number(book.spineRatio)))
        : Math.min(68, Math.max(38, 26 + book.title.length * 1.1 + (hash % 4) * 3));
    return { color: SPINE_COLORS[hash % SPINE_COLORS.length], width: Math.round(width), height };
}

const surname = (author) => (author || "").split(",")[0].trim().split(/\s+/).pop() || "";

function visibleBooks() {
    const query = $("#filter").value.trim().toLowerCase();
    const sort = $("#sort").value;

    return books
        .filter((b) => currentShelf === "all" || b.status === currentShelf)
        .filter((b) => !query || `${b.title} ${b.author}`.toLowerCase().includes(query))
        .sort((a, b) => {
            if (sort === "title") return a.title.localeCompare(b.title);
            if (sort === "author") return (a.author || "").localeCompare(b.author || "");
            if (sort === "rating") return b.rating - a.rating;
            return b.added - a.added;
        });
}

function bookElement(book) {
    const spine = spineFor(book);
    const el = document.createElement("button");
    el.className = "book";
    el.title = `${book.title}${book.author ? " — " + book.author : ""}${book.format === "kindle" ? " (Kindle)" : ""}`;
    el.style.setProperty("--binding", spine.color);
    el.style.width = `${spine.width}px`;
    el.style.height = `${spine.height}px`;
    el.addEventListener("click", () => openDialog(book));

    el.innerHTML = `<span class="book__title"></span><span class="book__rating"></span><span class="book__author"></span>`;
    el.querySelector(".book__title").textContent = book.title;
    el.querySelector(".book__author").textContent = surname(book.author);
    el.querySelector(".book__rating").textContent = "✦".repeat(book.rating || 0);

    // Spine photo first, then the edition's cover art, then plain leather.
    if (book.spine) {
        el.classList.add("book--photo");
        el.style.backgroundImage = `url("${book.spine}")`;
    } else if (book.cover) {
        const probe = new Image();
        probe.onload = () => {
            el.classList.add("book--cover");
            el.style.setProperty("--cover", `url("${book.cover}")`);
        };
        probe.src = book.cover;
    }
    return el;
}

// Fill each shelf to the width of the bookcase, like books packed side by side.
function render() {
    const list = visibleBooks();
    bookcase.hidden = false;
    const shelfWidth = bookcase.clientWidth - SHELF_PADDING;
    bookcase.innerHTML = "";

    let shelf = null;
    let used = 0;
    for (const book of list) {
        const width = spineFor(book).width + SPINE_GAP;
        if (!shelf || used + width > shelfWidth) {
            shelf = document.createElement("div");
            shelf.className = "shelf";
            bookcase.append(shelf);
            used = 0;
        }
        shelf.append(bookElement(book));
        used += width;
    }

    $("#empty").hidden = list.length > 0;
    bookcase.hidden = list.length === 0;

    const count = (s) => books.filter((b) => b.status === s).length;
    $("#stats").textContent =
        `${books.length} volumes · ${count("reading")} reading · ${count("want")} to read · ${count("read")} read`;
}

let resizeTimer;
window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(render, 120);
});

function showCover(url) {
    const img = $("#dialog-cover");
    img.hidden = !url;
    if (url) img.src = url;
}

/* ADD / EDIT */

function openDialog(book = null) {
    editingId = book ? book.id : null;
    form.reset();
    $("#lookup-results").innerHTML = "";
    $("#lookup-query").value = "";
    $("#dialog-title").textContent = book ? "Edit book" : "Add a book";
    $("#delete-book").hidden = !book;
    delete $("#delete-book").dataset.armed;
    $("#delete-book").textContent = "Delete";

    if (book) {
        for (const key of ["isbn", "format", "title", "author", "cover", "spine", "spineRatio", "status", "rating", "notes"]) {
            form.elements[key].value = book[key] ?? "";
        }
        form.elements.format.value ||= "hardcover";
    } else if (currentShelf !== "all") {
        form.elements.status.value = currentShelf;
    }
    if (!book) form.elements.spine.value = form.elements.spineRatio.value = "";
    showSpine();
    showCover(form.elements.cover.value);
    dialog.showModal();
}

dialog.addEventListener("close", () => {
    if (dialog.returnValue !== "save") return;

    const data = Object.fromEntries(new FormData(form));
    data.title = data.title.trim();
    data.author = data.author.trim();
    data.isbn = cleanIsbn(data.isbn);
    data.spineRatio = Number(data.spineRatio) || 0;
    data.rating = Number(data.rating);
    if (!data.title) return;

    if (editingId) {
        Object.assign(books.find((b) => b.id === editingId), data);
    } else {
        books.push({ id: crypto.randomUUID(), added: Date.now(), ...data });
    }
    save();
    render();
});

// First click asks for confirmation on the button itself; the second click deletes.
$("#delete-book").addEventListener("click", (e) => {
    const book = books.find((b) => b.id === editingId);
    if (!book) return;
    if (!e.currentTarget.dataset.armed) {
        e.currentTarget.dataset.armed = "true";
        e.currentTarget.textContent = "Click again to delete";
        return;
    }
    if (book.seedKey) rememberRemoved(book.seedKey);
    books = books.filter((b) => b.id !== editingId);
    save();
    dialog.close();
    render();
});

/* OPEN LIBRARY LOOKUP */

async function lookup() {
    const query = $("#lookup-query").value.trim();
    const results = $("#lookup-results");
    if (!query) return;

    results.innerHTML = "<li>Searching…</li>";
    try {
        const url = `https://openlibrary.org/search.json?q=${encodeURIComponent(query)}&limit=8&fields=key,title,author_name,cover_i,first_publish_year`;
        const { docs } = await (await fetch(url)).json();
        results.innerHTML = docs.length ? "" : "<li>No matches found.</li>";

        for (const doc of docs) {
            const cover = doc.cover_i ? `https://covers.openlibrary.org/b/id/${doc.cover_i}-M.jpg` : "";
            const author = (doc.author_name || []).join(", ");
            const li = document.createElement("li");
            li.innerHTML = `<img alt=""><div><div class="t"></div><small></small></div>`;
            if (cover) li.querySelector("img").src = cover.replace("-M", "-S");
            li.querySelector(".t").textContent = doc.title;
            li.querySelector("small").textContent = [author, doc.first_publish_year].filter(Boolean).join(" · ");
            li.addEventListener("click", async () => {
                form.elements.title.value = doc.title;
                form.elements.author.value = author;
                form.elements.cover.value = cover.replace("-M", "-L");
                showCover(form.elements.cover.value);
                if (form.elements.format.value !== "hardcover") {
                    results.innerHTML = "";
                    return;
                }
                results.innerHTML = "<li>Looking for a hardcover edition…</li>";
                const hardcover = await findHardcoverCover(doc.key);
                if (hardcover) form.elements.cover.value = hardcover;
                showCover(form.elements.cover.value);
                results.innerHTML = hardcover
                    ? "<li>Using the hardcover cover art.</li>"
                    : "<li>No hardcover cover found — using the default cover.</li>";
            });
            results.append(li);
        }
    } catch {
        results.innerHTML = "<li>Couldn't reach Open Library — fill in the details manually.</li>";
    }
}

// Open Library groups every edition under a "work"; pick the first hardcover
// edition that has a scanned cover, preferring English-language editions.
async function findHardcoverCover(workKey) {
    if (!workKey) return "";
    try {
        const { entries = [] } = await (await fetch(`https://openlibrary.org${workKey}/editions.json?limit=100`)).json();
        const hardcovers = entries.filter(
            (e) => /hard\s*(cover|back)/i.test(e.physical_format || "") && e.covers?.some((id) => id > 0)
        );
        const isEnglish = (e) => (e.languages || []).some((l) => l.key === "/languages/eng");
        const best = hardcovers.find(isEnglish) || hardcovers[0];
        return best ? `https://covers.openlibrary.org/b/id/${best.covers.find((id) => id > 0)}-L.jpg` : "";
    } catch {
        return "";
    }
}

// Typing an ISBN pins the cover to that exact edition and fills in missing details.
form.elements.isbn.addEventListener("change", async () => {
    const isbn = cleanIsbn(form.elements.isbn.value);
    if (isbn.length !== 10 && isbn.length !== 13) return;
    form.elements.cover.value = isbnCover(isbn);
    showCover(form.elements.cover.value);
    const details = (await fetchIsbnDetails([isbn]))[isbn];
    if (!details) return;
    if (!form.elements.title.value) form.elements.title.value = details.title;
    if (!form.elements.author.value) form.elements.author.value = details.author;
});

/* SPINE PHOTO */

const SPINE_PHOTO_HEIGHT = 360;

function showSpine() {
    const url = form.elements.spine.value;
    $("#spine-preview").hidden = $("#spine-remove").hidden = !url;
    $("#spine-choose").textContent = url ? "Replace photo" : "Choose photo";
    if (url) $("#spine-preview").src = url;
}

// Shrink the photo so hundreds of spines still fit in browser storage.
$("#spine-file").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const img = new Image();
    img.onload = () => {
        const scale = SPINE_PHOTO_HEIGHT / img.naturalHeight;
        const canvas = document.createElement("canvas");
        canvas.height = SPINE_PHOTO_HEIGHT;
        canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
        canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
        form.elements.spine.value = canvas.toDataURL("image/jpeg", 0.8);
        form.elements.spineRatio.value = (img.naturalWidth / img.naturalHeight).toFixed(3);
        URL.revokeObjectURL(img.src);
        showSpine();
    };
    img.src = URL.createObjectURL(file);
    e.target.value = "";
});

$("#spine-remove").addEventListener("click", () => {
    form.elements.spine.value = form.elements.spineRatio.value = "";
    showSpine();
});

$("#dialog-cover").addEventListener("error", (e) => (e.target.hidden = true));
form.elements.cover.addEventListener("change", () => showCover(form.elements.cover.value));

$("#lookup-btn").addEventListener("click", lookup);
$("#lookup-query").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        lookup();
    }
});

/* EXPORT / IMPORT */

$("#export").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(books, null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "my-library.json";
    link.click();
    URL.revokeObjectURL(link.href);
});

$("#import").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
        const imported = JSON.parse(await file.text());
        if (!Array.isArray(imported)) throw new Error();
        books = imported;
        save();
        render();
    } catch {
        alert("That file doesn't look like a library export.");
    }
    e.target.value = "";
});

/* TOOLBAR */

document.querySelectorAll(".tab").forEach((tab) =>
    tab.addEventListener("click", () => {
        document.querySelector(".tab--active").classList.remove("tab--active");
        tab.classList.add("tab--active");
        currentShelf = tab.dataset.shelf;
        render();
    })
);

$("#filter").addEventListener("input", render);
$("#sort").addEventListener("change", render);
$("#add-book").addEventListener("click", () => openDialog());

render();
syncCollection();
