    const exchangeSelect = document.getElementById("exchange-select")
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
                <tr>
                    <td class="px-4 py-2">${c.created_at}</td>
                    <td class="px-4 py-2">${(c.exchange_name || "").toUpperCase()}</td>
                    <td class="px-4 py-2">${c.label || ""}</td>
                    <td class="px-4 py-2">${c.client_id}</td>
                    <td class="px-4 py-2">${c.masked_secret}</td>
                    <td class="px-4 py-2 text-right">
                        <form action="/config/disconnect" method="post">
                            <input type="hidden" name="credentials_id" value="${c.id}">
                            <button type="submit" class="btn-inline btn-danger">Disconnect</button>
                        </form>
                    </td>
                </tr>
            `).join("")
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
