    const dashboardData = JSON.parse(document.getElementById("dashboard-data")?.textContent || "{}")
    const formatUsd = (value) => new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(Number(value) || 0)
    const formatSignedUsd = (value) => {
        const num = Number(value) || 0
        if (num > 0) return `+${formatUsd(num)}`
        return formatUsd(num)
    }
    const formatNumber = (value) => Number(value || 0).toFixed(2)
    const formatSignedPercent = (value) => {
        const num = Number(value) || 0
        if (num > 0) return `+${formatNumber(num)}%`
        if (num < 0) return `-${formatNumber(Math.abs(num))}%`
        return `${formatNumber(0)}%`
    }
    const upper = (value) => String(value || "").toUpperCase()
    const setupClosedTableSorting = () => {
        const table = document.getElementById("historical-closed-table")
        const body = document.getElementById("historical-closed-body")
        if (!table || !body) return
        const headers = Array.from(table.querySelectorAll("[data-sort-key]"))
        if (!headers.length) return
        const typeByKey = {
            start: "date",
            stop: "date",
            name: "text",
            exchange: "text",
            starting_capital_usdc: "number",
            fees_usdc: "number",
            pnl_usdc: "number",
            apr_percent: "number",
        }
        const state = { key: "stop", dir: "desc" }
        const getValue = (row, index, type) => {
            const cell = row.children[index]
            if (!cell) return type === "number" ? 0 : ""
            const raw = cell.getAttribute("data-value") ?? cell.textContent.trim()
            if (type === "number") return Number(raw) || 0
            if (type === "date") return raw ? new Date(raw).getTime() : 0
            return raw.toString().toLowerCase()
        }
        const updateIndicators = () => {
            headers.forEach((btn) => {
                const indicator = btn.querySelector("[data-sort-indicator]")
                if (!indicator) return
                indicator.textContent = btn.dataset.sortKey === state.key ? (state.dir === "asc" ? "▲" : "▼") : ""
            })
        }
        const sortRows = () => {
            const key = state.key
            const th = table.querySelector(`[data-sort-key="${key}"]`)?.closest("th")
            if (!th) return
            const index = Array.from(th.parentNode.children).indexOf(th)
            const type = typeByKey[key] || "text"
            const rows = Array.from(body.querySelectorAll("tr"))
            rows.sort((a, b) => {
                const av = getValue(a, index, type)
                const bv = getValue(b, index, type)
                if (av < bv) return state.dir === "asc" ? -1 : 1
                if (av > bv) return state.dir === "asc" ? 1 : -1
                return 0
            })
            rows.forEach((row) => body.appendChild(row))
        }
        headers.forEach((btn) => {
            btn.addEventListener("click", () => {
                const key = btn.dataset.sortKey
                if (!key) return
                if (state.key === key) {
                    state.dir = state.dir === "asc" ? "desc" : "asc"
                } else {
                    state.key = key
                    state.dir = key === "stop" ? "desc" : "asc"
                }
                updateIndicators()
                sortRows()
            })
        })
        updateIndicators()
        sortRows()
    }
    const renderChart = ({ prefix, series, legendSeries, min, max, dates, selectedKey, onLegendClick }) => {
        const loadingEl = document.getElementById(`${prefix}-loading`)
        if (loadingEl) loadingEl.classList.add("hidden")
        const emptyEl = document.getElementById(`${prefix}-empty`)
        const chartEl = document.getElementById(`${prefix}-chart`)
        const displaySeries = series || []
        const fullSeries = legendSeries || displaySeries
        if (!displaySeries || displaySeries.length === 0) {
            if (emptyEl) emptyEl.classList.remove("hidden")
            return
        }
        if (chartEl) chartEl.classList.remove("hidden")
        const linesEl = document.getElementById(`${prefix}-lines`)
        if (linesEl) linesEl.innerHTML = ""
        const axesEl = document.getElementById(`${prefix}-axes`)
        if (axesEl) axesEl.innerHTML = ""
        const svg = chartEl ? chartEl.querySelector("svg") : null
        const svgRect = svg ? svg.getBoundingClientRect() : { width: 0, height: 0 }
        const renderWidth = Math.max(1, Math.round(svgRect.width))
        const renderHeight = Math.max(1, Math.round(svgRect.height))
        const padding = 20
        if (svg) {
            svg.setAttribute("viewBox", `0 0 ${renderWidth} ${renderHeight}`)
        }
        const highlightKey = selectedKey ? String(selectedKey) : (displaySeries.find((item) => item.key === "all") ? "all" : String(displaySeries[0].key))
        const ticks = [min, (min + max) / 2, max]
        const measureText = (() => {
            const canvas = document.createElement("canvas")
            const ctx = canvas.getContext("2d")
            return (text) => {
                if (!ctx) return String(text || "").length * 6
                ctx.font = "8px Inter, sans-serif"
                return ctx.measureText(text).width
            }
        })()
        const maxLabelWidth = Math.max(...ticks.map((value) => measureText(value.toFixed(2))))
        const leftPadding = Math.max(padding, Math.ceil(maxLabelWidth + 12))
        const palette = ["#6d28d9", "#2563eb", "#0ea5e9", "#10b981", "#f59e0b", "#f97316", "#ef4444", "#ec4899"]
        const ordered = []
        const highlighted = []
        const colorByKey = {}
        let paletteIndex = 0
        fullSeries.forEach((item) => {
            if (item.key === "all") {
                colorByKey[item.key] = "#ffffff"
                return
            }
            colorByKey[item.key] = palette[paletteIndex % palette.length]
            paletteIndex += 1
        })
        displaySeries.forEach((item) => {
            const isHighlighted = String(item.key) === highlightKey
            if (isHighlighted) {
                highlighted.push(item)
            } else {
                ordered.push(item)
            }
        })
        const colorFor = (item) => {
            if (item.key === "all") {
                return "#ffffff"
            }
            return colorByKey[item.key] || "#ffffff"
        }
        const buildPoints = (values = [], dateList = []) => {
            const count = values.length
            if (!count) return ""
            const dateValues = (dateList || []).map((value) => {
                const parsed = new Date(value)
                const time = parsed.getTime()
                return Number.isNaN(time) ? null : time
            })
            const hasDates = dateValues.filter((value) => value !== null).length >= 2
            let minDate = null
            let maxDate = null
            if (hasDates) {
                const filtered = dateValues.filter((value) => value !== null)
                minDate = Math.min(...filtered)
                maxDate = Math.max(...filtered)
            }
            const totalDays = hasDates ? Math.max(0, (maxDate - minDate) / (1000 * 60 * 60 * 24)) : 0
            const step = count === 1 ? 0 : (renderWidth - leftPadding - padding) / (count - 1)
            const points = []
            values.forEach((value, idx) => {
                let x = leftPadding + step * idx
                if (hasDates && dateValues[idx] !== null && totalDays > 0) {
                    const ratio = (dateValues[idx] - minDate) / (totalDays * 24 * 60 * 60 * 1000)
                    x = leftPadding + ratio * (renderWidth - leftPadding - padding)
                }
                const ratio = max === min ? 0 : (value - min) / (max - min)
                const y = renderHeight - padding - ratio * (renderHeight - padding * 2)
                points.push(`${x.toFixed(1)},${y.toFixed(1)}`)
            })
            return points.join(" ")
        }
        const drawAxis = () => {
            if (!axesEl || displaySeries.length === 0) return
            const axisColor = "rgba(255, 255, 255, 0.6)"
            const xAxis = document.createElementNS("http://www.w3.org/2000/svg", "line")
            xAxis.setAttribute("x1", leftPadding)
            xAxis.setAttribute("y1", renderHeight - padding)
            xAxis.setAttribute("x2", renderWidth - padding)
            xAxis.setAttribute("y2", renderHeight - padding)
            xAxis.setAttribute("stroke", axisColor)
            xAxis.setAttribute("stroke-width", 1)
            axesEl.appendChild(xAxis)
            const yAxis = document.createElementNS("http://www.w3.org/2000/svg", "line")
            yAxis.setAttribute("x1", leftPadding)
            yAxis.setAttribute("y1", padding)
            yAxis.setAttribute("x2", leftPadding)
            yAxis.setAttribute("y2", renderHeight - padding)
            yAxis.setAttribute("stroke", axisColor)
            yAxis.setAttribute("stroke-width", 1)
            axesEl.appendChild(yAxis)
            ticks.forEach((value) => {
                const ratio = max === min ? 0 : (value - min) / (max - min)
                const y = renderHeight - padding - ratio * (renderHeight - padding * 2)
                const tick = document.createElementNS("http://www.w3.org/2000/svg", "line")
                tick.setAttribute("x1", leftPadding - 4)
                tick.setAttribute("y1", y)
                tick.setAttribute("x2", leftPadding)
                tick.setAttribute("y2", y)
                tick.setAttribute("stroke", axisColor)
                tick.setAttribute("stroke-width", 1)
                axesEl.appendChild(tick)
                const label = document.createElementNS("http://www.w3.org/2000/svg", "text")
                label.setAttribute("x", leftPadding - 8)
                label.setAttribute("y", y + 3)
                label.setAttribute("fill", axisColor)
                label.setAttribute("font-size", "10")
                label.setAttribute("text-anchor", "end")
                label.textContent = `${value.toFixed(2)}`
                axesEl.appendChild(label)
            })
            if (min <= 0 && max >= 0) {
                const zeroRatio = max === min ? 0 : (0 - min) / (max - min)
                const yZero = renderHeight - padding - zeroRatio * (renderHeight - padding * 2)
                const zeroLine = document.createElementNS("http://www.w3.org/2000/svg", "line")
                zeroLine.setAttribute("x1", leftPadding)
                zeroLine.setAttribute("y1", yZero)
                zeroLine.setAttribute("x2", renderWidth - padding)
                zeroLine.setAttribute("y2", yZero)
                zeroLine.setAttribute("stroke", axisColor)
                zeroLine.setAttribute("stroke-width", 1)
                zeroLine.setAttribute("stroke-dasharray", "3,3")
                axesEl.appendChild(zeroLine)
            }
            const pointDates = (displaySeries[0]?.dates && displaySeries[0].dates.length >= 2) ? displaySeries[0].dates : (dates || [])
            if (pointDates.length >= 2) {
                const labelCount = Math.max(2, Math.min(5, Math.floor(renderWidth / 180) + 1))
                const indices = new Set()
                for (let i = 0; i < labelCount; i += 1) {
                    const index = Math.round((i / (labelCount - 1)) * (pointDates.length - 1))
                    indices.add(index)
                }
                const sorted = Array.from(indices).sort((a, b) => a - b)
                const values = (displaySeries[0]?.values || [])
                const points = buildPoints(values, pointDates).split(" ")
                sorted.forEach((index, position) => {
                    const dateLabel = pointDates[index]
                    if (!dateLabel) return
                    const pair = points[index] || ""
                    const x = Number(pair.split(",")[0]) || padding
                    const y = renderHeight - padding + 10
                    const label = document.createElementNS("http://www.w3.org/2000/svg", "text")
                    label.setAttribute("x", x)
                    label.setAttribute("y", y)
                    label.setAttribute("fill", axisColor)
                    label.setAttribute("font-size", "10")
                    if (position === 0) {
                        label.setAttribute("text-anchor", "start")
                    } else if (position === sorted.length - 1) {
                        label.setAttribute("text-anchor", "end")
                    } else {
                        label.setAttribute("text-anchor", "middle")
                    }
                    label.textContent = dateLabel
                    axesEl.appendChild(label)
                })
            }
        }
        const draw = (item) => {
            if (!linesEl) return
            const line = document.createElementNS("http://www.w3.org/2000/svg", "polyline")
            const isAggregate = item.key === "all"
            const isHighlighted = String(item.key) === highlightKey
            const color = colorFor(item)
            const opacity = isAggregate ? 1 : (isHighlighted ? 1 : selectedKey ? 0.2 : 0.3)
            const width = 1.5
            const points = buildPoints(item.values || [], item.dates || dates || [])
            line.setAttribute("fill", "none")
            line.setAttribute("stroke", color)
            line.setAttribute("stroke-width", width)
            line.setAttribute("stroke-opacity", opacity)
            line.setAttribute("points", points)
            linesEl.appendChild(line)
        }
        ordered.forEach((item) => draw(item))
        highlighted.forEach((item) => draw(item))
        drawAxis()
        const legendEl = document.getElementById(`${prefix}-legend`)
        if (legendEl) legendEl.innerHTML = ""
        fullSeries.forEach((item) => {
            if (!legendEl) return
            const legendItem = document.createElement("div")
            legendItem.className = "equity-legend-item cursor-pointer"
            if (selectedKey && String(item.key) !== String(selectedKey)) {
                legendItem.classList.add("opacity-50")
            }
            const swatch = document.createElement("span")
            swatch.className = "equity-legend-swatch"
            swatch.style.backgroundColor = colorFor(item)
            const label = document.createElement("span")
            label.textContent = item.label
            legendItem.appendChild(swatch)
            legendItem.appendChild(label)
            if (onLegendClick) {
                legendItem.addEventListener("click", () => onLegendClick(item))
            }
            legendEl.appendChild(legendItem)
        })
        const tooltip = document.getElementById(`${prefix}-tooltip`)
        const focusSeries = displaySeries.find((item) => String(item.key) === highlightKey) || displaySeries[0]
        const focusPoints = buildPoints(focusSeries?.values || [], focusSeries?.dates || dates || [])
        const points = focusPoints.trim().split(" ").filter(Boolean)
        if (tooltip && svg && points.length > 0) {
            const coords = points.map((point) => {
                const [x, y] = point.split(",").map((value) => parseFloat(value))
                return { x, y }
            })
            const seriesValues = focusSeries.values || []
            let marker = svg.querySelector(`#${prefix}-marker`)
            if (!marker) {
                marker = document.createElementNS("http://www.w3.org/2000/svg", "circle")
                marker.setAttribute("id", `${prefix}-marker`)
                marker.setAttribute("r", "3")
                marker.setAttribute("fill", "#F5F5F0")
                marker.setAttribute("stroke", "#111111")
                marker.setAttribute("stroke-width", "1.5")
                svg.appendChild(marker)
            }
            const showTooltip = (index) => {
                const point = coords[index]
                if (!point) return
                let value = seriesValues[index]
                if (value === undefined || value === null) {
                const ratio = max === min ? 0 : (renderHeight - padding - point.y) / (renderHeight - padding * 2)
                    value = min + ratio * (max - min)
                }
                const dateList = focusSeries.dates || dates || []
                const dateLabel = dateList[index] || ""
                const seriesLabel = focusSeries.label || String(focusSeries.key) || "Series"
                tooltip.innerHTML = `<div>${seriesLabel} · ${dateLabel}</div><div class="num">${formatUsd(value)}</div>`
                const rect = svg.getBoundingClientRect()
                const scaleX = rect.width / renderWidth
                const scaleY = rect.height / renderHeight
                const px = point.x * scaleX
                const py = point.y * scaleY
                tooltip.style.left = `${px + 8}px`
                tooltip.style.top = `${py - 8}px`
                tooltip.classList.remove("hidden")
                marker.setAttribute("cx", `${point.x}`)
                marker.setAttribute("cy", `${point.y}`)
                marker.setAttribute("opacity", "1")
            }
            const hideTooltip = () => {
                tooltip.classList.add("hidden")
                marker.setAttribute("opacity", "0")
            }
            svg.addEventListener("mousemove", (event) => {
                const rect = svg.getBoundingClientRect()
                const x = event.clientX - rect.left
                let nearest = 0
                let nearestDist = Infinity
                coords.forEach((point, index) => {
                    const dist = Math.abs(point.x - x)
                    if (dist < nearestDist) {
                        nearestDist = dist
                        nearest = index
                    }
                })
                showTooltip(nearest)
            })
            svg.addEventListener("mouseleave", hideTooltip)
        }
    }
    const bindMaxButtons = (root = document) => {
        root.querySelectorAll("[data-max-button]").forEach((button) => {
            if (button.dataset.bound) return
            button.dataset.bound = "1"
            button.addEventListener("click", () => {
                const wrapper = button.closest("[data-max-wrapper]")
                const input = wrapper ? wrapper.querySelector("[data-max-input]") : null
                if (input) {
                    const maxValue = input.getAttribute("max")
                    if (maxValue) input.value = maxValue
                }
            })
        })
    }
    const applyToggleState = (form, action) => {
        form.dataset.action = action
        const actionTarget = action === "add" ? form.dataset.addAction : form.dataset.removeAction
        const nameTarget = action === "add" ? form.dataset.addName : form.dataset.removeName
        const maxTarget = action === "add" ? form.dataset.addMax : form.dataset.removeMax
        const availableTarget = action === "add" ? form.dataset.addAvailable : form.dataset.removeAvailable
        const input = form.querySelector("[data-amount-input]")
        const available = form.querySelector("[data-available-value]")
        if (actionTarget) form.setAttribute("action", actionTarget)
        if (input) {
            input.setAttribute("name", nameTarget || "")
            if (maxTarget) input.setAttribute("max", maxTarget)
        }
        if (available && availableTarget) available.textContent = availableTarget
        form.querySelectorAll("[data-action-toggle]").forEach((toggle) => {
            const isActive = toggle.getAttribute("data-action-toggle") === action
            toggle.classList.toggle("toggle-active", isActive)
        })
    }
    const bindAmountForms = (root = document) => {
        root.querySelectorAll("[data-amount-form]").forEach((form) => {
            if (form.dataset.bound) return
            form.dataset.bound = "1"
            applyToggleState(form, form.dataset.action || "add")
            form.querySelectorAll("[data-action-toggle]").forEach((toggle) => {
                toggle.addEventListener("click", () => {
                    applyToggleState(form, toggle.getAttribute("data-action-toggle"))
                })
            })
        })
    }
    const bindSubmitFeedback = (root = document) => {
        root.querySelectorAll("form[data-submit-feedback]").forEach((form) => {
            if (form.dataset.submitBound) return
            form.dataset.submitBound = "1"
            form.addEventListener("submit", () => {
                if (form.dataset.confirmForm && form.dataset.confirmed !== "1") return
                const status = form.querySelector("[data-submit-status]")
                const button = form.querySelector("button[type='submit']")
                if (status) {
                    status.textContent = "Submitting..."
                    status.classList.remove("hidden")
                }
                if (button) {
                    button.disabled = true
                    button.classList.add("opacity-70")
                }
            })
        })
    }
    const confirmModal = document.querySelector("[data-confirm-modal]")
    const confirmAction = confirmModal ? confirmModal.querySelector("[data-confirm-action]") : null
    const confirmStrategy = confirmModal ? confirmModal.querySelector("[data-confirm-strategy]") : null
    const confirmExchange = confirmModal ? confirmModal.querySelector("[data-confirm-exchange]") : null
    const confirmAsset = confirmModal ? confirmModal.querySelector("[data-confirm-asset]") : null
    const confirmAmount = confirmModal ? confirmModal.querySelector("[data-confirm-amount]") : null
    const confirmQuote = confirmModal ? confirmModal.querySelector("[data-confirm-quote]") : null
    const confirmCancel = confirmModal ? confirmModal.querySelector("[data-confirm-cancel]") : null
    const confirmAccept = confirmModal ? confirmModal.querySelector("[data-confirm-accept]") : null
    let pendingForm = null
    const setRow = (key, value) => {
        const row = confirmModal ? confirmModal.querySelector(`[data-confirm-row="${key}"]`) : null
        if (!row) return
        if (value) {
            row.classList.remove("hidden")
        } else {
            row.classList.add("hidden")
        }
    }
    const actionLabel = (form) => {
        const raw = (form.dataset.confirmAction || form.dataset.action || "").toLowerCase()
        if (raw === "start") return "Start strategy"
        if (raw === "stop") return "Stop strategy"
        if (raw === "remove") return "Remove capital"
        return "Add capital"
    }
    const openConfirm = (form) => {
        if (!confirmModal) return
        const strategyName = form.dataset.strategyName || "Strategy"
        const exchangeName = form.dataset.exchangeName || ""
        const asset = form.dataset.asset || ""
        const quote = form.dataset.quoteCurrency || "USDC"
        const amountInput = form.querySelector("[data-amount-input]") || form.querySelector("input[name='capital_usdc']")
        const amountValue = amountInput ? amountInput.value : ""
        if (confirmAction) confirmAction.textContent = actionLabel(form)
        if (confirmStrategy) confirmStrategy.textContent = strategyName
        if (confirmExchange) confirmExchange.textContent = exchangeName ? upper(exchangeName) : "-"
        if (confirmAsset) confirmAsset.textContent = asset ? upper(asset) : "-"
        if (confirmAmount) confirmAmount.textContent = amountValue || "-"
        if (confirmQuote) confirmQuote.textContent = amountValue ? quote : ""
        setRow("action", true)
        setRow("strategy", true)
        setRow("exchange", true)
        setRow("asset", true)
        setRow("amount", Boolean(amountValue))
        confirmModal.classList.remove("hidden")
        confirmModal.classList.add("flex")
        pendingForm = form
    }
    const resetSubmitState = (form) => {
        if (!form) return
        const status = form.querySelector("[data-submit-status]")
        const button = form.querySelector("button[type='submit']")
        if (status) {
            status.textContent = ""
            status.classList.add("hidden")
        }
        if (button) {
            button.disabled = false
            button.classList.remove("opacity-70")
        }
    }
    const closeConfirm = () => {
        if (!confirmModal) return
        if (pendingForm) resetSubmitState(pendingForm)
        confirmModal.classList.add("hidden")
        confirmModal.classList.remove("flex")
        pendingForm = null
    }
    if (confirmCancel) {
        confirmCancel.addEventListener("click", () => closeConfirm())
    }
    if (confirmModal) {
        confirmModal.addEventListener("click", (event) => {
            if (event.target === confirmModal) closeConfirm()
        })
    }
    if (confirmAccept) {
        confirmAccept.addEventListener("click", () => {
            if (!pendingForm) return
            pendingForm.dataset.confirmed = "1"
            if (typeof pendingForm.requestSubmit === "function") {
                pendingForm.requestSubmit()
            } else {
                pendingForm.submit()
            }
            closeConfirm()
        })
    }
    const bindConfirmations = (root = document) => {
        root.querySelectorAll("form[data-confirm-form]").forEach((form) => {
            if (form.dataset.confirmBound) return
            form.dataset.confirmBound = "1"
            form.addEventListener("submit", (event) => {
                if (form.dataset.confirmed === "1") return
                if (!form.reportValidity()) {
                    event.preventDefault()
                    return
                }
                event.preventDefault()
                openConfirm(form)
            })
        })
    }
    const manageModal = document.querySelector("[data-manage-modal]")
    const manageForm = manageModal ? manageModal.querySelector("form") : null
    const manageCancel = manageModal ? manageModal.querySelector("[data-manage-cancel]") : null
    const manageIdInput = manageModal ? manageModal.querySelector("[data-strategy-id-input]") : null
    const manageAvailableQuote = manageModal ? manageModal.querySelector("[data-available-quote]") : null
    const openManage = (button) => {
        if (!manageModal || !manageForm) return
        const strategyId = button.dataset.strategyId || ""
        const name = button.dataset.strategyName || "Strategy"
        const asset = button.dataset.asset || ""
        const exchangeName = button.dataset.exchangeName || ""
        const quote = button.dataset.quoteCurrency || "USDC"
        const exchangeAvailable = Number(button.dataset.exchangeAvailable || 0)
        const reduceMax = Number(button.dataset.reduceMax || 0)
        manageForm.dataset.addMax = exchangeAvailable.toString()
        manageForm.dataset.removeMax = reduceMax.toString()
        manageForm.dataset.addAvailable = formatNumber(exchangeAvailable)
        manageForm.dataset.removeAvailable = formatNumber(reduceMax)
        manageForm.dataset.strategyName = name
        manageForm.dataset.asset = asset
        manageForm.dataset.exchangeName = exchangeName
        manageForm.dataset.quoteCurrency = quote
        if (manageIdInput) manageIdInput.value = strategyId
        if (manageAvailableQuote) manageAvailableQuote.textContent = quote
        applyToggleState(manageForm, manageForm.dataset.action || "add")
        manageModal.classList.remove("hidden")
        manageModal.classList.add("flex")
    }
    const closeManage = () => {
        if (!manageModal) return
        manageModal.classList.add("hidden")
        manageModal.classList.remove("flex")
    }
    let activeView = "current"
    const equityState = {
        view: "cumulative",
        filterKey: null,
        allSeries: [],
        activeSeries: [],
        cumulativeSeries: [],
        min: 0,
        max: 0,
        dates: [],
    }
    const equityTabs = Array.from(document.querySelectorAll("[data-equity-tab]"))
    const renderEquity = () => {
        const viewSeries = equityState.view === "active" ? equityState.activeSeries : equityState.cumulativeSeries
        let displaySeries = viewSeries
        if (equityState.filterKey) {
            displaySeries = viewSeries.filter((item) => String(item.key) === String(equityState.filterKey))
            if (!displaySeries.length) displaySeries = viewSeries
        }
        renderChart({
            prefix: "equity",
            series: displaySeries,
            legendSeries: viewSeries,
            min: equityState.min,
            max: equityState.max,
            dates: equityState.dates,
            selectedKey: equityState.filterKey,
            onLegendClick: (item) => {
                if (equityState.view !== "active") return
                const key = String(item.key)
                equityState.filterKey = equityState.filterKey === key ? null : key
                renderEquity()
            },
        })
    }
    const setEquityView = (view) => {
        equityState.view = view
        if (view !== "active") equityState.filterKey = null
        equityTabs.forEach((button) => {
            const isActive = button.getAttribute("data-equity-view") === view
            button.classList.toggle("font-semibold", isActive)
            button.classList.toggle("btn-inline-manage", isActive)
        })
        renderEquity()
    }
    setupClosedTableSorting()
    equityTabs.forEach((button) => {
        button.addEventListener("click", () => {
            const view = button.getAttribute("data-equity-view") || "cumulative"
            setEquityView(view)
        })
    })
    {
        const data = dashboardData
        if (!data || data.error) {
        } else {
            const metrics = data.metrics || {}
            const setText = (id, value) => {
                const el = document.getElementById(id)
                if (el) el.textContent = value
            }
            const cumulativePnl = data.cumulative_pnl_usdc ?? 0
            const activeBalance = data.current_balance_usdc ?? metrics.current_capital_usdc ?? 0
            setText("metric-cumulative-pnl", formatSignedUsd(cumulativePnl))
            setText("metric-active-balance", formatUsd(activeBalance))
            const pnlEl = document.getElementById("metric-pnl")
            if (pnlEl) {
                const pnl = metrics.pnl_usdc || 0
                pnlEl.textContent = formatSignedUsd(pnl)
                pnlEl.classList.toggle("metric-positive", pnl > 0)
                pnlEl.classList.toggle("metric-negative", pnl < 0)
            }
            const terminatedPnlEl = document.getElementById("metric-terminated-pnl")
            if (terminatedPnlEl) {
                const pnl = data.terminated_pnl_usdc ?? 0
                terminatedPnlEl.textContent = formatSignedUsd(pnl)
                terminatedPnlEl.classList.toggle("metric-positive", pnl > 0)
                terminatedPnlEl.classList.toggle("metric-negative", pnl < 0)
            }
            document.querySelectorAll(".loading-text").forEach((el) => el.classList.remove("loading-text"))
            const allSeries = data.equity_series || []
            equityState.allSeries = allSeries
            equityState.cumulativeSeries = allSeries.filter((item) => item.key === "all")
            equityState.activeSeries = allSeries.filter((item) => item.key !== "all")
            equityState.min = data.equity_min ?? 0
            equityState.max = data.equity_max ?? 0
            equityState.dates = data.equity_dates || []
            setEquityView("cumulative")
        }
    }
    window.addEventListener("resize", () => {
        if (equityState.allSeries.length) renderEquity()
    })
    bindMaxButtons()
    bindAmountForms()
    bindSubmitFeedback()
    bindConfirmations()
    document.querySelectorAll("[data-manage-open]").forEach((button) => {
        if (button.dataset.manageBound) return
        button.dataset.manageBound = "1"
        button.addEventListener("click", () => openManage(button))
    })
    if (manageCancel) {
        manageCancel.addEventListener("click", () => closeManage())
    }
    if (manageModal) {
        manageModal.addEventListener("click", (event) => {
            if (event.target === manageModal) closeManage()
        })
    }
    const viewContainer = document.querySelector("[data-dashboard-views]")
    if (viewContainer) {
        const panels = Array.from(viewContainer.querySelectorAll("[data-view-panel]"))
        const buttons = Array.from(document.querySelectorAll("[data-view-button]"))
        const setView = (view) => {
            activeView = view
            panels.forEach((panel) => {
                panel.classList.toggle("hidden", panel.getAttribute("data-view-panel") !== view)
            })
            buttons.forEach((button) => {
                const isActive = button.getAttribute("data-view") === view
                button.classList.toggle("font-semibold", isActive)
                button.classList.toggle("bg-[#E7E1FF]", isActive)
            })
        }
        const defaultView = viewContainer.getAttribute("data-default-view") || "current"
        setView(defaultView)
        buttons.forEach((button) => {
            button.addEventListener("click", () => setView(button.getAttribute("data-view")))
        })
    }
