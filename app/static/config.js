const exchangeSelect = document.getElementById("exchange-select")
const escapeHtml = (value) => String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;")
const loadConfigData = () => {
    return fetch(`/config/data`, { credentials: "same-origin" })
}
const renderConfig = (data) => {
    if (!data || data.error) throw new Error("load_failed")
    const loading = document.getElementById("config-loading")
    const exchangeCount = document.getElementById("config-exchange-count")
    if (loading) loading.classList.add("hidden")
    const empty = document.getElementById("config-empty")
    const errorEl = document.getElementById("config-error")
    const table = document.getElementById("config-table")
    const body = document.getElementById("config-body")
    const credentials = data.credentials || []
    if (exchangeCount) exchangeCount.textContent = `${credentials.length}`
    if (exchangeCount) exchangeCount.classList.remove("loading-text")
    if (!credentials.length) {
        if (errorEl) errorEl.classList.add("hidden")
        if (empty) empty.classList.remove("hidden")
        if (table) table.classList.add("hidden")
        return
    }
    if (table) table.classList.remove("hidden")
    if (body) {
        body.innerHTML = credentials.map((c) => `
            <tr data-config-row-id="${c.id}">
                <td class="px-4 py-2">${escapeHtml(c.created_at)}</td>
                <td class="px-4 py-2">${escapeHtml((c.exchange_name || "").toUpperCase())}</td>
                <td class="px-4 py-2">${escapeHtml(c.label || "")}</td>
                <td class="px-4 py-2" data-config-api-key-view>${escapeHtml(c.client_id || "")}</td>
                <td class="px-4 py-2" data-config-secret-view>${escapeHtml(c.masked_secret || "")}</td>
                <td class="px-4 py-2 text-right">
                    <div class="flex items-center justify-end gap-2" data-config-actions-view>
                        <button type="button" class="btn-inline" data-config-modify-toggle="${c.id}">Modify</button>
                        <form action="/config/disconnect" method="post">
                            <input type="hidden" name="credentials_id" value="${c.id}">
                            <button type="submit" class="btn-inline btn-danger">Disconnect</button>
                        </form>
                    </div>
                    <form action="/config/modify" method="post" class="hidden" data-config-edit-form="${c.id}">
                        <input type="hidden" name="credentials_id" value="${c.id}">
                        <div class="flex items-center justify-end gap-2">
                            <button type="submit" class="btn-inline">Save</button>
                            <button type="button" class="btn-inline btn-danger" data-config-edit-cancel="${c.id}">Cancel</button>
                        </div>
                    </form>
                </td>
            </tr>
        `).join("")
        credentials.forEach((c) => {
            const row = body.querySelector(`[data-config-row-id="${c.id}"]`)
            if (!row) return
            const toggleBtn = row.querySelector(`[data-config-modify-toggle="${c.id}"]`)
            const cancelBtn = row.querySelector(`[data-config-edit-cancel="${c.id}"]`)
            const form = row.querySelector(`[data-config-edit-form="${c.id}"]`)
            const keyCell = row.querySelector("[data-config-api-key-view]")
            const secretCell = row.querySelector("[data-config-secret-view]")
            const actionView = row.querySelector("[data-config-actions-view]")
            if (!toggleBtn || !cancelBtn || !form || !keyCell || !secretCell || !actionView) return
            const openEdit = () => {
                keyCell.innerHTML = `<input type="text" name="api_key" required class="input w-full" form="${form.id}">`
                secretCell.innerHTML = `<input type="password" name="api_secret" required class="input w-full" form="${form.id}">`
                const keyInput = keyCell.querySelector("input")
                const secretInput = secretCell.querySelector("input")
                if (keyInput) keyInput.value = c.client_id || ""
                if (secretInput) secretInput.value = ""
                actionView.classList.add("hidden")
                form.classList.remove("hidden")
            }
            const closeEdit = () => {
                keyCell.textContent = c.client_id || ""
                secretCell.textContent = c.masked_secret || ""
                form.classList.add("hidden")
                actionView.classList.remove("hidden")
            }
            form.id = `config-edit-form-${c.id}`
            toggleBtn.addEventListener("click", openEdit)
            cancelBtn.addEventListener("click", closeEdit)
        })
    }
    document.querySelectorAll(".loading-text").forEach((el) => el.classList.remove("loading-text"))
}
const loadAndRender = () => {
    const loading = document.getElementById("config-loading")
    const empty = document.getElementById("config-empty")
    const errorEl = document.getElementById("config-error")
    const table = document.getElementById("config-table")
    if (loading) loading.classList.remove("hidden")
    if (empty) empty.classList.add("hidden")
    if (errorEl) errorEl.classList.add("hidden")
    if (table) table.classList.add("hidden")
    loadConfigData()
        .then((res) => res.ok ? res.json() : Promise.reject(res))
        .then(renderConfig)
        .catch(() => {
            if (loading) loading.classList.add("hidden")
            if (errorEl) errorEl.classList.remove("hidden")
        })
}
loadAndRender()
if (exchangeSelect) {
    exchangeSelect.addEventListener("change", () => {
        loadAndRender()
    })
}
