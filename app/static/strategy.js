    const exchangeSelect = document.getElementById("strategy-exchange-select")
    const accountSelect = document.getElementById("strategy-account-select")
    const strategyKeyInput = document.querySelector("[data-strategy-key-input]")
    const getSelectedStrategyKey = () => {
        const selectedCard = document.querySelector("[data-strategy-card].strategy-select-card-active")
        if (strategyKeyInput && strategyKeyInput.value) return strategyKeyInput.value
        return selectedCard ? selectedCard.dataset.strategyKey || "" : ""
    }
    const loadStrategyData = () => {
        const exchangeName = exchangeSelect ? exchangeSelect.value : ""
        const strategyKey = getSelectedStrategyKey()
        const params = new URLSearchParams()
        if (exchangeName) params.set("exchange_name", exchangeName)
        if (strategyKey) params.set("strategy_key", strategyKey)
        if (accountSelect && accountSelect.value) params.set("exchange_account_id", accountSelect.value)
        const query = params.toString() ? `?${params.toString()}` : ""
        return fetch(`/strategy/data${query}`)
    }
    const upper = (value) => String(value || "").toUpperCase()
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
        const exchangeName = form.dataset.exchangeName || (form.querySelector("#strategy-exchange-select") || {}).value || ""
        const asset = form.dataset.asset || (form.querySelector("[data-asset-select]") || {}).value || ""
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
    let latestBalance = 0
    let refreshLiveBalance = () => {}
    let liveBalanceRequestId = 0
    const hlpRiskNote = document.querySelector("[data-hlp-risk-note]")
    const applyHlpRiskNote = () => {
        if (!hlpRiskNote) return
        const isHlp = String(getSelectedStrategyKey() || "").toLowerCase() === "hlp"
        hlpRiskNote.classList.toggle("hidden", !isHlp)
    }
    const updateSummary = () => {
        const strategyEl = document.querySelector("[data-summary-strategy]")
        const exchangeEl = document.querySelector("[data-summary-exchange]")
        const pairEl = document.querySelector("[data-summary-pair]")
        const apyEl = document.querySelector("[data-summary-apy]")
        const selectedCard = document.querySelector("[data-strategy-card].strategy-select-card-active")
        const strategyName = selectedCard ? selectedCard.dataset.strategyName : "Strategy"
        const apy = selectedCard ? selectedCard.dataset.strategyApy : ""
        const exchangeValue = exchangeSelect ? exchangeSelect.value : ""
        const accountLabel = accountSelect ? (accountSelect.selectedOptions[0] || {}).textContent || "" : ""
        const pairValue = (document.querySelector("[data-asset-select]") || {}).value || ""
        if (strategyEl) strategyEl.textContent = strategyName || "--"
        if (exchangeEl) {
            const accountText = accountLabel ? ` · ${accountLabel}` : ""
            exchangeEl.textContent = exchangeValue ? `${upper(exchangeValue)}${accountText}` : "--"
        }
        if (pairEl) pairEl.textContent = pairValue ? upper(pairValue) : "--"
        if (apyEl) apyEl.textContent = apy || "--"
    }
    const syncExchangeOptions = (data) => {
        if (!exchangeSelect) return
        const exchanges = Array.isArray(data.exchanges) ? data.exchanges.filter(Boolean) : []
        const previousValue = exchangeSelect.value
        exchangeSelect.innerHTML = ""
        if (!exchanges.length) {
            exchangeSelect.disabled = true
            const option = document.createElement("option")
            option.value = ""
            option.textContent = "--"
            exchangeSelect.appendChild(option)
            exchangeSelect.value = ""
            return
        }
        exchangeSelect.disabled = false
        for (const exchangeName of exchanges) {
            const option = document.createElement("option")
            option.value = exchangeName
            option.textContent = upper(exchangeName)
            exchangeSelect.appendChild(option)
        }
        const selectedValue = data.exchange_name || previousValue
        const hasSelectedValue = Array.from(exchangeSelect.options).some((option) => option.value === selectedValue)
        exchangeSelect.value = hasSelectedValue ? selectedValue : exchangeSelect.options[0].value
    }
    const syncAccountOptions = (data) => {
        if (!accountSelect) return
        const accounts = Array.isArray(data.exchange_accounts) ? data.exchange_accounts : []
        const previousValue = accountSelect.value
        accountSelect.innerHTML = ""
        if (!accounts.length) {
            accountSelect.disabled = true
            const option = document.createElement("option")
            option.value = ""
            option.textContent = "--"
            accountSelect.appendChild(option)
            accountSelect.value = ""
            return
        }
        accountSelect.disabled = false
        for (const account of accounts) {
            if (!account || !account.id) continue
            const option = document.createElement("option")
            option.value = String(account.id)
            option.textContent = account.label || `Account ${account.id}`
            accountSelect.appendChild(option)
        }
        const selectedValue = data.exchange_account_id ? String(data.exchange_account_id) : previousValue
        const hasSelectedValue = Array.from(accountSelect.options).some((option) => option.value === selectedValue)
        accountSelect.value = hasSelectedValue ? selectedValue : accountSelect.options[0].value
    }
    const updateAllocation = () => {
        const input = document.querySelector("[data-capital-input]")
        const donut = document.querySelector("[data-allocation-donut]")
        const percentEl = document.querySelector("[data-allocation-percent]")
        const value = Number(input ? input.value : 0)
        const percent = latestBalance > 0 ? Math.min(100, Math.max(0, (value / latestBalance) * 100)) : 0
        if (donut) donut.style.setProperty("--alloc-percent", `${percent}%`)
        if (percentEl) percentEl.textContent = `${Math.round(percent)}%`
    }
    const fetchLiveBalance = () => {
        const exchangeAccountId = accountSelect ? accountSelect.value : ""
        const strategyKey = getSelectedStrategyKey()
        if (!exchangeAccountId || !strategyKey) return
        const requestId = ++liveBalanceRequestId
        document.querySelectorAll("[data-usdc-balance]").forEach((el) => {
            el.textContent = "Loading..."
        })
        const params = new URLSearchParams()
        params.set("exchange_account_id", exchangeAccountId)
        params.set("strategy_key", strategyKey)
        fetch(`/strategy/live-balance?${params.toString()}`)
            .then((res) => res.json())
            .then((data) => {
                if (requestId !== liveBalanceRequestId) return
                const balance = Number(data && data.balance ? data.balance : 0)
                latestBalance = balance
                document.querySelectorAll("[data-usdc-balance]").forEach((el) => {
                    el.textContent = balance.toFixed(2)
                })
                document.querySelectorAll("[data-usdc-max]").forEach((el) => {
                    el.setAttribute("max", balance.toString())
                })
                const quoteCurrency = String((data && data.quote_currency) || "").trim() || "USD"
                document.querySelectorAll("[data-quote-currency]").forEach((el) => {
                    el.textContent = quoteCurrency
                })
                updateAllocation()
            })
            .catch(() => {
                if (requestId !== liveBalanceRequestId) return
                const balance = Number(latestBalance || 0)
                document.querySelectorAll("[data-usdc-balance]").forEach((el) => {
                    el.textContent = balance.toFixed(2)
                })
                updateAllocation()
            })
    }
    const applyStrategyData = (data) => {
        if (!data || data.error) return
        const loadingEl = document.getElementById("strategy-loading")
        if (loadingEl) loadingEl.classList.add("hidden")
        const noCreds = document.getElementById("strategy-no-credentials")
        const form = document.getElementById("strategy-form")
        if (data.has_credentials) {
            if (form) form.classList.remove("hidden")
            if (noCreds) noCreds.classList.add("hidden")
        } else {
            if (noCreds) noCreds.classList.remove("hidden")
            if (form) form.classList.add("hidden")
        }
        const quoteCurrency = String(data.quote_currency || "").trim() || "USD"
        document.querySelectorAll("[data-quote-currency]").forEach((el) => {
            el.textContent = quoteCurrency
        })
        const balance = Number(data.usdc_balance || 0)
        latestBalance = balance
        document.querySelectorAll("[data-usdc-balance]").forEach((el) => {
            el.textContent = balance.toFixed(2)
        })
        document.querySelectorAll("[data-usdc-max]").forEach((el) => {
            el.setAttribute("max", balance.toString())
        })
        document.querySelectorAll(".loading-text").forEach((el) => el.classList.remove("loading-text"))
        syncExchangeOptions(data)
        syncAccountOptions(data)

        const assetSelect = document.querySelector("[data-asset-select]")
        if (assetSelect) {
            const allowed = Array.isArray(data.allowed_assets) ? data.allowed_assets.filter(Boolean) : []
            const prev = assetSelect.value
            if (allowed.length > 0) {
                assetSelect.disabled = false
                assetSelect.innerHTML = allowed.map((a) => `<option value="${a}">${a}</option>`).join("")
                assetSelect.value = allowed.includes(prev) ? prev : allowed[0]
            } else {
                assetSelect.disabled = true
                assetSelect.innerHTML = `<option value="" selected disabled>--</option>`
            }
        }
        applyHlpRiskNote()
        updateSummary()
        updateAllocation()
        refreshLiveBalance()

        const minCapital = Number(data.min_capital_usd)
        document.querySelectorAll("[data-min-capital-input]").forEach((input) => {
            if (Number.isFinite(minCapital)) {
                input.setAttribute("min", minCapital.toString())
                input.dataset.minCapital = minCapital.toString()
            }
            input.dataset.quoteCurrency = quoteCurrency
            if (!input.dataset.minValidation) {
                input.addEventListener("input", () => input.setCustomValidity(""))
                input.addEventListener("invalid", () => {
                    const minValue = input.getAttribute("min")
                    if (minValue && input.validity.rangeUnderflow) {
                        const currency = input.dataset.quoteCurrency || "USD"
                        input.setCustomValidity(`Value must be at least ${minValue} ${currency}.`)
                    } else {
                        input.setCustomValidity("")
                    }
                })
                input.dataset.minValidation = "1"
            }
        })
    }
    let strategyDataRequestId = 0
    const refreshStrategyData = () => {
        const requestId = ++strategyDataRequestId
        loadStrategyData()
            .then((res) => res.json())
            .then((data) => {
                if (requestId !== strategyDataRequestId) return
                applyStrategyData(data)
            })
    }
    refreshStrategyData()
    if (exchangeSelect) {
        exchangeSelect.addEventListener("change", refreshStrategyData)
    }
    if (accountSelect) {
        accountSelect.addEventListener("change", refreshStrategyData)
    }
    bindMaxButtons()
    bindSubmitFeedback()
    bindConfirmations()
    const wizard = document.querySelector("[data-strategy-wizard]")
    if (wizard) {
        const steps = Array.from(wizard.querySelectorAll("[data-wizard-step]"))
        const ticks = Array.from(document.querySelectorAll("[data-wizard-tick]"))
        const backBtn = wizard.querySelector("[data-wizard-back]")
        const nextBtn = wizard.querySelector("[data-wizard-next]")
        const submitBtn = wizard.querySelector("[data-wizard-submit]")
        let currentStep = 0
        const setStep = (index) => {
            currentStep = Math.max(0, Math.min(index, steps.length - 1))
            steps.forEach((step, i) => {
                const isVisible = i === currentStep
                step.classList.toggle("hidden", !isVisible)
                step.style.display = isVisible ? "" : "none"
            })
            ticks.forEach((tick, i) => tick.classList.toggle("wizard-progress-bar-active", i === currentStep))
            if (backBtn) {
                const isDisabled = currentStep === 0
                backBtn.disabled = isDisabled
                backBtn.classList.toggle("opacity-50", isDisabled)
            }
            if (nextBtn) {
                const isLast = currentStep === steps.length - 1
                nextBtn.classList.toggle("hidden", isLast)
                nextBtn.style.display = isLast ? "none" : ""
            }
            if (submitBtn) {
                const isLast = currentStep === steps.length - 1
                submitBtn.classList.toggle("hidden", !isLast)
                submitBtn.style.display = isLast ? "" : "none"
            }
            if (currentStep === steps.length - 1) fetchLiveBalance()
        }
        refreshLiveBalance = () => {
            if (currentStep === steps.length - 1) fetchLiveBalance()
        }
        const validateStep = (index) => {
            if (index === 0 && !getSelectedStrategyKey()) return false
            const step = steps[index]
            if (!step) return true
            const inputs = Array.from(step.querySelectorAll("input, select")).filter((el) => !el.disabled)
            for (const input of inputs) {
                if (!input.checkValidity()) {
                    input.reportValidity()
                    return false
                }
            }
            return true
        }
        if (nextBtn) {
            nextBtn.addEventListener("click", () => {
                if (!validateStep(currentStep)) return
                setStep(currentStep + 1)
            })
        }
        if (backBtn) backBtn.addEventListener("click", () => setStep(currentStep - 1))
        setStep(0)
    }
    const strategyCards = Array.from(document.querySelectorAll("[data-strategy-card]"))
    const activateCard = (card) => {
        if (!card) return
        strategyCards.forEach((item) => item.classList.toggle("strategy-select-card-active", item === card))
        const form = document.getElementById("strategy-form")
        if (strategyKeyInput && card.dataset.strategyKey) strategyKeyInput.value = card.dataset.strategyKey
        if (form) form.dataset.strategyName = card.dataset.strategyName || "Strategy"
        applyHlpRiskNote()
        updateSummary()
    }
    strategyCards.forEach((card) => {
        card.addEventListener("click", () => {
            activateCard(card)
            refreshStrategyData()
        })
    })
    if (strategyCards.length) {
        const selectedKey = getSelectedStrategyKey()
        const activeCard = strategyCards.find((card) => card.dataset.strategyKey === selectedKey) || strategyCards.find((card) => card.classList.contains("strategy-select-card-active"))
        if (activeCard) activateCard(activeCard)
    }
    applyHlpRiskNote()
    const assetSelect = document.querySelector("[data-asset-select]")
    if (assetSelect) assetSelect.addEventListener("change", updateSummary)
    if (exchangeSelect) exchangeSelect.addEventListener("change", updateSummary)
    if (accountSelect) accountSelect.addEventListener("change", updateSummary)
    const capitalInput = document.querySelector("[data-capital-input]")
    if (capitalInput) capitalInput.addEventListener("input", updateAllocation)
