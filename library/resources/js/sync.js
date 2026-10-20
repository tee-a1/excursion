// Keeps the library in step across devices through Supabase. Each book is one
// row; whichever copy was edited last wins, and deletions travel as tombstones
// so other devices drop the book too.
const PENDING_DELETES_KEY = "my-library-pending-deletes";

const db = SUPABASE_URL && SUPABASE_KEY && window.supabase
    ? window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY)
    : null;

let session = null;
let syncing = false;
let syncAgain = false;
let applyingRemote = false;
let syncTimer;

/* STATUS */

function setStatus(text) {
    $("#sync-status").textContent = text;
}

function renderAccount() {
    $("#sync").hidden = !db;
    $("#sync-signin").hidden = !!session;
    $("#sync-signout").hidden = !session;
    if (!session) setStatus("Saved on this device only.");
}

/* PENDING DELETES (kept until the server has them) */

function pendingDeletes() {
    try {
        return JSON.parse(localStorage.getItem(PENDING_DELETES_KEY)) || [];
    } catch {
        return [];
    }
}

function setPendingDeletes(list) {
    try {
        localStorage.setItem(PENDING_DELETES_KEY, JSON.stringify(list));
    } catch {}
}

/* SYNC */

async function sync() {
    if (!db || !session) return;
    if (syncing) {
        syncAgain = true;
        return;
    }
    syncing = true;
    setStatus("Syncing…");

    try {
        const pending = pendingDeletes();
        if (pending.length) {
            const { error } = await db.from("books").upsert(
                pending.map((p) => ({ id: p.id, data: p.data, updated: p.updated, deleted: true }))
            );
            if (error) throw error;
            setPendingDeletes([]);
        }

        const { data: rows, error } = await db.from("books").select("id, data, updated, deleted");
        if (error) throw error;
        const remote = new Map(rows.map((r) => [r.id, r]));
        let changed = false;

        for (const row of remote.values()) {
            // A book that only exists here may be another device's copy of this row.
            const match = (b) => b.id === row.id || (!remote.has(b.id) && sameBook(b, row.data));

            if (row.deleted) {
                const before = books.length;
                books = books.filter((b) => !match(b));
                if (books.length !== before) changed = true;
                if (row.data?.seedKey) rememberRemoved(row.data.seedKey);
                continue;
            }

            const local = books.find(match);
            if (!local) {
                books.push({ ...row.data, id: row.id });
                changed = true;
            } else if ((row.updated || 0) >= (local.updated || 0)) {
                if (local.id !== row.id || JSON.stringify(local) !== JSON.stringify({ ...row.data, id: row.id })) {
                    books[books.indexOf(local)] = { ...row.data, id: row.id };
                    changed = true;
                }
            } else if (local.id !== row.id) {
                local.id = row.id; // newer here: keep it and push it below
                changed = true;
            }
        }

        const outgoing = books.filter((b) => {
            const row = remote.get(b.id);
            return !row || (!row.deleted && (b.updated || 0) > (row.updated || 0));
        });
        if (outgoing.length) {
            for (const b of outgoing) b.updated ||= b.added || Date.now();
            const { error: pushError } = await db.from("books").upsert(
                outgoing.map((b) => ({ id: b.id, data: b, updated: b.updated, deleted: false }))
            );
            if (pushError) throw pushError;
            changed = true;
        }

        if (changed) {
            applyingRemote = true;
            save();
            applyingRemote = false;
            render();
        }
        setStatus(`Synced as ${session.user.email}.`);
    } catch (err) {
        console.error("Sync failed", err);
        setStatus(navigator.onLine ? "Couldn't sync just now; will try again." : "Offline; changes will sync later.");
    } finally {
        syncing = false;
        if (syncAgain) {
            syncAgain = false;
            sync();
        }
    }
}

function queueSync(delay = 1200) {
    clearTimeout(syncTimer);
    syncTimer = setTimeout(sync, delay);
}

window.librarySync = {
    changed() {
        if (!applyingRemote && session) queueSync();
    },
    deleted(book) {
        if (!session) return;
        setPendingDeletes([...pendingDeletes(), { id: book.id, updated: Date.now(), data: book }]);
        queueSync();
    },
};

/* SIGN IN (email code, so it also works from a home-screen app) */

const syncDialog = $("#sync-dialog");
let codeSentTo = "";

function showSyncStep(sent) {
    $("#sync-email-field").hidden = sent;
    $("#sync-code-field").hidden = !sent;
    $("#sync-email").required = !sent;
    $("#sync-code").required = sent;
    $("#sync-submit").textContent = sent ? "Sign in" : "Send code";
    $("#sync-intro").textContent = sent
        ? `We sent a code to ${codeSentTo}. Enter it here, or open the link in the email on this device.`
        : "Enter your email. We'll send a sign-in link and a 6-digit code.";
}

function showSyncError(text) {
    $("#sync-error").hidden = !text;
    $("#sync-error").textContent = text || "";
}

$("#sync-signin").addEventListener("click", () => {
    codeSentTo = "";
    $("#sync-form").reset();
    showSyncError("");
    showSyncStep(false);
    syncDialog.showModal();
});

$("#sync-cancel").addEventListener("click", () => syncDialog.close());

$("#sync-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    showSyncError("");
    $("#sync-submit").disabled = true;
    try {
        if (!codeSentTo) {
            const email = $("#sync-email").value.trim();
            const { error } = await db.auth.signInWithOtp({
                email,
                options: { emailRedirectTo: location.origin + location.pathname },
            });
            if (error) throw error;
            codeSentTo = email;
            showSyncStep(true);
        } else {
            const { error } = await db.auth.verifyOtp({
                email: codeSentTo,
                token: $("#sync-code").value.trim(),
                type: "email",
            });
            if (error) throw error;
            syncDialog.close();
        }
    } catch (err) {
        showSyncError(err.message || "Something went wrong. Check your connection and try again.");
    } finally {
        $("#sync-submit").disabled = false;
    }
});

$("#sync-signout").addEventListener("click", async () => {
    await db.auth.signOut();
});

if (db) {
    db.auth.onAuthStateChange((event, newSession) => {
        session = newSession;
        renderAccount();
        // Supabase asks not to call it from inside this callback, so sync just after.
        if (session && (event === "SIGNED_IN" || event === "INITIAL_SESSION")) setTimeout(sync, 0);
    });
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") sync();
    });
    window.addEventListener("online", () => sync());
}
renderAccount();
